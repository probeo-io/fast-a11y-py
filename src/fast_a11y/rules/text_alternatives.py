"""Text alternative rules: image-alt, input-image-alt, object-alt,
role-img-alt, svg-img-alt, area-alt, server-side-image-map
"""

from __future__ import annotations

from ..accessible_name import get_accessible_name
from ..rule_engine import NodeCheckDetail, RuleCheck, RuleRunResult, make_check
from ..tree import FastNode, find_by_tag, get_node_text, is_hidden_or_ancestor_hidden


class _ImageAlt:
    rule_id = "image-alt"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        for node in find_by_tag(nodes, "img"):
            if is_hidden_or_ancestor_hidden(node):
                continue
            role = node.attrs.get("role")
            if role in ("none", "presentation"):
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("image-alt", "critical", f'Element has role="{role}"')]
                )
                continue
            has_alt = "alt" in node.attrs
            has_aria_label = bool(node.attrs.get("aria-label", "").strip())
            has_aria_labelledby = bool(node.attrs.get("aria-labelledby", "").strip())
            if has_alt or has_aria_label or has_aria_labelledby:
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("image-alt", "critical", "Element has alternative text")]
                )
            else:
                result.violations.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("image-alt", "critical",
                        'Element does not have an alt attribute, and does not have role="none" or role="presentation"')]
                )
        return result


class _InputImageAlt:
    rule_id = "input-image-alt"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        for node in find_by_tag(nodes, "input"):
            if is_hidden_or_ancestor_hidden(node):
                continue
            if (node.attrs.get("type") or "").lower() != "image":
                continue
            name = get_accessible_name(node, all_nodes)
            if name:
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("input-image-alt", "critical", "Element has an accessible name")]
                )
            else:
                result.violations.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("input-image-alt", "critical", "Element has no accessible name")]
                )
        return result


class _ObjectAlt:
    rule_id = "object-alt"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        for node in find_by_tag(nodes, "object"):
            if is_hidden_or_ancestor_hidden(node):
                continue
            role = node.attrs.get("role")
            if role in ("none", "presentation"):
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("object-alt", "serious", f'Element has role="{role}"')]
                )
                continue
            has_aria_label = bool(node.attrs.get("aria-label", "").strip())
            has_aria_labelledby = bool(node.attrs.get("aria-labelledby", "").strip())
            has_title = bool(node.attrs.get("title", "").strip())
            has_text = bool(get_node_text(node))
            if has_aria_label or has_aria_labelledby or has_title or has_text:
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("object-alt", "serious", "Element has alternative text")]
                )
            else:
                result.violations.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("object-alt", "serious",
                        "Element does not have alt text (aria-label, aria-labelledby, title, or text content)")]
                )
        return result


class _RoleImgAlt:
    rule_id = "role-img-alt"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        for node in nodes:
            if is_hidden_or_ancestor_hidden(node):
                continue
            if node.attrs.get("role") != "img":
                continue
            name = get_accessible_name(node, all_nodes)
            if name:
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("role-img-alt", "serious", "Element has an accessible name")]
                )
            else:
                result.violations.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("role-img-alt", "serious", "Element has no accessible name")]
                )
        return result


class _SvgImgAlt:
    rule_id = "svg-img-alt"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        for node in find_by_tag(nodes, "svg"):
            if is_hidden_or_ancestor_hidden(node):
                continue
            if node.attrs.get("role") != "img":
                continue
            has_aria_label = bool(node.attrs.get("aria-label", "").strip())
            has_aria_labelledby = bool(node.attrs.get("aria-labelledby", "").strip())
            has_title_child = any(
                c.tag == "title" and get_node_text(c) for c in node.children
            )
            if has_aria_label or has_aria_labelledby or has_title_child:
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("svg-img-alt", "serious", "Element has an accessible name")]
                )
            else:
                result.violations.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("svg-img-alt", "serious", "Element has no accessible name")]
                )
        return result


class _AreaAlt:
    rule_id = "area-alt"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        for node in find_by_tag(nodes, "area"):
            if is_hidden_or_ancestor_hidden(node):
                continue
            if "href" not in node.attrs:
                continue
            has_alt = bool(node.attrs.get("alt", "").strip())
            has_aria_label = bool(node.attrs.get("aria-label", "").strip())
            has_aria_labelledby = bool(node.attrs.get("aria-labelledby", "").strip())
            if has_alt or has_aria_label or has_aria_labelledby:
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("area-alt", "critical", "Element has alternative text")]
                )
            else:
                result.violations.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("area-alt", "critical", "Element does not have alt text")]
                )
        return result


class _ServerSideImageMap:
    rule_id = "server-side-image-map"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        for node in find_by_tag(nodes, "img"):
            if is_hidden_or_ancestor_hidden(node):
                continue
            if "ismap" in node.attrs:
                result.violations.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("server-side-image-map", "minor",
                        "Element has ismap attribute -- server-side image maps should not be used")]
                )
            else:
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("server-side-image-map", "minor",
                        "Element does not use a server-side image map")]
                )
        return result


text_alternative_rules: list[RuleCheck] = [
    _ImageAlt(),
    _InputImageAlt(),
    _ObjectAlt(),
    _RoleImgAlt(),
    _SvgImgAlt(),
    _AreaAlt(),
    _ServerSideImageMap(),
]
