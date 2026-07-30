"""RoadmapIndex: fast lookup with parent-child relationships and level filtering."""

from roadmap.models import CareerLevel, RoadmapNode, RoadmapRole, levels_in_range


class RoadmapIndex:
    """In-memory index over a flat list of RoadmapNode objects."""

    def __init__(self, nodes: list[RoadmapNode]) -> None:
        self._by_id: dict[str, RoadmapNode] = {}
        self._by_role_level: dict[tuple[RoadmapRole, CareerLevel], list[RoadmapNode]] = {}
        self._by_parent_id: dict[str, list[RoadmapNode]] = {}
        self._by_level: dict[CareerLevel, list[RoadmapNode]] = {}
        self._by_ownership: dict[str, list[RoadmapNode]] = {}

        for node in nodes:
            # id index (deduplicated)
            if node.id not in self._by_id:
                self._by_id[node.id] = node

            # Index by parent_id for hierarchy traversal
            if node.parent_id:
                self._by_parent_id.setdefault(node.parent_id, []).append(node)

            # Index by level
            self._by_level.setdefault(node.level, []).append(node)
            
            # Index by ownership type
            self._by_ownership.setdefault(node.ownership, []).append(node)

            # Index by role+level combination (now nodes have role)
            key = (node.role, node.level)
            self._by_role_level.setdefault(key, []).append(node)

    def by_id(self, id: str) -> RoadmapNode | None:
        """Return the node with the given *id*, or None."""
        return self._by_id.get(id)

    def by_role_level(self, role: RoadmapRole, level: CareerLevel) -> list[RoadmapNode]:
        """Return nodes matching *role* and *level*."""
        return self._by_role_level.get((role, level), [])

    def by_level(self, level: CareerLevel) -> list[RoadmapNode]:
        """Retrieve all nodes for a given career level across all roles."""
        return self._by_level.get(level, [])
    
    def by_parent_id(self, parent_id: str) -> list[RoadmapNode]:
        """Retrieve all child nodes for a given parent ID."""
        return self._by_parent_id.get(parent_id, [])

    def by_role_level_range(
        self,
        role: RoadmapRole,
        from_level: CareerLevel,
        to_level: CareerLevel,
    ) -> list[RoadmapNode]:
        """Return nodes for *role* across the level range (inclusive), deduplicated by id."""
        seen: set[str] = set()
        result: list[RoadmapNode] = []
        for level in levels_in_range(from_level, to_level):
            for node in self.by_role_level(role, level):
                if node.id not in seen:
                    seen.add(node.id)
                    result.append(node)
        return result

    def by_level_range(
        self,
        from_level: CareerLevel,
        to_level: CareerLevel,
    ) -> list[RoadmapNode]:
        """Return nodes across the level range (inclusive), deduplicated by id."""
        seen: set[str] = set()
        result: list[RoadmapNode] = []
        for level in levels_in_range(from_level, to_level):
            for node in self.by_level(level):
                if node.id not in seen:
                    seen.add(node.id)
                    result.append(node)
        return result
    
    def by_ownership(self, ownership: str) -> list[RoadmapNode]:
        """Retrieve all nodes by ownership type ('proprio' or 'referencia')."""
        return self._by_ownership.get(ownership, [])
    
    def get_hierarchy(self, node_id: str) -> dict:
        """Get the full hierarchy for a node (parent and children).
        
        Returns a dict with:
        - node: The requested node
        - parent: Parent node if exists
        - children: List of child nodes
        - siblings: List of sibling nodes (same parent)
        """
        node = self.by_id(node_id)
        if not node:
            return {}
        
        parent = self.by_id(node.parent_id) if node.parent_id else None
        children = self.by_parent_id(node_id)
        siblings = []
        
        if node.parent_id:
            siblings = [n for n in self.by_parent_id(node.parent_id) if n.id != node_id]
        
        return {
            "node": node,
            "parent": parent,
            "children": children,
            "siblings": siblings
        }
    
    def filter_nodes(
        self,
        role: RoadmapRole | None = None,
        level: CareerLevel | None = None,
        ownership: str | None = None,
        node_type: str | None = None
    ) -> list[RoadmapNode]:
        """Filter nodes by multiple criteria.
        
        Args:
            role: Filter by role (e.g., RoadmapRole.ai_engineer)
            level: Filter by career level (e.g., CareerLevel.junior)
            ownership: Filter by ownership ('proprio' or 'referencia')
            node_type: Filter by type ('skill' or 'group')
        
        Returns:
            List of nodes matching all specified criteria
        """
        # Start with all nodes
        results = list(self._by_id.values())
        
        # Apply filters
        if role:
            results = [n for n in results if n.role == role]
        
        if level:
            results = [n for n in results if n.level == level]
        
        if ownership:
            results = [n for n in results if n.ownership == ownership]
        
        if node_type:
            results = [n for n in results if n.type == node_type]
        
        return results

    def is_valid_subset(self, node_ids: list[str]) -> bool:
        """ADR-008 strict-subset validator.

        Returns ``True`` only if every id in *node_ids* exists in the index.
        """
        all_ids = self.get_all_ids()
        return all(nid in all_ids for nid in node_ids)

    def get_all_ids(self) -> set[str]:
        """Return the set of all indexed node ids."""
        return set(self._by_id.keys())
