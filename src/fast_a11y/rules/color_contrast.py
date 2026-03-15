"""Color contrast rule: best-effort static analysis.

Parses inline styles and <style> blocks to determine foreground/background
colors, then computes WCAG contrast ratios. Unresolvable colors go to
incomplete[] rather than violations.
"""

from __future__ import annotations

import math
import re

from ..rule_engine import NodeCheckDetail, RuleRunResult, make_check
from ..tree import FastNode, TextNode, get_text_content, is_hidden_or_ancestor_hidden

# ═══════════════════════════════════════════════════════════════════════
#  Named CSS colors (all 148)
# ═══════════════════════════════════════════════════════════════════════

RGBA = tuple[int, int, int, float]

NAMED_COLORS: dict[str, RGBA] = {
    "aliceblue": (240, 248, 255, 1), "antiquewhite": (250, 235, 215, 1),
    "aqua": (0, 255, 255, 1), "aquamarine": (127, 255, 212, 1),
    "azure": (240, 255, 255, 1), "beige": (245, 245, 220, 1),
    "bisque": (255, 228, 196, 1), "black": (0, 0, 0, 1),
    "blanchedalmond": (255, 235, 205, 1), "blue": (0, 0, 255, 1),
    "blueviolet": (138, 43, 226, 1), "brown": (165, 42, 42, 1),
    "burlywood": (222, 184, 135, 1), "cadetblue": (95, 158, 160, 1),
    "chartreuse": (127, 255, 0, 1), "chocolate": (210, 105, 30, 1),
    "coral": (255, 127, 80, 1), "cornflowerblue": (100, 149, 237, 1),
    "cornsilk": (255, 248, 220, 1), "crimson": (220, 20, 60, 1),
    "cyan": (0, 255, 255, 1), "darkblue": (0, 0, 139, 1),
    "darkcyan": (0, 139, 139, 1), "darkgoldenrod": (184, 134, 11, 1),
    "darkgray": (169, 169, 169, 1), "darkgreen": (0, 100, 0, 1),
    "darkgrey": (169, 169, 169, 1), "darkkhaki": (189, 183, 107, 1),
    "darkmagenta": (139, 0, 139, 1), "darkolivegreen": (85, 107, 47, 1),
    "darkorange": (255, 140, 0, 1), "darkorchid": (153, 50, 204, 1),
    "darkred": (139, 0, 0, 1), "darksalmon": (233, 150, 122, 1),
    "darkseagreen": (143, 188, 143, 1), "darkslateblue": (72, 61, 139, 1),
    "darkslategray": (47, 79, 79, 1), "darkslategrey": (47, 79, 79, 1),
    "darkturquoise": (0, 206, 209, 1), "darkviolet": (148, 0, 211, 1),
    "deeppink": (255, 20, 147, 1), "deepskyblue": (0, 191, 255, 1),
    "dimgray": (105, 105, 105, 1), "dimgrey": (105, 105, 105, 1),
    "dodgerblue": (30, 144, 255, 1), "firebrick": (178, 34, 34, 1),
    "floralwhite": (255, 250, 240, 1), "forestgreen": (34, 139, 34, 1),
    "fuchsia": (255, 0, 255, 1), "gainsboro": (220, 220, 220, 1),
    "ghostwhite": (248, 248, 255, 1), "gold": (255, 215, 0, 1),
    "goldenrod": (218, 165, 32, 1), "gray": (128, 128, 128, 1),
    "green": (0, 128, 0, 1), "greenyellow": (173, 255, 47, 1),
    "grey": (128, 128, 128, 1), "honeydew": (240, 255, 240, 1),
    "hotpink": (255, 105, 180, 1), "indianred": (205, 92, 92, 1),
    "indigo": (75, 0, 130, 1), "ivory": (255, 255, 240, 1),
    "khaki": (240, 230, 140, 1), "lavender": (230, 230, 250, 1),
    "lavenderblush": (255, 240, 245, 1), "lawngreen": (124, 252, 0, 1),
    "lemonchiffon": (255, 250, 205, 1), "lightblue": (173, 216, 230, 1),
    "lightcoral": (240, 128, 128, 1), "lightcyan": (224, 255, 255, 1),
    "lightgoldenrodyellow": (250, 250, 210, 1), "lightgray": (211, 211, 211, 1),
    "lightgreen": (144, 238, 144, 1), "lightgrey": (211, 211, 211, 1),
    "lightpink": (255, 182, 193, 1), "lightsalmon": (255, 160, 122, 1),
    "lightseagreen": (32, 178, 170, 1), "lightskyblue": (135, 206, 250, 1),
    "lightslategray": (119, 136, 153, 1), "lightslategrey": (119, 136, 153, 1),
    "lightsteelblue": (176, 196, 222, 1), "lightyellow": (255, 255, 224, 1),
    "lime": (0, 255, 0, 1), "limegreen": (50, 205, 50, 1),
    "linen": (250, 240, 230, 1), "magenta": (255, 0, 255, 1),
    "maroon": (128, 0, 0, 1), "mediumaquamarine": (102, 205, 170, 1),
    "mediumblue": (0, 0, 205, 1), "mediumorchid": (186, 85, 211, 1),
    "mediumpurple": (147, 111, 219, 1), "mediumseagreen": (60, 179, 113, 1),
    "mediumslateblue": (123, 104, 238, 1), "mediumspringgreen": (0, 250, 154, 1),
    "mediumturquoise": (72, 209, 204, 1), "mediumvioletred": (199, 21, 133, 1),
    "midnightblue": (25, 25, 112, 1), "mintcream": (245, 255, 250, 1),
    "mistyrose": (255, 228, 225, 1), "moccasin": (255, 228, 181, 1),
    "navajowhite": (255, 222, 173, 1), "navy": (0, 0, 128, 1),
    "oldlace": (253, 245, 230, 1), "olive": (128, 128, 0, 1),
    "olivedrab": (107, 142, 35, 1), "orange": (255, 165, 0, 1),
    "orangered": (255, 69, 0, 1), "orchid": (218, 112, 214, 1),
    "palegoldenrod": (238, 232, 170, 1), "palegreen": (152, 251, 152, 1),
    "paleturquoise": (175, 238, 238, 1), "palevioletred": (219, 112, 147, 1),
    "papayawhip": (255, 239, 213, 1), "peachpuff": (255, 218, 185, 1),
    "peru": (205, 133, 63, 1), "pink": (255, 192, 203, 1),
    "plum": (221, 160, 221, 1), "powderblue": (176, 224, 230, 1),
    "purple": (128, 0, 128, 1), "rebeccapurple": (102, 51, 153, 1),
    "red": (255, 0, 0, 1), "rosybrown": (188, 143, 143, 1),
    "royalblue": (65, 105, 225, 1), "saddlebrown": (139, 69, 19, 1),
    "salmon": (250, 128, 114, 1), "sandybrown": (244, 164, 96, 1),
    "seagreen": (46, 139, 87, 1), "seashell": (255, 245, 238, 1),
    "sienna": (160, 82, 45, 1), "silver": (192, 192, 192, 1),
    "skyblue": (135, 206, 235, 1), "slateblue": (106, 90, 205, 1),
    "slategray": (112, 128, 144, 1), "slategrey": (112, 128, 144, 1),
    "snow": (255, 250, 250, 1), "springgreen": (0, 255, 127, 1),
    "steelblue": (70, 130, 180, 1), "tan": (210, 180, 140, 1),
    "teal": (0, 128, 128, 1), "thistle": (216, 191, 216, 1),
    "tomato": (255, 99, 71, 1), "turquoise": (64, 224, 208, 1),
    "violet": (238, 130, 238, 1), "wheat": (245, 222, 179, 1),
    "white": (255, 255, 255, 1), "whitesmoke": (245, 245, 245, 1),
    "yellow": (255, 255, 0, 1), "yellowgreen": (154, 205, 50, 1),
    "transparent": (0, 0, 0, 0),
}


def _clamp255(n: int) -> int:
    return max(0, min(255, n))


def _parse_color(color: str) -> RGBA | None:
    """Parse a CSS color string into RGBA. Returns None if unparseable."""
    if not color:
        return None
    c = color.strip().lower()
    if c in NAMED_COLORS:
        return NAMED_COLORS[c]
    if c in ("currentcolor", "inherit", "initial", "unset", "revert"):
        return None
    if c.startswith("#"):
        h = c[1:]
        if len(h) == 3:
            return (_clamp255(int(h[0] * 2, 16)), _clamp255(int(h[1] * 2, 16)),
                    _clamp255(int(h[2] * 2, 16)), 1.0)
        if len(h) == 4:
            return (_clamp255(int(h[0] * 2, 16)), _clamp255(int(h[1] * 2, 16)),
                    _clamp255(int(h[2] * 2, 16)), int(h[3] * 2, 16) / 255)
        if len(h) == 6:
            return (_clamp255(int(h[0:2], 16)), _clamp255(int(h[2:4], 16)),
                    _clamp255(int(h[4:6], 16)), 1.0)
        if len(h) == 8:
            return (_clamp255(int(h[0:2], 16)), _clamp255(int(h[2:4], 16)),
                    _clamp255(int(h[4:6], 16)), int(h[6:8], 16) / 255)
        return None
    m = re.match(r"^rgb\(\s*(\d+)\s*[,\s]\s*(\d+)\s*[,\s]\s*(\d+)\s*\)$", c)
    if m:
        return (_clamp255(int(m.group(1))), _clamp255(int(m.group(2))),
                _clamp255(int(m.group(3))), 1.0)
    m = re.match(r"^rgba?\(\s*(\d+)\s*[,\s]\s*(\d+)\s*[,\s]\s*(\d+)\s*[,/]\s*([\d.]+%?)\s*\)$", c)
    if m:
        a = float(m.group(4).rstrip("%"))
        if m.group(4).endswith("%"):
            a /= 100
        return (_clamp255(int(m.group(1))), _clamp255(int(m.group(2))),
                _clamp255(int(m.group(3))), max(0.0, min(1.0, a)))
    m = re.match(
        r"^rgb\(\s*([\d.]+)%\s*[,\s]\s*([\d.]+)%\s*[,\s]\s*([\d.]+)%\s*\)$", c
    )
    if m:
        return (_clamp255(round(float(m.group(1)) * 2.55)),
                _clamp255(round(float(m.group(2)) * 2.55)),
                _clamp255(round(float(m.group(3)) * 2.55)), 1.0)
    m = re.match(
        r"^hsla?\(\s*([\d.]+)\s*[,\s]\s*([\d.]+)%\s*[,\s]\s*([\d.]+)%\s*(?:[,/]\s*([\d.]+%?))?\s*\)$", c
    )
    if m:
        h_val = float(m.group(1)) / 360
        s_val = float(m.group(2)) / 100
        l_val = float(m.group(3)) / 100
        alpha = 1.0
        if m.group(4):
            alpha = float(m.group(4).rstrip("%"))
            if m.group(4).endswith("%"):
                alpha /= 100
        r, g, b = _hsl_to_rgb(h_val, s_val, l_val)
        return (r, g, b, max(0.0, min(1.0, alpha)))
    return None


def _hsl_to_rgb(h: float, s: float, l: float) -> tuple[int, int, int]:
    if s == 0:
        v = round(l * 255)
        return (v, v, v)

    def hue2rgb(p: float, q: float, t: float) -> float:
        if t < 0:
            t += 1
        if t > 1:
            t -= 1
        if t < 1 / 6:
            return p + (q - p) * 6 * t
        if t < 1 / 2:
            return q
        if t < 2 / 3:
            return p + (q - p) * (2 / 3 - t) * 6
        return p

    q = l * (1 + s) if l < 0.5 else l + s - l * s
    p = 2 * l - q
    return (
        round(hue2rgb(p, q, h + 1 / 3) * 255),
        round(hue2rgb(p, q, h) * 255),
        round(hue2rgb(p, q, h - 1 / 3) * 255),
    )


# ═══════════════════════════════════════════════════════════════════════
#  Style sheet parsing
# ═══════════════════════════════════════════════════════════════════════

def _parse_style_sheet(css: str) -> list[tuple[str, dict[str, str]]]:
    """Parse <style> block text into simple (selector, properties) tuples."""
    rules: list[tuple[str, dict[str, str]]] = []
    cleaned = re.sub(r"/\*[\s\S]*?\*/", "", css)
    for match in re.finditer(r"([^{}]+)\{([^{}]*)\}", cleaned):
        selector_group = match.group(1).strip()
        body = match.group(2).strip()
        properties: dict[str, str] = {}
        for prop in body.split(";"):
            colon_idx = prop.find(":")
            if colon_idx < 0:
                continue
            name = prop[:colon_idx].strip().lower()
            value = re.sub(r"!important", "", prop[colon_idx + 1:], flags=re.IGNORECASE).strip()
            if name and value:
                properties[name] = value
        if not properties:
            continue
        for sel in selector_group.split(","):
            trimmed = sel.strip()
            if trimmed:
                rules.append((trimmed, properties))
    return rules


def _matches_simple_selector(node: FastNode, selector: str) -> bool:
    """Very simple selector matching for basic selectors."""
    s = selector.strip()
    if " " in s and not s.startswith(".") and not s.startswith("#"):
        return False
    if ":" in s and "::" not in s:
        if s == ":root":
            return node.tag == "html"
        return False
    if "::" in s:
        return False
    if any(ch in s for ch in (">", "+", "~")):
        return False
    remaining = s
    tag = None
    id_val = None
    classes: list[str] = []
    tag_match = re.match(r"^([a-zA-Z][a-zA-Z0-9-]*)", remaining)
    if tag_match:
        tag = tag_match.group(1).lower()
        remaining = remaining[len(tag_match.group(0)):]
    id_match = re.search(r"#([a-zA-Z0-9_-]+)", remaining)
    if id_match:
        id_val = id_match.group(1)
        remaining = remaining.replace(id_match.group(0), "")
    for cm in re.finditer(r"\.([a-zA-Z0-9_-]+)", remaining):
        classes.append(cm.group(1))
    if tag and node.tag != tag:
        return False
    if id_val and node.attrs.get("id") != id_val:
        return False
    for cls in classes:
        node_classes = (node.attrs.get("class") or "").split()
        if cls not in node_classes:
            return False
    if not tag and not id_val and not classes:
        return False
    return True


# ═══════════════════════════════════════════════════════════════════════
#  Color resolution
# ═══════════════════════════════════════════════════════════════════════

def _get_inline_style_property(style: str, prop: str) -> str | None:
    pattern = re.compile(
        r"(?:^|;)\s*" + prop.replace("-", r"\-") + r"\s*:\s*([^;!]+)", re.IGNORECASE
    )
    m = pattern.search(style)
    return m.group(1).strip() if m else None


def _build_style_map(all_nodes: list[FastNode]) -> dict[int, dict[str, str]]:
    style_map: dict[int, dict[str, str]] = {}
    style_rules: list[tuple[str, dict[str, str]]] = []
    for node in all_nodes:
        if node.tag == "style":
            text = get_text_content(node)
            if text:
                style_rules.extend(_parse_style_sheet(text))
    for selector, properties in style_rules:
        for node in all_nodes:
            if _matches_simple_selector(node, selector):
                node_id = id(node)
                if node_id not in style_map:
                    style_map[node_id] = {}
                style_map[node_id].update(properties)
    return style_map


def _extract_bg_color(bg: str | None) -> str | None:
    if not bg:
        return None
    for part in bg.strip().split():
        if _parse_color(part):
            return part
    return None


def _resolve_styles(
    node: FastNode, style_map: dict[int, dict[str, str]]
) -> tuple[RGBA | None, RGBA | None, str | None, str | None]:
    """Resolve effective color/background for a node. Returns (color, bg, fontSize, fontWeight)."""
    color: RGBA | None = None
    bg: RGBA | None = None
    font_size: str | None = None
    font_weight: str | None = None
    chain: list[FastNode] = []
    current: FastNode | None = node
    while current:
        chain.insert(0, current)
        current = current.parent
    for n in chain:
        inline = n.attrs.get("style", "")
        sheet_styles = style_map.get(id(n), {})
        inline_color = _get_inline_style_property(inline, "color")
        sheet_color = sheet_styles.get("color")
        color_val = inline_color or sheet_color
        if color_val:
            parsed = _parse_color(color_val)
            if parsed:
                color = parsed
            elif color_val not in ("inherit", "initial", "unset"):
                color = None
        inline_bg = _get_inline_style_property(inline, "background-color")
        sheet_bg = sheet_styles.get("background-color")
        inline_bg_short = _get_inline_style_property(inline, "background")
        sheet_bg_short = sheet_styles.get("background")
        bg_val = inline_bg or sheet_bg or _extract_bg_color(inline_bg_short) or _extract_bg_color(sheet_bg_short)
        if bg_val:
            parsed = _parse_color(bg_val)
            if parsed:
                bg = parsed
        inline_fs = _get_inline_style_property(inline, "font-size")
        sheet_fs = sheet_styles.get("font-size")
        if inline_fs:
            font_size = inline_fs
        elif sheet_fs:
            font_size = sheet_fs
        inline_fw = _get_inline_style_property(inline, "font-weight")
        sheet_fw = sheet_styles.get("font-weight")
        if inline_fw:
            font_weight = inline_fw
        elif sheet_fw:
            font_weight = sheet_fw
    return color, bg, font_size, font_weight


# ═══════════════════════════════════════════════════════════════════════
#  WCAG contrast computation
# ═══════════════════════════════════════════════════════════════════════

def _relative_luminance(rgba: RGBA) -> float:
    """Compute relative luminance per WCAG 2.0."""
    vals = []
    for i in range(3):
        s_rgb = rgba[i] / 255
        vals.append(s_rgb / 12.92 if s_rgb <= 0.04045 else ((s_rgb + 0.055) / 1.055) ** 2.4)
    return 0.2126 * vals[0] + 0.7152 * vals[1] + 0.0722 * vals[2]


def _alpha_composite(fg: RGBA, bg_color: RGBA) -> RGBA:
    a = fg[3]
    if a >= 1:
        return fg
    return (
        round(fg[0] * a + bg_color[0] * (1 - a)),
        round(fg[1] * a + bg_color[1] * (1 - a)),
        round(fg[2] * a + bg_color[2] * (1 - a)),
        1.0,
    )


def _contrast_ratio(fg: RGBA, bg_color: RGBA) -> float:
    composite = _alpha_composite(fg, bg_color)
    l1 = _relative_luminance(composite)
    l2 = _relative_luminance(bg_color)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def _is_large_text(font_size: str | None, font_weight: str | None) -> bool:
    if not font_size:
        return False
    size_in_pt = 0.0
    m = re.match(r"([\d.]+)\s*px", font_size, re.IGNORECASE)
    if m:
        size_in_pt = float(m.group(1)) * 0.75
    else:
        m = re.match(r"([\d.]+)\s*pt", font_size, re.IGNORECASE)
        if m:
            size_in_pt = float(m.group(1))
        else:
            m = re.match(r"([\d.]+)\s*rem", font_size, re.IGNORECASE)
            if m:
                size_in_pt = float(m.group(1)) * 12
            else:
                m = re.match(r"([\d.]+)\s*em", font_size, re.IGNORECASE)
                if m:
                    size_in_pt = float(m.group(1)) * 12
    is_bold = font_weight in ("bold", "bolder")
    if not is_bold and font_weight:
        try:
            is_bold = int(font_weight) >= 700
        except ValueError:
            pass
    if size_in_pt >= 18:
        return True
    if size_in_pt >= 14 and is_bold:
        return True
    return False


SKIP_TAGS = frozenset({
    "html", "head", "body", "script", "style", "link", "meta", "title",
    "br", "hr", "img", "input", "select", "textarea", "button", "svg",
    "video", "audio", "canvas", "iframe", "object", "embed", "noscript",
    "template", "base",
})


class _ColorContrast:
    rule_id = "color-contrast"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        style_map = _build_style_map(all_nodes)
        DEFAULT_FG: RGBA = (0, 0, 0, 1.0)
        DEFAULT_BG: RGBA = (255, 255, 255, 1.0)

        for node in nodes:
            if node.tag in SKIP_TAGS:
                continue
            if is_hidden_or_ancestor_hidden(node):
                continue
            has_direct_text = any(
                isinstance(child, TextNode) and child.data.strip()
                for child in node.child_nodes
            )
            if not has_direct_text:
                continue
            fg, bg, font_size, font_weight = _resolve_styles(node, style_map)
            if not fg and not bg:
                if style_map:
                    continue
                continue
            fg_color = fg or DEFAULT_FG
            bg_color = bg or DEFAULT_BG
            if fg_color[3] == 0:
                continue
            # Check for background images
            has_bg_image = False
            current: FastNode | None = node
            while current:
                inline = current.attrs.get("style", "")
                sheet = style_map.get(id(current), {})
                if re.search(r"background(-image)?\s*:.*(?:url|gradient)", inline, re.IGNORECASE):
                    has_bg_image = True
                    break
                bg_img = sheet.get("background-image", "") or sheet.get("background", "")
                if re.search(r"url|gradient", bg_img, re.IGNORECASE):
                    has_bg_image = True
                    break
                current = current.parent
            if has_bg_image:
                result.incomplete.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("color-contrast", "serious",
                        "Element has a background image -- cannot determine contrast ratio")]
                )
                continue
            ratio = _contrast_ratio(fg_color, bg_color)
            large = _is_large_text(font_size, font_weight)
            required_ratio = 3.0 if large else 4.5
            ratio_str = f"{ratio:.2f}"
            fg_str = f"rgb({fg_color[0]}, {fg_color[1]}, {fg_color[2]})"
            bg_str = f"rgb({bg_color[0]}, {bg_color[1]}, {bg_color[2]})"
            large_text = " [large text]" if large else ""
            if ratio >= required_ratio:
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("color-contrast", "serious",
                        f"Element has sufficient contrast ratio of {ratio_str}:1"
                        f" (foreground: {fg_str}, background: {bg_str}){large_text}",
                        {"fgColor": fg_str, "bgColor": bg_str, "contrastRatio": ratio_str,
                         "fontSize": font_size, "fontWeight": font_weight})]
                )
            else:
                result.violations.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("color-contrast", "serious",
                        f"Element has insufficient contrast ratio of {ratio_str}:1"
                        f" (foreground: {fg_str}, background: {bg_str})"
                        f". Expected ratio of {required_ratio}:1{large_text}",
                        {"fgColor": fg_str, "bgColor": bg_str, "contrastRatio": ratio_str,
                         "expectedRatio": required_ratio, "fontSize": font_size,
                         "fontWeight": font_weight})]
                )
        return result


color_contrast_rules = [_ColorContrast()]
