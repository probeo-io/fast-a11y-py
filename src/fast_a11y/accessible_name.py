"""Simplified Accessible Name Computation.

Follows the W3C Accessible Name and Description Computation algorithm,
simplified for static HTML analysis.

Priority: aria-labelledby > aria-label > native label > alt/title > text content
"""

from __future__ import annotations

import re

from .tree import FastNode, TextNode, find_by_id, get_node_text, get_text_content


def get_accessible_name(node: FastNode, all_nodes: list[FastNode]) -> str:
    """Compute the accessible name for a node.

    Returns empty string if no accessible name can be determined.
    """
    # 1. aria-labelledby -- resolve referenced IDs, concatenate
    labelled_by = node.attrs.get("aria-labelledby")
    if labelled_by:
        ids = labelled_by.strip().split()
        parts: list[str] = []
        for id_val in ids:
            referenced = find_by_id(all_nodes, id_val)
            if referenced:
                parts.append(get_node_text(referenced))
        result = " ".join(parts).strip()
        if result:
            return result

    # 2. aria-label
    aria_label = node.attrs.get("aria-label")
    if aria_label and aria_label.strip():
        return aria_label.strip()

    # 3. Native labelling mechanisms
    native_name = _get_native_name(node, all_nodes)
    if native_name:
        return native_name

    # 4. title attribute (last resort)
    title = node.attrs.get("title")
    if title and title.strip():
        return title.strip()

    return ""


def _get_native_name(node: FastNode, all_nodes: list[FastNode]) -> str:
    """Get name from native HTML labelling mechanisms."""
    tag = node.tag

    # <img>, <input type="image"> -- alt attribute
    if tag == "img" or (tag == "input" and node.attrs.get("type") == "image"):
        alt = node.attrs.get("alt")
        if alt is not None:
            return alt.strip()

    # <input>, <select>, <textarea> -- associated <label>
    if tag in ("input", "select", "textarea"):
        id_val = node.attrs.get("id")
        if id_val:
            # Find <label for="id">
            for n in all_nodes:
                if n.tag == "label" and n.attrs.get("for") == id_val:
                    text = get_node_text(n)
                    if text:
                        return text
                    break

        # Check if wrapped in <label>
        parent = node.parent
        while parent:
            if parent.tag == "label":
                text = _get_label_text_excluding_input(parent, node)
                if text:
                    return text
            parent = parent.parent

        # <input> value for buttons
        if tag == "input":
            type_val = (node.attrs.get("type") or "").lower()
            if type_val == "submit":
                return node.attrs.get("value", "Submit")
            if type_val == "reset":
                return node.attrs.get("value", "Reset")
            if type_val == "button":
                return node.attrs.get("value", "")
            if type_val == "image":
                return node.attrs.get("alt") or node.attrs.get("value", "")

        # Placeholder as last resort
        placeholder = node.attrs.get("placeholder")
        if placeholder:
            return placeholder.strip()

        return ""

    # <fieldset> -- <legend>
    if tag == "fieldset":
        for child in node.children:
            if child.tag == "legend":
                return get_node_text(child)

    # <table> -- <caption>
    if tag == "table":
        for child in node.children:
            if child.tag == "caption":
                return get_node_text(child)

    # <figure> -- <figcaption>
    if tag == "figure":
        for child in node.children:
            if child.tag == "figcaption":
                return get_node_text(child)

    # <a>, <button>, headings, etc. -- text content (including alt text from child images)
    if tag in ("a", "button", "summary", "legend", "caption", "option") or re.match(
        r"^h[1-6]$", tag
    ):
        return get_accessible_text(node, all_nodes)

    # Generic: text content
    text = get_node_text(node)
    if text:
        return text

    return ""


def get_accessible_text(node: FastNode, all_nodes: list[FastNode]) -> str:
    """Get accessible text content, including alt text from child images.

    This is different from plain textContent -- it resolves image alt text.
    """
    parts: list[str] = []

    for child in node.child_nodes:
        if isinstance(child, TextNode):
            parts.append(child.data)
        elif isinstance(child, FastNode):
            if child.tag == "img":
                alt = child.attrs.get("alt")
                if alt:
                    parts.append(alt)
            elif child.tag == "svg":
                # Check for <title> child in SVG
                for svg_child in child.children:
                    if svg_child.tag == "title":
                        parts.append(get_text_content(svg_child))
                        break
            else:
                # Find the FastNode in all_nodes for recursive resolution
                fast_child = child
                parts.append(get_accessible_text(fast_child, all_nodes))

    return "".join(parts).strip()


def _get_label_text_excluding_input(label: FastNode, input_node: FastNode) -> str:
    """Get label text excluding the input element's own text."""
    parts: list[str] = []

    def walk(node: FastNode) -> None:
        for child in node.child_nodes:
            if isinstance(child, TextNode):
                parts.append(child.data)
            elif isinstance(child, FastNode) and child is not input_node:
                walk(child)

    walk(label)
    return "".join(parts).strip()
