"""Navigation rules: link-name, frame-title, frame-title-unique,
bypass, tabindex, accesskeys, region
"""

from __future__ import annotations

import re
from collections import defaultdict

from ..accessible_name import get_accessible_name
from ..rule_engine import NodeCheckDetail, RuleRunResult, make_check
from ..tree import (
    FastNode,
    find_by_tag,
    get_role,
    is_hidden_or_ancestor_hidden,
)

LANDMARK_ROLES = frozenset({
    "banner", "complementary", "contentinfo", "form", "main",
    "navigation", "region", "search",
})


class _LinkName:
    rule_id = "link-name"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        for node in nodes:
            if is_hidden_or_ancestor_hidden(node):
                continue
            is_link = (
                (node.tag == "a" and "href" in node.attrs)
                or node.attrs.get("role") == "link"
            )
            if not is_link:
                continue
            name = get_accessible_name(node, all_nodes)
            if name:
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("link-name", "serious", "Element has discernible text")]
                )
            else:
                result.violations.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("link-name", "serious",
                        "Element does not have discernible text")]
                )
        return result


class _FrameTitle:
    rule_id = "frame-title"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        for node in nodes:
            if node.tag not in ("iframe", "frame"):
                continue
            if is_hidden_or_ancestor_hidden(node):
                continue
            role = node.attrs.get("role")
            if role in ("none", "presentation"):
                continue
            title = node.attrs.get("title")
            if title and title.strip():
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("frame-title", "serious",
                        f'Element has a title attribute: "{title.strip()}"')]
                )
            else:
                has_aria_label = bool(node.attrs.get("aria-label", "").strip())
                has_aria_labelledby = bool(node.attrs.get("aria-labelledby", "").strip())
                if has_aria_label or has_aria_labelledby:
                    result.passes.append(node)
                    result.check_details[id(node)] = NodeCheckDetail(
                        any=[make_check("frame-title", "serious",
                            "Element has an accessible name via ARIA")]
                    )
                else:
                    result.violations.append(node)
                    result.check_details[id(node)] = NodeCheckDetail(
                        any=[make_check("frame-title", "serious",
                            "Element does not have an accessible name")]
                    )
        return result


class _FrameTitleUnique:
    rule_id = "frame-title-unique"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        frames = [
            n for n in nodes
            if n.tag in ("iframe", "frame") and not is_hidden_or_ancestor_hidden(n)
        ]
        title_map: dict[str, list[FastNode]] = defaultdict(list)
        for node in frames:
            title = (node.attrs.get("title") or "").strip().lower()
            if title:
                title_map[title].append(node)
        for title, frame_list in title_map.items():
            if len(frame_list) > 1:
                srcs = {f.attrs.get("src", "") for f in frame_list}
                if len(srcs) > 1:
                    for node in frame_list:
                        result.violations.append(node)
                        result.check_details[id(node)] = NodeCheckDetail(
                            any=[make_check("frame-title-unique", "serious",
                                f'Multiple frames have the same title "{title}" but different content')]
                        )
                else:
                    for node in frame_list:
                        result.passes.append(node)
                        result.check_details[id(node)] = NodeCheckDetail(
                            any=[make_check("frame-title-unique", "serious",
                                "Frames with same title have same source")]
                        )
            else:
                result.passes.append(frame_list[0])
                result.check_details[id(frame_list[0])] = NodeCheckDetail(
                    any=[make_check("frame-title-unique", "serious", "Frame title is unique")]
                )
        return result


class _Bypass:
    rule_id = "bypass"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        html_nodes = find_by_tag(nodes, "html")
        target = html_nodes[0] if html_nodes else (nodes[0] if nodes else None)
        if not target:
            return result
        has_skip_link = any(
            n.tag == "a" and n.attrs.get("href", "").startswith("#")
            and len(n.attrs.get("href", "")) >= 2
            and any(t.attrs.get("id") == n.attrs["href"][1:] for t in all_nodes)
            for n in nodes
        )
        has_landmarks = any(
            get_role(n) in LANDMARK_ROLES for n in nodes if get_role(n)
        )
        has_headings = any(
            re.match(r"^h[1-6]$", n.tag) and not is_hidden_or_ancestor_hidden(n)
            for n in nodes
        )
        if has_skip_link or has_landmarks or has_headings:
            methods = []
            if has_skip_link:
                methods.append("skip link")
            if has_landmarks:
                methods.append("landmarks")
            if has_headings:
                methods.append("headings")
            result.passes.append(target)
            result.check_details[id(target)] = NodeCheckDetail(
                any=[make_check("bypass", "serious",
                    f"Page has mechanism to bypass repeated blocks: {', '.join(methods)}")]
            )
        else:
            result.violations.append(target)
            result.check_details[id(target)] = NodeCheckDetail(
                any=[make_check("bypass", "serious",
                    "Page does not have a mechanism to bypass repeated blocks")]
            )
        return result


class _Tabindex:
    rule_id = "tabindex"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        for node in nodes:
            if is_hidden_or_ancestor_hidden(node):
                continue
            tabindex = node.attrs.get("tabindex")
            if tabindex is None:
                continue
            try:
                value = int(tabindex)
            except ValueError:
                continue
            if value > 0:
                result.violations.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("tabindex", "serious",
                        f'Element has a tabindex greater than 0: tabindex="{tabindex}"')]
                )
            else:
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("tabindex", "serious",
                        "Element has appropriate tabindex value")]
                )
        return result


class _Accesskeys:
    rule_id = "accesskeys"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        key_map: dict[str, list[FastNode]] = defaultdict(list)
        for node in nodes:
            if is_hidden_or_ancestor_hidden(node):
                continue
            key = node.attrs.get("accesskey")
            if not key:
                continue
            key_map[key.lower()].append(node)
        for key, node_list in key_map.items():
            if len(node_list) > 1:
                for node in node_list:
                    result.violations.append(node)
                    result.check_details[id(node)] = NodeCheckDetail(
                        any=[make_check("accesskeys", "serious",
                            f'accesskey value "{key}" is not unique')]
                    )
            else:
                result.passes.append(node_list[0])
                result.check_details[id(node_list[0])] = NodeCheckDetail(
                    any=[make_check("accesskeys", "serious", "accesskey value is unique")]
                )
        return result


class _Region:
    rule_id = "region"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        ignored_tags = frozenset({
            "html", "head", "body", "script", "style", "link", "meta", "title",
            "noscript", "template", "base",
        })
        landmark_nodes: set[int] = set()
        for node in nodes:
            role = get_role(node)
            if role and role in LANDMARK_ROLES:
                landmark_nodes.add(id(node))
        if not landmark_nodes:
            return result

        def is_inside_landmark(node: FastNode) -> bool:
            current: FastNode | None = node
            while current:
                if id(current) in landmark_nodes:
                    return True
                current = current.parent
            return False

        body_nodes = find_by_tag(nodes, "body")
        if not body_nodes:
            return result
        for node in nodes:
            if node.tag in ignored_tags:
                continue
            if is_hidden_or_ancestor_hidden(node):
                continue
            if not is_inside_landmark(node):
                is_top_level = False
                p = node.parent
                while p:
                    if p.tag == "body":
                        is_top_level = True
                        break
                    p_role = get_role(p)
                    if p_role and p_role in LANDMARK_ROLES:
                        break
                    p = p.parent
                if is_top_level and id(node) in landmark_nodes:
                    result.passes.append(node)
                    result.check_details[id(node)] = NodeCheckDetail(
                        any=[make_check("region", "moderate", "Element is a landmark")]
                    )
                elif is_top_level and node.parent and node.parent.tag == "body":
                    result.violations.append(node)
                    result.check_details[id(node)] = NodeCheckDetail(
                        any=[make_check("region", "moderate",
                            "Element is not contained within a landmark region")]
                    )
        return result


navigation_rules = [
    _LinkName(),
    _FrameTitle(),
    _FrameTitleUnique(),
    _Bypass(),
    _Tabindex(),
    _Accesskeys(),
    _Region(),
]
