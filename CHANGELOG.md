# Changelog

All notable changes to this project will be documented in this file.

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
