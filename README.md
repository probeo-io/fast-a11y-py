# fast-a11y

Fast, zero-DOM accessibility checker with **axe-core compatible output**. Runs on raw HTML using static analysis -- no browser, no Selenium, no Playwright.

## Why?

axe-core is the gold standard for accessibility testing, but it requires a full DOM environment (JSDOM or a real browser). For crawlers, CI pipelines, and build tools processing thousands of pages, that's a memory and performance bottleneck.

**fast-a11y** implements 86 WCAG rules using only Python's stdlib `html.parser`. It returns the exact same output format as axe-core, so it's a drop-in replacement.

| | axe-core + browser | fast-a11y |
|---|---|---|
| 1000 elements | ~200-500MB, ~2-5s | ~5MB, ~30ms |
| Requires browser/DOM | Yes | No |
| Output format | AxeResults | AxeResults (identical) |
| WCAG rules | ~95 | 86 |
| Dependencies | Heavy | Zero (stdlib only) |

## Install

```bash
pip install fast-a11y
```

## Usage

```python
from fast_a11y import fast_a11y

html = """<!DOCTYPE html>
<html lang="en">
<head><title>My Page</title></head>
<body>
  <img src="photo.jpg">
  <a href="/page"></a>
</body>
</html>"""

results = fast_a11y(html)

print(results["violations"])
# [
#   {"id": "image-alt", "impact": "critical", "nodes": [...]},
#   {"id": "link-name", "impact": "serious", "nodes": [...]},
# ]
```

## Options

```python
from fast_a11y import fast_a11y

# Filter by WCAG tags (same as axe-core)
results = fast_a11y(html, {"runOnly": {"type": "tag", "values": ["wcag2a", "wcag2aa"]}})

# Filter by specific rules
results = fast_a11y(html, {"runOnly": {"type": "rule", "values": ["image-alt", "link-name"]}})

# Disable specific rules
results = fast_a11y(html, {"rules": {"color-contrast": {"enabled": False}}})

# Include URL in output
results = fast_a11y(html, url="https://example.com/page")
```

## Output Format

The output is **identical** to axe-core's `AxeResults`:

```python
{
    "testEngine": {"name": "fast-a11y", "version": "0.1.0"},
    "testRunner": {"name": "fast-a11y"},
    "testEnvironment": {"userAgent": "", "windowWidth": 0, "windowHeight": 0},
    "url": "",
    "timestamp": "2026-01-01T00:00:00+00:00",
    "toolOptions": {},
    "passes": [...],
    "violations": [...],
    "incomplete": [...],
    "inapplicable": [...],
}
```

Each `RuleResult` contains `id`, `impact`, `tags`, `description`, `help`, `helpUrl`, and `nodes[]` -- exactly matching axe-core.

## Rules Covered (86)

### Text Alternatives
`image-alt`, `input-image-alt`, `object-alt`, `role-img-alt`, `svg-img-alt`, `area-alt`, `server-side-image-map`

### Language
`html-has-lang`, `html-lang-valid`, `html-xml-lang-mismatch`, `valid-lang`

### Structure
`document-title`, `definition-list`, `dlitem`, `list`, `listitem`, `heading-order`, `empty-heading`, `empty-table-header`, `duplicate-id`, `duplicate-id-aria`, `nested-interactive`, `page-has-heading-one`

### Forms
`label`, `select-name`, `input-button-name`, `button-name`, `form-field-multiple-labels`, `autocomplete-valid`, `label-title-only`

### ARIA (25 rules)
`aria-allowed-attr`, `aria-allowed-role`, `aria-hidden-body`, `aria-hidden-focus`, `aria-required-attr`, `aria-required-children`, `aria-required-parent`, `aria-roles`, `aria-valid-attr`, `aria-valid-attr-value`, `aria-roledescription`, `aria-input-field-name`, `aria-toggle-field-name`, `aria-command-name`, `aria-meter-name`, `aria-progressbar-name`, `aria-tooltip-name`, `aria-treeitem-name`, `aria-dialog-name`, `aria-text`, `aria-deprecated-role`, `aria-prohibited-attr`, `aria-braille-equivalent`, `aria-conditional-attr`, `presentation-role-conflict`

### Navigation
`link-name`, `frame-title`, `frame-title-unique`, `bypass`, `tabindex`, `accesskeys`, `region`

### Media & Time
`blink`, `marquee`, `meta-refresh`, `meta-refresh-no-exceptions`, `meta-viewport`, `meta-viewport-large`, `no-autoplay-audio`, `video-caption`

### Tables
`td-headers-attr`, `th-has-data-cells`, `td-has-header`, `table-duplicate-name`, `table-fake-caption`, `scope-attr-valid`

### Landmarks
`landmark-one-main`, `landmark-no-duplicate-main`, `landmark-no-duplicate-banner`, `landmark-no-duplicate-contentinfo`, `landmark-banner-is-top-level`, `landmark-contentinfo-is-top-level`, `landmark-complementary-is-top-level`, `landmark-main-is-top-level`, `landmark-unique`

### Color Contrast (best-effort)
`color-contrast` -- Checks inline styles and `<style>` blocks. Colors that can't be resolved statically (external CSS, var(), background images) are reported as `incomplete` rather than violations.

## Rules NOT Covered (~9)

These rules fundamentally require a rendered DOM:

- `target-size` -- requires `getBoundingClientRect()`
- `link-in-text-block` -- requires computed styles
- `css-orientation-lock` -- requires CSS media query analysis
- `p-as-heading` -- requires computed font styling
- `scrollable-region-focusable` -- requires overflow computation
- `focus-order-semantics` -- requires tab order computation
- `hidden-content` -- requires full visibility computation
- `label-content-name-mismatch` -- requires rendered visible text
- `frame-tested` -- runtime axe concept

## Replacing axe-core

If you're currently using axe-core with a browser:

```python
# Before (axe-core + Playwright)
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.set_content(html)
    results = page.evaluate("axe.run()")

# After (fast-a11y)
from fast_a11y import fast_a11y

results = fast_a11y(html)
```

Same output format. Synchronous. No browser. 100x less memory.

## See Also

| Package | Description |
|---|---|
| [@probeo/fast-a11y](https://github.com/probeo-io/fast-a11y) | TypeScript version of this package |
| [workflow-py](https://github.com/probeo-io/workflow-py) | Stage-based pipeline engine -- use fast-a11y as a step |

## License

MIT
