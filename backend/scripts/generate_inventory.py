"""One-off generator for the illustrative inventory catalog.

Run manually with `python scripts/generate_inventory.py` whenever the
catalog needs to be regenerated. The output (`app/data/inventory.json`) is
committed and loaded at runtime -- this script is not imported by the app.

Prices are illustrative placeholders for evaluation purposes, not verified
market quotes.
"""
import json
import random
from pathlib import Path

random.seed(42)

METALS = [
    ("gold", "14k", "yellow"),
    ("gold", "18k", "yellow"),
    ("gold", "18k", "white"),
    ("gold", "18k", "rose"),
    ("gold", "14k", "white"),
    ("gold", "22k", "yellow"),
    ("platinum", "950_platinum", "white"),
    ("silver", "925_silver", "white"),
]

CENTER_STONES = [
    ("diamond", "round", 0.3, 0.6),
    ("diamond", "oval", 0.8, 1.2),
    ("diamond", "oval", 1.3, 1.8),
    ("diamond", "princess", 0.5, 0.9),
    ("diamond", "cushion", 1.0, 1.5),
    ("diamond", "emerald_cut", 1.2, 1.8),
    ("diamond", "pear", 0.7, 1.1),
    ("diamond", "radiant", 1.0, 1.6),
    ("sapphire", "oval", 1.0, 1.6),
    ("sapphire", "round", 0.6, 1.0),
    ("ruby", "oval", 0.8, 1.3),
    ("emerald", "emerald_cut", 0.9, 1.4),
    ("moissanite", "round", 1.0, 1.5),
    ("moissanite", "oval", 1.2, 1.8),
    ("morganite", "oval", 1.5, 2.2),
    ("aquamarine", "round", 0.8, 1.2),
    ("amethyst", "oval", 1.0, 1.6),
    ("pearl", "unknown", 0.0, 0.0),
]

SETTINGS = ["prong", "pave", "bezel", "halo", "channel", "tension", "cluster"]
DESIGNS = [
    "engagement_ring", "wedding_band", "eternity_band", "cocktail_ring",
    "solitaire", "halo_ring", "three_stone", "cluster_ring",
]
SIDE_STONE_TYPES = ["diamond", "moissanite", "sapphire", "unknown"]

NAME_TEMPLATES = [
    "{design} {shape} {metal_color} {metal} Ring",
    "{metal_color} {metal} {stone} {design}",
    "Classic {shape} {stone} {design} in {metal_color} {metal}",
    "{design} with {side_count} Side Stones - {metal_color} {metal}",
]


def pretty(s: str) -> str:
    return s.replace("_", " ").title()


def build_item(idx: int) -> dict:
    metal_type, purity, color = random.choice(METALS)
    stone_type, shape, cmin, cmax = random.choice(CENTER_STONES)
    setting = random.choice(SETTINGS)
    design = random.choice(DESIGNS)
    side_stone_type = random.choice(SIDE_STONE_TYPES)
    side_count = random.choice([0, 2, 6, 8, 10, 12, 14, 16])
    band_width = round(random.uniform(1.3, 4.5), 1)

    # Pricing: illustrative base formula by metal, stone, and carat midpoint.
    metal_base = {"gold": 650, "platinum": 950, "silver": 180, "palladium": 700}[metal_type]
    stone_base = {
        "diamond": 2600, "sapphire": 900, "ruby": 1000, "emerald": 950,
        "moissanite": 450, "morganite": 300, "aquamarine": 260,
        "amethyst": 180, "pearl": 150, "other": 300, "unknown": 150,
    }[stone_type]
    carat_mid = (cmin + cmax) / 2
    side_cost = side_count * 35
    unit_price = round(metal_base + stone_base * max(carat_mid, 0.2) * 1.4 + side_cost, 2)

    name = random.choice(NAME_TEMPLATES).format(
        design=pretty(design), shape=pretty(shape), metal_color=pretty(color),
        metal=pretty(metal_type), stone=pretty(stone_type), side_count=side_count,
    )

    return {
        "product_id": f"SV-{idx:03d}",
        "name": name,
        "product_type": "ring",
        "design_category": design,
        "metal_type": metal_type,
        "metal_purity": purity,
        "metal_color": color,
        "setting_type": setting,
        "center_stone_type": stone_type,
        "center_stone_shape": shape,
        "center_stone_carat_min": cmin,
        "center_stone_carat_max": cmax,
        "side_stone_type": side_stone_type if side_count > 0 else "unknown",
        "side_stone_count": side_count,
        "band_width_mm": band_width,
        "unit_price": unit_price,
        "currency": "USD",
    }


def main() -> None:
    items = [build_item(i) for i in range(1, 43)]
    out_path = Path(__file__).resolve().parent.parent / "app" / "data" / "inventory.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(items, indent=2), encoding="utf-8")
    print(f"Wrote {len(items)} items to {out_path}")


if __name__ == "__main__":
    main()
