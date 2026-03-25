"""Lightweight DOM tree built from stdlib html.parser.

Provides parent/child traversal, attribute access, text extraction,
CSS selector generation, and outerHTML snippets.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Any, Callable


@dataclass
class FastNode:
    """A node in the parsed HTML tree."""

    tag: str
    attrs: dict[str, str]
    parent: FastNode | None = field(default=None, repr=False)
    children: list[FastNode] = field(default_factory=list, repr=False)
    child_nodes: list[Any] = field(default_factory=list, repr=False)
    depth: int = 0


@dataclass
class TextNode:
    """A text node in the tree."""

    data: str
    type: str = "text"


# Self-closing / void tags that never have children.
VOID_TAGS = frozenset({
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
})


class _TreeBuilder(HTMLParser):
    """Build a FastNode tree from HTML using stdlib html.parser."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root_children: list[FastNode] = []
        self._all_nodes: list[FastNode] = []
        self._stack: list[FastNode] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attr_dict: dict[str, str] = {}
        for k, v in attrs:
            attr_dict[k.lower()] = v if v is not None else ""

        parent = self._stack[-1] if self._stack else None
        node = FastNode(
            tag=tag,
            attrs=attr_dict,
            parent=parent,
            depth=len(self._stack),
        )
        if parent:
            parent.children.append(node)
            parent.child_nodes.append(node)
        else:
            self.root_children.append(node)
        self._all_nodes.append(node)

        if tag not in VOID_TAGS:
            self._stack.append(node)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        # Pop back to matching tag (handles unclosed tags gracefully)
        for i in range(len(self._stack) - 1, -1, -1):
            if self._stack[i].tag == tag:
                self._stack = self._stack[:i]
                return

    def handle_data(self, data: str) -> None:
        if self._stack:
            self._stack[-1].child_nodes.append(TextNode(data=data))

    def handle_comment(self, data: str) -> None:
        pass  # Ignore comments

    def handle_decl(self, decl: str) -> None:
        pass  # Ignore DOCTYPE

    def unknown_decl(self, data: str) -> None:
        pass


def parse(html: str) -> list[FastNode]:
    """Parse HTML string and return a flat list of all FastNodes."""
    builder = _TreeBuilder()
    builder.feed(html)
    return builder._all_nodes


def build_tree(html: str) -> list[FastNode]:
    """Parse HTML and return all FastNodes (flat list for iteration)."""
    return parse(html)


def get_text_content(node: FastNode | TextNode) -> str:
    """Get text content of a node (recursive, like textContent)."""
    if isinstance(node, TextNode):
        return node.data

    text = ""
    for child in node.child_nodes:
        if isinstance(child, TextNode):
            text += child.data
        elif isinstance(child, FastNode):
            text += get_text_content(child)
    return text


def get_node_text(node: FastNode) -> str:
    """Get trimmed text content from a FastNode."""
    return get_text_content(node).strip()


def get_selector(node: FastNode) -> str:
    """Generate a CSS selector path for a node (for axe-compatible target[])."""
    parts: list[str] = []
    current: FastNode | None = node

    while current:
        selector = current.tag

        if current.attrs.get("id"):
            selector = f"#{_css_escape(current.attrs['id'])}"
            parts.insert(0, selector)
            break

        if current.parent:
            same_tag_siblings = [c for c in current.parent.children if c.tag == current.tag]
            if len(same_tag_siblings) > 1:
                idx = same_tag_siblings.index(current) + 1
                selector += f":nth-child({idx})"

        parts.insert(0, selector)
        current = current.parent

    return " > ".join(parts)


def get_outer_html(node: FastNode, max_length: int = 250) -> str:
    """Generate an outerHTML snippet for a node (truncated for readability)."""
    tag = node.tag
    attr_parts = []
    for k, v in node.attrs.items():
        if v == "":
            attr_parts.append(k)
        else:
            attr_parts.append(f'{k}="{_escape_attr(v)}"')
    attr_str = " ".join(attr_parts)

    open_tag = f"<{tag} {attr_str}>" if attr_str else f"<{tag}>"

    if tag in VOID_TAGS:
        return open_tag[:max_length] + "..." if len(open_tag) > max_length else open_tag

    inner_text = get_node_text(node)
    inner = inner_text[:50] + "..." if len(inner_text) > 50 else inner_text
    full = f"{open_tag}{inner}</{tag}>"
    return full[:max_length] + "..." if len(full) > max_length else full


def find_by_tag(nodes: list[FastNode], tag: str) -> list[FastNode]:
    """Find all nodes matching a tag name."""
    return [n for n in nodes if n.tag == tag]


def find_by_id(nodes: list[FastNode], id_val: str) -> FastNode | None:
    """Find a node by ID."""
    for n in nodes:
        if n.attrs.get("id") == id_val:
            return n
    return None


def get_role(node: FastNode) -> str | None:
    """Get the effective role (explicit or implicit)."""
    if node.attrs.get("role"):
        return node.attrs["role"]

    implicit_roles: dict[str, str | Callable[[FastNode], str | None]] = {
        "a": lambda n: "link" if "href" in n.attrs else None,
        "article": "article",
        "aside": "complementary",
        "button": "button",
        "details": "group",
        "dialog": "dialog",
        "footer": "contentinfo",
        "form": "form",
        "h1": "heading",
        "h2": "heading",
        "h3": "heading",
        "h4": "heading",
        "h5": "heading",
        "h6": "heading",
        "header": "banner",
        "hr": "separator",
        "img": lambda n: "presentation" if n.attrs.get("alt") == "" else "img",
        "input": _input_implicit_role,
        "li": "listitem",
        "main": "main",
        "math": "math",
        "menu": "list",
        "nav": "navigation",
        "ol": "list",
        "optgroup": "group",
        "option": "option",
        "output": "status",
        "progress": "progressbar",
        "section": lambda n: (
            "region"
            if n.attrs.get("aria-label") or n.attrs.get("aria-labelledby")
            else None
        ),
        "select": lambda n: (
            "listbox"
            if "multiple" in n.attrs or int(n.attrs.get("size", "1")) > 1
            else "combobox"
        ),
        "summary": "button",
        "table": "table",
        "tbody": "rowgroup",
        "td": "cell",
        "textarea": "textbox",
        "tfoot": "rowgroup",
        "th": lambda n: "columnheader" if n.attrs.get("scope") == "col" else "rowheader",
        "thead": "rowgroup",
        "tr": "row",
        "ul": "list",
    }

    mapping = implicit_roles.get(node.tag)
    if callable(mapping):
        return mapping(node)
    return mapping


def _input_implicit_role(node: FastNode) -> str | None:
    """Get implicit role for <input> based on type."""
    type_val = (node.attrs.get("type") or "text").lower()
    type_roles: dict[str, str] = {
        "button": "button",
        "checkbox": "checkbox",
        "email": "textbox",
        "image": "button",
        "number": "spinbutton",
        "radio": "radio",
        "range": "slider",
        "reset": "button",
        "search": "searchbox",
        "submit": "button",
        "tel": "textbox",
        "text": "textbox",
        "url": "textbox",
    }
    return type_roles.get(type_val)


def is_focusable(node: FastNode) -> bool:
    """Check if a node is focusable."""
    if "disabled" in node.attrs:
        return False
    if node.attrs.get("tabindex") == "-1":
        return False
    if node.attrs.get("tabindex") is not None:
        return True
    focusable_tags = {"a", "button", "input", "select", "textarea", "summary"}
    if node.tag in focusable_tags:
        if node.tag == "a" and "href" not in node.attrs:
            return False
        return True
    return False


def is_interactive(node: FastNode) -> bool:
    """Check if a node is interactive."""
    interactive_tags = {"a", "button", "input", "select", "textarea", "summary", "details"}
    if node.tag in interactive_tags:
        if node.tag == "a" and "href" not in node.attrs:
            return False
        if node.tag == "input" and node.attrs.get("type") == "hidden":
            return False
        return True
    tabindex = node.attrs.get("tabindex")
    if tabindex is not None and tabindex != "-1":
        return True
    role = node.attrs.get("role")
    if role:
        interactive_roles = {
            "button", "link", "checkbox", "radio", "tab", "switch",
            "menuitem", "menuitemcheckbox", "menuitemradio", "option",
            "combobox", "textbox", "searchbox", "spinbutton", "slider",
        }
        if role in interactive_roles:
            return True
    return False


def is_hidden(node: FastNode) -> bool:
    """Check if a node is hidden via static analysis."""
    if "hidden" in node.attrs:
        return True
    if node.attrs.get("aria-hidden") == "true":
        return True
    if node.tag == "input" and node.attrs.get("type") == "hidden":
        return True
    style = node.attrs.get("style", "")
    if re.search(r"display\s*:\s*none", style, re.IGNORECASE):
        return True
    if re.search(r"visibility\s*:\s*hidden", style, re.IGNORECASE):
        return True
    return False


def is_hidden_or_ancestor_hidden(node: FastNode) -> bool:
    """Check if a node or any ancestor is hidden."""
    current: FastNode | None = node
    while current:
        if is_hidden(current):
            return True
        current = current.parent
    return False


def _css_escape(s: str) -> str:
    """Escape a string for use in a CSS selector."""
    return re.sub(r"([^\w-])", r"\\\1", s)


def _escape_attr(s: str) -> str:
    """Escape a string for use in an HTML attribute."""
    return s.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")
