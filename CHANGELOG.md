# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2026-03-26

### Added

- Initial release
- 86 WCAG rules via static HTML analysis — no browser, no DOM
- axe-core compatible output format (dict matching `AxeResults`)
- Zero dependencies — stdlib `html.parser` only
- Rule filtering by WCAG tags or specific rule IDs
- Best-effort color contrast checking from inline styles and `<style>` blocks
- Drop-in replacement for axe-core + Playwright/Selenium workflows
