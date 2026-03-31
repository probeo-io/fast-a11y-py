"""Exhaustive tests for fast-a11y -- covers all major rule categories,
output format, edge cases, and rule filtering.
"""

from __future__ import annotations

from fast_a11y import AxeResults, RunOptions, fast_a11y

# ── Helpers ───────────────────────────────────────────────────────────


def _wrap(body: str, lang: str = "en") -> str:
    """Wrap body HTML in a valid page shell."""
    return (
        f'<!DOCTYPE html><html lang="{lang}">'
        f"<head><title>Test</title></head>"
        f"<body>{body}</body></html>"
    )


def _find_violation(results: AxeResults, rule_id: str) -> dict | None:
    """Find a violation by rule ID."""
    return next(
        (v for v in results["violations"] if v["id"] == rule_id), None
    )


def _find_pass(results: AxeResults, rule_id: str) -> dict | None:
    """Find a pass by rule ID."""
    return next(
        (p for p in results["passes"] if p["id"] == rule_id), None
    )


def _find_incomplete(results: AxeResults, rule_id: str) -> dict | None:
    """Find an incomplete result by rule ID."""
    return next(
        (i for i in results["incomplete"] if i["id"] == rule_id), None
    )


def _find_inapplicable(results: AxeResults, rule_id: str) -> dict | None:
    """Find an inapplicable result by rule ID."""
    return next(
        (i for i in results["inapplicable"] if i["id"] == rule_id), None
    )


def _all_rule_ids(results: AxeResults) -> set[str]:
    """Get all rule IDs across all categories."""
    ids: set[str] = set()
    for cat in ("violations", "passes", "incomplete", "inapplicable"):
        for r in results[cat]:  # type: ignore[literal-required]
            ids.add(r["id"])
    return ids


# ══════════════════════════════════════════════════════════════════════
#  Output format -- axe-core compatible structure
# ══════════════════════════════════════════════════════════════════════


class TestOutputFormat:
    def test_top_level_keys(self) -> None:
        results = fast_a11y(_wrap("<p>Hello</p>"))
        required = {
            "testEngine", "testRunner", "testEnvironment",
            "url", "timestamp", "toolOptions",
            "passes", "violations", "incomplete", "inapplicable",
        }
        assert required.issubset(set(results.keys()))

    def test_engine_metadata(self) -> None:
        results = fast_a11y(_wrap("<p>Hi</p>"))
        assert results["testEngine"]["name"] == "fast-a11y"
        assert results["testEngine"]["version"] == "0.1.0"
        assert results["testRunner"]["name"] == "fast-a11y"

    def test_timestamp_is_iso(self) -> None:
        results = fast_a11y(_wrap("<p>Hi</p>"))
        ts = results["timestamp"]
        assert "T" in ts
        assert ts.endswith("+00:00") or ts.endswith("Z")

    def test_url_passthrough(self) -> None:
        results = fast_a11y(_wrap("<p>Hi</p>"), url="https://example.com")
        assert results["url"] == "https://example.com"

    def test_tool_options_empty_by_default(self) -> None:
        results = fast_a11y(_wrap("<p>Hi</p>"))
        assert results["toolOptions"] == {}

    def test_tool_options_echoed(self) -> None:
        opts: RunOptions = {"runOnly": {"type": "tag", "values": ["wcag2a"]}}
        results = fast_a11y(_wrap("<p>Hi</p>"), opts)
        assert results["toolOptions"]["runOnly"]["type"] == "tag"

    def test_rule_result_shape(self) -> None:
        results = fast_a11y(_wrap('<img src="x.jpg">'))
        v = _find_violation(results, "image-alt")
        assert v is not None
        assert "id" in v
        assert "impact" in v
        assert "tags" in v
        assert "description" in v
        assert "help" in v
        assert "helpUrl" in v
        assert isinstance(v["nodes"], list)

    def test_node_result_shape(self) -> None:
        results = fast_a11y(_wrap('<img src="x.jpg">'))
        v = _find_violation(results, "image-alt")
        assert v is not None
        node = v["nodes"][0]
        assert "html" in node
        assert "target" in node
        assert isinstance(node["target"], list)
        assert len(node["target"]) >= 1

    def test_help_url_format(self) -> None:
        results = fast_a11y(_wrap('<img src="x.jpg">'))
        v = _find_violation(results, "image-alt")
        assert v is not None
        assert "dequeuniversity.com" in v["helpUrl"]
        assert "image-alt" in v["helpUrl"]

    def test_categories_are_lists(self) -> None:
        results = fast_a11y(_wrap("<p>Hi</p>"))
        assert isinstance(results["passes"], list)
        assert isinstance(results["violations"], list)
        assert isinstance(results["incomplete"], list)
        assert isinstance(results["inapplicable"], list)


# ══════════════════════════════════════════════════════════════════════
#  Images -- text alternatives
# ══════════════════════════════════════════════════════════════════════


class TestImageAlt:
    def test_missing_alt_violation(self) -> None:
        results = fast_a11y(_wrap('<img src="pic.jpg">'))
        assert _find_violation(results, "image-alt") is not None

    def test_empty_alt_passes(self) -> None:
        results = fast_a11y(_wrap('<img src="pic.jpg" alt="">'))
        assert _find_violation(results, "image-alt") is None
        assert _find_pass(results, "image-alt") is not None

    def test_alt_with_text_passes(self) -> None:
        results = fast_a11y(_wrap('<img src="pic.jpg" alt="Photo">'))
        assert _find_violation(results, "image-alt") is None

    def test_aria_label_passes(self) -> None:
        results = fast_a11y(_wrap('<img src="pic.jpg" aria-label="Photo">'))
        assert _find_violation(results, "image-alt") is None

    def test_role_presentation_passes(self) -> None:
        results = fast_a11y(_wrap('<img src="x.jpg" role="presentation">'))
        assert _find_violation(results, "image-alt") is None

    def test_role_none_passes(self) -> None:
        results = fast_a11y(_wrap('<img src="x.jpg" role="none">'))
        assert _find_violation(results, "image-alt") is None

    def test_hidden_img_ignored(self) -> None:
        results = fast_a11y(_wrap('<img src="x.jpg" hidden>'))
        assert _find_violation(results, "image-alt") is None

    def test_multiple_missing_alt(self) -> None:
        html = _wrap('<img src="a.jpg"><img src="b.jpg">')
        results = fast_a11y(html)
        v = _find_violation(results, "image-alt")
        assert v is not None
        assert len(v["nodes"]) == 2


class TestInputImageAlt:
    def test_missing_alt_violation(self) -> None:
        html = _wrap('<input type="image" src="btn.png">')
        results = fast_a11y(html)
        assert _find_violation(results, "input-image-alt") is not None

    def test_alt_present_passes(self) -> None:
        html = _wrap('<input type="image" src="btn.png" alt="Submit">')
        results = fast_a11y(html)
        assert _find_violation(results, "input-image-alt") is None


class TestSvgImgAlt:
    def test_svg_role_img_no_name_violation(self) -> None:
        html = _wrap('<svg role="img"></svg>')
        results = fast_a11y(html)
        assert _find_violation(results, "svg-img-alt") is not None

    def test_svg_role_img_with_label_passes(self) -> None:
        html = _wrap('<svg role="img" aria-label="Logo"></svg>')
        results = fast_a11y(html)
        assert _find_violation(results, "svg-img-alt") is None

    def test_svg_role_img_with_title_child_passes(self) -> None:
        html = _wrap('<svg role="img"><title>Logo</title></svg>')
        results = fast_a11y(html)
        assert _find_violation(results, "svg-img-alt") is None


class TestRoleImgAlt:
    def test_role_img_no_name_violation(self) -> None:
        html = _wrap('<div role="img"></div>')
        results = fast_a11y(html)
        assert _find_violation(results, "role-img-alt") is not None

    def test_role_img_with_label_passes(self) -> None:
        html = _wrap('<div role="img" aria-label="Chart"></div>')
        results = fast_a11y(html)
        assert _find_violation(results, "role-img-alt") is None


class TestAreaAlt:
    def test_area_no_alt_violation(self) -> None:
        html = _wrap('<map><area href="/link"></map>')
        results = fast_a11y(html)
        assert _find_violation(results, "area-alt") is not None

    def test_area_with_alt_passes(self) -> None:
        html = _wrap('<map><area href="/link" alt="Link text"></map>')
        results = fast_a11y(html)
        assert _find_violation(results, "area-alt") is None


class TestObjectAlt:
    def test_object_no_alt_violation(self) -> None:
        html = _wrap('<object data="movie.swf"></object>')
        results = fast_a11y(html)
        assert _find_violation(results, "object-alt") is not None

    def test_object_with_aria_label_passes(self) -> None:
        html = _wrap('<object data="movie.swf" aria-label="Movie"></object>')
        results = fast_a11y(html)
        assert _find_violation(results, "object-alt") is None

    def test_object_with_text_content_passes(self) -> None:
        html = _wrap('<object data="movie.swf">Fallback text</object>')
        results = fast_a11y(html)
        assert _find_violation(results, "object-alt") is None


class TestServerSideImageMap:
    def test_ismap_violation(self) -> None:
        html = _wrap('<img src="map.jpg" alt="Map" ismap>')
        results = fast_a11y(html)
        v = _find_violation(results, "server-side-image-map")
        assert v is not None


# ══════════════════════════════════════════════════════════════════════
#  Links
# ══════════════════════════════════════════════════════════════════════


class TestLinkName:
    def test_empty_link_violation(self) -> None:
        results = fast_a11y(_wrap('<a href="/page"></a>'))
        assert _find_violation(results, "link-name") is not None

    def test_link_with_text_passes(self) -> None:
        results = fast_a11y(_wrap('<a href="/page">About</a>'))
        assert _find_violation(results, "link-name") is None

    def test_link_with_aria_label_passes(self) -> None:
        html = _wrap('<a href="/page" aria-label="About us"></a>')
        results = fast_a11y(html)
        assert _find_violation(results, "link-name") is None

    def test_link_with_img_alt_passes(self) -> None:
        html = _wrap('<a href="/"><img src="logo.png" alt="Home"></a>')
        results = fast_a11y(html)
        assert _find_violation(results, "link-name") is None

    def test_anchor_without_href_ignored(self) -> None:
        results = fast_a11y(_wrap("<a>Not a link</a>"))
        assert _find_violation(results, "link-name") is None


class TestFrameTitle:
    def test_iframe_no_title_violation(self) -> None:
        html = _wrap('<iframe src="https://example.com"></iframe>')
        results = fast_a11y(html)
        assert _find_violation(results, "frame-title") is not None

    def test_iframe_with_title_passes(self) -> None:
        html = _wrap('<iframe src="https://example.com" title="Embed"></iframe>')
        results = fast_a11y(html)
        assert _find_violation(results, "frame-title") is None


# ══════════════════════════════════════════════════════════════════════
#  Headings
# ══════════════════════════════════════════════════════════════════════


class TestHeadingOrder:
    def test_skipped_level_violation(self) -> None:
        html = _wrap("<h1>Title</h1><h3>Skipped h2</h3>")
        results = fast_a11y(html)
        assert _find_violation(results, "heading-order") is not None

    def test_sequential_levels_pass(self) -> None:
        html = _wrap("<h1>Title</h1><h2>Sub</h2><h3>Detail</h3>")
        results = fast_a11y(html)
        assert _find_violation(results, "heading-order") is None

    def test_same_level_passes(self) -> None:
        html = _wrap("<h1>A</h1><h1>B</h1>")
        results = fast_a11y(html)
        assert _find_violation(results, "heading-order") is None

    def test_going_back_up_passes(self) -> None:
        html = _wrap("<h1>A</h1><h2>B</h2><h1>C</h1>")
        results = fast_a11y(html)
        assert _find_violation(results, "heading-order") is None


class TestEmptyHeading:
    def test_empty_heading_violation(self) -> None:
        results = fast_a11y(_wrap("<h2></h2>"))
        assert _find_violation(results, "empty-heading") is not None

    def test_heading_with_text_passes(self) -> None:
        results = fast_a11y(_wrap("<h2>Title</h2>"))
        assert _find_violation(results, "empty-heading") is None

    def test_heading_whitespace_only_violation(self) -> None:
        results = fast_a11y(_wrap("<h2>   </h2>"))
        assert _find_violation(results, "empty-heading") is not None


class TestPageHasHeadingOne:
    def test_missing_h1_violation(self) -> None:
        html = _wrap("<h2>Not a main heading</h2>")
        results = fast_a11y(html)
        assert _find_violation(results, "page-has-heading-one") is not None

    def test_h1_present_passes(self) -> None:
        html = _wrap("<h1>Main heading</h1>")
        results = fast_a11y(html)
        assert _find_pass(results, "page-has-heading-one") is not None

    def test_aria_heading_level_1_passes(self) -> None:
        html = _wrap('<div role="heading" aria-level="1">Main</div>')
        results = fast_a11y(html)
        assert _find_pass(results, "page-has-heading-one") is not None


# ══════════════════════════════════════════════════════════════════════
#  Forms
# ══════════════════════════════════════════════════════════════════════


class TestFormLabel:
    def test_input_no_label_violation(self) -> None:
        results = fast_a11y(_wrap('<input type="text">'))
        assert _find_violation(results, "label") is not None

    def test_input_with_label_for_passes(self) -> None:
        html = _wrap(
            '<label for="name">Name</label><input type="text" id="name">'
        )
        results = fast_a11y(html)
        assert _find_violation(results, "label") is None

    def test_input_with_aria_label_passes(self) -> None:
        html = _wrap('<input type="text" aria-label="Search">')
        results = fast_a11y(html)
        assert _find_violation(results, "label") is None

    def test_input_wrapped_in_label_passes(self) -> None:
        html = _wrap("<label>Name <input type='text'></label>")
        results = fast_a11y(html)
        assert _find_violation(results, "label") is None

    def test_hidden_input_ignored(self) -> None:
        html = _wrap('<input type="hidden" name="csrf">')
        results = fast_a11y(html)
        assert _find_violation(results, "label") is None

    def test_textarea_no_label_violation(self) -> None:
        results = fast_a11y(_wrap("<textarea></textarea>"))
        assert _find_violation(results, "label") is not None

    def test_select_no_label_violation(self) -> None:
        html = _wrap("<select><option>A</option></select>")
        results = fast_a11y(html)
        assert _find_violation(results, "select-name") is not None

    def test_select_with_aria_label_passes(self) -> None:
        html = _wrap(
            '<select aria-label="Color"><option>Red</option></select>'
        )
        results = fast_a11y(html)
        assert _find_violation(results, "select-name") is None


class TestButtonName:
    def test_empty_button_violation(self) -> None:
        results = fast_a11y(_wrap("<button></button>"))
        assert _find_violation(results, "button-name") is not None

    def test_button_with_text_passes(self) -> None:
        results = fast_a11y(_wrap("<button>Submit</button>"))
        assert _find_violation(results, "button-name") is None

    def test_button_with_aria_label_passes(self) -> None:
        html = _wrap('<button aria-label="Close"></button>')
        results = fast_a11y(html)
        assert _find_violation(results, "button-name") is None

    def test_role_button_empty_violation(self) -> None:
        html = _wrap('<div role="button"></div>')
        results = fast_a11y(html)
        assert _find_violation(results, "button-name") is not None


class TestInputButtonName:
    def test_input_button_no_value_violation(self) -> None:
        html = _wrap('<input type="button">')
        results = fast_a11y(html)
        assert _find_violation(results, "input-button-name") is not None

    def test_input_submit_has_default_name(self) -> None:
        html = _wrap('<input type="submit">')
        results = fast_a11y(html)
        assert _find_violation(results, "input-button-name") is None

    def test_input_button_with_value_passes(self) -> None:
        html = _wrap('<input type="button" value="Go">')
        results = fast_a11y(html)
        assert _find_violation(results, "input-button-name") is None


class TestFormFieldMultipleLabels:
    def test_multiple_labels_violation(self) -> None:
        html = _wrap(
            '<label for="x">A</label>'
            '<label for="x">B</label>'
            '<input id="x" type="text">'
        )
        results = fast_a11y(html)
        v = _find_violation(results, "form-field-multiple-labels")
        assert v is not None

    def test_single_label_passes(self) -> None:
        html = _wrap('<label for="x">Name</label><input id="x" type="text">')
        results = fast_a11y(html)
        assert _find_violation(results, "form-field-multiple-labels") is None


class TestAutocompleteValid:
    def test_invalid_autocomplete_violation(self) -> None:
        html = _wrap('<input type="text" autocomplete="foobar">')
        results = fast_a11y(html)
        assert _find_violation(results, "autocomplete-valid") is not None

    def test_valid_autocomplete_passes(self) -> None:
        html = _wrap('<input type="email" autocomplete="email">')
        results = fast_a11y(html)
        assert _find_violation(results, "autocomplete-valid") is None

    def test_empty_autocomplete_violation(self) -> None:
        html = _wrap('<input type="text" autocomplete="">')
        results = fast_a11y(html)
        assert _find_violation(results, "autocomplete-valid") is not None


class TestLabelTitleOnly:
    def test_title_only_violation(self) -> None:
        html = _wrap('<input type="text" title="Name">')
        results = fast_a11y(html)
        assert _find_violation(results, "label-title-only") is not None

    def test_proper_label_passes(self) -> None:
        html = _wrap(
            '<label for="x">Name</label><input type="text" id="x" title="Name">'
        )
        results = fast_a11y(html)
        assert _find_violation(results, "label-title-only") is None


# ══════════════════════════════════════════════════════════════════════
#  ARIA
# ══════════════════════════════════════════════════════════════════════


class TestAriaRoles:
    def test_invalid_role_violation(self) -> None:
        html = _wrap('<div role="fakewidget">Content</div>')
        results = fast_a11y(html)
        assert _find_violation(results, "aria-roles") is not None

    def test_valid_role_passes(self) -> None:
        html = _wrap('<div role="alert">Warning!</div>')
        results = fast_a11y(html)
        assert _find_violation(results, "aria-roles") is None


class TestAriaRequiredAttr:
    def test_checkbox_missing_checked_violation(self) -> None:
        html = _wrap('<div role="checkbox" aria-label="Agree">X</div>')
        results = fast_a11y(html)
        assert _find_violation(results, "aria-required-attr") is not None

    def test_checkbox_with_checked_passes(self) -> None:
        html = _wrap(
            '<div role="checkbox" aria-checked="false" aria-label="Agree">X</div>'
        )
        results = fast_a11y(html)
        assert _find_violation(results, "aria-required-attr") is None


class TestAriaValidAttr:
    def test_invalid_aria_attr_violation(self) -> None:
        html = _wrap('<div aria-foobar="true">Text</div>')
        results = fast_a11y(html)
        assert _find_violation(results, "aria-valid-attr") is not None

    def test_valid_aria_attr_passes(self) -> None:
        html = _wrap('<div aria-hidden="true">Text</div>')
        results = fast_a11y(html)
        assert _find_violation(results, "aria-valid-attr") is None


class TestAriaHiddenBody:
    def test_aria_hidden_on_body_violation(self) -> None:
        html = (
            '<!DOCTYPE html><html lang="en"><head><title>T</title></head>'
            '<body aria-hidden="true"><p>Hello</p></body></html>'
        )
        results = fast_a11y(html)
        assert _find_violation(results, "aria-hidden-body") is not None

    def test_no_aria_hidden_on_body_passes(self) -> None:
        results = fast_a11y(_wrap("<p>Hello</p>"))
        v = _find_violation(results, "aria-hidden-body")
        assert v is None


class TestAriaHiddenFocus:
    def test_focusable_inside_hidden_violation(self) -> None:
        html = _wrap('<div aria-hidden="true"><button>Click</button></div>')
        results = fast_a11y(html)
        assert _find_violation(results, "aria-hidden-focus") is not None

    def test_no_focusable_inside_hidden_passes(self) -> None:
        html = _wrap('<div aria-hidden="true"><span>Text</span></div>')
        results = fast_a11y(html)
        assert _find_violation(results, "aria-hidden-focus") is None


class TestAriaRequiredChildren:
    def test_list_without_listitem_violation(self) -> None:
        html = _wrap('<div role="list"><div>Item</div></div>')
        results = fast_a11y(html)
        assert _find_violation(results, "aria-required-children") is not None

    def test_list_with_listitem_passes(self) -> None:
        html = _wrap(
            '<div role="list"><div role="listitem">Item</div></div>'
        )
        results = fast_a11y(html)
        assert _find_violation(results, "aria-required-children") is None


class TestAriaRequiredParent:
    def test_listitem_outside_list_violation(self) -> None:
        html = _wrap('<div role="listitem">Item</div>')
        results = fast_a11y(html)
        assert _find_violation(results, "aria-required-parent") is not None

    def test_listitem_inside_list_passes(self) -> None:
        html = _wrap(
            '<div role="list"><div role="listitem">Item</div></div>'
        )
        results = fast_a11y(html)
        assert _find_violation(results, "aria-required-parent") is None


class TestAriaDeprecatedRole:
    def test_directory_role_violation(self) -> None:
        html = _wrap('<div role="directory">Items</div>')
        results = fast_a11y(html)
        assert _find_violation(results, "aria-deprecated-role") is not None


class TestAriaRoledescription:
    def test_roledescription_on_div_violation(self) -> None:
        html = _wrap('<div aria-roledescription="slide">Content</div>')
        results = fast_a11y(html)
        assert _find_violation(results, "aria-roledescription") is not None

    def test_roledescription_on_button_passes(self) -> None:
        html = _wrap(
            '<button aria-roledescription="slide">Next</button>'
        )
        results = fast_a11y(html)
        assert _find_violation(results, "aria-roledescription") is None


class TestAriaNameRules:
    def test_input_field_no_name_violation(self) -> None:
        html = _wrap('<div role="textbox"></div>')
        results = fast_a11y(html)
        assert _find_violation(results, "aria-input-field-name") is not None

    def test_input_field_with_label_passes(self) -> None:
        html = _wrap('<div role="textbox" aria-label="Search"></div>')
        results = fast_a11y(html)
        assert _find_violation(results, "aria-input-field-name") is None

    def test_toggle_field_no_name_violation(self) -> None:
        html = _wrap(
            '<div role="checkbox" aria-checked="false"></div>'
        )
        results = fast_a11y(html)
        assert _find_violation(results, "aria-toggle-field-name") is not None

    def test_command_no_name_violation(self) -> None:
        html = _wrap('<div role="button"></div>')
        results = fast_a11y(html)
        assert _find_violation(results, "aria-command-name") is not None

    def test_dialog_no_name_violation(self) -> None:
        html = _wrap('<div role="dialog"></div>')
        results = fast_a11y(html)
        assert _find_violation(results, "aria-dialog-name") is not None

    def test_dialog_with_label_passes(self) -> None:
        html = _wrap(
            '<div role="dialog" aria-label="Settings"><p>Content</p></div>'
        )
        results = fast_a11y(html)
        assert _find_violation(results, "aria-dialog-name") is None


# ══════════════════════════════════════════════════════════════════════
#  Tables
# ══════════════════════════════════════════════════════════════════════


class TestEmptyTableHeader:
    def test_empty_th_violation(self) -> None:
        html = _wrap("<table><tr><th></th><td>Data</td></tr></table>")
        results = fast_a11y(html)
        assert _find_violation(results, "empty-table-header") is not None

    def test_th_with_text_passes(self) -> None:
        html = _wrap(
            "<table><tr><th>Name</th><td>Alice</td></tr></table>"
        )
        results = fast_a11y(html)
        assert _find_violation(results, "empty-table-header") is None


class TestTdHeadersAttr:
    def test_invalid_headers_ref_violation(self) -> None:
        html = _wrap(
            '<table><tr><th id="h1">Name</th></tr>'
            '<tr><td headers="nonexistent">Alice</td></tr></table>'
        )
        results = fast_a11y(html)
        assert _find_violation(results, "td-headers-attr") is not None

    def test_valid_headers_ref_passes(self) -> None:
        html = _wrap(
            '<table><tr><th id="h1">Name</th></tr>'
            '<tr><td headers="h1">Alice</td></tr></table>'
        )
        results = fast_a11y(html)
        assert _find_violation(results, "td-headers-attr") is None


class TestTdHasHeader:
    def test_large_table_no_headers_violation(self) -> None:
        rows = ""
        for i in range(4):
            cells = "".join(
                f'<td id="c{i}{j}">Cell {i}-{j}</td>' for j in range(4)
            )
            rows += f"<tr>{cells}</tr>"
        html = _wrap(f"<table>{rows}</table>")
        results = fast_a11y(html)
        assert _find_violation(results, "td-has-header") is not None

    def test_large_table_with_headers_passes(self) -> None:
        header = "<tr>" + "".join(
            f'<th id="h{j}">H{j}</th>' for j in range(4)
        ) + "</tr>"
        rows = ""
        for i in range(3):
            cells = "".join(
                f'<td id="d{i}{j}">Cell {i}-{j}</td>' for j in range(4)
            )
            rows += f"<tr>{cells}</tr>"
        html = _wrap(f"<table>{header}{rows}</table>")
        results = fast_a11y(html)
        assert _find_violation(results, "td-has-header") is None

    def test_small_table_not_checked(self) -> None:
        html = _wrap(
            '<table><tr><td id="a">A</td><td id="b">B</td></tr>'
            '<tr><td id="c">C</td><td id="d">D</td></tr></table>'
        )
        results = fast_a11y(html)
        assert _find_violation(results, "td-has-header") is None


class TestTableDuplicateName:
    def test_same_summary_and_caption_violation(self) -> None:
        html = _wrap(
            '<table summary="Sales"><caption>Sales</caption>'
            "<tr><th>Q</th><td>100</td></tr></table>"
        )
        results = fast_a11y(html)
        v = _find_violation(results, "table-duplicate-name")
        assert v is not None


class TestScopeAttrValid:
    def test_scope_on_td_violation(self) -> None:
        html = _wrap(
            '<table><tr><td scope="col">Oops</td></tr></table>'
        )
        results = fast_a11y(html)
        assert _find_violation(results, "scope-attr-valid") is not None

    def test_valid_scope_on_th_passes(self) -> None:
        html = _wrap(
            '<table><tr><th scope="col">Name</th></tr></table>'
        )
        results = fast_a11y(html)
        assert _find_violation(results, "scope-attr-valid") is None


# ══════════════════════════════════════════════════════════════════════
#  Language
# ══════════════════════════════════════════════════════════════════════


class TestHtmlHasLang:
    def test_missing_lang_violation(self) -> None:
        html = "<!DOCTYPE html><html><head><title>T</title></head><body></body></html>"
        results = fast_a11y(html)
        assert _find_violation(results, "html-has-lang") is not None

    def test_lang_present_passes(self) -> None:
        results = fast_a11y(_wrap("<p>Hi</p>"))
        assert _find_violation(results, "html-has-lang") is None


class TestHtmlLangValid:
    def test_invalid_lang_violation(self) -> None:
        html = (
            '<!DOCTYPE html><html lang="zzz">'
            "<head><title>T</title></head><body></body></html>"
        )
        results = fast_a11y(html)
        assert _find_violation(results, "html-lang-valid") is not None

    def test_valid_lang_passes(self) -> None:
        results = fast_a11y(_wrap("<p>Hi</p>", lang="en"))
        assert _find_violation(results, "html-lang-valid") is None

    def test_regional_subtag_valid(self) -> None:
        results = fast_a11y(_wrap("<p>Hi</p>", lang="en-US"))
        assert _find_violation(results, "html-lang-valid") is None


class TestHtmlXmlLangMismatch:
    def test_mismatch_violation(self) -> None:
        html = (
            '<!DOCTYPE html><html lang="en" xml:lang="fr">'
            "<head><title>T</title></head><body></body></html>"
        )
        results = fast_a11y(html)
        assert _find_violation(results, "html-xml-lang-mismatch") is not None

    def test_matching_langs_pass(self) -> None:
        html = (
            '<!DOCTYPE html><html lang="en" xml:lang="en">'
            "<head><title>T</title></head><body></body></html>"
        )
        results = fast_a11y(html)
        assert _find_violation(results, "html-xml-lang-mismatch") is None


class TestValidLang:
    def test_invalid_lang_on_element_violation(self) -> None:
        html = _wrap('<p lang="xyz">Text</p>')
        results = fast_a11y(html)
        assert _find_violation(results, "valid-lang") is not None

    def test_valid_lang_on_element_passes(self) -> None:
        html = _wrap('<p lang="fr">Bonjour</p>')
        results = fast_a11y(html)
        assert _find_violation(results, "valid-lang") is None


# ══════════════════════════════════════════════════════════════════════
#  Semantic / Structure
# ══════════════════════════════════════════════════════════════════════


class TestDocumentTitle:
    def test_missing_title_violation(self) -> None:
        html = '<!DOCTYPE html><html lang="en"><head></head><body></body></html>'
        results = fast_a11y(html)
        assert _find_violation(results, "document-title") is not None

    def test_empty_title_violation(self) -> None:
        html = (
            '<!DOCTYPE html><html lang="en">'
            "<head><title></title></head><body></body></html>"
        )
        results = fast_a11y(html)
        assert _find_violation(results, "document-title") is not None

    def test_title_present_passes(self) -> None:
        results = fast_a11y(_wrap("<p>Hi</p>"))
        assert _find_violation(results, "document-title") is None


class TestDuplicateId:
    def test_duplicate_ids_violation(self) -> None:
        html = _wrap('<div id="x">A</div><div id="x">B</div>')
        results = fast_a11y(html)
        assert _find_violation(results, "duplicate-id") is not None

    def test_unique_ids_pass(self) -> None:
        html = _wrap('<div id="a">A</div><div id="b">B</div>')
        results = fast_a11y(html)
        assert _find_violation(results, "duplicate-id") is None


class TestNestedInteractive:
    def test_button_inside_link_violation(self) -> None:
        html = _wrap('<a href="/"><button>Click</button></a>')
        results = fast_a11y(html)
        assert _find_violation(results, "nested-interactive") is not None

    def test_no_nesting_passes(self) -> None:
        html = _wrap('<a href="/">Link</a><button>Click</button>')
        results = fast_a11y(html)
        v = _find_violation(results, "nested-interactive")
        # Should not flag non-nested elements
        if v:
            # If there is a violation, nodes should not include non-nested
            for node in v["nodes"]:
                assert "button" not in node["html"] or "a" in node["html"]


class TestListStructure:
    def test_ul_with_div_child_violation(self) -> None:
        html = _wrap("<ul><div>Not an li</div></ul>")
        results = fast_a11y(html)
        assert _find_violation(results, "list") is not None

    def test_ul_with_li_passes(self) -> None:
        html = _wrap("<ul><li>Item</li></ul>")
        results = fast_a11y(html)
        assert _find_violation(results, "list") is None

    def test_li_outside_list_violation(self) -> None:
        html = _wrap("<li>Orphan item</li>")
        results = fast_a11y(html)
        assert _find_violation(results, "listitem") is not None

    def test_dl_with_invalid_child_violation(self) -> None:
        html = _wrap("<dl><span>Bad</span></dl>")
        results = fast_a11y(html)
        assert _find_violation(results, "definition-list") is not None

    def test_dl_with_dt_dd_passes(self) -> None:
        html = _wrap("<dl><dt>Term</dt><dd>Def</dd></dl>")
        results = fast_a11y(html)
        assert _find_violation(results, "definition-list") is None

    def test_dt_outside_dl_violation(self) -> None:
        html = _wrap("<dt>Orphan term</dt>")
        results = fast_a11y(html)
        assert _find_violation(results, "dlitem") is not None


# ══════════════════════════════════════════════════════════════════════
#  Media
# ══════════════════════════════════════════════════════════════════════


class TestBlink:
    def test_blink_violation(self) -> None:
        results = fast_a11y(_wrap("<blink>Blinking</blink>"))
        assert _find_violation(results, "blink") is not None


class TestMarquee:
    def test_marquee_violation(self) -> None:
        results = fast_a11y(_wrap("<marquee>Scrolling</marquee>"))
        assert _find_violation(results, "marquee") is not None


class TestMetaRefresh:
    def test_meta_refresh_with_delay_violation(self) -> None:
        html = (
            '<!DOCTYPE html><html lang="en"><head><title>T</title>'
            '<meta http-equiv="refresh" content="5;url=http://example.com">'
            "</head><body></body></html>"
        )
        results = fast_a11y(html)
        assert _find_violation(results, "meta-refresh") is not None

    def test_meta_refresh_zero_passes(self) -> None:
        html = (
            '<!DOCTYPE html><html lang="en"><head><title>T</title>'
            '<meta http-equiv="refresh" content="0;url=http://example.com">'
            "</head><body></body></html>"
        )
        results = fast_a11y(html)
        assert _find_violation(results, "meta-refresh") is None


class TestMetaViewport:
    def test_user_scalable_no_violation(self) -> None:
        html = (
            '<!DOCTYPE html><html lang="en"><head><title>T</title>'
            '<meta name="viewport" content="width=device-width, user-scalable=no">'
            "</head><body></body></html>"
        )
        results = fast_a11y(html)
        assert _find_violation(results, "meta-viewport") is not None

    def test_max_scale_too_low_violation(self) -> None:
        html = (
            '<!DOCTYPE html><html lang="en"><head><title>T</title>'
            '<meta name="viewport" content="width=device-width, maximum-scale=1.0">'
            "</head><body></body></html>"
        )
        results = fast_a11y(html)
        assert _find_violation(results, "meta-viewport") is not None

    def test_good_viewport_passes(self) -> None:
        html = (
            '<!DOCTYPE html><html lang="en"><head><title>T</title>'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            "</head><body></body></html>"
        )
        results = fast_a11y(html)
        assert _find_violation(results, "meta-viewport") is None


class TestVideoCaption:
    def test_video_no_track_incomplete(self) -> None:
        html = _wrap('<video src="movie.mp4"></video>')
        results = fast_a11y(html)
        assert _find_incomplete(results, "video-caption") is not None

    def test_video_with_captions_passes(self) -> None:
        html = _wrap(
            '<video src="movie.mp4">'
            '<track kind="captions" src="captions.vtt">'
            "</video>"
        )
        results = fast_a11y(html)
        assert _find_pass(results, "video-caption") is not None


class TestNoAutoplayAudio:
    def test_autoplay_no_controls_violation(self) -> None:
        html = _wrap('<audio autoplay src="sound.mp3"></audio>')
        results = fast_a11y(html)
        assert _find_violation(results, "no-autoplay-audio") is not None

    def test_autoplay_muted_passes(self) -> None:
        html = _wrap('<video autoplay muted src="vid.mp4"></video>')
        results = fast_a11y(html)
        assert _find_violation(results, "no-autoplay-audio") is None

    def test_autoplay_with_controls_incomplete(self) -> None:
        html = _wrap('<audio autoplay controls src="sound.mp3"></audio>')
        results = fast_a11y(html)
        assert _find_incomplete(results, "no-autoplay-audio") is not None

    def test_no_autoplay_passes(self) -> None:
        html = _wrap('<audio src="sound.mp3"></audio>')
        results = fast_a11y(html)
        assert _find_pass(results, "no-autoplay-audio") is not None


# ══════════════════════════════════════════════════════════════════════
#  Landmarks
# ══════════════════════════════════════════════════════════════════════


class TestLandmarks:
    def test_no_main_landmark_violation(self) -> None:
        html = _wrap("<div><p>Content</p></div>")
        results = fast_a11y(html)
        assert _find_violation(results, "landmark-one-main") is not None

    def test_main_landmark_passes(self) -> None:
        html = _wrap("<main><p>Content</p></main>")
        results = fast_a11y(html)
        assert _find_pass(results, "landmark-one-main") is not None

    def test_duplicate_main_violation(self) -> None:
        html = _wrap("<main>A</main><main>B</main>")
        results = fast_a11y(html)
        v = _find_violation(results, "landmark-no-duplicate-main")
        assert v is not None

    def test_banner_inside_landmark_violation(self) -> None:
        html = _wrap("<main><header>Nested banner</header></main>")
        results = fast_a11y(html)
        v = _find_violation(results, "landmark-banner-is-top-level")
        assert v is not None


# ══════════════════════════════════════════════════════════════════════
#  Navigation / keyboard
# ══════════════════════════════════════════════════════════════════════


class TestTabindex:
    def test_positive_tabindex_violation(self) -> None:
        html = _wrap('<input type="text" tabindex="5" aria-label="Field">')
        results = fast_a11y(html)
        assert _find_violation(results, "tabindex") is not None

    def test_zero_tabindex_passes(self) -> None:
        html = _wrap('<div tabindex="0">Focusable</div>')
        results = fast_a11y(html)
        assert _find_violation(results, "tabindex") is None


class TestAccesskeys:
    def test_duplicate_accesskey_violation(self) -> None:
        html = _wrap(
            '<a href="/a" accesskey="s">Save</a>'
            '<a href="/b" accesskey="s">Search</a>'
        )
        results = fast_a11y(html)
        assert _find_violation(results, "accesskeys") is not None

    def test_unique_accesskeys_pass(self) -> None:
        html = _wrap(
            '<a href="/a" accesskey="s">Save</a>'
            '<a href="/b" accesskey="x">Exit</a>'
        )
        results = fast_a11y(html)
        assert _find_violation(results, "accesskeys") is None


class TestBypass:
    def test_page_with_headings_passes(self) -> None:
        html = _wrap("<h1>Title</h1><p>Content</p>")
        results = fast_a11y(html)
        assert _find_pass(results, "bypass") is not None

    def test_page_with_skip_link_passes(self) -> None:
        html = _wrap(
            '<a href="#main">Skip to content</a>'
            '<main id="main"><p>Content</p></main>'
        )
        results = fast_a11y(html)
        assert _find_pass(results, "bypass") is not None


# ══════════════════════════════════════════════════════════════════════
#  Color contrast
# ══════════════════════════════════════════════════════════════════════


class TestColorContrast:
    def test_low_contrast_violation(self) -> None:
        html = _wrap('<p style="color: #ccc; background-color: #fff;">Light text</p>')
        results = fast_a11y(html)
        assert _find_violation(results, "color-contrast") is not None

    def test_high_contrast_passes(self) -> None:
        html = _wrap('<p style="color: #000; background-color: #fff;">Dark text</p>')
        results = fast_a11y(html)
        assert _find_pass(results, "color-contrast") is not None

    def test_background_image_incomplete(self) -> None:
        html = _wrap(
            '<p style="color: #000; background-image: url(bg.jpg);">Text</p>'
        )
        results = fast_a11y(html)
        assert _find_incomplete(results, "color-contrast") is not None


# ══════════════════════════════════════════════════════════════════════
#  Edge cases
# ══════════════════════════════════════════════════════════════════════


class TestEdgeCases:
    def test_empty_html_no_crash(self) -> None:
        results = fast_a11y("")
        assert isinstance(results, dict)
        assert "violations" in results

    def test_empty_string_returns_valid_structure(self) -> None:
        results = fast_a11y("")
        assert isinstance(results["passes"], list)
        assert isinstance(results["violations"], list)

    def test_whitespace_only_no_crash(self) -> None:
        results = fast_a11y("   \n\t  ")
        assert isinstance(results, dict)

    def test_malformed_html_no_crash(self) -> None:
        results = fast_a11y("<div><p>Unclosed tags<span>")
        assert isinstance(results, dict)

    def test_deeply_nested_html_no_crash(self) -> None:
        html = "<div>" * 50 + "Content" + "</div>" * 50
        results = fast_a11y(html)
        assert isinstance(results, dict)

    def test_html_with_comments(self) -> None:
        html = _wrap("<!-- comment --><p>Content</p>")
        results = fast_a11y(html)
        assert isinstance(results, dict)

    def test_special_characters_in_attrs(self) -> None:
        html = _wrap('<img src="x.jpg" alt="A &amp; B &lt;C&gt;">')
        results = fast_a11y(html)
        assert _find_violation(results, "image-alt") is None

    def test_self_closing_tags(self) -> None:
        html = _wrap("<br><hr><input type='hidden' name='x'>")
        results = fast_a11y(html)
        assert isinstance(results, dict)

    def test_no_html_tag(self) -> None:
        results = fast_a11y("<p>Just a paragraph</p>")
        assert isinstance(results, dict)

    def test_only_doctype(self) -> None:
        results = fast_a11y("<!DOCTYPE html>")
        assert isinstance(results, dict)


# ══════════════════════════════════════════════════════════════════════
#  Rule filtering
# ══════════════════════════════════════════════════════════════════════


class TestRuleFiltering:
    def test_run_only_by_tag(self) -> None:
        html = _wrap('<img src="x.jpg">')
        opts: RunOptions = {
            "runOnly": {"type": "tag", "values": ["wcag2a"]},
        }
        results = fast_a11y(html, opts)
        assert _find_violation(results, "image-alt") is not None
        # meta-viewport is wcag2aa, should not appear
        assert "meta-viewport" not in _all_rule_ids(results)

    def test_run_only_by_rule(self) -> None:
        html = _wrap('<img src="x.jpg">')
        opts: RunOptions = {
            "runOnly": {"type": "rule", "values": ["image-alt"]},
        }
        results = fast_a11y(html, opts)
        assert _find_violation(results, "image-alt") is not None
        ids = _all_rule_ids(results)
        assert ids == {"image-alt"}

    def test_disable_specific_rule(self) -> None:
        html = _wrap('<img src="x.jpg">')
        opts: RunOptions = {
            "rules": {"image-alt": {"enabled": False}},
        }
        results = fast_a11y(html, opts)
        assert "image-alt" not in _all_rule_ids(results)

    def test_best_practice_tag_filter(self) -> None:
        html = _wrap("<h1>Title</h1><h3>Skipped h2</h3>")
        opts: RunOptions = {
            "runOnly": {"type": "tag", "values": ["best-practice"]},
        }
        results = fast_a11y(html, opts)
        assert _find_violation(results, "heading-order") is not None


# ══════════════════════════════════════════════════════════════════════
#  Comprehensive valid page
# ══════════════════════════════════════════════════════════════════════


class TestValidPage:
    def test_well_formed_page_no_critical(self) -> None:
        html = """<!DOCTYPE html>
<html lang="en">
<head><title>Accessible Page</title></head>
<body>
  <header><nav><a href="/">Home</a></nav></header>
  <main>
    <h1>Welcome</h1>
    <p>Well-structured page.</p>
    <img src="photo.jpg" alt="A scenic view">
    <form>
      <label for="email">Email</label>
      <input type="email" id="email" autocomplete="email">
      <button type="submit">Submit</button>
    </form>
  </main>
  <footer><p>Footer content</p></footer>
</body>
</html>"""
        results = fast_a11y(html)
        assert len(results["passes"]) > 0
        critical = [
            v for v in results["violations"] if v["impact"] == "critical"
        ]
        assert len(critical) == 0

    def test_inapplicable_rules_exist(self) -> None:
        results = fast_a11y(_wrap("<p>Simple page</p>"))
        assert len(results["inapplicable"]) > 0


class TestRecursionRegression:
    """Regression tests for RecursionError in FastNode equality.

    Table cells without IDs that share the same tag caused infinite
    recursion when get_selector() compared nodes via the default
    dataclass __eq__, which walked parent/child references.
    """

    def test_table_cells_without_ids_no_recursion(self) -> None:
        html = _wrap("""
        <table>
          <tr><td>A</td><td>B</td><td>C</td></tr>
          <tr><td>D</td><td>E</td><td>F</td></tr>
          <tr><td>G</td><td>H</td><td>I</td></tr>
        </table>
        """)
        # This would raise RecursionError before the fix
        results = fast_a11y(html)
        assert "violations" in results

    def test_large_table_no_recursion(self) -> None:
        rows = "".join(
            f"<tr>{''.join(f'<td>{r}_{c}</td>' for c in range(10))}</tr>"
            for r in range(20)
        )
        html = _wrap(f"<table>{rows}</table>")
        results = fast_a11y(html)
        assert "violations" in results

    def test_get_selector_disambiguates_same_tag_siblings(self) -> None:
        from fast_a11y.tree import build_tree, get_selector

        html = "<table><tr><td>A</td><td>B</td><td>C</td></tr></table>"
        nodes = build_tree(html)
        td_nodes = [n for n in nodes if n.tag == "td"]
        selectors = [get_selector(n) for n in td_nodes]
        # Each cell should get a unique selector via nth-child
        assert len(selectors) == len(set(selectors))
