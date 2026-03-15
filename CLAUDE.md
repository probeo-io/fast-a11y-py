# fast-a11y (Python)

Zero-DOM accessibility checker with axe-core compatible output.

## Build & Test

```bash
pip install -e .          # editable install
pip install pytest ruff mypy   # dev dependencies
pytest                    # run tests
ruff check src/ tests/    # lint
mypy src/                 # type check
```

## Architecture

- `src/fast_a11y/__init__.py` -- Main entry: `fast_a11y(html, options?)` returns `AxeResults`
- `src/fast_a11y/tree.py` -- HTML parser (stdlib html.parser) and lightweight tree walker
- `src/fast_a11y/types.py` -- Axe-core compatible output types (AxeResults, RuleResult, NodeResult, etc.)
- `src/fast_a11y/rule_engine.py` -- Rule runner, result builder, check/node/rule result construction
- `src/fast_a11y/rule_meta.py` -- Metadata for all 86 rules (tags, description, help, helpUrl, impact)
- `src/fast_a11y/accessible_name.py` -- Simplified W3C Accessible Name Computation
- `src/fast_a11y/rules/` -- Rule implementations split by category:
  - `text_alternatives.py` -- image-alt, input-image-alt, object-alt, etc.
  - `language.py` -- html-has-lang, html-lang-valid, etc.
  - `structure.py` -- document-title, heading-order, duplicate-id, nested-interactive, etc.
  - `forms.py` -- label, button-name, select-name, autocomplete-valid, etc.
  - `aria.py` -- 25 ARIA rules with full lookup tables
  - `navigation.py` -- link-name, frame-title, bypass, tabindex, etc.
  - `media.py` -- meta-viewport, blink, marquee, video-caption, etc.
  - `tables.py` -- td-headers-attr, th-has-data-cells, scope-attr-valid, etc.
  - `landmarks.py` -- landmark-one-main, landmark-*-is-top-level, etc.
  - `color_contrast.py` -- Best-effort contrast checking via inline/style block parsing
  - `__init__.py` -- `get_all_rules()` combines all rule files

## Key Design Decisions

- Output format MUST match axe-core's AxeResults exactly -- this is a drop-in replacement
- Rules skip hidden elements using `is_hidden_or_ancestor_hidden()`
- Color contrast puts unresolvable colors in `incomplete[]`, not `violations[]`
- ~9 rules that truly need a rendered DOM are not implemented (color-contrast is best-effort)
- Pure Python, zero external dependencies (stdlib html.parser only)
- Python 3.10+, PEP 561 typed package

## Adding a New Rule

1. Add metadata to `src/fast_a11y/rule_meta.py` using the `RuleMeta` dataclass
2. Implement a class with `rule_id` attribute and `run()` method in the appropriate `src/fast_a11y/rules/*.py` file
3. Add it to the exported list in that file
4. The rule is automatically picked up by `get_all_rules()`
