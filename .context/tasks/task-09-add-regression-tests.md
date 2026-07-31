# Task 9 — Add Regression and Unit Tests for All Four Fixes

## Goal Reference

- **Goal:** Ensure all four fixes (level-range scoring, alias-aware focus matching, methodology entailment prompt, and 25-item cap) are covered by automated tests. Fix existing tests that encode the buggy behavior.
- **Depends on:** Tasks 5, 6, 7, 8 (all implementation must be complete before tests can pass)
- **Depended on by:** None (test task)

## Problem

The existing test suite has gaps and one test that explicitly asserts the buggy behavior:

1. `apps/api/tests/test_score.py:102-115` (`test_excludes_nodes_from_other_level`) asserts that nodes from non-target levels are **excluded from scoring**. With Task 5, nodes from the full current→target level range should be **included**. This test must be rewritten.

2. There are no tests for `RoadmapIndex.by_role_level_range`.
3. There are no tests for `_prioritize_gaps` with multi-word focus phrases or alias matching.
4. There is no test asserting the roadmap cap value (20 or 25).
5. There is no test verifying that the `_ANALYZE_SYSTEM_PROMPT` contains methodology reasoning instructions (basic string-presence smoke test — the actual LLM output cannot be tested without an API key).

## Affected Files

- `apps/api/tests/test_score.py` — update existing tests, add new test classes
- `apps/api/tests/test_roadmap.py` — new file (or extend an existing test file) for index and prioritization tests
- `apps/api/src/roadmap/index.py` — ensure `by_role_level_range` is importable (already public)
- `apps/api/src/agent/nodes/roadmap_select.py` — ensure `_prioritize_gaps` is importable for unit testing

## Approach

### Test Group 1 — `RoadmapIndex.by_role_level_range` (new, in `tests/test_roadmap.py`)

```python
import pytest
from roadmap.models import CareerLevel, RoadmapNode, RoadmapRole
from roadmap.index import RoadmapIndex


def _make_node(id: str, role: RoadmapRole, level: CareerLevel, importance: int = 50):
    return RoadmapNode(
        id=id,
        name=f"Node {id}",
        type="skill",
        category="Test",
        description="",
        level=level,
        importance=importance,
        estimated_hours=10,
        aliases=[],
        role=role,
    )


class TestByRoleLevelRange:
    def test_single_level_range(self):
        """from_level == to_level returns same as by_role_level."""
        nodes = [
            _make_node("n1", RoadmapRole.ai_engineer, CareerLevel.senior),
            _make_node("n2", RoadmapRole.ai_engineer, CareerLevel.senior),
        ]
        index = RoadmapIndex(nodes)
        result = index.by_role_level_range(
            RoadmapRole.ai_engineer, CareerLevel.senior, CareerLevel.senior
        )
        assert len(result) == 2

    def test_two_level_range(self):
        nodes = [
            _make_node("n1", RoadmapRole.ai_engineer, CareerLevel.mid),
            _make_node("n2", RoadmapRole.ai_engineer, CareerLevel.senior),
        ]
        index = RoadmapIndex(nodes)
        result = index.by_role_level_range(
            RoadmapRole.ai_engineer, CareerLevel.mid, CareerLevel.senior
        )
        assert len(result) == 2

    def test_three_level_range(self):
        nodes = [
            _make_node("n1", RoadmapRole.ai_engineer, CareerLevel.junior),
            _make_node("n2", RoadmapRole.ai_engineer, CareerLevel.mid),
            _make_node("n3", RoadmapRole.ai_engineer, CareerLevel.senior),
            _make_node("n4", RoadmapRole.ai_engineer, CareerLevel.staff),
        ]
        index = RoadmapIndex(nodes)
        result = index.by_role_level_range(
            RoadmapRole.ai_engineer, CareerLevel.junior, CareerLevel.staff
        )
        assert len(result) == 4

    def test_deduplicates_across_levels(self):
        nodes = [
            _make_node("shared", RoadmapRole.ai_engineer, CareerLevel.mid),
            _make_node("shared", RoadmapRole.ai_engineer, CareerLevel.senior),  # same id
        ]
        index = RoadmapIndex(nodes)
        result = index.by_role_level_range(
            RoadmapRole.ai_engineer, CareerLevel.mid, CareerLevel.senior
        )
        assert len(result) == 1  # deduped

    def test_excludes_other_role(self):
        nodes = [
            _make_node("n1", RoadmapRole.software_engineer, CareerLevel.staff),
        ]
        index = RoadmapIndex(nodes)
        result = index.by_role_level_range(
            RoadmapRole.ai_engineer, CareerLevel.staff, CareerLevel.staff
        )
        assert len(result) == 0

    def test_returns_empty_when_from_above_to(self):
        """from_level > to_level raises or returns empty."""
        index = RoadmapIndex([])
        # Depending on implementation choice: assert raises ValueError
        # or assert returns empty list
        import inspect
        # Test that it handles gracefully (no crash)
        result = index.by_role_level_range(
            RoadmapRole.ai_engineer, CareerLevel.staff, CareerLevel.junior
        )
        # Either raises or returns empty - test doesn't enforce which
        # but must not throw unrelated exception
```

### Test Group 2 — Update `test_score.py` for level-range scoring

1. **Replace `test_excludes_nodes_from_other_level`** with a test that verifies multi-level inclusion:

```python
def test_score_includes_level_range(self):
    """junior→staff should include junior+mid+senior+staff nodes in denominator."""
    index = MagicMock()
    junior = [self._make_node("j1", 50)]
    mid = [self._make_node("m1", 50)]
    senior = [self._make_node("s1", 50)]
    staff = [self._make_node("sf1", 50)]
    # by_role_level_range returns combined
    index.by_role_level_range.return_value = junior + mid + senior + staff
    index.by_id.side_effect = lambda nid: {
        "j1": junior[0], "m1": mid[0], "s1": senior[0], "sf1": staff[0]
    }.get(nid)

    # Only staff node is covered
    matched = [
        type("Matched", (), {"id": "j1", "status": "gap"})(),
        type("Matched", (), {"id": "m1", "status": "gap"})(),
        type("Matched", (), {"id": "s1", "status": "gap"})(),
        type("Matched", (), {"id": "sf1", "status": "covered"})(),
    ]
    score = self._compute_score(matched, junior + mid + senior + staff)
    assert score == 25  # 50 / 200 = 0.25
```

2. **Add a test for weighted scoring across levels:**

```python
def test_score_weighted_with_level_range(self):
    """Different-importance nodes across levels should weight correctly."""
    index = MagicMock()
    j1 = self._make_node("j1", 80)   # high-importance junior gap
    s1 = self._make_node("s1", 20)   # low-importance senior covered
    index.by_role_level_range.return_value = [j1, s1]
    index.by_id.side_effect = lambda nid: {"j1": j1, "s1": s1}.get(nid)

    matched = [
        type("Matched", (), {"id": "j1", "status": "gap"})(),
        type("Matched", (), {"id": "s1", "status": "covered"})(),
    ]
    score = self._compute_score(matched, [j1, s1])
    assert score == 20  # 20 / 100 = 0.2
```

### Test Group 3 — `_prioritize_gaps` token/alias matching (new, in `tests/test_roadmap.py` or dedicated `tests/test_prioritize.py`)

```python
class TestPrioritizeGaps:
    def _make_match(self, nid: str, status: str = "gap"):
        return type("MatchedNode", (), {"id": nid, "status": status, "reason": None, "evidence": None})()

    def test_single_token_focus_matches_name(self):
        """Focus 'AWS' should boost a node named 'AWS'."""
        # Setup index with one node
        node = _make_node("n1", RoadmapRole.ai_engineer, CareerLevel.senior)
        node.name = "AWS"
        node.category = "Cloud"
        node.aliases = []
        node.importance = 50
        index = RoadmapIndex([node])
        from agent.nodes.roadmap_select import _prioritize_gaps

        result = _prioritize_gaps(
            [self._make_match("n1")], index, focus_areas=["AWS"]
        )
        assert result == ["n1"]  # not empty, node gets found

    def test_multi_word_focus_tokenizes_correctly(self):
        """Focus 'AWS Cloud' should match both 'AWS' node and 'Cloud' category."""
        node1 = _make_node("n1", RoadmapRole.ai_engineer, CareerLevel.senior)
        node1.name = "AWS"
        node1.category = "Cloud"
        node1.aliases = []
        node1.importance = 50
        
        node2 = _make_node("n2", RoadmapRole.ai_engineer, CareerLevel.senior)
        node2.name = "Docker"
        node2.category = "Container"
        node2.aliases = []
        node2.importance = 50

        index = RoadmapIndex([node1, node2])
        from agent.nodes.roadmap_select import _prioritize_gaps

        result = _prioritize_gaps(
            [self._make_match("n1"), self._make_match("n2")],
            index,
            focus_areas=["AWS Cloud"],
        )
        # n1 should rank higher (matches both 'aws' and 'cloud' tokens + cloud cat exact)
        assert result[0] == "n1"

    def test_alias_matches(self):
        """Node aliases should be searchable for token match."""
        node = _make_node("n1", RoadmapRole.ai_engineer, CareerLevel.senior)
        node.name = "Kubernetes"
        node.category = "Infrastructure"
        node.aliases = ["K8s", "container orchestration"]
        node.importance = 50

        index = RoadmapIndex([node])
        from agent.nodes.roadmap_select import _prioritize_gaps

        result = _prioritize_gaps(
            [self._make_match("n1")], index, focus_areas=["container orchestration"]
        )
        assert result == ["n1"]

    def test_empty_focus_areas_uses_importance(self):
        """When no focus areas given, sort by importance descending."""
        node1 = _make_node("n1", RoadmapRole.ai_engineer, CareerLevel.senior)
        node1.importance = 80
        node2 = _make_node("n2", RoadmapRole.ai_engineer, CareerLevel.senior)
        node2.importance = 50
        node3 = _make_node("n3", RoadmapRole.ai_engineer, CareerLevel.senior)
        node3.importance = 90

        index = RoadmapIndex([node1, node2, node3])
        from agent.nodes.roadmap_select import _prioritize_gaps

        result = _prioritize_gaps(
            [self._make_match("n1"), self._make_match("n2"), self._make_match("n3")],
            index,
            focus_areas=[],
        )
        assert result == ["n3", "n1", "n2"]  # 90, 80, 50
```

### Test Group 4 — Roadmap cap

Add to the existing `test_score.py` or a new file:

```python
class TestRoadmapCap:
    def test_roadmap_capped_at_25(self):
        """With 30 gaps, only first 25 prioritized IDs are selected."""
        # This tests the [:25] slice behavior
        import asyncio
        from agent.nodes.roadmap_select import roadmap_select_node
        from unittest.mock import MagicMock

        # Create 30 nodes
        nodes = []
        for i in range(30):
            n = _make_node(f"n{i}", RoadmapRole.ai_engineer, CareerLevel.staff, importance=50)
            n.category = "Cloud"
            nodes.append(n)

        index = MagicMock()
        index.by_id.side_effect = lambda nid: next((n for n in nodes if n.id == nid), None)
        index.is_valid_subset.return_value = True

        from agent.state import AgentState, CareerFrame
        state = AgentState()
        state.matched_nodes = [
            type("MatchedNode", (), {"id": f"n{i}", "status": "gap", "reason": None, "evidence": None})()
            for i in range(30)
        ]
        state.career_frame = CareerFrame(
            current_role="ai_engineer",
            current_level="senior",
            target_role="ai_engineer",
            target_level="staff",
            focus_areas=["Cloud"],
        )

        node_fn = roadmap_select_node(index)
        result = node_fn(state)
        assert len(result.personalized_roadmap) == 25

    def test_roadmap_returns_all_when_under_cap(self):
        """With 10 gaps, all 10 should be returned."""
        # Similar setup with 10 nodes
        # ... (truncated for brevity)
        assert len(result.personalized_roadmap) == 10
```

### Test Group 5 — Prompt smoke test

Add a minimal test that the prompt string contains methodology guidance:

```python
class TestAnalyzePromptMethodology:
    def test_prompt_contains_methodology_examples(self):
        from agent.nodes.analyze import _ANALYZE_SYSTEM_PROMPT
        # The prompt should contain at least one methodology example
        assert "methodology" in _ANALYZE_SYSTEM_PROMPT.lower() or \
               "prática" in _ANALYZE_SYSTEM_PROMPT.lower() or \
               "práticas" in _ANALYZE_SYSTEM_PROMPT.lower()
```

## Acceptance Criteria

1. `test_excludes_nodes_from_other_level` is replaced by a test that verifies multi-level inclusion.
2. `test_three_level_range` passes with `junior→staff` returning 4 nodes across all levels.
3. `test_multi_word_focus_tokenizes_correctly` passes: "AWS Cloud" ranks the AWS+Cloud node above Docker.
4. `test_alias_matches` passes: "container orchestration" matches Kubernetes via alias.
5. `test_roadmap_capped_at_25` passes: 30 gaps → exactly 25 in roadmap.
6. `test_roadmap_returns_all_when_under_cap` passes: 10 gaps → all 10 in roadmap.
7. `test_prompt_contains_methodology_examples` passes as a basic smoke test.
8. `test_deduplicates_across_levels` passes: shared node id across levels counted once.
9. All existing tests continue to pass.

## Dependencies

- Tasks 5, 6, 7, 8 must be implemented first so the tests can actually run against the new behavior.
