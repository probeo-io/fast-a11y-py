"""ARIA rules: aria-allowed-attr, aria-hidden-body, aria-hidden-focus,
aria-required-attr, aria-required-children, aria-required-parent,
aria-roles, aria-valid-attr, aria-valid-attr-value, aria-roledescription,
aria-input-field-name, aria-toggle-field-name, aria-command-name,
aria-meter-name, aria-progressbar-name, aria-tooltip-name,
aria-treeitem-name, aria-dialog-name, aria-text, aria-deprecated-role,
aria-prohibited-attr, aria-braille-equivalent, aria-allowed-role,
aria-conditional-attr, presentation-role-conflict
"""

from __future__ import annotations

from ..accessible_name import get_accessible_name
from ..rule_engine import NodeCheckDetail, RuleRunResult, make_check
from ..tree import (
    FastNode,
    find_by_tag,
    get_role,
    is_focusable,
    is_hidden_or_ancestor_hidden,
)
from ..types import ImpactValue

# ═══════════════════════════════════════════════════════════════════════
#  Lookup tables
# ═══════════════════════════════════════════════════════════════════════

VALID_ROLES = frozenset({
    "alert", "alertdialog", "application", "article", "banner", "blockquote",
    "button", "caption", "cell", "checkbox", "code", "columnheader", "combobox",
    "command", "comment", "complementary", "composite", "contentinfo", "definition",
    "deletion", "dialog", "directory", "document", "emphasis", "feed", "figure",
    "form", "generic", "grid", "gridcell", "group", "heading", "img", "input",
    "insertion", "landmark", "link", "list", "listbox", "listitem", "log", "main",
    "mark", "marquee", "math", "menu", "menubar", "menuitem", "menuitemcheckbox",
    "menuitemradio", "meter", "navigation", "none", "note", "option", "paragraph",
    "presentation", "progressbar", "radio", "radiogroup", "range", "region",
    "roletype", "row", "rowgroup", "rowheader", "scrollbar", "search", "searchbox",
    "section", "sectionhead", "select", "separator", "slider", "spinbutton",
    "status", "strong", "structure", "subscript", "superscript", "switch", "tab",
    "table", "tablist", "tabpanel", "term", "text", "textbox", "time", "timer",
    "toolbar", "tooltip", "tree", "treegrid", "treeitem", "widget", "window",
})

DEPRECATED_ROLES = frozenset({"directory"})

REQUIRED_ATTRS: dict[str, list[str]] = {
    "checkbox": ["aria-checked"],
    "combobox": ["aria-expanded"],
    "heading": ["aria-level"],
    "meter": ["aria-valuemin", "aria-valuemax", "aria-valuenow"],
    "option": ["aria-selected"],
    "radio": ["aria-checked"],
    "scrollbar": ["aria-controls", "aria-valuenow"],
    "separator": [],
    "slider": ["aria-valuenow"],
    "spinbutton": ["aria-valuenow"],
    "switch": ["aria-checked"],
}

REQUIRED_CHILDREN: dict[str, list[str]] = {
    "feed": ["article"],
    "grid": ["row", "rowgroup"],
    "list": ["listitem"],
    "listbox": ["option", "group"],
    "menu": ["menuitem", "menuitemcheckbox", "menuitemradio", "group"],
    "menubar": ["menuitem", "menuitemcheckbox", "menuitemradio", "group"],
    "radiogroup": ["radio"],
    "row": ["cell", "columnheader", "gridcell", "rowheader"],
    "rowgroup": ["row"],
    "tablist": ["tab"],
    "table": ["row", "rowgroup"],
    "tree": ["treeitem", "group"],
    "treegrid": ["row", "rowgroup"],
}

REQUIRED_PARENT: dict[str, list[str]] = {
    "caption": ["figure", "grid", "listbox", "table", "tablist", "tree", "treegrid"],
    "cell": ["row"],
    "columnheader": ["row"],
    "gridcell": ["row"],
    "listitem": ["list", "group"],
    "menuitem": ["menu", "menubar", "group"],
    "menuitemcheckbox": ["menu", "menubar", "group"],
    "menuitemradio": ["menu", "menubar", "group"],
    "option": ["listbox", "group"],
    "row": ["grid", "rowgroup", "table", "treegrid"],
    "rowheader": ["row"],
    "tab": ["tablist"],
    "treeitem": ["tree", "group"],
}

GLOBAL_ARIA_ATTRS = frozenset({
    "aria-atomic", "aria-braillelabel", "aria-brailleroledescription",
    "aria-busy", "aria-controls", "aria-current", "aria-describedby",
    "aria-description", "aria-details", "aria-disabled", "aria-dropeffect",
    "aria-errormessage", "aria-flowto", "aria-grabbed", "aria-haspopup",
    "aria-hidden", "aria-invalid", "aria-keyshortcuts", "aria-label",
    "aria-labelledby", "aria-live", "aria-owns", "aria-relevant",
    "aria-roledescription",
})

VALID_ARIA_ATTRS = frozenset({
    *GLOBAL_ARIA_ATTRS,
    "aria-activedescendant", "aria-autocomplete", "aria-checked",
    "aria-colcount", "aria-colindex", "aria-colindextext", "aria-colspan",
    "aria-expanded", "aria-level", "aria-modal", "aria-multiline",
    "aria-multiselectable", "aria-orientation", "aria-placeholder",
    "aria-posinset", "aria-pressed", "aria-readonly", "aria-required",
    "aria-rowcount", "aria-rowindex", "aria-rowindextext", "aria-rowspan",
    "aria-selected", "aria-setsize", "aria-sort",
    "aria-valuemax", "aria-valuemin", "aria-valuenow", "aria-valuetext",
})

ROLE_ALLOWED_ATTRS: dict[str, list[str]] = {
    "alert": [],
    "alertdialog": ["aria-modal"],
    "application": ["aria-activedescendant", "aria-expanded"],
    "article": ["aria-expanded"],
    "banner": [],
    "button": ["aria-expanded", "aria-pressed"],
    "cell": [
        "aria-colindex", "aria-colspan", "aria-rowindex", "aria-rowspan",
        "aria-colindextext", "aria-rowindextext",
    ],
    "checkbox": ["aria-checked", "aria-expanded", "aria-readonly", "aria-required"],
    "columnheader": [
        "aria-colindex", "aria-colspan", "aria-expanded", "aria-readonly",
        "aria-required", "aria-rowindex", "aria-rowspan", "aria-selected",
        "aria-sort", "aria-colindextext", "aria-rowindextext",
    ],
    "combobox": ["aria-activedescendant", "aria-autocomplete", "aria-expanded", "aria-readonly", "aria-required"],
    "complementary": [],
    "contentinfo": [],
    "definition": [],
    "dialog": ["aria-modal"],
    "document": ["aria-expanded"],
    "feed": [],
    "figure": [],
    "form": [],
    "grid": [
        "aria-activedescendant", "aria-colcount", "aria-expanded", "aria-level",
        "aria-multiselectable", "aria-readonly", "aria-rowcount",
    ],
    "gridcell": [
        "aria-colindex", "aria-colspan", "aria-expanded", "aria-readonly",
        "aria-required", "aria-rowindex", "aria-rowspan", "aria-selected",
        "aria-colindextext", "aria-rowindextext",
    ],
    "group": ["aria-activedescendant", "aria-expanded"],
    "heading": ["aria-expanded", "aria-level"],
    "img": [],
    "link": ["aria-expanded"],
    "list": [],
    "listbox": [
        "aria-activedescendant", "aria-expanded", "aria-multiselectable",
        "aria-orientation", "aria-readonly", "aria-required",
    ],
    "listitem": ["aria-expanded", "aria-level", "aria-posinset", "aria-setsize"],
    "log": [],
    "main": [],
    "math": [],
    "menu": ["aria-activedescendant", "aria-orientation"],
    "menubar": ["aria-activedescendant", "aria-orientation"],
    "menuitem": ["aria-expanded", "aria-posinset", "aria-setsize"],
    "menuitemcheckbox": ["aria-checked", "aria-expanded", "aria-posinset", "aria-setsize"],
    "menuitemradio": ["aria-checked", "aria-expanded", "aria-posinset", "aria-setsize"],
    "meter": ["aria-valuemax", "aria-valuemin", "aria-valuenow", "aria-valuetext"],
    "navigation": [],
    "none": [],
    "note": [],
    "option": ["aria-checked", "aria-posinset", "aria-selected", "aria-setsize"],
    "presentation": [],
    "progressbar": ["aria-valuemax", "aria-valuemin", "aria-valuenow", "aria-valuetext"],
    "radio": ["aria-checked", "aria-posinset", "aria-setsize"],
    "radiogroup": ["aria-activedescendant", "aria-expanded", "aria-orientation", "aria-readonly", "aria-required"],
    "region": [],
    "row": [
        "aria-activedescendant", "aria-colindex", "aria-expanded", "aria-level",
        "aria-posinset", "aria-rowindex", "aria-selected", "aria-setsize",
        "aria-colindextext", "aria-rowindextext",
    ],
    "rowgroup": [],
    "rowheader": [
        "aria-colindex", "aria-colspan", "aria-expanded", "aria-readonly",
        "aria-required", "aria-rowindex", "aria-rowspan", "aria-selected",
        "aria-sort", "aria-colindextext", "aria-rowindextext",
    ],
    "scrollbar": [
        "aria-controls", "aria-orientation", "aria-valuemax",
        "aria-valuemin", "aria-valuenow", "aria-valuetext",
    ],
    "search": [],
    "searchbox": [
        "aria-activedescendant", "aria-autocomplete", "aria-multiline",
        "aria-placeholder", "aria-readonly", "aria-required",
    ],
    "separator": ["aria-orientation", "aria-valuemax", "aria-valuemin", "aria-valuenow", "aria-valuetext"],
    "slider": [
        "aria-orientation", "aria-readonly", "aria-valuemax",
        "aria-valuemin", "aria-valuenow", "aria-valuetext",
    ],
    "spinbutton": [
        "aria-readonly", "aria-required", "aria-valuemax",
        "aria-valuemin", "aria-valuenow", "aria-valuetext",
    ],
    "status": [],
    "switch": ["aria-checked", "aria-readonly", "aria-required"],
    "tab": ["aria-expanded", "aria-posinset", "aria-selected", "aria-setsize"],
    "table": ["aria-colcount", "aria-rowcount"],
    "tablist": ["aria-activedescendant", "aria-multiselectable", "aria-orientation"],
    "tabpanel": [],
    "term": [],
    "textbox": [
        "aria-activedescendant", "aria-autocomplete", "aria-multiline",
        "aria-placeholder", "aria-readonly", "aria-required",
    ],
    "timer": [],
    "toolbar": ["aria-activedescendant", "aria-orientation"],
    "tooltip": [],
    "tree": ["aria-activedescendant", "aria-multiselectable", "aria-orientation", "aria-required"],
    "treegrid": [
        "aria-activedescendant", "aria-colcount", "aria-expanded", "aria-level",
        "aria-multiselectable", "aria-orientation", "aria-readonly",
        "aria-required", "aria-rowcount",
    ],
    "treeitem": ["aria-checked", "aria-expanded", "aria-level", "aria-posinset", "aria-selected", "aria-setsize"],
}

PROHIBITED_ATTRS: dict[str, list[str]] = {
    "caption": ["aria-label", "aria-labelledby"],
    "code": ["aria-label", "aria-labelledby"],
    "definition": ["aria-label", "aria-labelledby"],
    "deletion": ["aria-label", "aria-labelledby"],
    "emphasis": ["aria-label", "aria-labelledby"],
    "generic": ["aria-label", "aria-labelledby", "aria-roledescription"],
    "insertion": ["aria-label", "aria-labelledby"],
    "none": ["aria-label", "aria-labelledby"],
    "paragraph": ["aria-label", "aria-labelledby"],
    "presentation": ["aria-label", "aria-labelledby"],
    "strong": ["aria-label", "aria-labelledby"],
    "subscript": ["aria-label", "aria-labelledby"],
    "superscript": ["aria-label", "aria-labelledby"],
}

ROLEDESCRIPTION_SUPPORTED_ROLES = frozenset({
    "alert", "alertdialog", "application", "article", "banner", "button",
    "cell", "checkbox", "columnheader", "combobox", "complementary",
    "contentinfo", "definition", "dialog", "document", "feed", "figure",
    "form", "grid", "gridcell", "group", "heading", "img", "landmark",
    "link", "list", "listbox", "listitem", "log", "main", "marquee",
    "math", "menu", "menubar", "menuitem", "menuitemcheckbox", "menuitemradio",
    "meter", "navigation", "note", "option", "progressbar", "radio",
    "radiogroup", "region", "row", "rowgroup", "rowheader", "scrollbar",
    "search", "searchbox", "separator", "slider", "spinbutton", "status",
    "switch", "tab", "table", "tablist", "tabpanel", "term", "textbox",
    "timer", "toolbar", "tooltip", "tree", "treegrid", "treeitem",
})

NO_ROLE_ELEMENTS = frozenset({"col", "colgroup", "head", "html", "meta", "script", "style"})

BOOLEAN_ATTRS = frozenset({
    "aria-atomic", "aria-busy", "aria-disabled", "aria-grabbed", "aria-hidden",
    "aria-modal", "aria-multiline", "aria-multiselectable", "aria-readonly",
    "aria-required",
})

TRISTATE_ATTRS = frozenset({"aria-checked", "aria-pressed"})

TOKEN_ATTRS: dict[str, list[str]] = {
    "aria-autocomplete": ["inline", "list", "both", "none"],
    "aria-current": ["page", "step", "location", "date", "time", "true", "false"],
    "aria-dropeffect": ["copy", "execute", "link", "move", "none", "popup"],
    "aria-haspopup": ["true", "false", "menu", "listbox", "tree", "grid", "dialog"],
    "aria-invalid": ["grammar", "false", "spelling", "true"],
    "aria-live": ["assertive", "off", "polite"],
    "aria-orientation": ["horizontal", "vertical", "undefined"],
    "aria-relevant": ["additions", "all", "removals", "text"],
    "aria-sort": ["ascending", "descending", "none", "other"],
    "aria-expanded": ["true", "false", "undefined"],
    "aria-selected": ["true", "false", "undefined"],
}

ELEMENT_ALLOWED_ROLES: dict[str, list[str] | str] = {
    "a": [
        "button", "checkbox", "menuitem", "menuitemcheckbox", "menuitemradio",
        "option", "radio", "switch", "tab", "treeitem", "doc-backlink",
        "doc-biblioref", "doc-glossref", "doc-noteref",
    ],
    "article": ["application", "document", "feed", "main", "none", "presentation", "region"],
    "aside": [
        "doc-dedication", "doc-example", "doc-footnote", "doc-glossary",
        "doc-pullquote", "doc-tip", "feed", "none", "note", "presentation",
        "region", "search",
    ],
    "blockquote": ["*"],
    "button": [
        "checkbox", "combobox", "link", "menuitem", "menuitemcheckbox",
        "menuitemradio", "option", "radio", "switch", "tab",
    ],
    "details": ["group"],
    "div": "*",
    "dl": ["group", "list", "none", "presentation"],
    "fieldset": ["group", "none", "presentation", "radiogroup"],
    "footer": ["contentinfo", "doc-footnote", "group", "none", "presentation"],
    "form": ["none", "presentation", "search"],
    "h1": ["doc-subtitle", "none", "presentation", "tab"],
    "h2": ["doc-subtitle", "none", "presentation", "tab"],
    "h3": ["doc-subtitle", "none", "presentation", "tab"],
    "h4": ["doc-subtitle", "none", "presentation", "tab"],
    "h5": ["doc-subtitle", "none", "presentation", "tab"],
    "h6": ["doc-subtitle", "none", "presentation", "tab"],
    "header": ["banner", "group", "none", "presentation"],
    "hr": ["doc-pagebreak", "none", "presentation", "separator"],
    "img": [
        "button", "checkbox", "link", "menuitem", "menuitemcheckbox",
        "menuitemradio", "option", "progressbar", "radio", "scrollbar",
        "separator", "slider", "switch", "tab", "treeitem", "doc-cover",
        "img", "none", "presentation",
    ],
    "input": "*",
    "li": [
        "doc-biblioentry", "doc-endnote", "menuitem", "menuitemcheckbox",
        "menuitemradio", "option", "none", "presentation", "radio",
        "separator", "tab", "treeitem",
    ],
    "main": ["*"],
    "nav": ["doc-index", "doc-pagelist", "doc-toc", "menu", "menubar", "none", "presentation", "tablist"],
    "ol": [
        "directory", "group", "listbox", "menu", "menubar", "none",
        "presentation", "radiogroup", "tablist", "toolbar", "tree",
    ],
    "p": ["*"],
    "section": [
        "alert", "alertdialog", "application", "banner", "complementary",
        "contentinfo", "dialog", "doc-abstract", "doc-acknowledgments",
        "doc-afterword", "doc-appendix", "doc-bibliography", "doc-chapter",
        "doc-colophon", "doc-conclusion", "doc-credit", "doc-credits",
        "doc-dedication", "doc-endnotes", "doc-epilogue", "doc-errata",
        "doc-example", "doc-foreword", "doc-glossary", "doc-index",
        "doc-introduction", "doc-notice", "doc-pagelist", "doc-part",
        "doc-preface", "doc-prologue", "doc-pullquote", "doc-qna", "doc-toc",
        "document", "feed", "group", "log", "main", "marquee", "navigation",
        "none", "note", "presentation", "region", "search", "status",
        "tabpanel",
    ],
    "select": ["menu"],
    "span": "*",
    "table": ["*"],
    "td": ["*"],
    "textarea": ["*"],
    "th": ["*"],
    "tr": ["*"],
    "ul": [
        "directory", "group", "listbox", "menu", "menubar", "none",
        "presentation", "radiogroup", "tablist", "toolbar", "tree",
    ],
}


# ═══════════════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════════════

def _get_aria_attrs(node: FastNode) -> list[tuple[str, str]]:
    """Get all aria-* attributes from a node."""
    return [(k, v) for k, v in node.attrs.items() if k.startswith("aria-")]


def _has_focusable_descendant(node: FastNode) -> bool:
    """Check if a node or any descendant is focusable."""
    for child in node.children:
        if is_focusable(child):
            return True
        if _has_focusable_descendant(child):
            return True
    return False


def _has_descendant_with_role(node: FastNode, roles: list[str]) -> bool:
    """Check if any descendant has one of the required roles."""
    for child in node.children:
        child_role = get_role(child)
        if child_role and child_role in roles:
            return True
        if _has_descendant_with_role(child, roles):
            return True
    return False


# ═══════════════════════════════════════════════════════════════════════
#  Rules
# ═══════════════════════════════════════════════════════════════════════

class _AriaAllowedAttr:
    rule_id = "aria-allowed-attr"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        for node in nodes:
            if is_hidden_or_ancestor_hidden(node):
                continue
            aria_attrs = _get_aria_attrs(node)
            if not aria_attrs:
                continue
            role = get_role(node)
            if not role:
                disallowed = [a for a, _ in aria_attrs if a not in GLOBAL_ARIA_ATTRS]
                if disallowed:
                    result.violations.append(node)
                    result.check_details[id(node)] = NodeCheckDetail(
                        all=[make_check("aria-allowed-attr", "critical",
                            f"ARIA attribute(s) not allowed: {', '.join(disallowed)}")]
                    )
                else:
                    result.passes.append(node)
                continue
            allowed = set(GLOBAL_ARIA_ATTRS) | set(ROLE_ALLOWED_ATTRS.get(role, [])) | set(REQUIRED_ATTRS.get(role, []))
            disallowed = [a for a, _ in aria_attrs if a not in allowed]
            if disallowed:
                result.violations.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("aria-allowed-attr", "critical",
                        f'ARIA attribute(s) not allowed for role "{role}": {", ".join(disallowed)}')]
                )
            else:
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("aria-allowed-attr", "critical",
                        f'ARIA attributes are allowed for role "{role}"')]
                )
        return result


class _AriaHiddenBody:
    rule_id = "aria-hidden-body"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        for node in find_by_tag(nodes, "body"):
            if node.attrs.get("aria-hidden") == "true":
                result.violations.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("aria-hidden-body", "critical",
                        'aria-hidden="true" must not be present on the document body')]
                )
            else:
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("aria-hidden-body", "critical",
                        "Document body does not have aria-hidden")]
                )
        return result


class _AriaHiddenFocus:
    rule_id = "aria-hidden-focus"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        for node in nodes:
            if node.attrs.get("aria-hidden") != "true":
                continue
            self_focusable = is_focusable(node)
            descendant_focusable = _has_focusable_descendant(node)
            if self_focusable or descendant_focusable:
                result.violations.append(node)
                msg = ('Element with aria-hidden="true" is focusable'
                       if self_focusable
                       else 'Element with aria-hidden="true" contains focusable elements')
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("aria-hidden-focus", "serious", msg)]
                )
            else:
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("aria-hidden-focus", "serious",
                        'Element with aria-hidden="true" has no focusable content')]
                )
        return result


class _AriaRequiredAttr:
    rule_id = "aria-required-attr"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        for node in nodes:
            if is_hidden_or_ancestor_hidden(node):
                continue
            role = node.attrs.get("role")
            if not role:
                continue
            if role not in VALID_ROLES:
                continue
            required = REQUIRED_ATTRS.get(role)
            if not required:
                continue
            # Skip native elements that implicitly provide the required state
            if node.tag == "input" and role in ("checkbox", "radio", "switch"):
                continue
            if node.tag == "select" and role == "combobox":
                continue
            if node.tag == "option":
                continue
            import re
            if re.match(r"^h[1-6]$", node.tag) and role == "heading":
                continue
            missing = [attr for attr in required if attr not in node.attrs]
            if missing:
                result.violations.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("aria-required-attr", "critical",
                        f'Required ARIA attribute(s) missing for role "{role}": {", ".join(missing)}')]
                )
            else:
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("aria-required-attr", "critical",
                        "All required ARIA attributes are present")]
                )
        return result


class _AriaRequiredChildren:
    rule_id = "aria-required-children"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        for node in nodes:
            if is_hidden_or_ancestor_hidden(node):
                continue
            role = get_role(node)
            if not role:
                continue
            required_children = REQUIRED_CHILDREN.get(role)
            if not required_children:
                continue
            if "aria-owns" in node.attrs:
                result.incomplete.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("aria-required-children", "critical",
                        "Element uses aria-owns -- cannot fully verify required children")]
                )
                continue
            if _has_descendant_with_role(node, required_children):
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("aria-required-children", "critical",
                        "Element has required child role(s)")]
                )
            else:
                result.violations.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("aria-required-children", "critical",
                        f'Required child role(s) missing for role "{role}": {", ".join(required_children)}')]
                )
        return result


class _AriaRequiredParent:
    rule_id = "aria-required-parent"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        for node in nodes:
            if is_hidden_or_ancestor_hidden(node):
                continue
            role = get_role(node)
            if not role:
                continue
            required_parents = REQUIRED_PARENT.get(role)
            if not required_parents:
                continue
            found = False
            current = node.parent
            while current:
                parent_role = get_role(current)
                if parent_role and parent_role in required_parents:
                    found = True
                    break
                current = current.parent
            if found:
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("aria-required-parent", "critical",
                        "Element has the required parent role")]
                )
            else:
                result.violations.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("aria-required-parent", "critical",
                        f'Required parent role missing for role "{role}": {", ".join(required_parents)}')]
                )
        return result


class _AriaRoles:
    rule_id = "aria-roles"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        for node in nodes:
            if is_hidden_or_ancestor_hidden(node):
                continue
            role = node.attrs.get("role")
            if not role:
                continue
            roles = role.strip().split()
            invalid_roles = [r for r in roles if r not in VALID_ROLES]
            if invalid_roles:
                result.violations.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("aria-roles", "critical",
                        f"Invalid ARIA role(s): {', '.join(invalid_roles)}")]
                )
            else:
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("aria-roles", "critical", "ARIA role is valid")]
                )
        return result


class _AriaValidAttr:
    rule_id = "aria-valid-attr"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        for node in nodes:
            if is_hidden_or_ancestor_hidden(node):
                continue
            aria_attrs = _get_aria_attrs(node)
            if not aria_attrs:
                continue
            invalid = [a for a, _ in aria_attrs if a not in VALID_ARIA_ATTRS]
            if invalid:
                result.violations.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("aria-valid-attr", "critical",
                        f"Invalid ARIA attribute(s): {', '.join(invalid)}")]
                )
            else:
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("aria-valid-attr", "critical",
                        "All ARIA attributes are valid")]
                )
        return result


class _AriaValidAttrValue:
    rule_id = "aria-valid-attr-value"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        for node in nodes:
            if is_hidden_or_ancestor_hidden(node):
                continue
            aria_attrs = _get_aria_attrs(node)
            if not aria_attrs:
                continue
            invalid_attrs: list[str] = []
            for attr, value in aria_attrs:
                if attr not in VALID_ARIA_ATTRS:
                    continue
                if attr in BOOLEAN_ATTRS:
                    if value not in ("true", "false"):
                        invalid_attrs.append(f'{attr}="{value}"')
                    continue
                if attr in TRISTATE_ATTRS:
                    if value not in ("true", "false", "mixed"):
                        invalid_attrs.append(f'{attr}="{value}"')
                    continue
                if attr in TOKEN_ATTRS:
                    valid_values = TOKEN_ATTRS[attr]
                    if attr == "aria-relevant":
                        tokens = value.strip().split()
                        if any(t not in valid_values for t in tokens):
                            invalid_attrs.append(f'{attr}="{value}"')
                    elif value not in valid_values:
                        invalid_attrs.append(f'{attr}="{value}"')
                    continue
                numeric_int_attrs = {
                    "aria-level", "aria-posinset", "aria-setsize",
                    "aria-colcount", "aria-colindex", "aria-colspan",
                    "aria-rowcount", "aria-rowindex", "aria-rowspan",
                }
                if attr in numeric_int_attrs:
                    if value.strip():
                        try:
                            int(value.strip())
                        except ValueError:
                            invalid_attrs.append(f'{attr}="{value}"')
                    continue
                numeric_float_attrs = {"aria-valuemax", "aria-valuemin", "aria-valuenow"}
                if attr in numeric_float_attrs:
                    if value.strip():
                        try:
                            float(value.strip())
                        except ValueError:
                            invalid_attrs.append(f'{attr}="{value}"')
                    continue
                id_ref_attrs = {
                    "aria-activedescendant", "aria-controls",
                    "aria-errormessage", "aria-flowto",
                    "aria-owns", "aria-details",
                }
                if attr in id_ref_attrs:
                    if not value.strip():
                        invalid_attrs.append(f"{attr} (empty value)")
                    continue
                if attr in ("aria-labelledby", "aria-describedby"):
                    if not value.strip():
                        invalid_attrs.append(f"{attr} (empty value)")
                    continue
            if invalid_attrs:
                result.violations.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("aria-valid-attr-value", "critical",
                        f"Invalid ARIA attribute value(s): {', '.join(invalid_attrs)}")]
                )
            else:
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("aria-valid-attr-value", "critical",
                        "All ARIA attribute values are valid")]
                )
        return result


class _AriaRoledescription:
    rule_id = "aria-roledescription"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        for node in nodes:
            if is_hidden_or_ancestor_hidden(node):
                continue
            if "aria-roledescription" not in node.attrs:
                continue
            role = get_role(node)
            if role and role in ROLEDESCRIPTION_SUPPORTED_ROLES:
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("aria-roledescription", "serious",
                        "aria-roledescription is used on an element with a valid role")]
                )
            else:
                result.violations.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("aria-roledescription", "serious",
                        "aria-roledescription is used on an element without an appropriate role")]
                )
        return result


def _aria_name_check(rule_id: str, impact: ImpactValue, target_roles: list[str]) -> object:
    """Create an accessible name check rule for a set of roles."""

    class _Rule:
        def __init__(self) -> None:
            self.rule_id = rule_id

        def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
            result = RuleRunResult()
            for node in nodes:
                if is_hidden_or_ancestor_hidden(node):
                    continue
                role = get_role(node)
                if not role or role not in target_roles:
                    continue
                name = get_accessible_name(node, all_nodes)
                if name:
                    result.passes.append(node)
                    result.check_details[id(node)] = NodeCheckDetail(
                        any=[make_check(rule_id, impact, "Element has an accessible name")]
                    )
                else:
                    result.violations.append(node)
                    result.check_details[id(node)] = NodeCheckDetail(
                        any=[make_check(rule_id, impact,
                            f'Element with role="{role}" does not have an accessible name')]
                    )
            return result

    return _Rule()


class _AriaText:
    rule_id = "aria-text"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        for node in nodes:
            if is_hidden_or_ancestor_hidden(node):
                continue
            if node.attrs.get("role") != "text":
                continue
            if _has_focusable_descendant(node):
                result.violations.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("aria-text", "serious",
                        'Element with role="text" has focusable descendants')]
                )
            else:
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("aria-text", "serious",
                        'Element with role="text" has no focusable descendants')]
                )
        return result


class _AriaDeprecatedRole:
    rule_id = "aria-deprecated-role"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        for node in nodes:
            if is_hidden_or_ancestor_hidden(node):
                continue
            role = node.attrs.get("role")
            if not role:
                continue
            if role in DEPRECATED_ROLES:
                result.violations.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("aria-deprecated-role", "minor",
                        f'Role "{role}" is deprecated')]
                )
            elif role in VALID_ROLES:
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("aria-deprecated-role", "minor",
                        "Role is not deprecated")]
                )
        return result


class _AriaProhibitedAttr:
    rule_id = "aria-prohibited-attr"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        for node in nodes:
            if is_hidden_or_ancestor_hidden(node):
                continue
            role = get_role(node)
            if not role:
                continue
            prohibited = PROHIBITED_ATTRS.get(role)
            if not prohibited:
                continue
            present = [attr for attr in prohibited if attr in node.attrs]
            if present:
                result.violations.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("aria-prohibited-attr", "serious",
                        f'Prohibited ARIA attribute(s) for role "{role}": {", ".join(present)}')]
                )
            else:
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("aria-prohibited-attr", "serious",
                        "No prohibited ARIA attributes used")]
                )
        return result


class _AriaBrailleEquivalent:
    rule_id = "aria-braille-equivalent"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        for node in nodes:
            if is_hidden_or_ancestor_hidden(node):
                continue
            has_braille_label = "aria-braillelabel" in node.attrs
            has_braille_roledescription = "aria-brailleroledescription" in node.attrs
            if not has_braille_label and not has_braille_roledescription:
                continue
            issues: list[str] = []
            if has_braille_label:
                name = get_accessible_name(node, all_nodes)
                if not name:
                    issues.append("aria-braillelabel is used without a non-braille accessible name")
            if has_braille_roledescription:
                if "aria-roledescription" not in node.attrs:
                    issues.append("aria-brailleroledescription is used without aria-roledescription")
            if issues:
                result.violations.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("aria-braille-equivalent", "serious", "; ".join(issues))]
                )
            else:
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("aria-braille-equivalent", "serious",
                        "Braille attributes have non-braille equivalents")]
                )
        return result


class _AriaAllowedRole:
    rule_id = "aria-allowed-role"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        for node in nodes:
            if is_hidden_or_ancestor_hidden(node):
                continue
            role = node.attrs.get("role")
            if not role:
                continue
            if role not in VALID_ROLES:
                continue
            if node.tag in NO_ROLE_ELEMENTS:
                result.violations.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("aria-allowed-role", "minor",
                        f"Element <{node.tag}> cannot have a role attribute")]
                )
                continue
            allowed = ELEMENT_ALLOWED_ROLES.get(node.tag)
            if allowed is None or allowed == "*":
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("aria-allowed-role", "minor",
                        "Role is allowed for this element")]
                )
                continue
            if isinstance(allowed, list) and (role in allowed or "*" in allowed):
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("aria-allowed-role", "minor",
                        "Role is allowed for this element")]
                )
            else:
                result.violations.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("aria-allowed-role", "minor",
                        f'Role "{role}" is not allowed on <{node.tag}>')]
                )
        return result


class _AriaConditionalAttr:
    rule_id = "aria-conditional-attr"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        for node in nodes:
            if is_hidden_or_ancestor_hidden(node):
                continue
            role = get_role(node)
            if not role:
                continue
            issues: list[str] = []
            if role == "separator" and not is_focusable(node):
                value_attrs = ["aria-valuenow", "aria-valuemin", "aria-valuemax", "aria-valuetext"]
                present = [a for a in value_attrs if a in node.attrs]
                if present:
                    issues.append(f"Non-focusable separator should not have: {', '.join(present)}")
            if issues:
                result.violations.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("aria-conditional-attr", "serious", "; ".join(issues))]
                )
            else:
                aria_attrs = _get_aria_attrs(node)
                if aria_attrs:
                    result.passes.append(node)
                    result.check_details[id(node)] = NodeCheckDetail(
                        all=[make_check("aria-conditional-attr", "serious",
                            "ARIA attributes are used correctly for the role")]
                    )
        return result


class _PresentationRoleConflict:
    rule_id = "presentation-role-conflict"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        for node in nodes:
            if is_hidden_or_ancestor_hidden(node):
                continue
            role = node.attrs.get("role")
            if role not in ("none", "presentation"):
                continue
            has_tabindex = (
                node.attrs.get("tabindex") is not None
                and node.attrs.get("tabindex") != "-1"
            )
            has_global_aria = any(
                a in GLOBAL_ARIA_ATTRS and a != "aria-hidden"
                for a, _ in _get_aria_attrs(node)
            )
            if has_tabindex or has_global_aria:
                reasons = []
                if has_tabindex:
                    reasons.append("has tabindex")
                if has_global_aria:
                    reasons.append("has global ARIA attributes")
                result.violations.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("presentation-role-conflict", "minor",
                        f'Element with role="{role}" {" and ".join(reasons)}')]
                )
            else:
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("presentation-role-conflict", "minor",
                        f'Element with role="{role}" correctly has no global ARIA or tabindex')]
                )
        return result


aria_rules = [
    _AriaAllowedAttr(),
    _AriaHiddenBody(),
    _AriaHiddenFocus(),
    _AriaRequiredAttr(),
    _AriaRequiredChildren(),
    _AriaRequiredParent(),
    _AriaRoles(),
    _AriaValidAttr(),
    _AriaValidAttrValue(),
    _AriaRoledescription(),
    _aria_name_check("aria-input-field-name", "serious",
        ["combobox", "listbox", "searchbox", "spinbutton", "textbox"]),
    _aria_name_check("aria-toggle-field-name", "serious",
        ["checkbox", "menu", "menuitemcheckbox", "menuitemradio", "radio", "radiogroup", "switch"]),
    _aria_name_check("aria-command-name", "serious",
        ["button", "link", "menuitem"]),
    _aria_name_check("aria-meter-name", "serious", ["meter"]),
    _aria_name_check("aria-progressbar-name", "serious", ["progressbar"]),
    _aria_name_check("aria-tooltip-name", "serious", ["tooltip"]),
    _aria_name_check("aria-treeitem-name", "serious", ["treeitem"]),
    _aria_name_check("aria-dialog-name", "serious", ["dialog", "alertdialog"]),
    _AriaText(),
    _AriaDeprecatedRole(),
    _AriaProhibitedAttr(),
    _AriaBrailleEquivalent(),
    _AriaAllowedRole(),
    _AriaConditionalAttr(),
    _PresentationRoleConflict(),
]
