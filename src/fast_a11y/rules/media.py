"""Media rules: blink, marquee, meta-refresh, meta-refresh-no-exceptions,
meta-viewport, meta-viewport-large, no-autoplay-audio, video-caption
"""

from __future__ import annotations

import re

from ..rule_engine import NodeCheckDetail, RuleCheck, RuleRunResult, make_check
from ..tree import FastNode, find_by_tag, is_hidden_or_ancestor_hidden


def _parse_meta_refresh(content: str) -> dict[str, object] | None:
    """Parse a meta refresh content attribute."""
    if not content:
        return None
    trimmed = content.strip()
    match = re.match(r"^(\d+)\s*(?:[;,]\s*(?:url\s*=\s*)?(.+))?$", trimmed, re.IGNORECASE)
    if not match:
        return None
    return {
        "delay": int(match.group(1)),
        "url": match.group(2).strip() if match.group(2) else None,
    }


def _parse_viewport(content: str) -> dict[str, str]:
    """Parse viewport meta content."""
    result: dict[str, str] = {}
    parts = re.split(r"[,;]", content)
    for part in parts:
        kv = part.split("=", 1)
        if kv[0]:
            key = kv[0].strip().lower()
            value = kv[1].strip().lower() if len(kv) > 1 else ""
            result[key] = value
    return result


class _Blink:
    rule_id = "blink"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        for node in find_by_tag(nodes, "blink"):
            result.violations.append(node)
            result.check_details[id(node)] = NodeCheckDetail(
                all=[make_check("blink", "serious",
                    "<blink> elements are deprecated and must not be used")]
            )
        return result


class _Marquee:
    rule_id = "marquee"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        for node in find_by_tag(nodes, "marquee"):
            result.violations.append(node)
            result.check_details[id(node)] = NodeCheckDetail(
                all=[make_check("marquee", "serious",
                    "<marquee> elements are deprecated and must not be used")]
            )
        return result


class _MetaRefresh:
    rule_id = "meta-refresh"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        for node in find_by_tag(nodes, "meta"):
            http_equiv = (node.attrs.get("http-equiv") or "").lower()
            if http_equiv != "refresh":
                continue
            content = node.attrs.get("content", "")
            parsed = _parse_meta_refresh(content)
            if not parsed:
                result.passes.append(node)
                continue
            delay = parsed["delay"]
            url = parsed["url"]
            if delay > 0 and url:  # type: ignore[operator]
                result.violations.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("meta-refresh", "critical",
                        f"Timed refresh with redirect found: delay={delay}s")]
                )
            elif delay > 72000:  # type: ignore[operator]
                result.violations.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("meta-refresh", "critical",
                        f"Page auto-refreshes with delay of {delay} seconds")]
                )
            elif delay == 0:
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("meta-refresh", "critical",
                        "Immediate redirect (delay=0) is acceptable")]
                )
            elif delay > 0 and not url:  # type: ignore[operator]
                result.violations.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("meta-refresh", "critical",
                        f"Page auto-refreshes with delay of {delay} seconds")]
                )
            else:
                result.passes.append(node)
        return result


class _MetaRefreshNoExceptions:
    rule_id = "meta-refresh-no-exceptions"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        for node in find_by_tag(nodes, "meta"):
            http_equiv = (node.attrs.get("http-equiv") or "").lower()
            if http_equiv != "refresh":
                continue
            content = node.attrs.get("content", "")
            parsed = _parse_meta_refresh(content)
            if not parsed:
                continue
            delay = parsed["delay"]
            if delay > 0:  # type: ignore[operator]
                result.violations.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("meta-refresh-no-exceptions", "minor",
                        f"meta refresh with delay of {delay} seconds found")]
                )
            else:
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("meta-refresh-no-exceptions", "minor",
                        "Immediate redirect (delay=0) found")]
                )
        return result


class _MetaViewport:
    rule_id = "meta-viewport"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        for node in find_by_tag(nodes, "meta"):
            name = (node.attrs.get("name") or "").lower()
            if name != "viewport":
                continue
            content = node.attrs.get("content", "")
            vp = _parse_viewport(content)
            issues: list[str] = []
            if vp.get("user-scalable") in ("no", "0"):
                issues.append("user-scalable=no disables zooming")
            max_scale_str = vp.get("maximum-scale", "")
            if max_scale_str:
                try:
                    max_scale = float(max_scale_str)
                    if max_scale < 2:
                        issues.append(
                            f"maximum-scale={max_scale} prevents adequate zooming (minimum 2)"
                        )
                except ValueError:
                    pass
            if issues:
                result.violations.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("meta-viewport", "critical", "; ".join(issues))]
                )
            else:
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    all=[make_check("meta-viewport", "critical",
                        "Viewport meta tag does not disable zooming")]
                )
        return result


class _MetaViewportLarge:
    rule_id = "meta-viewport-large"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        for node in find_by_tag(nodes, "meta"):
            name = (node.attrs.get("name") or "").lower()
            if name != "viewport":
                continue
            content = node.attrs.get("content", "")
            vp = _parse_viewport(content)
            max_scale_str = vp.get("maximum-scale", "")
            if max_scale_str:
                try:
                    max_scale = float(max_scale_str)
                    if max_scale < 5:
                        result.violations.append(node)
                        result.check_details[id(node)] = NodeCheckDetail(
                            all=[make_check("meta-viewport-large", "minor",
                                f"maximum-scale={max_scale} should be >= 5 for 500% zoom")]
                        )
                        continue
                except ValueError:
                    pass
            result.passes.append(node)
            result.check_details[id(node)] = NodeCheckDetail(
                all=[make_check("meta-viewport-large", "minor",
                    "Viewport allows adequate zoom level")]
            )
        return result


class _NoAutoplayAudio:
    rule_id = "no-autoplay-audio"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        for node in nodes:
            if node.tag not in ("video", "audio"):
                continue
            if is_hidden_or_ancestor_hidden(node):
                continue
            has_autoplay = "autoplay" in node.attrs
            if not has_autoplay:
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("no-autoplay-audio", "moderate",
                        "Element does not have autoplay attribute")]
                )
                continue
            has_muted = "muted" in node.attrs
            has_controls = "controls" in node.attrs
            if has_muted:
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("no-autoplay-audio", "moderate",
                        "Element has autoplay but is muted")]
                )
            elif has_controls:
                result.incomplete.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("no-autoplay-audio", "moderate",
                        "Element has autoplay with controls -- verify audio duration "
                        "is < 3 seconds or user can control playback")]
                )
            else:
                result.violations.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("no-autoplay-audio", "moderate",
                        "Element autoplays without muted attribute or controls")]
                )
        return result


class _VideoCaption:
    rule_id = "video-caption"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        for node in find_by_tag(nodes, "video"):
            if is_hidden_or_ancestor_hidden(node):
                continue
            has_caption = any(
                child.tag == "track"
                and child.attrs.get("kind") in ("captions", "subtitles")
                for child in node.children
            )
            if has_caption:
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("video-caption", "critical",
                        "Video element has captions track")]
                )
            else:
                result.incomplete.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("video-caption", "critical",
                        'No <track kind="captions"> found -- verify captions are provided')]
                )
        return result


media_rules: list[RuleCheck] = [
    _Blink(),
    _Marquee(),
    _MetaRefresh(),
    _MetaRefreshNoExceptions(),
    _MetaViewport(),
    _MetaViewportLarge(),
    _NoAutoplayAudio(),
    _VideoCaption(),
]
