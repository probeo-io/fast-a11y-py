"""Structure rules: document-title, definition-list, dlitem, list, listitem,
heading-order, empty-heading, empty-table-header, duplicate-id,
duplicate-id-aria, nested-interactive, page-has-heading-one
"""

from __future__ import annotations

import re
from collections import defaultdict

from ..accessible_name import get_accessible_name
from ..rule_engine import NodeCheckDetail, RuleRunResult, make_check
from ..tree import (
    FastNode,
    find_by_tag,
    get_node_text,
    is_hidden_or_ancestor_hidden,
    is_interactive,
)


class _DocumentTitle:
    rule_id = "document-title"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        html_nodes = find_by_tag(nodes, "html")
        if not html_nodes:
            return result
        html_node = html_nodes[0]
        title_nodes = find_by_tag(nodes, "title")
        title_in_head = None
        for t in title_nodes:
            p = t.parent
            while p:
                if p.tag == "head":
                    title_in_head = t
                    break
                p = p.parent
            if title_in_head:
                break
        if title_in_head and get_node_text(title_in_head).strip():
            result.passes.append(html_node)
            result.check_details[id(html_node)] = NodeCheckDetail(
                any=[make_check("document-title", "serious",
                    "Document has a non-empty <title> element")]
            )
        else:
            result.violations.append(html_node)
            msg = ("Document has an empty <title> element"
                   if title_in_head
                   else "Document does not have a <title> element")
            result.check_details[id(html_node)] = NodeCheckDetail(
                any=[make_check("document-title", "serious", msg)]
            )
        return result


class _DefinitionList:
    rule_id = "definition-list"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        allowed = {"dt", "dd", "div", "script", "template"}
        for node in find_by_tag(nodes, "dl"):
            if is_hidden_or_ancestor_hidden(node):
                continue
            role = node.attrs.get("role")
            if role and role not in ("list", "none", "presentation"):
                result.passes.append(node)
                continue
            invalid_children = [c for c in node.children if c.tag not in allowed]
            if invalid_children:
                result.violations.append(node)
                bad_tags = ", ".join(f"<{c.tag}>" for c in invalid_children)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("definition-list", "serious",
                        f"List has invalid child element(s): {bad_tags}")]
                )
            else:
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("definition-list", "serious",
                        "List has only allowed child elements")]
                )
        return result


class _DlItem:
    rule_id = "dlitem"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        for node in nodes:
            if node.tag not in ("dt", "dd"):
                continue
            if is_hidden_or_ancestor_hidden(node):
                continue
            parent = node.parent
            found_dl = False
            while parent:
                if parent.tag == "dl":
                    found_dl = True
                    break
                if parent.tag == "div":
                    parent = parent.parent
                    continue
                break
            if found_dl:
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("dlitem", "serious", "Element is contained by a <dl>")]
                )
            else:
                result.violations.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("dlitem", "serious", "Element is not contained by a <dl>")]
                )
        return result


class _List:
    rule_id = "list"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        allowed = {"li", "script", "template"}
        for node in nodes:
            if node.tag not in ("ul", "ol"):
                continue
            if is_hidden_or_ancestor_hidden(node):
                continue
            role = node.attrs.get("role")
            if role and role != "list":
                result.passes.append(node)
                continue
            invalid_children = [c for c in node.children if c.tag not in allowed]
            if invalid_children:
                result.violations.append(node)
                bad_tags = ", ".join(f"<{c.tag}>" for c in invalid_children)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("list", "serious",
                        f"List has invalid child element(s): {bad_tags}")]
                )
            else:
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("list", "serious",
                        "List has only allowed child elements")]
                )
        return result


class _ListItem:
    rule_id = "listitem"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        for node in find_by_tag(nodes, "li"):
            if is_hidden_or_ancestor_hidden(node):
                continue
            parent = node.parent
            if parent:
                parent_tag = parent.tag
                parent_role = parent.attrs.get("role")
                if parent_tag in ("ul", "ol", "menu") or parent_role == "list":
                    result.passes.append(node)
                    result.check_details[id(node)] = NodeCheckDetail(
                        any=[make_check("listitem", "serious",
                            "Element is contained in a list")]
                    )
                    continue
            result.violations.append(node)
            result.check_details[id(node)] = NodeCheckDetail(
                any=[make_check("listitem", "serious",
                    'Element is not contained in a <ul>, <ol>, or element with role="list"')]
            )
        return result


class _HeadingOrder:
    rule_id = "heading-order"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        headings = [
            n for n in nodes
            if re.match(r"^h[1-6]$", n.tag) and not is_hidden_or_ancestor_hidden(n)
        ]
        prev_level = 0
        for node in headings:
            level = int(node.tag[1])
            if prev_level == 0 or level <= prev_level + 1:
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("heading-order", "moderate", "Heading order is valid")]
                )
            else:
                result.violations.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("heading-order", "moderate",
                        f"Heading level jumps from h{prev_level} to h{level}")]
                )
            prev_level = level
        return result


class _EmptyHeading:
    rule_id = "empty-heading"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        headings = [n for n in nodes if re.match(r"^h[1-6]$", n.tag)]
        for node in headings:
            if is_hidden_or_ancestor_hidden(node):
                continue
            name = get_accessible_name(node, all_nodes)
            if name:
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("empty-heading", "minor",
                        "Heading has discernible text")]
                )
            else:
                result.violations.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("empty-heading", "minor", "Heading is empty")]
                )
        return result


class _EmptyTableHeader:
    rule_id = "empty-table-header"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        for node in find_by_tag(nodes, "th"):
            if is_hidden_or_ancestor_hidden(node):
                continue
            name = get_accessible_name(node, all_nodes)
            if name:
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("empty-table-header", "minor",
                        "Table header has discernible text")]
                )
            else:
                result.violations.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("empty-table-header", "minor",
                        "Table header is empty")]
                )
        return result


class _DuplicateId:
    rule_id = "duplicate-id"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        id_map: dict[str, list[FastNode]] = defaultdict(list)
        for node in nodes:
            id_val = node.attrs.get("id")
            if id_val:
                id_map[id_val].append(node)
        for id_val, node_list in id_map.items():
            if len(node_list) > 1:
                for node in node_list:
                    result.violations.append(node)
                    result.check_details[id(node)] = NodeCheckDetail(
                        any=[make_check("duplicate-id", "minor",
                            f"Document has multiple elements with the same id attribute: {id_val}")]
                    )
            else:
                result.passes.append(node_list[0])
                result.check_details[id(node_list[0])] = NodeCheckDetail(
                    any=[make_check("duplicate-id", "minor",
                        "Document has no elements with the same id")]
                )
        return result


class _DuplicateIdAria:
    rule_id = "duplicate-id-aria"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        referenced_ids: set[str] = set()
        for node in nodes:
            for attr in ("aria-labelledby", "aria-describedby"):
                val = node.attrs.get(attr)
                if val:
                    for id_val in val.strip().split():
                        referenced_ids.add(id_val)
        if not referenced_ids:
            return result
        id_map: dict[str, list[FastNode]] = defaultdict(list)
        for node in nodes:
            id_val = node.attrs.get("id")
            if id_val and id_val in referenced_ids:
                id_map[id_val].append(node)
        for id_val, node_list in id_map.items():
            if len(node_list) > 1:
                for node in node_list:
                    result.violations.append(node)
                    result.check_details[id(node)] = NodeCheckDetail(
                        any=[make_check("duplicate-id-aria", "critical",
                            f"Document has multiple elements referenced with ARIA with the same id attribute: {id_val}")]
                    )
            else:
                result.passes.append(node_list[0])
                result.check_details[id(node_list[0])] = NodeCheckDetail(
                    any=[make_check("duplicate-id-aria", "critical",
                        "ARIA referenced id is unique")]
                )
        return result


class _NestedInteractive:
    rule_id = "nested-interactive"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        for node in nodes:
            if not is_interactive(node):
                continue
            if is_hidden_or_ancestor_hidden(node):
                continue
            interactive_descendants = _find_interactive_descendants(node)
            if interactive_descendants:
                result.violations.append(node)
                tags = ", ".join(f"<{d.tag}>" for d in interactive_descendants)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("nested-interactive", "serious",
                        f"Element has nested interactive element(s): {tags}")]
                )
            else:
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("nested-interactive", "serious",
                        "Element does not contain nested interactive elements")]
                )
        return result


def _find_interactive_descendants(node: FastNode) -> list[FastNode]:
    found: list[FastNode] = []

    def walk(children: list[FastNode]) -> None:
        for child in children:
            if is_interactive(child):
                found.append(child)
            walk(child.children)

    walk(node.children)
    return found


class _PageHasHeadingOne:
    rule_id = "page-has-heading-one"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        h1_nodes = [
            n for n in find_by_tag(nodes, "h1") if not is_hidden_or_ancestor_hidden(n)
        ]
        role_heading_one = [
            n for n in nodes
            if n.attrs.get("role") == "heading"
            and n.attrs.get("aria-level") == "1"
            and not is_hidden_or_ancestor_hidden(n)
        ]
        all_h1 = h1_nodes + role_heading_one
        html_nodes = find_by_tag(nodes, "html")
        target = html_nodes[0] if html_nodes else (nodes[0] if nodes else None)
        if not target:
            return result
        if all_h1:
            result.passes.append(target)
            result.check_details[id(target)] = NodeCheckDetail(
                any=[make_check("page-has-heading-one", "moderate",
                    "Page has at least one level-one heading")]
            )
        else:
            result.violations.append(target)
            result.check_details[id(target)] = NodeCheckDetail(
                any=[make_check("page-has-heading-one", "moderate",
                    "Page does not have a level-one heading")]
            )
        return result


structure_rules = [
    _DocumentTitle(),
    _DefinitionList(),
    _DlItem(),
    _List(),
    _ListItem(),
    _HeadingOrder(),
    _EmptyHeading(),
    _EmptyTableHeader(),
    _DuplicateId(),
    _DuplicateIdAria(),
    _NestedInteractive(),
    _PageHasHeadingOne(),
]
