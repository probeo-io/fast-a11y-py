"""fast-a11y -- Fast, zero-DOM accessibility checker with axe-core compatible output.

Usage:
    from fast_a11y import fast_a11y
    results = fast_a11y(html)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .rule_engine import RuleContext, run_rules
from .rules import get_all_rules
from .tree import parse
from .types import AxeResults, RunOptions

__all__ = ["fast_a11y", "AxeResults", "RunOptions"]

VERSION = "0.2.0"


def fast_a11y(
    html: str,
    options: RunOptions | None = None,
    *,
    url: str = "",
    external_stylesheets: list[str] | None = None,
) -> AxeResults:
    """Run accessibility checks on raw HTML.

    Returns axe-core compatible AxeResults.

    Args:
        html: Raw HTML string to check.
        options: Optional run options (runOnly, rules).
        url: URL of the page being tested (included in output).
        external_stylesheets: Pre-fetched external CSS strings for improved
            color contrast analysis. The caller fetches <link rel="stylesheet">
            URLs; fast-a11y stays zero-network.

    Returns:
        AxeResults dict matching axe-core's output format exactly.
    """
    all_nodes = parse(html)
    rules = get_all_rules()
    context = RuleContext(external_stylesheets=external_stylesheets or [])

    categorized = run_rules(rules, all_nodes, options, context)

    tool_options: dict[str, Any] = {}
    if options:
        tool_options = dict(options)

    return {
        "testEngine": {"name": "fast-a11y", "version": VERSION},
        "testRunner": {"name": "fast-a11y"},
        "testEnvironment": {
            "userAgent": "",
            "windowWidth": 0,
            "windowHeight": 0,
        },
        "url": url,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "toolOptions": tool_options,
        "passes": categorized["passes"],
        "violations": categorized["violations"],
        "incomplete": categorized["incomplete"],
        "inapplicable": categorized["inapplicable"],
    }
