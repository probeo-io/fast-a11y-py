"""Form rules: label, select-name, input-button-name, button-name,
form-field-multiple-labels, autocomplete-valid, label-title-only
"""

from __future__ import annotations

from collections import defaultdict

from ..accessible_name import get_accessible_name
from ..rule_engine import NodeCheckDetail, RuleRunResult, make_check
from ..tree import FastNode, find_by_tag, is_hidden_or_ancestor_hidden

# Autocomplete tokens from the HTML spec.
AUTOCOMPLETE_TOKENS = frozenset({
    # Section names
    "shipping", "billing",
    # Contact types
    "home", "work", "mobile", "fax", "pager",
    # Field names
    "name", "honorific-prefix", "given-name", "additional-name",
    "family-name", "honorific-suffix", "nickname", "username",
    "new-password", "current-password", "one-time-code",
    "organization-title", "organization",
    "street-address", "address-line1", "address-line2", "address-line3",
    "address-level4", "address-level3", "address-level2", "address-level1",
    "country", "country-name", "postal-code",
    "cc-name", "cc-given-name", "cc-additional-name", "cc-family-name",
    "cc-number", "cc-exp", "cc-exp-month", "cc-exp-year",
    "cc-csc", "cc-type",
    "transaction-currency", "transaction-amount",
    "language", "bday", "bday-day", "bday-month", "bday-year",
    "sex", "url", "photo",
    "tel", "tel-country-code", "tel-national", "tel-area-code",
    "tel-local", "tel-local-prefix", "tel-local-suffix", "tel-extension",
    "email", "impp",
    # Special values
    "on", "off",
    # webauthn
    "webauthn",
})

# Input types that support autocomplete.
AUTOCOMPLETE_INPUT_TYPES = frozenset({
    "text", "search", "url", "tel", "email", "password",
    "date", "month", "week", "time", "datetime-local",
    "number", "range", "color",
})


def _is_labelable_input(node: FastNode) -> bool:
    """Check if a form element is a type that should have a label."""
    if node.tag in ("select", "textarea"):
        return True
    if node.tag == "input":
        type_val = (node.attrs.get("type") or "text").lower()
        return type_val not in ("hidden", "submit", "reset", "button", "image")
    return False


class _Label:
    rule_id = "label"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        for node in nodes:
            if not _is_labelable_input(node):
                continue
            if is_hidden_or_ancestor_hidden(node):
                continue
            role = node.attrs.get("role")
            if role in ("presentation", "none"):
                continue
            name = get_accessible_name(node, all_nodes)
            if name:
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("label", "critical", "Element has an accessible name")]
                )
            else:
                result.violations.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("label", "critical",
                        "Form element does not have an accessible name")]
                )
        return result


class _SelectName:
    rule_id = "select-name"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        for node in find_by_tag(nodes, "select"):
            if is_hidden_or_ancestor_hidden(node):
                continue
            name = get_accessible_name(node, all_nodes)
            if name:
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("select-name", "critical",
                        "Element has an accessible name")]
                )
            else:
                result.violations.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("select-name", "critical",
                        "Select element does not have an accessible name")]
                )
        return result


class _InputButtonName:
    rule_id = "input-button-name"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        button_types = {"submit", "reset", "button"}
        for node in find_by_tag(nodes, "input"):
            if is_hidden_or_ancestor_hidden(node):
                continue
            type_val = (node.attrs.get("type") or "").lower()
            if type_val not in button_types:
                continue
            name = get_accessible_name(node, all_nodes)
            if name:
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("input-button-name", "critical",
                        "Element has discernible text")]
                )
            else:
                result.violations.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("input-button-name", "critical",
                        "Element does not have discernible text")]
                )
        return result


class _ButtonName:
    rule_id = "button-name"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        for node in nodes:
            if is_hidden_or_ancestor_hidden(node):
                continue
            is_button = node.tag == "button" or node.attrs.get("role") == "button"
            if not is_button:
                continue
            if node.tag == "input":
                continue
            name = get_accessible_name(node, all_nodes)
            if name:
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("button-name", "critical",
                        "Element has an accessible name")]
                )
            else:
                result.violations.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("button-name", "critical",
                        "Element does not have an accessible name")]
                )
        return result


class _FormFieldMultipleLabels:
    rule_id = "form-field-multiple-labels"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        label_for_count: dict[str, int] = defaultdict(int)
        for node in find_by_tag(nodes, "label"):
            for_attr = node.attrs.get("for")
            if for_attr:
                label_for_count[for_attr] += 1
        for node in nodes:
            if not _is_labelable_input(node):
                continue
            if is_hidden_or_ancestor_hidden(node):
                continue
            id_val = node.attrs.get("id")
            if not id_val:
                continue
            count = label_for_count.get(id_val, 0)
            if count > 1:
                result.violations.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("form-field-multiple-labels", "moderate",
                        f"Element has {count} label elements associated via for attribute")]
                )
            elif count == 1:
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("form-field-multiple-labels", "moderate",
                        "Element has a single label")]
                )
        return result


class _AutocompleteValid:
    rule_id = "autocomplete-valid"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        for node in nodes:
            if is_hidden_or_ancestor_hidden(node):
                continue
            autocomplete = node.attrs.get("autocomplete")
            if autocomplete is None:
                continue
            if node.tag == "input":
                type_val = (node.attrs.get("type") or "text").lower()
                if type_val not in AUTOCOMPLETE_INPUT_TYPES and type_val != "hidden":
                    continue
            elif node.tag not in ("select", "textarea"):
                continue
            value = autocomplete.strip().lower()
            if not value:
                result.violations.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("autocomplete-valid", "serious",
                        "Element has an empty autocomplete attribute")]
                )
                continue
            tokens = value.split()
            valid = True
            for token in tokens:
                if token.startswith("section-"):
                    continue
                if token not in AUTOCOMPLETE_TOKENS:
                    valid = False
                    break
            if valid:
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("autocomplete-valid", "serious",
                        "Element has a valid autocomplete value")]
                )
            else:
                result.violations.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("autocomplete-valid", "serious",
                        f"Element has an invalid autocomplete value: {autocomplete}")]
                )
        return result


class _LabelTitleOnly:
    rule_id = "label-title-only"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        for node in nodes:
            if not _is_labelable_input(node):
                continue
            if is_hidden_or_ancestor_hidden(node):
                continue
            has_aria_label = bool(node.attrs.get("aria-label", "").strip())
            has_aria_labelledby = bool(node.attrs.get("aria-labelledby", "").strip())
            has_title = bool(node.attrs.get("title", "").strip())
            has_label = False
            id_val = node.attrs.get("id")
            if id_val:
                has_label = any(
                    n.tag == "label" and n.attrs.get("for") == id_val for n in all_nodes
                )
            if not has_label:
                p = node.parent
                while p:
                    if p.tag == "label":
                        has_label = True
                        break
                    p = p.parent
            if has_label or has_aria_label or has_aria_labelledby:
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("label-title-only", "serious",
                        "Element has a proper label mechanism")]
                )
            elif has_title:
                result.violations.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("label-title-only", "serious",
                        "Element is labeled only by the title attribute")]
                )
        return result


form_rules = [
    _Label(),
    _SelectName(),
    _InputButtonName(),
    _ButtonName(),
    _FormFieldMultipleLabels(),
    _AutocompleteValid(),
    _LabelTitleOnly(),
]
