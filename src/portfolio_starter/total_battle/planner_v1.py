from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable, Sequence

from .models import ItemQty, Recipe, UnlockCost

# ---------- Types / helpers ----------

Tier = str
Material = str
InvKey = tuple[Tier, Material]

TIER_ORDER: dict[Tier, int] = {
    "grey": 0,
    "white": 1,
    "green": 2,
    "blue": 3,
    "purple": 4,
    "orange": 5,
    "red": 6,
    "yellow": 7,
}


def tier_rank(tier: Tier) -> int:
    return TIER_ORDER.get(tier, -1)


def add_inv(inv: dict[InvKey, float], tier: Tier, material: Material, qty: float) -> None:
    inv[(tier, material)] = inv.get((tier, material), 0.0) + qty


def has_inv(inv: dict[InvKey, float], items: Iterable[ItemQty]) -> bool:
    return all(inv.get((x.tier, x.material), 0.0) + 1e-9 >= float(x.qty) for x in items)


def spend_inv(inv: dict[InvKey, float], items: Iterable[ItemQty]) -> None:
    for x in items:
        key = (x.tier, x.material)
        inv[key] = inv.get(key, 0.0) - float(x.qty)


def mult_from_level(level: int) -> float:
    """
    Your game's meaning: level3=400%=x4, level4=800%=x8, level5=1600%=x16, level6=3200%=x32.
    This matches 2^(level-1).
    """
    if level < 1:
        return 1.0
    return float(2 ** (level - 1))


def eff_recipe(recipe: Recipe, shop_mult: float) -> tuple[list[ItemQty], list[ItemQty], float]:
    """
    Apply shop throughput multiplier to BOTH inputs and outputs for shop recipes.
    For huts, multiplier is applied only to outputs (since huts have no inputs).
    """
    if recipe.building == "shop":
        ins = [ItemQty(x.tier, x.material, int(float(x.qty) * shop_mult)) for x in recipe.inputs]
        outs = [ItemQty(x.tier, x.material, int(float(x.qty) * shop_mult)) for x in recipe.outputs]
        dur = float(recipe.time_hours)
        return ins, outs, dur

    # hut
    ins = []
    outs = [ItemQty(x.tier, x.material, int(float(x.qty) * shop_mult)) for x in recipe.outputs]
    dur = float(recipe.time_hours)
    return ins, outs, dur


@dataclass(frozen=True)
class Goal:
    """Goal is expressed as "want at least qty of each listed item in inventory"."""

    id: str
    want: list[ItemQty]


@dataclass(frozen=True)
class UnlockTask:
    unlock_id: str
    spend: list[ItemQty]


@dataclass(frozen=True)
class Milestone:
    name: str
    reached_at: datetime
    hours_from_start: float
    details: str


@dataclass(frozen=True)
class HasteConfig:
    """
    Two haste mechanics:
    - hut_hours_instant: instantly grants hut production for N hours at time 0 (like "collect next N hours now").
    - shop_jobs_instant: next N shop batches complete instantly (duration=0).
    Optional coin math:
    - coins_per_hut_hour: if you know it, planner will estimate required coins.
    - coins_per_shop_hour: if you know it, planner will estimate required coins (duration_hours * coins_per_shop_hour).
    """

    hut_hours_instant: float = 0.0
    shop_jobs_instant: int = 0
    coins_per_hut_hour: float | None = None
    coins_per_shop_hour: float | None = None


@dataclass(frozen=True)
class PlannerConfig:
    start: datetime
    deadline: datetime

    # Buildings
    num_huts: int
    hut_level: int
    hut_split: dict[Material, int]  # {"A":2,"B":2,"C":1}
    num_shops: int
    shop_level: int

    # Current unlock state
    unlocked_unlocks: set[str]

    # Optional: a fixed unlock roadmap; if empty, planner will only try to reach the goal with what is already unlocked.
    unlock_sequence: list[str]

    # Haste knobs
    haste: HasteConfig


@dataclass(frozen=True)
class PlanResult:
    feasible: bool
    finished_at: datetime | None
    hours_needed: float | None
    hours_available: float
    milestones: list[Milestone]
    final_inventory: dict[InvKey, float]
    coins_estimate: dict[str, float]


# ---------- Core planner ----------


class PlannerV1:
    def __init__(self, recipes: list[Recipe], unlocks: list[UnlockCost]) -> None:
        self.recipes = recipes
        self.unlocks_by_id: dict[str, UnlockCost] = {u.id: u for u in unlocks}

        # Index recipes by their single output (your recipes are single-output per row)
        self.recipes_by_output: dict[InvKey, list[Recipe]] = {}
        for r in recipes:
            if not r.outputs:
                continue
            out = r.outputs[0]
            key = (out.tier, out.material)
            self.recipes_by_output.setdefault(key, []).append(r)

    def _best_recipe_for(
        self,
        key: InvKey,
        unlocked: set[str],
        shop_mult: float,
    ) -> Recipe | None:
        """
        Pick the "best" unlocked recipe for an output item.
        Current heuristic: maximize output_per_hour (after multiplier).
        """
        candidates = self.recipes_by_output.get(key, [])
        best: tuple[float, Recipe] | None = None

        for r in candidates:
            if r.unlock_id is not None and r.unlock_id not in unlocked:
                continue

            ins, outs, dur = eff_recipe(r, shop_mult if r.building == "shop" else shop_mult)
            # outs[0] is the output of this recipe
            out_qty = float(outs[0].qty) if outs else 0.0
            if dur <= 0:
                continue
            score = out_qty / dur
            if best is None or score > best[0]:
                best = (score, r)

        return best[1] if best else None

    def _goal_met(self, inv: dict[InvKey, float], want: list[ItemQty]) -> bool:
        return all(inv.get((x.tier, x.material), 0.0) + 1e-9 >= float(x.qty) for x in want)

    def _apply_hut_instant(self, inv: dict[InvKey, float], cfg: PlannerConfig) -> dict[str, float]:
        coins: dict[str, float] = {}
        hours = max(0.0, cfg.haste.hut_hours_instant)
        if hours <= 0:
            return coins

        hut_mult = mult_from_level(cfg.hut_level)
        # Blue hut base is 1000/hour in your config; multiplier gives 4k/h at L3.
        base_per_hut_per_hour = 1000.0

        for mat, count in cfg.hut_split.items():
            if count <= 0:
                continue
            produced = hours * count * base_per_hut_per_hour * hut_mult
            add_inv(inv, "blue", mat, produced)

        if cfg.haste.coins_per_hut_hour is not None:
            coins["hut_coins"] = hours * float(cfg.haste.coins_per_hut_hour)

        return coins

    def run(self, cfg: PlannerConfig, inventory: dict[InvKey, float], goal: Goal) -> PlanResult:
        inv = dict(inventory)  # copy so we don't mutate caller
        unlocked = set(cfg.unlocked_unlocks)

        shop_mult = mult_from_level(cfg.shop_level)
        hut_mult = mult_from_level(cfg.hut_level)

        hours_available = (cfg.deadline - cfg.start).total_seconds() / 3600.0
        if hours_available < 0:
            return PlanResult(
                feasible=False,
                finished_at=None,
                hours_needed=None,
                hours_available=hours_available,
                milestones=[],
                final_inventory=inv,
                coins_estimate={},
            )

        milestones: list[Milestone] = []
        coins_est: dict[str, float] = {}

        # Haste: instant hut hours at time 0
        coins_est.update(self._apply_hut_instant(inv, cfg))

        # Convert unlock sequence into tasks
        tasks: list[UnlockTask] = []
        for unlock_id in cfg.unlock_sequence:
            if unlock_id not in self.unlocks_by_id:
                continue
            u = self.unlocks_by_id[unlock_id]
            tasks.append(UnlockTask(unlock_id=unlock_id, spend=u.spend))

        # Add final goal as a "want"
        now = cfg.start
        t_hours = 0.0

        # Shop simulation state
        # Each slot holds (busy_until, pending_outputs, duration_used_for_coin_calc)
        shops: list[tuple[datetime, list[ItemQty], float]] = [
            (cfg.start, [], 0.0) for _ in range(max(0, cfg.num_shops))
        ]
        haste_jobs_left = max(0, cfg.haste.shop_jobs_instant)

        def hut_produce(delta_hours: float) -> None:
            if delta_hours <= 0:
                return
            base_per_hut_per_hour = 1000.0
            for mat, count in cfg.hut_split.items():
                if count <= 0:
                    continue
                produced = delta_hours * count * base_per_hut_per_hour * hut_mult
                add_inv(inv, "blue", mat, produced)

        def start_one_shop_job(desired: InvKey) -> bool:
            """
            Try to start a shop job that helps the desired output.
            If direct job can't start due to missing inputs, we recursively try to produce missing inputs.
            """
            nonlocal haste_jobs_left

            r = self._best_recipe_for(desired, unlocked, shop_mult)
            if r is None:
                return False

            ins, outs, dur = eff_recipe(r, shop_mult)

            if not has_inv(inv, ins):
                # Try to satisfy missing inputs first (one step: pick the highest-tier missing input and produce it)
                missing: list[InvKey] = []
                for x in ins:
                    key = (x.tier, x.material)
                    if inv.get(key, 0.0) + 1e-9 < float(x.qty):
                        missing.append(key)

                if not missing:
                    return False

                missing.sort(key=lambda k: tier_rank(k[0]), reverse=True)
                return start_one_shop_job(missing[0])

            # Find an idle shop slot
            idle_idx = None
            for i, (busy_until, _, _) in enumerate(shops):
                if busy_until <= now:
                    idle_idx = i
                    break
            if idle_idx is None:
                return False

            spend_inv(inv, ins)

            used_duration = dur
            finish = now + timedelta(hours=dur)

            # Haste: complete N jobs instantly
            if haste_jobs_left > 0:
                haste_jobs_left -= 1
                finish = now
                used_duration = dur  # still counts for coin estimate

                # Outputs land immediately
                for o in outs:
                    add_inv(inv, o.tier, o.material, float(o.qty))
                shops[idle_idx] = (finish, [], used_duration)
            else:
                shops[idle_idx] = (finish, outs, used_duration)

            return True

        def settle_finished_jobs() -> None:
            for i, (busy_until, pending_outs, dur_used) in enumerate(shops):
                if busy_until <= now and pending_outs:
                    for o in pending_outs:
                        add_inv(inv, o.tier, o.material, float(o.qty))
                    shops[i] = (busy_until, [], dur_used)

        def next_shop_event_time() -> datetime | None:
            future = [t for (t, pending, _) in shops if pending and t > now]
            return min(future) if future else None

        def fill_idle_shops(target_keys: Sequence[InvKey]) -> None:

            # Keep trying to start jobs while we have idle slots and there is something useful to do.
            # Prioritize higher tiers first, then bigger deficits.
            for _ in range(len(shops) * 3):
                idle_exists = any(busy_until <= now for (busy_until, _, _) in shops)
                if not idle_exists:
                    break

                started_any = False
                for key in target_keys:
                    if start_one_shop_job(key):
                        started_any = True
                        break

                if not started_any:
                    break

        def coins_from_shop_haste() -> None:
            if cfg.haste.coins_per_shop_hour is None:
                return
            # Estimate: total duration of instant-finished jobs * coins_per_shop_hour
            # We track durations used on each slot (not perfect, but ok for v1).
            total_dur = 0.0
            for _, _, dur_used in shops:
                total_dur += float(dur_used)
            coins_est["shop_coins_est"] = total_dur * float(cfg.haste.coins_per_shop_hour)

        def run_until_want(want: list[ItemQty], label: str) -> tuple[bool, str]:
            nonlocal now, t_hours

            # Prepare a stable list of target keys ordered by tier priority
            target_keys = [(x.tier, x.material) for x in want]
            target_keys.sort(key=lambda k: tier_rank(k[0]), reverse=True)

            # Main loop
            while not self._goal_met(inv, want):
                # Stop if deadline exceeded
                if t_hours > hours_available + 1e-9:
                    return False, "Exceeded deadline while producing required materials."

                # Fill idle shops based on targets
                fill_idle_shops(target_keys)

                # Determine next event: either shop finishes, or 1-hour tick for hut production
                nxt_shop = next_shop_event_time()
                nxt_tick = now + timedelta(hours=1)

                nxt = nxt_tick if nxt_shop is None else min(nxt_tick, nxt_shop)

                delta = (nxt - now).total_seconds() / 3600.0
                hut_produce(delta)
                now = nxt
                t_hours += delta

                settle_finished_jobs()

            milestones.append(
                Milestone(
                    name=label,
                    reached_at=now,
                    hours_from_start=t_hours,
                    details="",
                )
            )
            return True, ""

        # 1) Execute unlock roadmap (if provided)
        for task in tasks:
            # Produce enough to pay unlock spend
            ok, msg = run_until_want(task.spend, f"Gather materials for unlock: {task.unlock_id}")
            if not ok:
                coins_from_shop_haste()
                return PlanResult(
                    feasible=False,
                    finished_at=None,
                    hours_needed=None,
                    hours_available=hours_available,
                    milestones=milestones
                    + [
                        Milestone(
                            name=f"FAILED before unlock {task.unlock_id}",
                            reached_at=now,
                            hours_from_start=t_hours,
                            details=msg,
                        )
                    ],
                    final_inventory=inv,
                    coins_estimate=coins_est,
                )

            # Spend and unlock
            spend_inv(inv, task.spend)
            unlocked.add(task.unlock_id)
            milestones.append(
                Milestone(
                    name=f"UNLOCKED: {task.unlock_id}",
                    reached_at=now,
                    hours_from_start=t_hours,
                    details="Spent unlock cost from inventory.",
                )
            )

        # 2) Produce final goal
        ok, msg = run_until_want(goal.want, f"Goal reached: {goal.id}")
        coins_from_shop_haste()

        if not ok:
            return PlanResult(
                feasible=False,
                finished_at=None,
                hours_needed=None,
                hours_available=hours_available,
                milestones=milestones
                + [
                    Milestone(
                        name="FAILED",
                        reached_at=now,
                        hours_from_start=t_hours,
                        details=msg,
                    )
                ],
                final_inventory=inv,
                coins_estimate=coins_est,
            )

        return PlanResult(
            feasible=True,
            finished_at=now,
            hours_needed=t_hours,
            hours_available=hours_available,
            milestones=milestones,
            final_inventory=inv,
            coins_estimate=coins_est,
        )
