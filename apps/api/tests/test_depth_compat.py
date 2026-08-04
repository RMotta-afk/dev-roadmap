"""Tests for the depth filter, compatibility agent, and topic dedup."""

from unittest.mock import patch

from agent.nodes.compatibility import compatibility_node
from agent.nodes.depth_filter import depth_filter_node
from agent.state import AgentState, CareerFrame, MatchedNode
from roadmap.index import RoadmapIndex
from roadmap.models import CareerLevel, RoadmapNode, RoadmapRole


def _make_node(
    nid: str,
    level: CareerLevel,
    importance: int = 50,
    name: str | None = None,
    aliases: list[str] | None = None,
):
    return RoadmapNode(
        id=nid,
        name=name or f"Node {nid}",
        type="skill",
        category="Test",
        description="",
        level=level,
        importance=importance,
        estimated_hours=10,
        aliases=aliases or [],
        role=RoadmapRole.ai_engineer,
    )


def _state(matched: list[MatchedNode], current: str = "junior", target: str = "staff") -> AgentState:
    state = AgentState(
        user_id="t",
        raw_cv_text="cv",
        raw_description="desc",
        career_frame=CareerFrame(
            current_role="ai_engineer",
            current_level=current,
            target_role="ai_engineer",
            target_level=target,
            focus_areas=[],
        ),
    )
    state.matched_nodes = matched
    return state


class TestDepthFilter:
    def test_applies_same_or_lower_verdicts(self):
        nodes = [_make_node("n1", CareerLevel.mid)]
        index = RoadmapIndex(nodes)
        state = _state(
            [
                MatchedNode(
                    id="n1",
                    status="gap",
                    confidence=0.7,
                    depth_candidate=True,
                    evidence="built rag system",
                )
            ]
        )
        verdicts = [{"id": "n1", "verdict": "same_or_lower", "reason": "domina o tema"}]

        with patch(
            "agent.nodes.depth_filter._adjudicate", return_value={"verdicts": verdicts}
        ):
            import asyncio

            result = asyncio.run(depth_filter_node(index)(state))

        node = result.matched_nodes[0]
        assert node.status == "known_via_experience"
        assert node.depth_candidate is False
        assert "domina o tema" in node.reason

    def test_keeps_gap_on_more_advanced_verdict(self):
        nodes = [_make_node("n1", CareerLevel.senior)]
        index = RoadmapIndex(nodes)
        state = _state(
            [MatchedNode(id="n1", status="gap", confidence=0.66, depth_candidate=True)]
        )
        verdicts = [{"id": "n1", "verdict": "more_advanced", "reason": "exige avanço"}]

        with patch(
            "agent.nodes.depth_filter._adjudicate", return_value={"verdicts": verdicts}
        ):
            import asyncio

            result = asyncio.run(depth_filter_node(index)(state))

        node = result.matched_nodes[0]
        assert node.status == "gap"
        assert node.depth_candidate is False
        assert "avançada" in node.reason

    def test_degrades_to_gap_without_llm(self):
        nodes = [_make_node("n1", CareerLevel.senior)]
        index = RoadmapIndex(nodes)
        state = _state(
            [MatchedNode(id="n1", status="gap", confidence=0.66, depth_candidate=True)]
        )

        with patch("agent.nodes.depth_filter._adjudicate", return_value=None):
            import asyncio

            result = asyncio.run(depth_filter_node(index)(state))

        node = result.matched_nodes[0]
        assert node.status == "gap"
        assert node.depth_candidate is False

    def test_no_candidates_leaves_state_unchanged(self):
        index = RoadmapIndex([])
        state = _state([MatchedNode(id="n1", status="covered")])
        state.matched_nodes[0].depth_candidate = False

        import asyncio

        result = asyncio.run(depth_filter_node(index)(state))
        assert result.matched_nodes[0].status == "covered"


class TestCompatibilityNode:
    async def _noop_calibrate(self, base_score, rationale, state, index):
        return base_score, rationale

    def _run(self, state, index):
        with patch(
            "agent.nodes.compatibility._calibrate", self._noop_calibrate
        ):
            import asyncio

            return asyncio.run(compatibility_node(index)(state))

    def test_blended_score_weights_next_level(self):
        nodes = [
            _make_node("j1", CareerLevel.junior),
            _make_node("m1", CareerLevel.mid),
            _make_node("s1", CareerLevel.senior),
        ]
        index = RoadmapIndex(nodes)
        state = _state(
            [
                MatchedNode(id="j1", status="covered"),
                MatchedNode(id="m1", status="gap"),
                MatchedNode(id="s1", status="gap"),
            ],
            current="junior",
            target="senior",
        )

        result = self._run(state, index)
        # current bucket (junior) = 100, next bucket (mid+senior) = 0
        # blended = 0.4*100 + 0.6*0 = 40
        assert result.compatibility_score == 40
        assert result.compatibility_rationale

    def test_all_covered_scores_100(self):
        nodes = [_make_node("j1", CareerLevel.junior)]
        index = RoadmapIndex(nodes)
        state = _state(
            [MatchedNode(id="j1", status="covered")],
            current="junior",
            target="mid",
        )

        result = self._run(state, index)
        assert result.compatibility_score == 100

    def test_zero_when_all_gaps(self):
        nodes = [_make_node("m1", CareerLevel.mid)]
        index = RoadmapIndex(nodes)
        state = _state(
            [MatchedNode(id="m1", status="gap")],
            current="junior",
            target="mid",
        )

        result = self._run(state, index)
        assert result.compatibility_score == 0

    def test_missing_context_sets_zero(self):
        index = RoadmapIndex([])
        state = AgentState(user_id="t", raw_cv_text="cv", raw_description="d")

        import asyncio

        result = asyncio.run(compatibility_node(index)(state))
        assert result.compatibility_score == 0


class TestDedupeByTopic:
    def _dedupe(self, matches, nodes, target: str = "senior"):
        from agent.nodes.roadmap_select import _dedupe_nodes_by_topic

        index = RoadmapIndex(nodes)
        return _dedupe_nodes_by_topic(matches, index, CareerLevel(target))

    def test_same_name_keeps_highest_importance(self):
        nodes = [
            _make_node("a", CareerLevel.senior, importance=50, name="Kubernetes"),
            _make_node("b", CareerLevel.senior, importance=90, name="Kubernetes"),
        ]
        matches = [MatchedNode(id="a", status="gap"), MatchedNode(id="b", status="gap")]

        result = self._dedupe(matches, nodes)
        assert [m.id for m in result] == ["b"]

    def test_name_grouped_ignoring_case_and_punctuation(self):
        nodes = [
            _make_node("a", CareerLevel.senior, name="Observabilidade e monitoramento"),
            _make_node("b", CareerLevel.senior, name="Observabilidade e monitoramento!"),
        ]
        matches = [MatchedNode(id="a", status="gap"), MatchedNode(id="b", status="gap")]

        result = self._dedupe(matches, nodes)
        assert len(result) == 1

    def test_alias_overlap_merges_groups(self):
        nodes = [
            _make_node("a", CareerLevel.senior, name="Kubernetes", aliases=["K8s"]),
            _make_node("b", CareerLevel.senior, name="Container Orchestration", aliases=["K8s"]),
        ]
        matches = [MatchedNode(id="a", status="gap"), MatchedNode(id="b", status="gap")]

        result = self._dedupe(matches, nodes)
        assert len(result) == 1

    def test_distinct_topics_kept(self):
        nodes = [
            _make_node("a", CareerLevel.senior, name="Kubernetes"),
            _make_node("b", CareerLevel.senior, name="AWS"),
        ]
        matches = [MatchedNode(id="a", status="gap"), MatchedNode(id="b", status="gap")]

        result = self._dedupe(matches, nodes)
        assert {m.id for m in result} == {"a", "b"}
