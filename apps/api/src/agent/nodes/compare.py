"""Compare node: classify all target role+level nodes for gap analysis."""

from agent.state import AgentState, MatchedNode
from rag.embeddings import get_embedding_service
from roadmap.index import RoadmapIndex
from roadmap.models import CareerLevel, RoadmapNode, RoadmapRole


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


def _classify_node(
    node: RoadmapNode,
    user_skills: set[str],
    competency_map: dict[str, tuple[str, str]],
) -> tuple[str, str | None, str | None]:
    """Classify a single node as covered / known_via_experience / gap."""
    node_aliases = _build_alias_set(node)

    # Check 1: Exact match in user's explicit skills
    if node_aliases & user_skills:
        return "covered", "Listado explicitamente em habilidades/tecnologias", None

    # Check 2: Match through known competencies (experience-based)
    for alias in node_aliases:
        if alias in competency_map:
            comp_evidence, comp_source = competency_map[alias]
            if comp_source in ("experience", "entailed"):
                return (
                    "known_via_experience",
                    "Demonstrado por meio de experiência profissional",
                    comp_evidence,
                )

    return "gap", None, None


def compare_node(index: RoadmapIndex):
    """Returns a LangGraph node function with the roadmap index injected.

    Classifies ALL target role+level nodes as covered, known_via_experience, or gap.
    """

    async def _node(state: AgentState) -> AgentState:
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
        competency_map: dict[str, tuple[str, str]] = {}
        for comp in state.known_competencies:
            norm_name = _normalize_for_match(comp.name)
            if comp.confidence >= 0.5:
                competency_map[norm_name] = (comp.evidence, comp.source)

        # Determine target role and level for filtering
        target_role = state.career_frame.target_role
        target_level = state.career_frame.target_level
        current_level = state.career_frame.current_level

        # Fallback: if no target set, use current
        if not target_role:
            target_role = state.career_frame.current_role
        if not target_level:
            target_level = state.career_frame.current_level
        if not current_level:
            current_level = target_level

        # Guard (role isolation): only operate within a single known role.
        # A professional stays on their current path unless an explicit switch
        # was extracted; an unknown/absent role must never fall back to a
        # role-agnostic query (which would leak cross-role nodes).
        try:
            role_slug = RoadmapRole(target_role)
        except ValueError:
            state.errors.append(
                f"Unknown role '{target_role}'; cannot build a roadmap."
            )
            state.matched_nodes = []
            return state

        # Build focus tokens from career frame
        focus_tokens: set[str] = set()
        if state.career_frame and state.career_frame.focus_areas:
            for phrase in state.career_frame.focus_areas:
                for token in phrase.lower().split():
                    focus_tokens.add(token)

        # Aggregate nodes from current level through target level (inclusive)
        if target_level == current_level:
            target_nodes = index.by_role_level(role_slug, target_level)
        else:
            target_nodes = index.by_role_level_range(
                role_slug, current_level, target_level
            )

        # Role isolation: if the single role has no nodes in this range, return
        # an empty result rather than pulling cross-role nodes via a
        # role-agnostic level-range fallback.
        if not target_nodes:
            state.matched_nodes = []
            return state

        # Supplement: focus-matched nodes from junior through current level
        if focus_tokens and current_level and current_level != CareerLevel.junior:
            base_nodes = index.by_role_level_range_focus_filtered(
                role_slug,
                CareerLevel.junior,
                current_level,
                focus_tokens,
            )
            existing_ids = {n.id for n in target_nodes}
            for node in base_nodes:
                if node.id not in existing_ids:
                    target_nodes.append(node)
                    existing_ids.add(node.id)

        # Build experience texts for embedding-similarity fallback
        experience_texts = _build_experience_texts(state)
        exp_vectors: list[list[float]] = []
        if experience_texts:
            try:
                embedding_service = get_embedding_service()
                all_embeddings = await embedding_service.embed(experience_texts)
                exp_vectors = all_embeddings
            except Exception:
                exp_vectors = []

        seen_ids: set[str] = set()
        matched_nodes: list[MatchedNode] = []
        pending: list[tuple[RoadmapNode, str | None, str | None]] = []

        for node in target_nodes:
            if node.id in seen_ids:
                continue
            seen_ids.add(node.id)

            status, reason, evidence = _classify_node(
                node, user_skills, competency_map
            )

            if status == "gap":
                pending.append((node, reason, evidence))
            else:
                matched_nodes.append(
                    MatchedNode(id=node.id, status=status, reason=reason, evidence=evidence)
                )

        # Check 3: Embedding-similarity fallback, batched in ONE call for depth-aware tiers.
        if pending and exp_vectors:
            try:
                embedding_service = get_embedding_service()
                node_embeddings = await embedding_service.embed([n.name for n, _, _ in pending])
                if node_embeddings:
                    for (node, reason, evidence), node_vec in zip(pending, node_embeddings):
                        best_sim = 0.0
                        best_evidence = ""
                        for i, exp_text in enumerate(experience_texts):
                            if i < len(exp_vectors):
                                sim = _cosine_similarity(node_vec, exp_vectors[i])
                                if sim > best_sim:
                                    best_sim = sim
                                    best_evidence = exp_text

                        if best_sim >= 0.82:
                            matched_nodes.append(
                                MatchedNode(
                                    id=node.id,
                                    status="known_via_experience",
                                    reason=(
                                        "Demonstrado por meio de experiência profissional"
                                        f" (similaridade: {best_sim:.2f})"
                                    ),
                                    evidence=best_evidence[:200],
                                    confidence=best_sim,
                                )
                            )
                        elif best_sim >= 0.60:
                            # Same topic, unclear depth -> defer to depth_filter LLM adjudication
                            matched_nodes.append(
                                MatchedNode(
                                    id=node.id,
                                    status="gap",
                                    reason=(
                                        "Tópico relacionado à experiência, profundidade a confirmar"
                                    ),
                                    evidence=best_evidence[:200],
                                    confidence=best_sim,
                                    depth_candidate=True,
                                )
                            )
                        else:
                            matched_nodes.append(
                                MatchedNode(id=node.id, status="gap", reason=reason, evidence=evidence)
                            )
            except Exception:
                for node, reason, evidence in pending:
                    matched_nodes.append(
                        MatchedNode(id=node.id, status="gap", reason=reason, evidence=evidence)
                    )
        else:
            for node, reason, evidence in pending:
                matched_nodes.append(
                    MatchedNode(id=node.id, status="gap", reason=reason, evidence=evidence)
                )

        state.matched_nodes = matched_nodes
        return state

    return _node