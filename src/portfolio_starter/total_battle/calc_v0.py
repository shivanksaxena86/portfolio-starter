from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .models import BuildingLevel, ItemQty, Recipe


@dataclass(frozen=True)
class EffectiveBatch:
    """A recipe batch after applying shop bonus multiplier."""

    time_hours: float
    inputs: list[ItemQty]
    outputs: list[ItemQty]


def apply_shop_bonus(recipe: Recipe, shop_level: BuildingLevel) -> EffectiveBatch:
    """
    Shop bonus multiplies BOTH inputs and outputs; time stays the same.
    Example (L3 = 4x):
      base: 1000+1000+1000 -> 1500 in 1h
      effective: 4000+4000+4000 -> 6000 in 1h
    """
    mult = shop_level.bonus_mult

    def scale(items: Iterable[ItemQty]) -> list[ItemQty]:
        out: list[ItemQty] = []
        for it in items:
            out.append(ItemQty(tier=it.tier, material=it.material, qty=int(it.qty * mult)))
        return out

    return EffectiveBatch(
        time_hours=recipe.time_hours,
        inputs=scale(recipe.inputs),
        outputs=scale(recipe.outputs),
    )


def items_per_hour_from_batch(output_qty: int, time_hours: float) -> float:
    return output_qty / time_hours if time_hours > 0 else 0.0


def eta_hours_for_target(rate_per_hour: float, target_qty: int) -> float:
    if rate_per_hour <= 0:
        return float("inf")
    return target_qty / rate_per_hour
