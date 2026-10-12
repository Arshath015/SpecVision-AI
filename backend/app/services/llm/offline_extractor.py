"""Deterministic, rule-based extraction used for offline/demo mode.

This is NOT a mocked LLM response and must never be reported as one -- the
processing metadata always tags results from this module with
ExtractionMethod.OFFLINE_FIXTURE. It is a legitimate keyword/regex
extractor so the whole pipeline (matching, CV, pricing, confidence,
review) remains exercisable without any network access or API key.
"""
from __future__ import annotations

import re

from app.models.enums import (
    DesignCategory,
    GemstoneShape,
    GemstoneType,
    MetalColor,
    MetalPurity,
    MetalType,
    ProductType,
    SettingType,
)
from app.models.extraction_raw import RawExtraction

_METAL_PURITY_PATTERNS = {
    MetalPurity.K10: [r"\b10\s*k\b", r"\b10[- ]?karat\b"],
    MetalPurity.K14: [r"\b14\s*k\b", r"\b14[- ]?karat\b"],
    MetalPurity.K18: [r"\b18\s*k\b", r"\b18[- ]?karat\b"],
    MetalPurity.K22: [r"\b22\s*k\b", r"\b22[- ]?karat\b"],
    MetalPurity.K24: [r"\b24\s*k\b", r"\b24[- ]?karat\b"],
    MetalPurity.PLATINUM_950: [r"\b950\s*platinum\b", r"\bplatinum\b"],
    MetalPurity.SILVER_925: [r"\b925\b", r"\bsterling silver\b"],
}

_METAL_TYPE_KEYWORDS = {
    MetalType.GOLD: ["gold"],
    MetalType.PLATINUM: ["platinum"],
    MetalType.SILVER: ["silver"],
    MetalType.PALLADIUM: ["palladium"],
}

_METAL_COLOR_KEYWORDS = {
    MetalColor.YELLOW: ["yellow gold", "yellow"],
    MetalColor.WHITE: ["white gold", "white metal", "white"],
    MetalColor.ROSE: ["rose gold", "rose", "pink gold"],
    MetalColor.TWO_TONE: ["two-tone", "two tone"],
}

_GEMSTONE_KEYWORDS = {
    GemstoneType.DIAMOND: ["diamond"],
    GemstoneType.SAPPHIRE: ["sapphire"],
    GemstoneType.RUBY: ["ruby"],
    GemstoneType.EMERALD: ["emerald"],
    GemstoneType.MOISSANITE: ["moissanite"],
    GemstoneType.MORGANITE: ["morganite"],
    GemstoneType.AQUAMARINE: ["aquamarine"],
    GemstoneType.AMETHYST: ["amethyst"],
    GemstoneType.TOPAZ: ["topaz"],
    GemstoneType.PEARL: ["pearl"],
}

_SHAPE_KEYWORDS = {
    GemstoneShape.ROUND: ["round"],
    GemstoneShape.OVAL: ["oval"],
    GemstoneShape.PRINCESS: ["princess"],
    GemstoneShape.CUSHION: ["cushion"],
    GemstoneShape.EMERALD_CUT: ["emerald cut", "emerald-cut"],
    GemstoneShape.PEAR: ["pear"],
    GemstoneShape.MARQUISE: ["marquise"],
    GemstoneShape.RADIANT: ["radiant"],
    GemstoneShape.ASSCHER: ["asscher"],
    GemstoneShape.HEART: ["heart"],
}

_SETTING_KEYWORDS = {
    SettingType.HALO: ["halo"],
    SettingType.PAVE: ["pave", "pavé"],
    SettingType.BEZEL: ["bezel"],
    SettingType.CHANNEL: ["channel"],
    SettingType.TENSION: ["tension"],
    SettingType.CLUSTER: ["cluster"],
    SettingType.PRONG: ["prong"],
}

_DESIGN_KEYWORDS = {
    DesignCategory.ENGAGEMENT_RING: ["engagement ring", "engagement"],
    DesignCategory.WEDDING_BAND: ["wedding band", "wedding ring"],
    DesignCategory.ETERNITY_BAND: ["eternity band", "eternity ring", "eternity"],
    DesignCategory.COCKTAIL_RING: ["cocktail ring"],
    DesignCategory.SOLITAIRE: ["solitaire"],
    DesignCategory.HALO_RING: ["halo ring"],
    DesignCategory.THREE_STONE: ["three stone", "three-stone", "trilogy"],
    DesignCategory.CLUSTER_RING: ["cluster ring"],
}

_NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
}


def _find_first(text: str, mapping: dict) -> object | None:
    for value, patterns in mapping.items():
        for pat in patterns:
            if re.search(pat, text):
                return value
    return None


def _find_first_keyword(text: str, mapping: dict) -> object | None:
    for value, keywords in mapping.items():
        for kw in keywords:
            # Word-boundary match -- plain substring containment would let
            # "pear" false-positive inside "pearl", "gold" inside a longer
            # compound word, etc.
            if re.search(r"\b" + re.escape(kw) + r"\b", text):
                return value
    return None


def _extract_carat(text: str) -> float | None:
    m = re.search(r"(\d+(?:\.\d+)?)\s*-?\s*carat", text)
    if m:
        return float(m.group(1))
    m = re.search(r"(\d+(?:\.\d+)?)\s*ct\b", text)
    if m:
        return float(m.group(1))
    return None


_NUM_WORD_PATTERN = r"(\d+|" + "|".join(_NUMBER_WORDS.keys()) + r")"


def _to_number(token: str) -> int | None:
    return int(token) if token.isdigit() else _NUMBER_WORDS.get(token)


def _extract_side_count(text: str) -> int | None:
    # Explicit "no side stones" / "without accent stones" -> 0.
    if re.search(r"\b(?:no|zero|without)\b[^.]{0,20}(?:side|accent)\s+stones?", text):
        return 0
    # "six small stones on each side" -> 6 per side -> 12 total
    m = re.search(_NUM_WORD_PATTERN + r"\s+(?:small\s+)?(?:stones?|diamonds?)\s+on\s+each\s+side", text)
    if m:
        n = _to_number(m.group(1))
        if n is not None:
            return n * 2
    # "12 side stones" / "eight moissanite side stones" / "total of 10 accent stones"
    m = re.search(_NUM_WORD_PATTERN + r"(?:\s+\w+){0,2}\s+(?:side|accent)\s+stones?", text)
    if m:
        n = _to_number(m.group(1))
        if n is not None:
            return n
    return None


def _extract_band_width(text: str) -> float | None:
    # Only an explicit numeric measurement counts. Qualitative descriptors
    # like "slim band" are deliberately left unknown rather than mapped to
    # an invented number -- inventing "slim = 1.5mm" would violate the
    # project's own never-fabricate-missing-values principle just as much
    # as an LLM guessing a number would.
    m = re.search(r"(\d+(?:\.\d+)?)\s*mm", text)
    if m:
        return float(m.group(1))
    return None


def _extract_ring_size(text: str) -> float | None:
    m = re.search(r"ring size\s*(?:of|is|:)?\s*(\d+(?:\.\d+)?)", text)
    if m:
        return float(m.group(1))
    return None


def extract_offline(brief: str) -> RawExtraction:
    """Keyword/regex extraction over the brief text. Deterministic and
    reproducible -- the same brief always yields the same result.
    """
    text = brief.lower()

    product_type = ProductType.RING if "ring" in text else None

    data = {
        "product_type": product_type,
        "design_category": _find_first_keyword(text, _DESIGN_KEYWORDS),
        "metal_type": _find_first_keyword(text, _METAL_TYPE_KEYWORDS),
        "metal_purity": _find_first(text, _METAL_PURITY_PATTERNS),
        "metal_color": _find_first_keyword(text, _METAL_COLOR_KEYWORDS),
        "setting_type": _find_first_keyword(text, _SETTING_KEYWORDS),
        "ring_size_us": _extract_ring_size(text),
        "band_width_mm": _extract_band_width(text),
        "center_stone_type": _find_first_keyword(text, _GEMSTONE_KEYWORDS),
        "center_stone_shape": _find_first_keyword(text, _SHAPE_KEYWORDS),
        "center_stone_carat": _extract_carat(text),
        "side_stone_type": _find_first_keyword(text, _GEMSTONE_KEYWORDS),
        "side_stone_shape": None,
        "side_stone_count_total": _extract_side_count(text),
        "side_stone_total_carat": None,
        "notes": "Extracted via deterministic offline keyword rules (no LLM call made).",
    }
    return RawExtraction.model_validate(data)
