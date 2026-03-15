"""Axe-core compatible result types.

These match axe-core's output format exactly for drop-in compatibility.
"""

from __future__ import annotations

from typing import Any, Literal, TypedDict

ImpactValue = Literal["minor", "moderate", "serious", "critical"]


class TestEngine(TypedDict):
    name: str
    version: str


class TestRunner(TypedDict):
    name: str


class TestEnvironment(TypedDict, total=False):
    userAgent: str
    windowWidth: int
    windowHeight: int
    orientationAngle: int
    orientationType: str


class RelatedNode(TypedDict):
    html: str
    target: list[str]


class CheckResult(TypedDict):
    id: str
    impact: ImpactValue
    message: str
    data: Any
    relatedNodes: list[RelatedNode]


class NodeResult(TypedDict, total=False):
    html: str
    impact: ImpactValue | None
    target: list[str]
    any: list[CheckResult]
    all: list[CheckResult]
    none: list[CheckResult]
    failureSummary: str


class RuleResult(TypedDict):
    id: str
    impact: ImpactValue | None
    tags: list[str]
    description: str
    help: str
    helpUrl: str
    nodes: list[NodeResult]


class AxeResults(TypedDict):
    testEngine: TestEngine
    testRunner: TestRunner
    testEnvironment: TestEnvironment
    url: str
    timestamp: str
    toolOptions: dict[str, Any]
    passes: list[RuleResult]
    violations: list[RuleResult]
    incomplete: list[RuleResult]
    inapplicable: list[RuleResult]


class RunOnlyConfig(TypedDict):
    type: Literal["tag", "rule"]
    values: list[str]


class RuleConfig(TypedDict):
    enabled: bool


class RunOptions(TypedDict, total=False):
    runOnly: RunOnlyConfig
    rules: dict[str, RuleConfig]
    include: list[str]
    exclude: list[str]
