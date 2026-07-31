"""Tests for RoadmapIndex level-range queries and gap prioritization."""

from unittest.mock import MagicMock

import pytest

from roadmap.index import RoadmapIndex
from roadmap.models import CareerLevel, RoadmapNode, RoadmapRole, levels_in_range


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


class TestLevelsInRange:
    def test_single_level(self):
        assert levels_in_range(CareerLevel.senior, CareerLevel.senior) == [CareerLevel.senior]

    def test_two_levels(self):
        assert levels_in_range(CareerLevel.mid, CareerLevel.senior) == [
            CareerLevel.mid, CareerLevel.senior
        ]

    def test_all_four_levels(self):
        assert levels_in_range(CareerLevel.junior, CareerLevel.staff) == [
            CareerLevel.junior, CareerLevel.mid,
            CareerLevel.senior, CareerLevel.staff,
        ]

    def test_raises_when_from_above_to(self):
        with pytest.raises(ValueError):
            levels_in_range(CareerLevel.staff, CareerLevel.junior)


class TestByRoleLevelRange:
    def test_single_level_range(self):
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
            _make_node("shared", RoadmapRole.ai_engineer, CareerLevel.senior),
        ]
        index = RoadmapIndex(nodes)
        result = index.by_role_level_range(
            RoadmapRole.ai_engineer, CareerLevel.mid, CareerLevel.senior
        )
        assert len(result) == 1

    def test_excludes_other_role(self):
        nodes = [
            _make_node("n1", RoadmapRole.software_engineer, CareerLevel.staff),
        ]
        index = RoadmapIndex(nodes)
        result = index.by_role_level_range(
            RoadmapRole.ai_engineer, CareerLevel.staff, CareerLevel.staff
        )
        assert len(result) == 0

    def test_returns_empty_when_no_nodes(self):
        index = RoadmapIndex([])
        result = index.by_role_level_range(
            RoadmapRole.ai_engineer, CareerLevel.staff, CareerLevel.staff
        )
        assert result == []


class TestPrioritizeGaps:
    def _make_match(self, nid: str, status: str = "gap"):
        return type("MatchedNode", (), {"id": nid, "status": status, "reason": None, "evidence": None})()

    def test_single_token_focus_matches_name(self):
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
        assert result == ["n1"]

    def test_multi_word_focus_tokenizes_correctly(self):
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
        assert result[0] == "n1"

    def test_alias_matches(self):
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
        assert result == ["n3", "n1", "n2"]

    def test_all_gaps_returned_when_no_focus(self):
        node1 = _make_node("n1", RoadmapRole.ai_engineer, CareerLevel.senior)
        node1.importance = 80
        node2 = _make_node("n2", RoadmapRole.ai_engineer, CareerLevel.senior)
        node2.importance = 50

        index = RoadmapIndex([node1, node2])
        from agent.nodes.roadmap_select import _prioritize_gaps

        result = _prioritize_gaps(
            [self._make_match("n1"), self._make_match("n2")],
            index,
            focus_areas=[],
        )
        assert len(result) == 2
        assert "n1" in result
        assert "n2" in result


class TestRoadmapCap:
    def test_roadmap_capped_at_35(self):
        from agent.nodes.roadmap_select import roadmap_select_node
        from agent.state import AgentState, CareerFrame

        nodes = []
        for i in range(40):
            n = _make_node(f"n{i}", RoadmapRole.ai_engineer, CareerLevel.staff, importance=50)
            n.category = "Cloud"
            nodes.append(n)

        index = MagicMock()
        index.by_id.side_effect = lambda nid: next((n for n in nodes if n.id == nid), None)
        index.is_valid_subset.return_value = True

        state = AgentState(
            user_id="test",
            raw_cv_text="test",
            raw_description="test",
        )
        state.matched_nodes = [
            type("MatchedNode", (), {"id": f"n{i}", "status": "gap", "reason": None, "evidence": None})()
            for i in range(40)
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
        assert len(result.personalized_roadmap) == 35

    def test_roadmap_returns_all_when_under_cap(self):

        from agent.nodes.roadmap_select import roadmap_select_node
        from agent.state import AgentState, CareerFrame

        nodes = []
        for i in range(10):
            n = _make_node(f"n{i}", RoadmapRole.ai_engineer, CareerLevel.staff, importance=50)
            n.category = "Cloud"
            nodes.append(n)

        index = MagicMock()
        index.by_id.side_effect = lambda nid: next((n for n in nodes if n.id == nid), None)
        index.is_valid_subset.return_value = True

        state = AgentState(
            user_id="test",
            raw_cv_text="test",
            raw_description="test",
        )
        state.matched_nodes = [
            type("MatchedNode", (), {"id": f"n{i}", "status": "gap", "reason": None, "evidence": None})()
            for i in range(10)
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
        assert len(result.personalized_roadmap) == 10


class TestAnalyzePromptMethodology:
    def test_prompt_contains_methodology_references(self):
        from agent.nodes.analyze import _ANALYZE_SYSTEM_PROMPT
        lower = _ANALYZE_SYSTEM_PROMPT.lower()
        assert any(term in lower for term in ("methodology", "prática", "práticas", "metodologia"))
