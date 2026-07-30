from unittest.mock import MagicMock

import pytest

from agent.nodes.level_guess import _compute_compatibility_score


class TestComputeCompatibilityScore:
    def test_score_zero_when_no_weight(self):
        assert _compute_compatibility_score(0.0, 0.0) == 0

    def test_score_zero_when_no_covered(self):
        assert _compute_compatibility_score(0.0, 100.0) == 0

    def test_score_hundred_when_all_covered(self):
        assert _compute_compatibility_score(100.0, 100.0) == 100

    def test_score_partial_coverage(self):
        assert _compute_compatibility_score(50.0, 100.0) == 50

    def test_score_clamps_to_hundred(self):
        assert _compute_compatibility_score(150.0, 100.0) == 100

    def test_score_clamps_to_zero(self):
        assert _compute_compatibility_score(-10.0, 100.0) == 0

    def test_score_weighted_importance(self):
        assert _compute_compatibility_score(80.0, 100.0) == 80


class TestFullScoreComputation:
    def _make_node(self, node_id: str, importance: int = 50):
        from roadmap.models import RoadmapNode, RoadmapRole, CareerLevel

        return RoadmapNode(
            id=node_id,
            name=f"Node {node_id}",
            type="skill",
            category="TestCategory",
            description=f"Test node {node_id}",
            level=CareerLevel.staff,
            importance=importance,
            estimated_hours=10,
            aliases=[],
            role=RoadmapRole.software_engineer,
        )

    def _compute_score(self, matched, nodes):
        from agent.nodes.level_guess import _compute_compatibility_score

        covered_weight = 0.0
        total_weight = 0.0
        for m in matched:
            node = next((n for n in nodes if n.id == m.id), None)
            if not node:
                continue
            weight = float(node.importance) if node.importance else 50.0
            total_weight += weight
            if m.status in ("covered", "known_via_experience"):
                covered_weight += weight
        return _compute_compatibility_score(covered_weight, total_weight)

    def test_score_zero_when_no_nodes_covered(self):
        index = MagicMock()
        nodes = [self._make_node("n1", 80), self._make_node("n2", 50)]
        index.by_role_level.return_value = nodes
        index.by_id.side_effect = lambda nid: next((n for n in nodes if n.id == nid), None)

        matched = [
            type("Matched", (), {"id": "n1", "status": "gap"})(),
            type("Matched", (), {"id": "n2", "status": "gap"})(),
        ]

        assert self._compute_score(matched, nodes) == 0

    def test_score_hundred_when_all_covered(self):
        index = MagicMock()
        nodes = [self._make_node("n1", 80), self._make_node("n2", 50)]
        index.by_role_level.return_value = nodes
        index.by_id.side_effect = lambda nid: next((n for n in nodes if n.id == nid), None)

        matched = [
            type("Matched", (), {"id": "n1", "status": "covered"})(),
            type("Matched", (), {"id": "n2", "status": "known_via_experience"})(),
        ]

        assert self._compute_score(matched, nodes) == 100

    def test_score_partial_weighted(self):
        index = MagicMock()
        nodes = [self._make_node("n1", 80), self._make_node("n2", 50)]
        index.by_role_level.return_value = nodes
        index.by_id.side_effect = lambda nid: next((n for n in nodes if n.id == nid), None)

        matched = [
            type("Matched", (), {"id": "n1", "status": "covered"})(),
            type("Matched", (), {"id": "n2", "status": "gap"})(),
        ]

        assert self._compute_score(matched, nodes) == 61

    def test_excludes_nodes_from_other_level(self):
        index = MagicMock()
        junior_nodes = [self._make_node("j1", 50)]
        staff_nodes = [self._make_node("s1", 80)]
        index.by_role_level.return_value = staff_nodes
        index.by_id.side_effect = lambda nid: next((n for n in staff_nodes if n.id == nid), None)

        matched = [
            type("Matched", (), {"id": "s1", "status": "covered"})(),
            type("Matched", (), {"id": "j1", "status": "gap"})(),
        ]

        score = self._compute_score(matched, staff_nodes)
        assert score == 100

    def test_empty_skills_gets_zero_score(self):
        index = MagicMock()
        nodes = [self._make_node("n1", 80), self._make_node("n2", 50)]
        index.by_role_level.return_value = nodes
        index.by_id.side_effect = lambda nid: next((n for n in nodes if n.id == nid), None)

        matched: list = []

        assert self._compute_score(matched, nodes) == 0