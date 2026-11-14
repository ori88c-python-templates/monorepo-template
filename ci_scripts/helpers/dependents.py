"""Reverse breadth-first search over workspace dependents."""

from __future__ import annotations

from collections import deque
from collections.abc import Set as AbstractSet

from helpers.workspace_graph import WorkspaceGraph


def affected_nodes(graph: WorkspaceGraph, origins: AbstractSet[str]) -> frozenset[str]:
    """Return ``origins`` and every member that depends on them.

    The walk follows reverse edges, including through other packages. A node's
    own dependencies are not included. Cycles stop at the first repeat.

    Args:
        graph: Workspace members and depends-on edges.
        origins: Package directory names whose dependents are required.

    Returns:
        The origin directory names plus every transitive dependent.
    """
    dependents_by_node: dict[str, set[str]] = {
        name: set() for name in graph.dependency_names_by_member
    }
    for node, deps in graph.dependency_names_by_member.items():
        for dependency in deps:
            dependents_by_node.setdefault(dependency, set()).add(node)
    seen: set[str] = set()
    queue: deque[str] = deque(origins)
    while queue:
        node = queue.popleft()
        if node in seen:
            continue
        seen.add(node)
        queue.extend(dependents_by_node.get(node, ()))
    return frozenset(seen)
