"""Axe-core compatible rule metadata.

Each rule has its ID, tags, description, help text, and help URL
matching axe-core's output exactly.
"""

from __future__ import annotations

from dataclasses import dataclass

from .types import ImpactValue

AXE_BASE_URL = "https://dequeuniversity.com/rules/axe/4.9"


@dataclass(frozen=True)
class RuleMeta:
    """Metadata for a single accessibility rule."""

    id: str
    impact: ImpactValue
    tags: list[str]
    help: str
    description: str
    help_url: str


def _meta(
    id: str,
    impact: ImpactValue,
    tags: list[str],
    help: str,
    description: str,
) -> RuleMeta:
    return RuleMeta(
        id=id,
        impact=impact,
        tags=list(tags),
        help=help,
        description=description,
        help_url=f"{AXE_BASE_URL}/{id}?application=axeAPI",
    )


# ── RULE METADATA ──────────────────────────────────────────────────────

RULE_META: dict[str, RuleMeta] = {
    # Text alternatives
    "image-alt": _meta(
        "image-alt", "critical",
        ["cat.text-alternatives", "wcag2a", "wcag111", "section508", "section508.22.a", "ACT"],
        "Images must have alternate text",
        'Ensures <img> elements have alternate text or a role of none or presentation',
    ),
    "input-image-alt": _meta(
        "input-image-alt", "critical",
        ["cat.text-alternatives", "wcag2a", "wcag111", "section508", "section508.22.a", "ACT"],
        "Image buttons must have alternate text",
        'Ensures <input type="image"> elements have alternate text',
    ),
    "object-alt": _meta(
        "object-alt", "serious",
        ["cat.text-alternatives", "wcag2a", "wcag111"],
        "<object> elements must have alternate text",
        "Ensures <object> elements have alternate text",
    ),
    "role-img-alt": _meta(
        "role-img-alt", "serious",
        ["cat.text-alternatives", "wcag2a", "wcag111", "ACT"],
        '[role="img"] elements must have an accessible name',
        "Ensures [role=\"img\"] elements have alternate text",
    ),
    "svg-img-alt": _meta(
        "svg-img-alt", "serious",
        ["cat.text-alternatives", "wcag2a", "wcag111", "ACT"],
        "SVG elements with an img role must have an accessible name",
        "Ensures SVG elements with an img role have an accessible name",
    ),
    "area-alt": _meta(
        "area-alt", "critical",
        ["cat.text-alternatives", "wcag2a", "wcag244", "wcag412", "section508", "section508.22.a", "ACT"],
        "Active <area> elements must have alternate text",
        "Ensures <area> elements of image maps have alternate text",
    ),
    "server-side-image-map": _meta(
        "server-side-image-map", "minor",
        ["cat.text-alternatives", "wcag2a", "wcag211", "section508", "section508.22.f"],
        "Server-side image maps must not be used",
        "Ensures that server-side image maps are not used",
    ),

    # Language
    "html-has-lang": _meta(
        "html-has-lang", "serious",
        ["cat.language", "wcag2a", "wcag311", "ACT"],
        "<html> element must have a lang attribute",
        "Ensures every HTML document has a lang attribute",
    ),
    "html-lang-valid": _meta(
        "html-lang-valid", "serious",
        ["cat.language", "wcag2a", "wcag311", "ACT"],
        "<html> element must have a valid value for the lang attribute",
        "Ensures the lang attribute of the <html> element has a valid value",
    ),
    "html-xml-lang-mismatch": _meta(
        "html-xml-lang-mismatch", "moderate",
        ["cat.language", "wcag2a", "wcag311", "ACT"],
        "HTML elements with lang and xml:lang must have the same base language",
        "Ensure that HTML elements with both valid lang and xml:lang attributes agree on the base language of the page",
    ),
    "valid-lang": _meta(
        "valid-lang", "serious",
        ["cat.language", "wcag2a", "wcag311", "ACT"],
        "lang attribute must have a valid value",
        "Ensures lang attributes have valid values",
    ),

    # Structure / Semantics
    "document-title": _meta(
        "document-title", "serious",
        ["cat.text-alternatives", "wcag2a", "wcag242", "ACT"],
        "Documents must have <title> element to aid in navigation",
        "Ensures each HTML document contains a non-empty <title> element",
    ),
    "definition-list": _meta(
        "definition-list", "serious",
        ["cat.structure", "wcag2a", "wcag131"],
        ("<dl> elements must only directly contain properly-ordered <dt> and <dd> groups, "
         "<script>, <template> or <div> elements"),
        "Ensures <dl> elements are structured correctly",
    ),
    "dlitem": _meta(
        "dlitem", "serious",
        ["cat.structure", "wcag2a", "wcag131"],
        "<dt> and <dd> elements must be contained by a <dl>",
        "Ensures <dt> and <dd> elements are contained by a <dl>",
    ),
    "list": _meta(
        "list", "serious",
        ["cat.structure", "wcag2a", "wcag131"],
        "<ul> and <ol> must only directly contain <li>, <script> or <template> elements",
        "Ensures that lists are structured correctly",
    ),
    "listitem": _meta(
        "listitem", "serious",
        ["cat.structure", "wcag2a", "wcag131"],
        "<li> elements must be contained in a <ul> or <ol>",
        "Ensures <li> elements are used semantically",
    ),
    "heading-order": _meta(
        "heading-order", "moderate",
        ["cat.semantics", "best-practice"],
        "Heading levels should only increase by one",
        "Ensures the order of headings is semantically correct",
    ),
    "empty-heading": _meta(
        "empty-heading", "minor",
        ["cat.name-role-value", "best-practice"],
        "Headings should not be empty",
        "Ensures headings have discernible text",
    ),
    "empty-table-header": _meta(
        "empty-table-header", "minor",
        ["cat.name-role-value", "best-practice"],
        "Table header cells should not be empty",
        "Ensures table headers have discernible text",
    ),
    "duplicate-id": _meta(
        "duplicate-id", "minor",
        ["cat.parsing", "wcag2a", "wcag411"],
        "id attribute value must be unique",
        "Ensures every id attribute value is unique",
    ),
    "duplicate-id-aria": _meta(
        "duplicate-id-aria", "critical",
        ["cat.parsing", "wcag2a", "wcag412"],
        "IDs used in ARIA and labels must be unique",
        "Ensures every id attribute value used in ARIA and in labels is unique",
    ),

    # Forms
    "label": _meta(
        "label", "critical",
        ["cat.forms", "wcag2a", "wcag412", "wcag131", "section508", "section508.22.n", "ACT"],
        "Form elements must have labels",
        "Ensures every form element has a label",
    ),
    "select-name": _meta(
        "select-name", "critical",
        ["cat.forms", "wcag2a", "wcag412", "wcag131", "section508", "section508.22.n", "ACT"],
        "Select element must have an accessible name",
        "Ensures select element has an accessible name",
    ),
    "input-button-name": _meta(
        "input-button-name", "critical",
        ["cat.forms", "wcag2a", "wcag412", "section508", "section508.22.a"],
        "Input buttons must have discernible text",
        "Ensures input buttons have discernible text",
    ),
    "form-field-multiple-labels": _meta(
        "form-field-multiple-labels", "moderate",
        ["cat.forms", "wcag2a", "wcag412"],
        "Form field should not have multiple label elements",
        "Ensures form field does not have multiple label elements",
    ),
    "autocomplete-valid": _meta(
        "autocomplete-valid", "serious",
        ["cat.forms", "wcag21a", "wcag135"],
        "autocomplete attribute must be used correctly",
        "Ensures the autocomplete attribute is correct and suitable for the form field",
    ),

    # Name/Role/Value
    "button-name": _meta(
        "button-name", "critical",
        ["cat.name-role-value", "wcag2a", "wcag412", "section508", "section508.22.a", "ACT"],
        "Buttons must have discernible text",
        "Ensures buttons have discernible text",
    ),
    "link-name": _meta(
        "link-name", "serious",
        ["cat.name-role-value", "wcag2a", "wcag412", "wcag244", "section508", "section508.22.a", "ACT"],
        "Links must have discernible text",
        "Ensures links have discernible text",
    ),
    "frame-title": _meta(
        "frame-title", "serious",
        ["cat.text-alternatives", "wcag2a", "wcag412", "wcag241", "section508", "section508.22.i"],
        "Frames must have an accessible name",
        "Ensures <iframe> and <frame> elements have an accessible name",
    ),
    "frame-title-unique": _meta(
        "frame-title-unique", "serious",
        ["cat.text-alternatives", "best-practice"],
        "Frames should have a unique title attribute",
        "Ensures <iframe> and <frame> elements contain a unique title attribute",
    ),

    # ARIA
    "aria-allowed-attr": _meta(
        "aria-allowed-attr", "critical",
        ["cat.aria", "wcag2a", "wcag412"],
        "Elements must only use allowed ARIA attributes",
        "Ensures ARIA attributes are allowed for an element's role",
    ),
    "aria-allowed-role": _meta(
        "aria-allowed-role", "minor",
        ["cat.aria", "best-practice"],
        "ARIA role should be appropriate for the element",
        "Ensures role attribute has an appropriate value for the element",
    ),
    "aria-hidden-body": _meta(
        "aria-hidden-body", "critical",
        ["cat.aria", "wcag2a", "wcag412"],
        'aria-hidden="true" must not be present on the document body',
        'Ensures aria-hidden="true" is not present on the document body',
    ),
    "aria-hidden-focus": _meta(
        "aria-hidden-focus", "serious",
        ["cat.name-role-value", "wcag2a", "wcag412", "wcag131"],
        "ARIA hidden element must not be focusable or contain focusable elements",
        "Ensures aria-hidden elements are not focusable nor contain focusable elements",
    ),
    "aria-required-attr": _meta(
        "aria-required-attr", "critical",
        ["cat.aria", "wcag2a", "wcag412"],
        "Required ARIA attributes must be provided",
        "Ensures elements with ARIA roles have all required ARIA attributes",
    ),
    "aria-required-children": _meta(
        "aria-required-children", "critical",
        ["cat.aria", "wcag2a", "wcag131"],
        "Certain ARIA roles must contain particular children",
        "Ensures elements with an ARIA role that require child roles contain them",
    ),
    "aria-required-parent": _meta(
        "aria-required-parent", "critical",
        ["cat.aria", "wcag2a", "wcag131"],
        "Certain ARIA roles must be contained by particular parents",
        "Ensures elements with an ARIA role that require parent roles are contained by them",
    ),
    "aria-roles": _meta(
        "aria-roles", "critical",
        ["cat.aria", "wcag2a", "wcag412"],
        "ARIA roles used must conform to valid values",
        "Ensures all elements with a role attribute use a valid value",
    ),
    "aria-valid-attr": _meta(
        "aria-valid-attr", "critical",
        ["cat.aria", "wcag2a", "wcag412"],
        "ARIA attributes must conform to valid names",
        "Ensures attributes that begin with aria- are valid ARIA attributes",
    ),
    "aria-valid-attr-value": _meta(
        "aria-valid-attr-value", "critical",
        ["cat.aria", "wcag2a", "wcag412"],
        "ARIA attributes must conform to valid values",
        "Ensures all ARIA attributes have valid values",
    ),
    "aria-roledescription": _meta(
        "aria-roledescription", "serious",
        ["cat.aria", "wcag2a", "wcag412"],
        "aria-roledescription must be on elements with an implicit or explicit role",
        "Ensure aria-roledescription is only used on elements with an implicit or explicit role",
    ),
    "aria-input-field-name": _meta(
        "aria-input-field-name", "serious",
        ["cat.aria", "wcag2a", "wcag412", "ACT"],
        "ARIA input fields must have an accessible name",
        "Ensures every ARIA input field has an accessible name",
    ),
    "aria-toggle-field-name": _meta(
        "aria-toggle-field-name", "serious",
        ["cat.aria", "wcag2a", "wcag412", "ACT"],
        "ARIA toggle fields must have an accessible name",
        "Ensures every ARIA toggle field has an accessible name",
    ),
    "aria-command-name": _meta(
        "aria-command-name", "serious",
        ["cat.aria", "wcag2a", "wcag412", "ACT"],
        "ARIA commands must have an accessible name",
        "Ensures every ARIA command element has an accessible name",
    ),
    "aria-meter-name": _meta(
        "aria-meter-name", "serious",
        ["cat.aria", "wcag2a", "wcag412"],
        "ARIA meter elements must have an accessible name",
        "Ensures every ARIA meter element has an accessible name",
    ),
    "aria-progressbar-name": _meta(
        "aria-progressbar-name", "serious",
        ["cat.aria", "wcag2a", "wcag412"],
        "ARIA progressbar elements must have an accessible name",
        "Ensures every ARIA progressbar element has an accessible name",
    ),
    "aria-tooltip-name": _meta(
        "aria-tooltip-name", "serious",
        ["cat.aria", "wcag2a", "wcag412"],
        "ARIA tooltip elements must have an accessible name",
        "Ensures every ARIA tooltip element has an accessible name",
    ),
    "aria-treeitem-name": _meta(
        "aria-treeitem-name", "serious",
        ["cat.aria", "wcag2a", "wcag412"],
        "ARIA treeitem elements must have an accessible name",
        "Ensures every ARIA treeitem element has an accessible name",
    ),
    "aria-dialog-name": _meta(
        "aria-dialog-name", "serious",
        ["cat.aria", "wcag2a", "wcag412"],
        "ARIA dialog and alertdialog elements must have an accessible name",
        "Ensures every ARIA dialog and alertdialog element has an accessible name",
    ),
    "aria-text": _meta(
        "aria-text", "serious",
        ["cat.aria", "wcag2a", "wcag412"],
        '"role=text" should have no focusable descendants',
        'Ensures "role=text" elements have no focusable descendants',
    ),
    "aria-deprecated-role": _meta(
        "aria-deprecated-role", "minor",
        ["cat.aria", "best-practice"],
        "Deprecated ARIA roles must not be used",
        "Ensures elements do not use deprecated roles",
    ),
    "aria-prohibited-attr": _meta(
        "aria-prohibited-attr", "serious",
        ["cat.aria", "wcag2a", "wcag412"],
        "Elements must only use permitted ARIA attributes",
        "Ensures ARIA attributes are not prohibited for an element's role",
    ),
    "aria-conditional-attr": _meta(
        "aria-conditional-attr", "serious",
        ["cat.aria", "best-practice"],
        "ARIA attributes must be used as specified for the element's role",
        "Ensures ARIA attributes are used as specified for the element's role",
    ),
    "aria-braille-equivalent": _meta(
        "aria-braille-equivalent", "serious",
        ["cat.aria", "wcag2a", "wcag412"],
        "aria-braille attributes must have a non-braille equivalent",
        "Ensure aria-braille attributes have a non-braille equivalent",
    ),

    # Time/Media
    "blink": _meta(
        "blink", "serious",
        ["cat.time-and-media", "wcag2a", "wcag222", "section508", "section508.22.j"],
        "<blink> elements are deprecated and must not be used",
        "Ensures <blink> elements are not used",
    ),
    "marquee": _meta(
        "marquee", "serious",
        ["cat.time-and-media", "wcag2a", "wcag222", "section508", "section508.22.j"],
        "<marquee> elements are deprecated and must not be used",
        "Ensures <marquee> elements are not used",
    ),
    "meta-refresh": _meta(
        "meta-refresh", "critical",
        ["cat.time-and-media", "wcag2a", "wcag221"],
        "Timed refresh must not exist",
        'Ensures <meta http-equiv="refresh"> is not used for delayed refresh',
    ),
    "meta-refresh-no-exceptions": _meta(
        "meta-refresh-no-exceptions", "minor",
        ["cat.time-and-media", "best-practice"],
        "Timed refresh must not exist",
        'Ensures <meta http-equiv="refresh"> is not used',
    ),
    "no-autoplay-audio": _meta(
        "no-autoplay-audio", "moderate",
        ["cat.time-and-media", "wcag2a", "wcag142", "ACT"],
        "<video> or <audio> elements must not play automatically",
        ("Ensures <video> or <audio> elements do not autoplay audio for more than 3 seconds "
         "without a control mechanism to stop or mute the audio"),
    ),
    "video-caption": _meta(
        "video-caption", "critical",
        ["cat.time-and-media", "wcag2a", "wcag122"],
        "<video> elements must have captions",
        "Ensures <video> elements have captions",
    ),

    # Meta / Viewport
    "meta-viewport": _meta(
        "meta-viewport", "critical",
        ["cat.sensory-and-visual-cues", "wcag2aa", "wcag144", "ACT"],
        "Zooming and scaling must not be disabled",
        'Ensures <meta name="viewport"> does not disable text scaling and zooming',
    ),
    "meta-viewport-large": _meta(
        "meta-viewport-large", "minor",
        ["cat.sensory-and-visual-cues", "best-practice"],
        "Users should be able to zoom and scale the text up to 500%",
        'Ensures <meta name="viewport"> can scale a significant amount',
    ),

    # Keyboard
    "nested-interactive": _meta(
        "nested-interactive", "serious",
        ["cat.keyboard", "wcag2a", "wcag412"],
        "Interactive controls must not be nested",
        ("Ensures interactive controls are not nested as they are not always announced "
         "by screen readers or can cause focus problems"),
    ),
    "tabindex": _meta(
        "tabindex", "serious",
        ["cat.keyboard", "best-practice"],
        "Elements should not have tabindex greater than zero",
        "Ensures tabindex attribute values are not greater than 0",
    ),
    "accesskeys": _meta(
        "accesskeys", "serious",
        ["cat.keyboard", "best-practice"],
        "accesskey attribute value should be unique",
        "Ensures every accesskey attribute value is unique",
    ),

    # Tables
    "td-headers-attr": _meta(
        "td-headers-attr", "serious",
        ["cat.tables", "wcag2a", "wcag131"],
        "All cells in a table that use the headers attribute must only refer to other cells in that table",
        "Ensures that each cell in a table that uses the headers attribute refers only to other cells in that table",
    ),
    "th-has-data-cells": _meta(
        "th-has-data-cells", "serious",
        ["cat.tables", "wcag2a", "wcag131"],
        "Table headers in a data table must refer to data cells",
        "Ensures that each table header in a data table refers to data cells",
    ),
    "td-has-header": _meta(
        "td-has-header", "serious",
        ["cat.tables", "wcag2a", "wcag131"],
        "Non-empty <td> elements in larger tables must be associated with a table header",
        "Ensures that each non-empty data cell in a table larger than 3 by 3 has one or more table headers",
    ),
    "table-duplicate-name": _meta(
        "table-duplicate-name", "minor",
        ["cat.tables", "best-practice"],
        "Tables should not have the same summary and caption",
        "Ensure the <caption> element does not contain the same text as the summary attribute",
    ),
    "table-fake-caption": _meta(
        "table-fake-caption", "serious",
        ["cat.tables", "best-practice"],
        "Data or header cells must not be used to give caption to a data table",
        "Ensures that tables with a caption use the <caption> element",
    ),
    "scope-attr-valid": _meta(
        "scope-attr-valid", "moderate",
        ["cat.tables", "best-practice"],
        "scope attribute should be used correctly",
        "Ensures the scope attribute is used correctly on tables",
    ),

    # Landmarks
    "landmark-one-main": _meta(
        "landmark-one-main", "moderate",
        ["cat.semantics", "best-practice"],
        "Document should have one main landmark",
        "Ensures the document has a main landmark",
    ),
    "landmark-no-duplicate-main": _meta(
        "landmark-no-duplicate-main", "moderate",
        ["cat.semantics", "best-practice"],
        "Document should not have more than one main landmark",
        "Ensures the document has at most one main landmark",
    ),
    "landmark-no-duplicate-banner": _meta(
        "landmark-no-duplicate-banner", "moderate",
        ["cat.semantics", "best-practice"],
        "Document should not have more than one banner landmark",
        "Ensures the document has at most one banner landmark",
    ),
    "landmark-no-duplicate-contentinfo": _meta(
        "landmark-no-duplicate-contentinfo", "moderate",
        ["cat.semantics", "best-practice"],
        "Document should not have more than one contentinfo landmark",
        "Ensures the document has at most one contentinfo landmark",
    ),
    "landmark-banner-is-top-level": _meta(
        "landmark-banner-is-top-level", "moderate",
        ["cat.semantics", "best-practice"],
        "Banner landmark should not be contained in another landmark",
        "Ensures the banner landmark is at top level",
    ),
    "landmark-contentinfo-is-top-level": _meta(
        "landmark-contentinfo-is-top-level", "moderate",
        ["cat.semantics", "best-practice"],
        "Contentinfo landmark should not be contained in another landmark",
        "Ensures the contentinfo landmark is at top level",
    ),
    "landmark-complementary-is-top-level": _meta(
        "landmark-complementary-is-top-level", "moderate",
        ["cat.semantics", "best-practice"],
        "Aside should not be contained in another landmark",
        "Ensures the complementary landmark or aside is at top level",
    ),
    "landmark-main-is-top-level": _meta(
        "landmark-main-is-top-level", "moderate",
        ["cat.semantics", "best-practice"],
        "Main landmark should not be contained in another landmark",
        "Ensures the main landmark is at top level",
    ),
    "page-has-heading-one": _meta(
        "page-has-heading-one", "moderate",
        ["cat.semantics", "best-practice"],
        "Page should contain a level-one heading",
        "Ensure that the page, or at least one of its frames contains a level-one heading",
    ),
    "landmark-unique": _meta(
        "landmark-unique", "moderate",
        ["cat.semantics", "best-practice"],
        "Ensures landmarks are unique",
        "Landmarks should have a unique role or role/label/title (i.e. accessible name) combination",
    ),
    "region": _meta(
        "region", "moderate",
        ["cat.keyboard", "best-practice"],
        "All page content should be contained by landmarks",
        "Ensures all page content is contained by landmarks",
    ),

    # Bypass
    "bypass": _meta(
        "bypass", "serious",
        ["cat.keyboard", "wcag2a", "wcag241", "section508", "section508.22.o"],
        "Page must have means to bypass repeated blocks",
        "Ensures each page has at least one mechanism for a user to bypass navigation and jump straight to the content",
    ),

    # Color contrast
    "color-contrast": _meta(
        "color-contrast", "serious",
        ["cat.color", "wcag2aa", "wcag143", "ACT"],
        "Elements must meet minimum color contrast ratio thresholds",
        ("Ensures the contrast between foreground and background colors meets "
         "WCAG 2 AA minimum contrast ratio thresholds"),
    ),

    # Presentation role
    "presentation-role-conflict": _meta(
        "presentation-role-conflict", "minor",
        ["cat.aria", "best-practice"],
        "Elements with role none or presentation should not have global ARIA or tabindex",
        ("Elements marked as presentational should not have global ARIA or tabindex "
         "to ensure they are truly removed from the accessibility tree"),
    ),

    # Label-title-only
    "label-title-only": _meta(
        "label-title-only", "serious",
        ["cat.forms", "best-practice"],
        "Form elements should not be labeled only by title attribute",
        "Ensures form elements are not solely labeled by the title or aria-describedby attributes",
    ),
}
