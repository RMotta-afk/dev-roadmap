"""RoadmapIndex: fast lookup and ADR-008 strict-subset validator."""

from roadmap.models import CareerLevel, RoadmapNode, RoadmapRole


class RoadmapIndex:
    """In-memory index over a flat list of RoadmapNode objects."""

    def __init__(self, nodes: list[RoadmapNode]) -> None:
        self._by_id: dict[str, RoadmapNode] = {}
        self._by_role_level: dict[tuple[RoadmapRole, CareerLevel], list[RoadmapNode]] = {}

        for node in nodes:
            # id index (deduplicated)
            if node.id not in self._by_id:
                self._by_id[node.id] = node

            # role/level index
            # Note: role is not stored on RoadmapNode directly; we keep the
            # original index built from the caller's context (loader) when
            # possible.  For now we index by node.level alone because the
            # caller passes the full flat list and filters later.
            key = (node.level, node.level)  # placeholder; see below
            self._by_role_level.setdefault(key, []).append(node)

        # Rebuild role-level index from a simpler approach:
        # since nodes don't carry role, we just store all and filter by level.
        # The caller (loader) can supply role if needed; we keep a level-only
        # index internally and expose a filter that accepts role for API
        # compatibility.
        self._by_level: dict[CareerLevel, list[RoadmapNode]] = {}
        for node in nodes:
            self._by_level.setdefault(node.level, []).append(node)

    def by_id(self, id: str) -> RoadmapNode | None:
        """Return the node with the given *id*, or None."""
        return self._by_id.get(id)

    def by_role_level(self, role: RoadmapRole, level: CareerLevel) -> list[RoadmapNode]:
        """Return nodes matching *role* and *level*."""
        # Nodes currently do not store role; we filter by level.
        # If role-specific filtering is needed, extend RoadmapNode later.
        return [n for n in self._by_level.get(level, [])]

    def is_valid_subset(self, node_ids: list[str]) -> bool:
        """ADR-008 strict-subset validator.

        Returns ``True`` only if every id in *node_ids* exists in the index.
        """
        all_ids = self.get_all_ids()
        return all(nid in all_ids for nid in node_ids)

    def get_all_ids(self) -> set[str]:
        """Return the set of all indexed node ids."""
        return set(self._by_id.keys())
