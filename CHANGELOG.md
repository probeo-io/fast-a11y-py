# Changelog

All notable changes to this project will be documented in this file.

## [0.2.0] - 2026-06-01

### Added

- **External stylesheet support** — pass pre-fetched CSS via `external_stylesheets` keyword argument; fast-a11y resolves colors and font sizes from external CSS without making network requests
- **CSS variable resolution** — resolves `var(--token)` in color and font-size values; handles chained variables, fallbacks (`var(--a, #333)`), and design system token patterns (Tailwind v4, Bootstrap 5, WordPress presets)
- **WCAG level grading** — contrast results now include `wcagLevel: "AA" | "AAA" | "fail"` in check data
- **Font-size variable resolution** — `font-size: var(--text-xl)` correctly feeds the large-text threshold check
- Color contrast test suite (25 tests covering variable resolution, external stylesheets, grading, real-world patterns)

### Fixed

- `_parse_color` now correctly uses fallback values from `var(--undefined, fallback)` even when no variables are defined (was incorrectly treating empty var_map as no-var_map)

### Changed

- Contrast check data now includes `wcagLevel` on all resolved nodes
- Violation messages updated to reference WCAG AA explicitly and include `requiredRatio`
- Version reported in `testEngine.version` updated to `0.2.0`

## [Unreleased]

### Fixed

- RecursionError in get_selector() when table cells share the same tag without IDs. FastNode now uses identity-based equality

### Added

- Exhaustive test suite (185 tests across 30 categories including regression tests for the RecursionError fix)
- "See Also" cross-links to related packages

## [0.1.0] - 2026-03-26

### Added

- Initial release
- 86 WCAG rules via static HTML analysis — no browser, no DOM
- axe-core compatible output format (dict matching `AxeResults`)
- Zero dependencies — stdlib `html.parser` only
- Rule filtering by WCAG tags or specific rule IDs
- Best-effort color contrast checking from inline styles and `<style>` blocks
- Drop-in replacement for axe-core + Playwright/Selenium workflows
