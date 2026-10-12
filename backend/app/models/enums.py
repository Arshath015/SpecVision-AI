"""Controlled vocabularies for the jewelry domain.

Enumerations keep extraction, matching, and inventory data mutually
consistent. Anything outside these lists is represented as UNKNOWN rather
than guessed.
"""
from __future__ import annotations

from enum import Enum


class ProductType(str, Enum):
    RING = "ring"
    NECKLACE = "necklace"
    EARRING = "earring"
    BRACELET = "bracelet"
    PENDANT = "pendant"
    UNKNOWN = "unknown"


class MetalType(str, Enum):
    GOLD = "gold"
    PLATINUM = "platinum"
    SILVER = "silver"
    PALLADIUM = "palladium"
    UNKNOWN = "unknown"


class MetalPurity(str, Enum):
    K10 = "10k"
    K14 = "14k"
    K18 = "18k"
    K22 = "22k"
    K24 = "24k"
    PLATINUM_950 = "950_platinum"
    SILVER_925 = "925_silver"
    UNKNOWN = "unknown"


class MetalColor(str, Enum):
    YELLOW = "yellow"
    WHITE = "white"
    ROSE = "rose"
    TWO_TONE = "two_tone"
    UNKNOWN = "unknown"


class GemstoneType(str, Enum):
    DIAMOND = "diamond"
    SAPPHIRE = "sapphire"
    RUBY = "ruby"
    EMERALD = "emerald"
    MOISSANITE = "moissanite"
    MORGANITE = "morganite"
    AQUAMARINE = "aquamarine"
    AMETHYST = "amethyst"
    TOPAZ = "topaz"
    PEARL = "pearl"
    OTHER = "other"
    UNKNOWN = "unknown"


class GemstoneShape(str, Enum):
    ROUND = "round"
    OVAL = "oval"
    PRINCESS = "princess"
    CUSHION = "cushion"
    EMERALD_CUT = "emerald_cut"
    PEAR = "pear"
    MARQUISE = "marquise"
    RADIANT = "radiant"
    ASSCHER = "asscher"
    HEART = "heart"
    UNKNOWN = "unknown"


class SettingType(str, Enum):
    PRONG = "prong"
    PAVE = "pave"
    BEZEL = "bezel"
    HALO = "halo"
    CHANNEL = "channel"
    TENSION = "tension"
    CLUSTER = "cluster"
    UNKNOWN = "unknown"


class DesignCategory(str, Enum):
    ENGAGEMENT_RING = "engagement_ring"
    WEDDING_BAND = "wedding_band"
    ETERNITY_BAND = "eternity_band"
    COCKTAIL_RING = "cocktail_ring"
    SOLITAIRE = "solitaire"
    HALO_RING = "halo_ring"
    THREE_STONE = "three_stone"
    CLUSTER_RING = "cluster_ring"
    UNKNOWN = "unknown"


class SourceType(str, Enum):
    """Where a field's value came from."""

    USER_PROVIDED = "user_provided"   # verbatim/explicit in the brief
    MODEL_INFERRED = "model_inferred"  # LLM inferred from context/domain knowledge
    IMAGE_ESTIMATED = "image_estimated"  # derived from classical CV on the image
    DEFAULT_ASSUMPTION = "default_assumption"  # system default used to fill a gap
    UNKNOWN = "unknown"  # value could not be determined by any source


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ReviewSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class ExtractionMethod(str, Enum):
    LLM_LIVE = "llm_live"
    LLM_LIVE_FALLBACK_MODEL = "llm_live_fallback_model"
    LLM_REPAIRED = "llm_repaired"
    OFFLINE_FIXTURE = "offline_fixture"
    SAFE_DEGRADATION = "safe_degradation"


class CVMethod(str, Enum):
    CONTOUR_AND_HOUGH = "contour_and_hough_hybrid"
    UNAVAILABLE = "unavailable"
