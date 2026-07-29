# API Problem: analyze pipeline stalls or produces no feedback

## Symptom

After submitting the CV form on `/home`, the browser navigates to `/analyze/[id]` and shows a spinning "Analyzing your CV…" message indefinitely (up to ~60 s). When events eventually arrive they always appear with `node: "unknown"`, and the pipeline often never reaches the final result.

## Root Cause

### 1. Wrong model in OpenAI chat call

`apps/api/src/agent/nodes/analyze.py:76`

```python
payload = {
    "model": settings.embedding_model,  # "text-embedding-3-small"
    ...
}
```

`text-embedding-3-small` is an **embedding** model, not a chat model.  
OpenAI rejects it with HTTP 4xx, but `httpx.AsyncClient(timeout=60.0)` at line 82 blocks for **60 seconds** before the exception surfaces. The `except` block then catches the error and falls back to `_mock_extraction`, but the artificial 60 s delay makes the pipeline feel broken.

**Fix:**  
- Add a dedicated `settings.chat_model` (e.g. `gpt-4o-mini` or `gpt-4o`) in `apps/api/src/app/config.py`.
- Replace `settings.embedding_model` with `settings.chat_model` in the payload.
- Restore a reasonable timeout (10–15 s).

### 2. LangGraph `astream` event keys are misread

`apps/api/src/agent/graph.py:60-67`

```python
async for event in graph.astream(initial_state):
    node_name = event.get("node", "unknown")        # ← wrong key
    yield { "node": node_name, "payload": event }
```

LangGraph 1.x `astream()` (default mode `"values"`) yields the full state dict **keyed by node name**, not a dict with a `"node"` key.  
`event.get("node")` always returns `None`, so every event is reported as `"unknown"`.

**Fix:**  
Use `astream(initial_state)` and extract the node name from the yielded key:

```python
async for node_name, state in graph.astream(initial_state, stream_mode="updates"):
    yield { "node": node_name, "payload": state }
```

### 3. No progress feedback during async nodes

Because `analyze_node` is the first `async` node in the sequential pipeline, every earlier node (ingest, strip) finishes instantly, then the generator blocks at `analyze_node` for 60 s. The frontend sees no events during that window and shows only the "connecting" spinner.

The user has no way to tell whether the system is working, waiting for an LLM, or broken.

**Potential mitigations:**  
- Emit a `"connecting"` / `"queued"` event before starting the pipeline.
- Split the LLM call into a background task and poll its progress separately.
- At minimum, reduce the HTTPX timeout so failure is surfaced in seconds, not a minute.

### 4. Compare node may further stall at Qdrant

`compare_node` calls `retriever.retrieve(item, top_k=5)` for every extracted skill/technology/domain. If the Qdrant collection is empty (seeder may not have completed before the first request), each retrieve call returns zero results quickly — no extra delay.  

However, if Qdrant is unreachable or the collection does not exist, `retrieve` could throw an exception that propagates unhandled out of `compare_node`, aborting the entire stream with an internal 500 error and no user-visible message.

**Fix:**  
Wrap the retriever call in a try/except and log + skip on failure so a transient Qdrant error does not kill the pipeline.

### 5. `settings.embedding_model` is overloaded

`apps/api/src/app/config.py` uses a single `EMBEDDING_MODEL` env var for both embedding generation (Qdrant vector generation) and chat completions (OpenAI). These are different model families and need separate configuration.

**Fix:**  
Add a new `LLM_MODEL` env var (default `gpt-4o-mini`), use it for chat, and keep `EMBEDDING_MODEL` for embeddings.

---

## Quick reference

| File | Line(s) | Issue |
|---|---|---|
| `apps/api/src/agent/nodes/analyze.py` | 70–88 | Uses `embedding_model` instead of a chat model; 60 s timeout |
| `apps/api/src/agent/graph.py` | 60–67 | Misreads LangGraph `astream` event keys |
| `apps/api/src/app/config.py` | missing | No dedicated `llm_model` setting |
| `apps/api/src/agent/nodes/compare.py` | 41 | Unhandled exception on Qdrant failure |
