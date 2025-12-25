from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from .models import BuildingLevel, ItemQty, Recipe, UnlockCost


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return cast(dict[str, Any], json.load(f))


def _itemqty(d: dict) -> ItemQty:
    return ItemQty(tier=d["tier"], material=d["material"], qty=int(d["qty"]))


def load_recipes_and_unlocks(recipes_path: Path) -> tuple[list[Recipe], list[UnlockCost]]:
    data = load_json(recipes_path)

    recipes: list[Recipe] = []
    for r in data["recipes"]:
        recipes.append(
            Recipe(
                id=r["id"],
                building=r["building"],
                time_hours=float(r["time_hours"]),
                inputs=[_itemqty(x) for x in r.get("inputs", [])],
                outputs=[_itemqty(x) for x in r.get("outputs", [])],
            )
        )

    unlocks: list[UnlockCost] = []
    for u in data.get("unlocks", []):
        unlocks.append(
            UnlockCost(
                id=u["id"],
                spend=[_itemqty(x) for x in u["spend"]],
            )
        )

    return recipes, unlocks


def load_building_levels(buildings_path: Path) -> dict:
    """
    Returns:
      {
        "hut": {3: BuildingLevel(...), 4: ...},
        "shop": {3: ..., 4: ...}
      }
    """
    data = load_json(buildings_path)
    out: dict = {"hut": {}, "shop": {}}

    for btype in ("hut", "shop"):
        for lvl_str, payload in data[btype]["levels"].items():
            lvl = int(lvl_str)
            out[btype][lvl] = BuildingLevel(
                level=lvl,
                bonus_mult=float(payload["bonus_mult"]),
                queue_slots_total=payload.get("queue_slots_total"),
            )
    return out
