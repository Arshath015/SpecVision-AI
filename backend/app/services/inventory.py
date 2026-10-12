"""Loads and caches the inventory catalog from the bundled JSON file."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from app.models.schemas import InventoryItem

_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "inventory.json"


@lru_cache
def load_inventory() -> list[InventoryItem]:
    raw = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
    return [InventoryItem.model_validate(item) for item in raw]


def get_item(product_id: str) -> InventoryItem | None:
    for item in load_inventory():
        if item.product_id == product_id:
            return item
    return None
