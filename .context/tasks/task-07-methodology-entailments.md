# Task 7 — Enhance Methodology/Practice Reasoning in Inferred Entailments

## Goal Reference

- **Goal:** Make the CV analysis infer **methodologies and practices** from experience descriptions (not just technologies), so the deduced competencies reflect what the user implicitly knows through their approach and context.
- **Depends on:** None (standalone prompt change)
- **Depended on by:** Task 9 (tests for entailment integration in matching)

## Problem

The `_ANALYZE_SYSTEM_PROMPT` in `analyze.py` (lines 14–89) has an `inferred_entailments` section (lines 51–57) with rules and examples that are **entirely technology-implication oriented**:

```
"inferred_entailments": [
  {
    "name": "skill/knowledge implied by their work",
    "because": "explanation: they did X so they must know Y"
  }
]
```

The only non-abstract example in the prompt (line 62):
```python
# Mark source as "entailed" when logically required
# (e.g., "deployed k8s production" → must know Docker, cloud, CI/CD)
```

This teaches the model to think only about **tech → tech** entailments (K8s → Docker → Cloud). It never instructs the model to reason about **practice → methodology** entailments:

- "Optimized RAG by 30% via embedding cache" → implies understanding of **performance optimization patterns in data-intensive workflows**, **caching strategies**, and **observability for latency measurement**.
- "Created microservices with complex high-availability API integrations" → implies understanding of **distributed systems design**, **resilience patterns** (circuit breakers, retries), **caching**, and **asynchronous communication**.

These implicit competencies are exactly what the roadmap nodes cover (e.g., roadmap has senior nodes for "Arquiteturas resilientes com circuit breakers, rate limiting, cache" and "Orquestração de pipelines com filas, workers, eventos, retries, timeouts"), but the LLM never generates them as `inferred_entailments`, so `compare.py` never matches them.

## Affected Files

- `apps/api/src/agent/nodes/analyze.py` — rewrite the `inferred_entailments` rules in `_ANALYZE_SYSTEM_PROMPT`

## Approach

### Step 1 — Rewrite the `inferred_entailments` section of the prompt

Replace the existing technology-centric guidance at lines 51–57 with a richer methodology-centric version. The new guidance should include:

**Explicit directive:**
```
RULES for inferred_entailments:
- Infer METHODOLOGIES and PRACTICES from described work, not just adjacent technologies.
- If the user describes WHAT they built, infer WHAT PRACTICES/KNOWLEDGE that implies.
- Focus on: performance optimization, reliability/resilience, distributed systems,
  caching strategies, async/message-driven patterns, monitoring/observability,
  CI/CD pipelines, architectural decision-making, agent orchestration/hand-offs,
  security/guardrails, testing strategies, team processes, scalability patterns.
```

**Worked examples (to replace the single k8s example):**

```
EXAMPLES of methodology entailment:
1. User: "Optimized a RAG system over 30% by implementing cache on embeddings and agentic RAG"
   → Entailment: {name: "Otimização de performance em workflows de dados",
      because: "Otimização de cache em embeddings e fluxos RAG demonstra entendimento de
                latência, throughput e estratégias de caching em sistemas de dados intensivos"}
   → Entailment: {name: "Orquestração de agentes e hand-offs",
      because: "Implementação de agentic RAG implica conhecimento de orquestração
                multi-etapa, ferramentas, hand-offs entre agentes e controle de fluxo"}

2. User: "Created microservices with complex API integrations in high availability"
   → Entailment: {name: "Arquiteturas resilientes e tolerância a falhas",
      because: "Trabalhar com integrações complexas em alta disponibilidade implica
                conhecimento de circuit breakers, retries, timeouts, degradação
                controlada e isolamento de falhas"}
   → Entailment: {name: "Sistemas distribuídos e cache",
      because: "Microserviços com alta disponibilidade exigem entendimento de cache
                distribuído, consistência eventual, balanceamento de carga e
                comunicação assíncrona entre serviços"}

3. User: "Led migration of monolith to microservices on AWS with zero downtime"
   → Entailment: {name: "Estratégias de migração e deploy",
      because: "Migração zero-downtime implica conhecimento de blue-green deployment,
                canary releases, feature flags, rollback planning e migração incremental"}
   → Entailment: {name: "Otimização de custo vs performance em cloud",
      because: "Migração para AWS com zero downtime implica decisões de arquitetura
                que balanceiam custo de infraestrutura com requisitos de performance"}
```

**Continued guidance (existing rules to keep/merge):**
- Keep the `"source": "entailed"` and `"confidence": 0.6` pattern from the existing code.
- Keep the Portuguese output rule — all entailment names and `because` text must be in Portuguese (Brazilian).
- Keep the "map to Portuguese roadmap equivalents" instruction — the model should name entailments using canonical terminology from the roadmap (e.g., "Otimização de performance em workflows de dados" not "Data perf optimization").
- Add: "Prefer methodology/practice names over technology names. Inventing a technology that isn't mentioned is worse than inferring a practice that is clearly implied."

### Step 2 — Preserve the existing `known_competencies` rules

The existing rules at lines 59–64 (evidence from experience bullets, source markers) stay unchanged. The new methodology focus is additive, not replacive.

### Step 3 — No mock fallback changes

Per decision, the no-LLK `_mock_extraction` fallback is left untouched — it will not generate methodology entailments. This is acceptable because:
- Without an LLM API key, the system already falls back to deterministic behavior with limited capabilities.
- The `inferred_entailments` in the mock (lines 201–206) only do basic tech-to-tech chaining (Docker → Containerization, K8s → Docker, K8s → Cloud). This is a known limitation of the fallback.

### Step 4 — Data audit recommendation

Current roadmap data (`data/roadmaps/*/levels/*/*.json`) uses empty `aliases: []` for most nodes. Methodology concepts do exist in node names (e.g., senior group-16 has "Arquiteturas resilientes com circuit breakers, rate limiting, cache, degradação controlada e isolamento de falhas"), but without aliases the embedding-similarity fallback in `compare.py` bears the burden of matching inferred entailments to roadmap nodes.

Consider adding canonical aliases to key methodology nodes after this task is verified, so exact-match (via `competency_map`) can surface them without relying on embedding similarity.

## Acceptance Criteria

1. Given a CV with "Optimizei um sistema RAG em 30% implementando cache em embeddings e agentic RAG", the LLM generates at least one `inferred_entailment` about performance optimization/caching methodology and at least one about agent orchestration.
2. Given a CV with "Criei microserviços com integrações complexas de API em alta disponibilidade", the LLM generates at least one entailment about resilience/distributed systems methodology.
3. All entailments are in Portuguese (Brazilian).
4. Entailment `source` is `"entailed"`, confidence is `0.6`.
5. No regression: the LLM still extracts technologies, skills, known_competencies, and explicit tech-to-tech entailments as before.

## Dependencies

- None (standalone prompt change).
- Recommended follow-up: Data audit to add aliases to methodology roadmap nodes (see Step 4).
