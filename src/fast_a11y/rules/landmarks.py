"""Landmark rules: landmark-one-main, landmark-no-duplicate-main,
landmark-no-duplicate-banner, landmark-no-duplicate-contentinfo,
landmark-banner-is-top-level, landmark-contentinfo-is-top-level,
landmark-complementary-is-top-level, landmark-main-is-top-level,
landmark-unique
"""

from __future__ import annotations

from collections import defaultdict

from ..accessible_name import get_accessible_name
from ..rule_engine import NodeCheckDetail, RuleCheck, RuleRunResult, make_check
from ..tree import FastNode, find_by_tag, get_role, is_hidden_or_ancestor_hidden

LANDMARK_ROLES = frozenset({
    "banner", "complementary", "contentinfo", "form", "main",
    "navigation", "region", "search",
})


def _find_landmarks_by_role(nodes: list[FastNode], role: str) -> list[FastNode]:
    """Get all nodes with a specific landmark role."""
    return [
        n for n in nodes
        if not is_hidden_or_ancestor_hidden(n) and get_role(n) == role
    ]


def _is_inside_landmark(node: FastNode) -> bool:
    """Check if a landmark node is nested inside another landmark."""
    parent = node.parent
    while parent:
        parent_role = get_role(parent)
        if parent_role and parent_role in LANDMARK_ROLES:
            return True
        parent = parent.parent
    return False


class _LandmarkOneMain:
    rule_id = "landmark-one-main"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        html_nodes = find_by_tag(nodes, "html")
        target = html_nodes[0] if html_nodes else (nodes[0] if nodes else None)
        if not target:
            return result
        main_landmarks = _find_landmarks_by_role(nodes, "main")
        if main_landmarks:
            result.passes.append(target)
            result.check_details[id(target)] = NodeCheckDetail(
                any=[make_check("landmark-one-main", "moderate",
                    "Document has a main landmark")]
            )
        else:
            result.violations.append(target)
            result.check_details[id(target)] = NodeCheckDetail(
                any=[make_check("landmark-one-main", "moderate",
                    "Document does not have a main landmark")]
            )
        return result


def _no_duplicate_landmark(rule_id: str, role: str) -> RuleCheck:
    """Create a no-duplicate landmark rule."""

    class _Rule:
        def __init__(self) -> None:
            self.rule_id = rule_id

        def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
            result = RuleRunResult()
            landmarks = _find_landmarks_by_role(nodes, role)
            if len(landmarks) <= 1:
                html_nodes = find_by_tag(nodes, "html")
                target = html_nodes[0] if html_nodes else (nodes[0] if nodes else None)
                if target:
                    result.passes.append(target)
                    result.check_details[id(target)] = NodeCheckDetail(
                        any=[make_check(rule_id, "moderate",
                            f"Document has at most one {role} landmark")]
                    )
            else:
                for node in landmarks:
                    result.violations.append(node)
                    result.check_details[id(node)] = NodeCheckDetail(
                        any=[make_check(rule_id, "moderate",
                            f"Document has {len(landmarks)} {role} landmarks -- should have at most one")]
                    )
            return result

    return _Rule()


def _top_level_landmark(rule_id: str, role: str) -> RuleCheck:
    """Create a top-level landmark rule."""

    class _Rule:
        def __init__(self) -> None:
            self.rule_id = rule_id

        def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
            result = RuleRunResult()
            landmarks = _find_landmarks_by_role(nodes, role)
            for node in landmarks:
                if _is_inside_landmark(node):
                    result.violations.append(node)
                    result.check_details[id(node)] = NodeCheckDetail(
                        any=[make_check(rule_id, "moderate",
                            f"{role} landmark is nested inside another landmark")]
                    )
                else:
                    result.passes.append(node)
                    result.check_details[id(node)] = NodeCheckDetail(
                        any=[make_check(rule_id, "moderate",
                            f"{role} landmark is at the top level")]
                    )
            return result

    return _Rule()


class _LandmarkUnique:
    rule_id = "landmark-unique"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        role_groups: dict[str, list[FastNode]] = defaultdict(list)
        for node in nodes:
            if is_hidden_or_ancestor_hidden(node):
                continue
            role = get_role(node)
            if not role or role not in LANDMARK_ROLES:
                continue
            role_groups[role].append(node)
        for role, landmarks in role_groups.items():
            if len(landmarks) <= 1:
                if landmarks:
                    result.passes.append(landmarks[0])
                    result.check_details[id(landmarks[0])] = NodeCheckDetail(
                        any=[make_check("landmark-unique", "moderate",
                            f"Landmark is unique -- only one {role} landmark")]
                    )
                continue
            name_map: dict[str, list[FastNode]] = defaultdict(list)
            for node in landmarks:
                name = get_accessible_name(node, all_nodes).lower().strip()
                key = f"{role}:{name}"
                name_map[key].append(node)
            for key, node_list in name_map.items():
                if len(node_list) > 1:
                    for node in node_list:
                        name = get_accessible_name(node, all_nodes)
                        result.violations.append(node)
                        label_msg = (
                            f' with the same label "{name}"' if name
                            else " without unique labels"
                        )
                        result.check_details[id(node)] = NodeCheckDetail(
                            any=[make_check("landmark-unique", "moderate",
                                f"Multiple {role} landmarks{label_msg} -- landmarks should have unique labels")]
                        )
                else:
                    result.passes.append(node_list[0])
                    result.check_details[id(node_list[0])] = NodeCheckDetail(
                        any=[make_check("landmark-unique", "moderate",
                            f"Landmark has a unique label among {role} landmarks")]
                    )
        return result


landmark_rules: list[RuleCheck] = [
    _LandmarkOneMain(),
    _no_duplicate_landmark("landmark-no-duplicate-main", "main"),
    _no_duplicate_landmark("landmark-no-duplicate-banner", "banner"),
    _no_duplicate_landmark("landmark-no-duplicate-contentinfo", "contentinfo"),
    _top_level_landmark("landmark-banner-is-top-level", "banner"),
    _top_level_landmark("landmark-contentinfo-is-top-level", "contentinfo"),
    _top_level_landmark("landmark-complementary-is-top-level", "complementary"),
    _top_level_landmark("landmark-main-is-top-level", "main"),
    _LandmarkUnique(),
]
