"""Compare node: retriever-backed gap analysis with role/level filtering."""

import math

from agent.state import AgentState, MatchedNode
from rag.retriever import create_retriever
from rag.embeddings import get_embedding_service
from roadmap.models import RoadmapNode


def _normalize_for_match(text: str) -> str:
    """Normalize text for case-insensitive matching."""
    return text.lower().strip()


def _build_alias_set(node: RoadmapNode) -> set[str]:
    """Build a set of normalized names and aliases for a node."""
    alias_set = {_normalize_for_match(node.name)}
    for alias in node.aliases:
        alias_set.add(_normalize_for_match(alias))
    return alias_set


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def _build_experience_texts(state: AgentState) -> list[str]:
    """Collect competency names and evidence texts from experience for similarity matching."""
    texts: list[str] = []
    for comp in state.known_competencies:
        texts.append(comp.name)
        if comp.evidence:
            texts.append(comp.evidence)
    for entail in getattr(state, "inferred_entailments", []):
        texts.append(entail.get("name", ""))
        texts.append(entail.get("because", ""))
    return texts


async def compare_node(state: AgentState) -> AgentState:
    """Retrieve roadmap nodes for extracted skills and classify as covered or gap.

    Steps:
        1. Build search queries from extracted skills, technologies, domain_areas,
           known_competencies, and focus_areas.
        2. Call the RoadmapRetriever with TARGET role and level filters.
        3. Deduplicate results by node id.
        4. Classify each unique node:
           - *covered*: node name/aliases match user's explicit skills/techs
           - *known_via_experience*: high-confidence competency match or
             embedding-similarity match with experience evidence
           - else *gap*
        5. Store MatchedNode objects with reason and evidence in state.matched_nodes.
    """
    if state.extracted_skills is None or state.career_frame is None:
        state.matched_nodes = []
        return state

    # Build a case-insensitive set of every skill/tech/domain the user explicitly has
    user_skills: set[str] = set()
    for category in ("skills", "technologies", "domain_areas"):
        for item in state.extracted_skills.get(category, []):
            if isinstance(item, str):
                user_skills.add(_normalize_for_match(item))

    # Build a mapping of competency names to evidence
    competency_map: dict[str, tuple[str, str]] = {}  # name -> (evidence, source)
    for comp in state.known_competencies:
        norm_name = _normalize_for_match(comp.name)
        if comp.confidence >= 0.5:  # Only use medium+ confidence competencies
            competency_map[norm_name] = (comp.evidence, comp.source)

    # Determine target role and level for filtering
    target_role = state.career_frame.target_role
    target_level = state.career_frame.target_level

    # Fallback: if no target set, use current
    if not target_role:
        target_role = state.career_frame.current_role
    if not target_level:
        target_level = state.career_frame.current_level

    retriever = create_retriever()
    seen_ids: set[str] = set()
    matched_nodes: list[MatchedNode] = []
    # Store retrieved nodes for embedding-similarity fallback
    retrieved_nodes: dict[str, RoadmapNode] = {}

    # Collect all query terms
    query_terms: set[str] = set()
    for category in ("skills", "technologies", "domain_areas"):
        for item in state.extracted_skills.get(category, []):
            if isinstance(item, str):
                query_terms.add(item)

    # Add focus areas with higher priority (query them too)
    for focus in state.career_frame.focus_areas:
        query_terms.add(focus)

    # Add competency names as queries
    for comp in state.known_competencies:
        query_terms.add(comp.name)

    for item in query_terms:
        if not isinstance(item, str):
            continue

        try:
            # KEY CHANGE: Pass role and level filters to retriever
            results: list[RoadmapNode] = await retriever.retrieve(
                item,
                role=target_role,
                level=target_level,
                top_k=5,
            )
        except Exception as exc:
            state.errors.append(
                f"Retrieval failed for '{item}' ({type(exc).__name__})"
            )
            continue

        for node in results:
            if node.id in seen_ids:
                continue
            seen_ids.add(node.id)
            retrieved_nodes[node.id] = node

            # Build node alias set for matching
            node_aliases = _build_alias_set(node)

            # Classification logic
            status = "gap"
            reason = None
            evidence = None

            # Check 1: Exact match in user's explicit skills
            if node_aliases & user_skills:
                status = "covered"
                reason = "Listado explicitamente em habilidades/tecnologias"
            else:
                # Check 2: Match through known competencies (experience-based)
                for alias in node_aliases:
                    if alias in competency_map:
                        comp_evidence, comp_source = competency_map[alias]
                        if comp_source in ("experience", "entailed"):
                            status = "known_via_experience"
                            reason = "Demonstrado por meio de experiência profissional"
                            evidence = comp_evidence
                            break

            matched_nodes.append(
                MatchedNode(
                    id=node.id,
                    status=status,
                    reason=reason,
                    evidence=evidence,
                )
            )

    # Third pass: embedding-similarity fallback for gap nodes
    gap_nodes = [m for m in matched_nodes if m.status == "gap"]
    if gap_nodes and retrieved_nodes:
        gap_node_names = [retrieved_nodes[nid].name for nid in gap_nodes if nid in retrieved_nodes]
        experience_texts = _build_experience_texts(state)

        # Avoid embedding nothing
        if gap_node_names and experience_texts:
            try:
                embedding_service = get_embedding_service()
                all_texts = experience_texts + gap_node_names
                embeddings = await embedding_service.embed(all_texts)
            except Exception:
                embeddings = []

            n_exp = len(experience_texts)
            exp_vectors = embeddings[:n_exp] if len(embeddings) >= n_exp else []
            node_vectors = embeddings[n_exp:] if len(embeddings) > n_exp else []

            # Map each gap node to its vector
            node_vec_by_id: dict[str, list[float]] = {}
            gap_ids = [m.id for m in gap_nodes]
            for i, nid in enumerate(gap_ids):
                if i < len(node_vectors):
                    node_vec_by_id[nid] = node_vectors[i]

            # Try similarity for each gap node against each experience text
            for m in gap_nodes:
                nid = m.id
                node_vec = node_vec_by_id.get(nid)
                if node_vec is None:
                    continue

                best_sim = 0.0
                best_evidence = ""
                for i, exp_text in enumerate(experience_texts):
                    if i < len(exp_vectors):
                        sim = _cosine_similarity(node_vec, exp_vectors[i])
                        if sim > best_sim:
                            best_sim = sim
                            best_evidence = exp_text

                if best_sim >= 0.75:
                    m.status = "known_via_experience"
                    m.reason = (
                        f"Demonstrado por meio de experiência profissional"
                        f" (similaridade: {best_sim:.2f})"
                    )
                    m.evidence = best_evidence[:200]

    state.matched_nodes = matched_nodes
    return state