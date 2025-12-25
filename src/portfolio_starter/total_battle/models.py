from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Tier = Literal["grey", "white", "green", "blue", "purple", "orange", "red", "yellow"]
Material = Literal["A", "B", "C"]
Building = Literal["hut", "shop"]


@dataclass(frozen=True)
class ItemQty:
    tier: Tier
    material: Material
    qty: int


@dataclass(frozen=True)
class Recipe:
    """
    A single recipe for one output material at one tier.

    NOTE: Shop bonus multiplies BOTH inputs and outputs; time stays the same.
    Hut bonus multiplies output rate (items/hour).
    """

    id: str
    building: Building
    time_hours: float
    inputs: list[ItemQty]
    outputs: list[ItemQty]
    unlock_id: str | None = None


@dataclass(frozen=True)
class UnlockCost:
    """
    A one-time spend (consume) requirement to unlock something.
    Example: unlock Purple r4 requires spending Orange 54k each A/B/C.
    """

    id: str
    spend: list[ItemQty]


@dataclass(frozen=True)
class BuildingLevel:
    level: int
    bonus_mult: float
    queue_slots_total: int | None = None  # only relevant for shops
