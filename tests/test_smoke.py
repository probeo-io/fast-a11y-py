"""Smoke tests for fast-a11y -- mirrors the TypeScript test suite."""

from fast_a11y import fast_a11y


def test_returns_axe_core_compatible_structure() -> None:
    html = '<!DOCTYPE html><html><head><title>Test</title></head><body><h1>Hello</h1></body></html>'
    results = fast_a11y(html)

    assert results["testEngine"]["name"] == "fast-a11y"
    assert results["testEngine"]["version"] == "0.1.0"
    assert "passes" in results
    assert "violations" in results
    assert "incomplete" in results
    assert "inapplicable" in results
    assert results["timestamp"]


def test_catches_missing_alt_on_img() -> None:
    html = '<!DOCTYPE html><html lang="en"><head><title>Test</title></head><body><img src="photo.jpg"></body></html>'
    results = fast_a11y(html)

    image_alt = next((v for v in results["violations"] if v["id"] == "image-alt"), None)
    assert image_alt is not None
    assert image_alt["impact"] == "critical"
    assert len(image_alt["nodes"]) == 1
    assert "img" in image_alt["nodes"][0]["html"]
    assert len(image_alt["nodes"][0]["target"]) == 1
    assert image_alt["nodes"][0].get("failureSummary")


def test_passes_when_img_has_alt() -> None:
    html = '<!DOCTYPE html><html lang="en"><head><title>Test</title></head><body><img src="photo.jpg" alt="A photo"></body></html>'
    results = fast_a11y(html)

    image_alt_v = next((v for v in results["violations"] if v["id"] == "image-alt"), None)
    assert image_alt_v is None

    image_alt_p = next((v for v in results["passes"] if v["id"] == "image-alt"), None)
    assert image_alt_p is not None


def test_catches_missing_lang_on_html() -> None:
    html = '<!DOCTYPE html><html><head><title>Test</title></head><body><p>Hello</p></body></html>'
    results = fast_a11y(html)

    html_lang = next((v for v in results["violations"] if v["id"] == "html-has-lang"), None)
    assert html_lang is not None


def test_catches_missing_document_title() -> None:
    html = '<!DOCTYPE html><html lang="en"><head></head><body><p>Hello</p></body></html>'
    results = fast_a11y(html)

    doc_title = next((v for v in results["violations"] if v["id"] == "document-title"), None)
    assert doc_title is not None


def test_catches_nested_interactive_elements() -> None:
    html = '<!DOCTYPE html><html lang="en"><head><title>Test</title></head><body><a href="/"><button>Click</button></a></body></html>'
    results = fast_a11y(html)

    nested = next((v for v in results["violations"] if v["id"] == "nested-interactive"), None)
    assert nested is not None


def test_catches_meta_viewport_disabling_zoom() -> None:
    html = '<!DOCTYPE html><html lang="en"><head><title>Test</title><meta name="viewport" content="width=device-width, user-scalable=no"></head><body><p>Hello</p></body></html>'
    results = fast_a11y(html)

    viewport = next((v for v in results["violations"] if v["id"] == "meta-viewport"), None)
    assert viewport is not None


def test_catches_heading_order_skip() -> None:
    html = '<!DOCTYPE html><html lang="en"><head><title>Test</title></head><body><h1>Title</h1><h3>Subtitle</h3></body></html>'
    results = fast_a11y(html)

    heading_order = next((v for v in results["violations"] if v["id"] == "heading-order"), None)
    assert heading_order is not None


def test_catches_button_without_name() -> None:
    html = '<!DOCTYPE html><html lang="en"><head><title>Test</title></head><body><button></button></body></html>'
    results = fast_a11y(html)

    button_name = next((v for v in results["violations"] if v["id"] == "button-name"), None)
    assert button_name is not None


def test_catches_link_without_name() -> None:
    html = '<!DOCTYPE html><html lang="en"><head><title>Test</title></head><body><a href="/page"></a></body></html>'
    results = fast_a11y(html)

    link_name = next((v for v in results["violations"] if v["id"] == "link-name"), None)
    assert link_name is not None


def test_filters_by_run_only_tags() -> None:
    html = '<!DOCTYPE html><html><head></head><body><img src="x.jpg"></body></html>'
    results = fast_a11y(html, {"runOnly": {"type": "tag", "values": ["wcag2a"]}})

    # Should include image-alt (wcag2a)
    image_alt = next((v for v in results["violations"] if v["id"] == "image-alt"), None)
    assert image_alt is not None

    # meta-viewport is wcag2aa, should not appear
    all_rule_ids = (
        [v["id"] for v in results["violations"]]
        + [v["id"] for v in results["passes"]]
        + [v["id"] for v in results["inapplicable"]]
    )
    assert "meta-viewport" not in all_rule_ids


def test_handles_duplicate_ids() -> None:
    html = '<!DOCTYPE html><html lang="en"><head><title>Test</title></head><body><div id="foo">A</div><div id="foo">B</div></body></html>'
    results = fast_a11y(html)

    dup_id = next((v for v in results["violations"] if v["id"] == "duplicate-id"), None)
    assert dup_id is not None


def test_catches_missing_form_label() -> None:
    html = '<!DOCTYPE html><html lang="en"><head><title>Test</title></head><body><input type="text"></body></html>'
    results = fast_a11y(html)

    label = next((v for v in results["violations"] if v["id"] == "label"), None)
    assert label is not None


def test_catches_blink_element() -> None:
    html = '<!DOCTYPE html><html lang="en"><head><title>Test</title></head><body><blink>Warning!</blink></body></html>'
    results = fast_a11y(html)

    blink = next((v for v in results["violations"] if v["id"] == "blink"), None)
    assert blink is not None


def test_valid_page_has_mostly_passes() -> None:
    html = """<!DOCTYPE html>
<html lang="en">
<head><title>Accessible Page</title></head>
<body>
  <header><nav><a href="/">Home</a></nav></header>
  <main>
    <h1>Welcome</h1>
    <p>This is a well-structured page.</p>
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
    # A well-formed page should have few or no critical violations
    critical = [v for v in results["violations"] if v["impact"] == "critical"]
    assert len(critical) == 0
