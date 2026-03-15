"""Rule index -- exports all rules combined into a single list."""

from __future__ import annotations

from ..rule_engine import RuleCheck
from .aria import aria_rules
from .color_contrast import color_contrast_rules
from .forms import form_rules
from .landmarks import landmark_rules
from .language import language_rules
from .media import media_rules
from .navigation import navigation_rules
from .structure import structure_rules
from .tables import table_rules
from .text_alternatives import text_alternative_rules


def get_all_rules() -> list[RuleCheck]:
    """Get all registered rule implementations."""
    return [
        *text_alternative_rules,
        *language_rules,
        *structure_rules,
        *form_rules,
        *aria_rules,
        *navigation_rules,
        *media_rules,
        *table_rules,
        *landmark_rules,
        *color_contrast_rules,
    ]


__all__ = [
    "get_all_rules",
    "text_alternative_rules",
    "language_rules",
    "structure_rules",
    "form_rules",
    "aria_rules",
    "navigation_rules",
    "media_rules",
    "table_rules",
    "landmark_rules",
    "color_contrast_rules",
]
