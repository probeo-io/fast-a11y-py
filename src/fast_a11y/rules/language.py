"""Language rules: html-has-lang, html-lang-valid, html-xml-lang-mismatch, valid-lang"""

from __future__ import annotations

from ..rule_engine import NodeCheckDetail, RuleCheck, RuleRunResult, make_check
from ..tree import FastNode, find_by_tag, is_hidden_or_ancestor_hidden

# ISO 639-1 primary language subtags.
VALID_LANG_SUBTAGS = frozenset({
    "aa", "ab", "af", "ak", "am", "an", "ar", "as", "av", "ay", "az",
    "ba", "be", "bg", "bh", "bi", "bm", "bn", "bo", "br", "bs",
    "ca", "ce", "ch", "co", "cr", "cs", "cu", "cv", "cy",
    "da", "de", "dv", "dz",
    "ee", "el", "en", "eo", "es", "et", "eu",
    "fa", "ff", "fi", "fj", "fo", "fr", "fy",
    "ga", "gd", "gl", "gn", "gu", "gv",
    "ha", "he", "hi", "ho", "hr", "ht", "hu", "hy", "hz",
    "ia", "id", "ie", "ig", "ii", "ik", "in", "io", "is", "it", "iu", "iw",
    "ja", "ji", "jv", "jw",
    "ka", "kg", "ki", "kj", "kk", "kl", "km", "kn", "ko", "kr", "ks", "ku", "kv", "kw", "ky",
    "la", "lb", "lg", "li", "ln", "lo", "lt", "lu", "lv",
    "mg", "mh", "mi", "mk", "ml", "mn", "mo", "mr", "ms", "mt", "my",
    "na", "nb", "nd", "ne", "ng", "nl", "nn", "no", "nr", "nv", "ny",
    "oc", "oj", "om", "or", "os",
    "pa", "pi", "pl", "ps", "pt",
    "qu",
    "rm", "rn", "ro", "ru", "rw",
    "sa", "sc", "sd", "se", "sg", "sh", "si", "sk", "sl", "sm", "sn", "so", "sq", "sr", "ss",
    "st", "su", "sv", "sw",
    "ta", "te", "tg", "th", "ti", "tk", "tl", "tn", "to", "tr", "ts", "tt", "tw", "ty",
    "ug", "uk", "ur", "uz",
    "ve", "vi", "vo",
    "wa", "wo",
    "xh",
    "yi", "yo",
    "za", "zh", "zu",
    # Grandfathered / common 3-letter subtags
    "ast", "ckb", "cmn", "fil", "gsw", "hak", "hsn", "lzh", "nan",
    "nds", "scn", "sco", "sma", "smj", "smn", "sms", "wuu", "yue",
    "ceb", "haw", "hmn", "ilo", "jbo", "kok", "mai", "mni", "sat",
    "sgn", "mis", "mul", "und", "zxx",
})


def _get_primary_subtag(lang: str) -> str:
    """Extract the primary subtag from a BCP 47 language tag."""
    return lang.strip().split("-")[0].split("_")[0].lower()


def _is_valid_lang(lang: str) -> bool:
    """Check if a lang value has a valid primary subtag."""
    if not lang or not lang.strip():
        return False
    return _get_primary_subtag(lang) in VALID_LANG_SUBTAGS


class _HtmlHasLang:
    rule_id = "html-has-lang"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        for node in find_by_tag(nodes, "html"):
            lang = node.attrs.get("lang")
            xml_lang = node.attrs.get("xml:lang")
            if (lang and lang.strip()) or (xml_lang and xml_lang.strip()):
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("html-has-lang", "serious",
                        "The <html> element has a lang attribute")]
                )
            else:
                result.violations.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("html-has-lang", "serious",
                        "The <html> element does not have a lang attribute")]
                )
        return result


class _HtmlLangValid:
    rule_id = "html-lang-valid"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        for node in find_by_tag(nodes, "html"):
            lang = node.attrs.get("lang")
            if not lang or not lang.strip():
                continue
            if _is_valid_lang(lang):
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("html-lang-valid", "serious",
                        f"Value of lang attribute is a valid language: {lang}")]
                )
            else:
                result.violations.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("html-lang-valid", "serious",
                        f"Value of lang attribute is not a valid language: {lang}")]
                )
        return result


class _HtmlXmlLangMismatch:
    rule_id = "html-xml-lang-mismatch"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        for node in find_by_tag(nodes, "html"):
            lang = node.attrs.get("lang")
            xml_lang = node.attrs.get("xml:lang")
            if not lang or not xml_lang:
                continue
            if not lang.strip() or not xml_lang.strip():
                continue
            lang_primary = _get_primary_subtag(lang)
            xml_lang_primary = _get_primary_subtag(xml_lang)
            if lang_primary == xml_lang_primary:
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("html-xml-lang-mismatch", "moderate",
                        "lang and xml:lang attributes have the same primary language")]
                )
            else:
                result.violations.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("html-xml-lang-mismatch", "moderate",
                        f'lang="{lang}" and xml:lang="{xml_lang}" have different primary languages')]
                )
        return result


class _ValidLang:
    rule_id = "valid-lang"

    def run(self, nodes: list[FastNode], all_nodes: list[FastNode]) -> RuleRunResult:
        result = RuleRunResult()
        for node in nodes:
            if node.tag == "html":
                continue
            if is_hidden_or_ancestor_hidden(node):
                continue
            lang = node.attrs.get("lang")
            if not lang:
                continue
            if _is_valid_lang(lang):
                result.passes.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("valid-lang", "serious",
                        f"Value of lang attribute is a valid language: {lang}")]
                )
            else:
                result.violations.append(node)
                result.check_details[id(node)] = NodeCheckDetail(
                    any=[make_check("valid-lang", "serious",
                        f"Value of lang attribute is not a valid language: {lang}")]
                )
        return result


language_rules: list[RuleCheck] = [
    _HtmlHasLang(),
    _HtmlLangValid(),
    _HtmlXmlLangMismatch(),
    _ValidLang(),
]
