"""Tests for single-role isolation in the analysis pipeline."""

import asyncio

from agent.nodes.analyze import _resolve_target_role
from agent.nodes.compare import compare_node
from agent.state import AgentState, CareerFrame
from roadmap.index import RoadmapIndex
from roadmap.models import CareerLevel, RoadmapNode, RoadmapRole


def _make_node(
    nid: str,
    role: RoadmapRole,
    level: CareerLevel = CareerLevel.mid,
    name: str | None = None,
):
    return RoadmapNode(
        id=nid,
        name=name or f"Node {nid}",
        type="skill",
        category="Test",
        description="",
        level=level,
        importance=50,
        estimated_hours=10,
        aliases=[],
        role=role,
    )


def _state(career_frame: CareerFrame) -> AgentState:
    state = AgentState(user_id="t", raw_cv_text="cv", raw_description="desc")
    state.career_frame = career_frame
    state.extracted_skills = {"skills": [], "technologies": [], "domain_areas": []}
    return state


class TestResolveTargetRole:
    def test_null_target_defaults_to_current(self):
        assert _resolve_target_role("ai_engineer", None) == "ai_engineer"

    def test_explicit_target_is_kept(self):
        assert _resolve_target_role("ai_engineer", "frontend_engineer") == "frontend_engineer"

    def test_both_null_stays_null(self):
        assert _resolve_target_role(None, None) is None

    def test_empty_string_target_defaults_to_current(self):
        assert _resolve_target_role("software_engineer", "") == "software_engineer"


class TestCompareRoleIsolation:
    def test_unknown_role_slug_returns_empty_with_error(self):
        index = RoadmapIndex([_make_node("n1", RoadmapRole.frontend_engineer)])
        state = _state(
            CareerFrame(
                current_role="ai_engineer",
                current_level="mid",
                target_role="fullstack_engineer",
                target_level="senior",
                focus_areas=[],
            )
        )

        asyncio.run(compare_node(index)(state))

        assert state.matched_nodes == []
        assert any("Unknown role" in e for e in state.errors)

    def test_missing_role_defaults_to_current_and_stays_in_role(self):
        index = RoadmapIndex(
            [
                _make_node("ai1", RoadmapRole.ai_engineer, CareerLevel.mid, "RAG pipeline"),
                _make_node("fe1", RoadmapRole.frontend_engineer, CareerLevel.mid, "React UI"),
            ]
        )
        state = _state(
            CareerFrame(
                current_role="ai_engineer",
                current_level="mid",
                target_role=None,  # treated as staying on the AI path
                target_level="mid",
                focus_areas=[],
            )
        )

        asyncio.run(compare_node(index)(state))

        ids = {m.id for m in state.matched_nodes}
        assert ids == {"ai1"}
        assert "fe1" not in ids

    def test_valid_role_with_no_nodes_returns_empty(self):
        index = RoadmapIndex([])
        state = _state(
            CareerFrame(
                current_role="ai_engineer",
                current_level="mid",
                target_role="ai_engineer",
                target_level="senior",
                focus_areas=[],
            )
        )

        asyncio.run(compare_node(index)(state))

        assert state.matched_nodes == []

    def test_cross_role_nodes_never_leak(self):
        index = RoadmapIndex(
            [_make_node("fe1", RoadmapRole.frontend_engineer, CareerLevel.senior, "CSS Grid")]
        )
        state = _state(
            CareerFrame(
                current_role="ai_engineer",
                current_level="mid",
                target_role="ai_engineer",
                target_level="senior",
                focus_areas=[],
            )
        )

        asyncio.run(compare_node(index)(state))

        assert state.matched_nodes == []
