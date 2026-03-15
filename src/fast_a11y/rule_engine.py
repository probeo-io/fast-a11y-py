"""Rule engine -- runs rules against the parsed tree,
collects results in axe-core compatible format.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from .rule_meta import RULE_META, RuleMeta
from .tree import FastNode, get_outer_html, get_selector
from .types import (
    CheckResult,
    ImpactValue,
    NodeResult,
    RuleResult,
    RunOptions,
)


@dataclass
class NodeCheckDetail:
    """Per-node check details."""

    any: list[CheckResult] = field(default_factory=list)
    all: list[CheckResult] = field(default_factory=list)
    none: list[CheckResult] = field(default_factory=list)


@dataclass
class RuleRunResult:
    """Result of running a single rule."""

    violations: list[FastNode] = field(default_factory=list)
    passes: list[FastNode] = field(default_factory=list)
    incomplete: list[FastNode] = field(default_factory=list)
    check_details: dict[int, NodeCheckDetail] = field(default_factory=dict)


class RuleCheck(Protocol):
    """Protocol for a rule implementation."""

    @property
    def rule_id(self) -> str: ...

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult: ...


def build_node_result(
    node: FastNode,
    impact: ImpactValue,
    detail: NodeCheckDetail | None = None,
) -> NodeResult:
    """Build a NodeResult from a FastNode."""
    any_checks = detail.any if detail else []
    all_checks = detail.all if detail else []
    none_checks = detail.none if detail else []

    # Build failure summary
    parts: list[str] = []
    failing_any = [c for c in any_checks if c["message"]]
    failing_all = [c for c in all_checks if c["message"]]
    failing_none = [c for c in none_checks if c["message"]]

    if failing_any:
        parts.append("Fix any of the following:")
        for c in failing_any:
            parts.append(f"  {c['message']}")
    if failing_all:
        parts.append("Fix all of the following:")
        for c in failing_all:
            parts.append(f"  {c['message']}")
    if failing_none:
        parts.append("Fix all of the following:")
        for c in failing_none:
            parts.append(f"  Element must not have: {c['message']}")

    failure_summary = "\n".join(parts) if parts else None

    result: NodeResult = {
        "html": get_outer_html(node),
        "impact": impact,
        "target": [get_selector(node)],
        "any": any_checks,
        "all": all_checks,
        "none": none_checks,
    }
    if failure_summary:
        result["failureSummary"] = failure_summary

    return result


def build_rule_result(meta: RuleMeta, node_results: list[NodeResult]) -> RuleResult:
    """Build a RuleResult from metadata and node results."""
    return {
        "id": meta.id,
        "impact": meta.impact if node_results else None,
        "tags": meta.tags,
        "description": meta.description,
        "help": meta.help,
        "helpUrl": meta.help_url,
        "nodes": node_results,
    }


def make_check(
    id: str,
    impact: ImpactValue,
    message: str,
    data: Any = None,
) -> CheckResult:
    """Create a simple check result."""
    return {
        "id": id,
        "impact": impact,
        "message": message,
        "data": data,
        "relatedNodes": [],
    }


def run_rules(
    rules: list[RuleCheck],
    all_nodes: list[FastNode],
    options: RunOptions | None = None,
) -> dict[str, list[RuleResult]]:
    """Run all registered rules and produce categorized results."""
    passes: list[RuleResult] = []
    violations: list[RuleResult] = []
    incomplete: list[RuleResult] = []
    inapplicable: list[RuleResult] = []

    for rule in rules:
        meta = RULE_META.get(rule.rule_id)
        if not meta:
            continue

        # Filter by runOnly
        if options and "runOnly" in options:
            run_only = options["runOnly"]
            if run_only["type"] == "tag":
                if not any(t in run_only["values"] for t in meta.tags):
                    continue
            elif run_only["type"] == "rule":
                if rule.rule_id not in run_only["values"]:
                    continue

        # Filter by rules enable/disable
        if options and "rules" in options:
            rule_config = options["rules"].get(rule.rule_id)
            if rule_config and not rule_config["enabled"]:
                continue

        result = rule.run(all_nodes, all_nodes)

        # Build node results for violations
        violation_nodes = [
            build_node_result(n, meta.impact, result.check_details.get(id(n)))
            for n in result.violations
        ]

        # Build node results for passes
        pass_nodes = [
            build_node_result(n, meta.impact, result.check_details.get(id(n)))
            for n in result.passes
        ]

        # Build node results for incomplete
        incomplete_nodes = [
            build_node_result(n, meta.impact, result.check_details.get(id(n)))
            for n in result.incomplete
        ]

        if violation_nodes:
            violations.append(build_rule_result(meta, violation_nodes))
        if pass_nodes:
            passes.append(build_rule_result(meta, pass_nodes))
        if incomplete_nodes:
            incomplete.append(build_rule_result(meta, incomplete_nodes))

        # If no nodes matched at all, it's inapplicable
        if not violation_nodes and not pass_nodes and not incomplete_nodes:
            inapplicable.append(build_rule_result(meta, []))

    return {
        "passes": passes,
        "violations": violations,
        "incomplete": incomplete,
        "inapplicable": inapplicable,
    }
