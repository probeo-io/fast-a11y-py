"""Color contrast tests -- CSS variable resolution and external stylesheet support.

Real-world patterns sourced from crawled sites where colors are typically defined
as CSS custom properties and applied via var() references.
"""

from __future__ import annotations

import pytest
from fast_a11y import fast_a11y


def _html(body: str, style: str = "") -> str:
    style_block = f"<style>{style}</style>" if style else ""
    return f'<!DOCTYPE html><html lang="en"><head><title>T</title>{style_block}</head><body>{body}</body></html>'


def _contrast(results: dict) -> dict:
    return {
        "violations": next((v for v in results["violations"] if v["id"] == "color-contrast"), None),
        "passes": next((v for v in results["passes"] if v["id"] == "color-contrast"), None),
        "incomplete": next((v for v in results["incomplete"] if v["id"] == "color-contrast"), None),
    }


# ─────────────────────────────────────────────
#  CSS variable resolution (inline <style>)
# ─────────────────────────────────────────────

class TestCSSVariableResolution:
    def test_resolves_root_variable_text_color_pass(self) -> None:
        css = ":root { --text-color: #111111; }"
        body = '<p style="color: var(--text-color); background-color: #ffffff">Hello</p>'
        r = _contrast(fast_a11y(_html(body, css)))
        assert r["violations"] is None
        assert r["passes"] is not None

    def test_resolves_root_variable_text_color_fail(self) -> None:
        css = ":root { --text-color: #aaaaaa; }"
        body = '<p style="color: var(--text-color); background-color: #ffffff">Low contrast</p>'
        r = _contrast(fast_a11y(_html(body, css)))
        assert r["violations"] is not None

    def test_resolves_root_variable_background_pass(self) -> None:
        css = ":root { --bg: #1a1a2e; }"
        body = '<p style="color: #ffffff; background-color: var(--bg)">White on dark</p>'
        r = _contrast(fast_a11y(_html(body, css)))
        assert r["violations"] is None
        assert r["passes"] is not None

    def test_resolves_both_fg_and_bg_from_variables_pass(self) -> None:
        css = ":root { --color-text: #1a1a1a; --color-surface: #f5f5f5; }"
        body = '<p style="color: var(--color-text); background-color: var(--color-surface)">Text</p>'
        r = _contrast(fast_a11y(_html(body, css)))
        assert r["violations"] is None

    def test_resolves_both_fg_and_bg_from_variables_fail(self) -> None:
        css = ":root { --color-text: #999999; --color-surface: #ffffff; }"
        body = '<p style="color: var(--color-text); background-color: var(--color-surface)">Text</p>'
        r = _contrast(fast_a11y(_html(body, css)))
        assert r["violations"] is not None

    def test_resolves_chained_variables(self) -> None:
        css = ":root { --brand-dark: #0a0a23; --text-primary: var(--brand-dark); }"
        body = '<p style="color: var(--text-primary); background-color: #ffffff">Text</p>'
        r = _contrast(fast_a11y(_html(body, css)))
        assert r["violations"] is None

    def test_fallback_when_variable_undefined_pass(self) -> None:
        body = '<p style="color: var(--undefined-var, #111111); background-color: #ffffff">Text</p>'
        r = _contrast(fast_a11y(_html(body)))
        assert r["violations"] is None
        assert r["passes"] is not None

    def test_fallback_when_variable_undefined_fail(self) -> None:
        body = '<p style="color: var(--undefined-var, #aaaaaa); background-color: #ffffff">Text</p>'
        r = _contrast(fast_a11y(_html(body)))
        assert r["violations"] is not None

    def test_stylesheet_rule_with_variable(self) -> None:
        css = ":root { --brand-text: #222222; } p { color: var(--brand-text); background-color: #ffffff; }"
        body = "<p>Text styled via stylesheet</p>"
        r = _contrast(fast_a11y(_html(body, css)))
        assert r["violations"] is None

    def test_truly_unresolvable_variable_not_false_violation(self) -> None:
        body = '<p style="color: var(--totally-unknown); background-color: #ffffff">Unknown</p>'
        r = _contrast(fast_a11y(_html(body)))
        assert r["violations"] is None


# ─────────────────────────────────────────────
#  External stylesheet support
# ─────────────────────────────────────────────

class TestExternalStylesheets:
    def test_resolves_variables_from_external_stylesheet(self) -> None:
        external = ":root { --color-primary: #1a1a2e; --color-bg: #ffffff; }"
        body = '<p style="color: var(--color-primary); background-color: var(--color-bg)">Text</p>'
        r = _contrast(fast_a11y(_html(body), external_stylesheets=[external]))
        assert r["violations"] is None

    def test_applies_rules_from_external_stylesheet(self) -> None:
        external = ":root { --text: #111; } p { color: var(--text); background-color: #ffffff; }"
        body = "<p>Externally styled</p>"
        r = _contrast(fast_a11y(_html(body), external_stylesheets=[external]))
        assert r["violations"] is None

    def test_detects_violation_via_external_stylesheet(self) -> None:
        external = "p { color: #aaaaaa; background-color: #ffffff; }"
        body = "<p>Low contrast via external CSS</p>"
        r = _contrast(fast_a11y(_html(body), external_stylesheets=[external]))
        assert r["violations"] is not None

    def test_multiple_external_stylesheets(self) -> None:
        sheet1 = ":root { --brand: #0d0d0d; }"
        sheet2 = "p { color: var(--brand); background-color: #ffffff; }"
        body = "<p>Multi-sheet</p>"
        r = _contrast(fast_a11y(_html(body), external_stylesheets=[sheet1, sheet2]))
        assert r["violations"] is None

    def test_external_and_inline_stylesheets_combined(self) -> None:
        inline_css = ":root { --bg: #ffffff; }"
        external = ":root { --fg: #222222; }"
        body = '<p style="color: var(--fg); background-color: var(--bg)">Text</p>'
        r = _contrast(fast_a11y(_html(body, inline_css), external_stylesheets=[external]))
        assert r["violations"] is None


# ─────────────────────────────────────────────
#  WCAG level grading
# ─────────────────────────────────────────────

class TestWCAGLevelGrading:
    def test_grades_aaa_for_black_on_white(self) -> None:
        body = '<p style="color: #000000; background-color: #ffffff">Black on white</p>'
        r = _contrast(fast_a11y(_html(body)))
        assert r["passes"] is not None
        assert r["passes"]["nodes"][0]["any"][0]["data"]["wcagLevel"] == "AAA"

    def test_grades_fail_for_insufficient_contrast(self) -> None:
        body = '<p style="color: #aaaaaa; background-color: #ffffff">Low contrast</p>'
        r = _contrast(fast_a11y(_html(body)))
        assert r["violations"] is not None
        assert r["violations"]["nodes"][0]["any"][0]["data"]["wcagLevel"] == "fail"
        assert r["violations"]["nodes"][0]["any"][0]["data"]["requiredRatio"] == 4.5

    def test_grades_aa_for_large_text_between_3_and_4_5(self) -> None:
        css = "p { font-size: 24pt; }"
        body = '<p style="color: #949494; background-color: #ffffff">Large AA</p>'
        r = _contrast(fast_a11y(_html(body, css)))
        assert r["passes"] is not None
        assert r["passes"]["nodes"][0]["any"][0]["data"]["wcagLevel"] == "AA"

    def test_grades_fail_for_large_text_below_3(self) -> None:
        css = "p { font-size: 24pt; }"
        body = '<p style="color: #bbbbbb; background-color: #ffffff">Large fail</p>'
        r = _contrast(fast_a11y(_html(body, css)))
        assert r["violations"] is not None
        assert r["violations"]["nodes"][0]["any"][0]["data"]["wcagLevel"] == "fail"
        assert r["violations"]["nodes"][0]["any"][0]["data"]["requiredRatio"] == 3.0

    def test_wcag_level_in_data_for_all_resolved_nodes(self) -> None:
        body = '<p style="color: #333333; background-color: #ffffff">Text</p>'
        r = _contrast(fast_a11y(_html(body)))
        node = r["passes"] or r["violations"]
        assert node is not None
        data = node["nodes"][0]["any"][0]["data"]
        assert "wcagLevel" in data
        assert "contrastRatio" in data
        assert "fgColor" in data
        assert "bgColor" in data


# ─────────────────────────────────────────────
#  Font-size variable resolution (Tailwind/Bootstrap)
# ─────────────────────────────────────────────

class TestFontSizeVariableResolution:
    def test_tailwind_font_size_variable_large_text(self) -> None:
        css = ":root { --text-2xl: 1.5rem; }"
        body = '<p style="color: #949494; background-color: #ffffff; font-size: var(--text-2xl)">Large Tailwind</p>'
        r = _contrast(fast_a11y(_html(body, css)))
        assert r["violations"] is None
        assert r["passes"] is not None
        assert r["passes"]["nodes"][0]["any"][0]["data"]["wcagLevel"] == "AA"

    def test_unresolvable_font_size_treated_as_normal_text(self) -> None:
        body = '<p style="color: #949494; background-color: #ffffff; font-size: var(--unknown-size)">Text</p>'
        r = _contrast(fast_a11y(_html(body)))
        assert r["violations"] is not None


# ─────────────────────────────────────────────
#  Real-world CSS patterns
# ─────────────────────────────────────────────

class TestRealWorldPatterns:
    def test_wordpress_preset_color_variables(self) -> None:
        css = """
            :root {
                --wp--preset--color--black: #000000;
                --wp--preset--color--white: #ffffff;
            }
            .has-black-color { color: var(--wp--preset--color--black); }
            .has-white-background-color { background-color: var(--wp--preset--color--white); }
        """
        body = '<p class="has-black-color has-white-background-color">WordPress text</p>'
        r = _contrast(fast_a11y(_html(body, css)))
        assert r["violations"] is None

    def test_design_token_chaining(self) -> None:
        css = """
            :root {
                --color-grey-900: #111827;
                --color-white: #ffffff;
                --color-text-primary: var(--color-grey-900);
                --color-surface-primary: var(--color-white);
            }
        """
        body = '<p style="color: var(--color-text-primary); background-color: var(--color-surface-primary)">Tokens</p>'
        r = _contrast(fast_a11y(_html(body, css)))
        assert r["violations"] is None

    def test_flags_low_contrast_design_tokens(self) -> None:
        css = """
            :root {
                --color-muted: #767676;
                --color-subtle-bg: #f0f0f0;
            }
        """
        body = '<p style="color: var(--color-muted); background-color: var(--color-subtle-bg)">Muted text</p>'
        r = _contrast(fast_a11y(_html(body, css)))
        assert r["violations"] is not None
