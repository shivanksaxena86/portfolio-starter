from __future__ import annotations

import math
from pathlib import Path

import streamlit as st
from portfolio_starter.total_battle.calc_v0 import (
    apply_shop_bonus,
    eta_hours_for_target,
    items_per_hour_from_batch,
)
from portfolio_starter.total_battle.config_io import (
    load_building_levels,
    load_recipes_and_unlocks,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RECIPES_PATH = DATA_DIR / "recipes.v0.json"
BUILDINGS_PATH = DATA_DIR / "buildings.v0.json"

TIER_BADGE = {
    "grey": "⬛",
    "white": "⬜",
    "green": "🟩",
    "blue": "🟦",
    "purple": "🟪",
    "orange": "🟧",
    "red": "🟥",
    "yellow": "🟨",
}


def badge(tier: str) -> str:
    return TIER_BADGE.get(tier, "•")


def main() -> None:
    st.set_page_config(page_title="Total Battle – Research Camp (v0)", layout="wide")
    st.title("Total Battle – Research Camp Calculator (v0)")
    st.caption(
        "v0 focuses on wiring data + quick ETA sanity checks. "
        "Next version (v1) will simulate full flows and recommend schedules/upgrades."
    )

    recipes, unlocks = load_recipes_and_unlocks(RECIPES_PATH)
    building_levels = load_building_levels(BUILDINGS_PATH)

    st.subheader("Buildings")
    col1, col2 = st.columns(2)

    with col1:
        shop_level = st.selectbox(
            f"{badge('purple')} Transmutation Shop level", options=[3, 4], index=0
        )
        num_shops = st.number_input("Number of shops", min_value=0, max_value=9, value=3, step=1)

    with col2:
        num_huts = st.number_input(
            f"{badge('blue')} Number of huts", min_value=0, max_value=9, value=5, step=1
        )
        st.write("Hut split (how many huts produce each material type):")
        huts_a = st.number_input("Huts on A", min_value=0, max_value=9, value=2, step=1)
        huts_b = st.number_input("Huts on B", min_value=0, max_value=9, value=2, step=1)
        huts_c = st.number_input("Huts on C", min_value=0, max_value=9, value=1, step=1)

        upgraded_hut_material = st.selectbox(
            "Optional: Upgrade ONE hut to level 4 (800%) on material",
            options=["None", "A", "B", "C"],
            index=0,
        )

    if huts_a + huts_b + huts_c != num_huts:
        st.warning(
            "Hut split must add up to total huts. Results may be misleading until corrected."
        )

    st.subheader("Inventory (current)")
    inv_col1, inv_col2, inv_col3 = st.columns(3)
    with inv_col1:
        blue_a = st.number_input(
            f"{badge('blue')} Blue A", min_value=0.0, value=55_000.0, step=100.0
        )
        purple_a = st.number_input(
            f"{badge('purple')} Purple A", min_value=0.0, value=135_000.0, step=100.0
        )
        orange_a = st.number_input(
            f"{badge('orange')} Orange A", min_value=0.0, value=200.0, step=10.0
        )
    with inv_col2:
        blue_b = st.number_input(
            f"{badge('blue')} Blue B", min_value=0.0, value=42_900.0, step=100.0
        )
        purple_b = st.number_input(
            f"{badge('purple')} Purple B", min_value=0.0, value=122_000.0, step=100.0
        )
        orange_b = st.number_input(
            f"{badge('orange')} Orange B", min_value=0.0, value=200.0, step=10.0
        )
    with inv_col3:
        blue_c = st.number_input(
            f"{badge('blue')} Blue C", min_value=0.0, value=77_000.0, step=100.0
        )
        purple_c = st.number_input(
            f"{badge('purple')} Purple C", min_value=0.0, value=109_000.0, step=100.0
        )
        orange_c = st.number_input(
            f"{badge('orange')} Orange C", min_value=0.0, value=200.0, step=10.0
        )

    st.subheader("Quick goal check (Orange recipe 1 only)")
    goal = st.selectbox(
        "Goal",
        [
            f"{badge('orange')} Slot 9 unlock (Orange 50k each)",
            f"{badge('orange')} Unlock Purple r4 (Orange 54k each)",
        ],
    )

    target_each = 50_000 if "50k" in goal else 54_000
    st.write(f"Target: **{badge('orange')} Orange {target_each:,} each** (A, B, C).")

    # Load Orange r1 recipes
    r1 = {r.id: r for r in recipes if r.id.startswith("orange_r1_")}
    shop_lvl = building_levels["shop"][int(shop_level)]

    # Shop allocation heuristic for v0:
    # - If you have >=3 shops, assume 1 dedicated per material 24x7.
    # - If fewer, split evenly as a rough estimate.
    if num_shops >= 3:
        shops_a = shops_b = shops_c = 1.0
    else:
        alloc = float(num_shops) / 3.0
        shops_a = shops_b = shops_c = alloc

    def rate_for(recipe_id: str, shops_alloc: float) -> float:
        eff = apply_shop_bonus(r1[recipe_id], shop_lvl)
        out_qty = eff.outputs[0].qty  # single output
        per_hour = items_per_hour_from_batch(out_qty, eff.time_hours)
        return per_hour * shops_alloc

    rate_a = rate_for("orange_r1_A", shops_a)
    rate_b = rate_for("orange_r1_B", shops_b)
    rate_c = rate_for("orange_r1_C", shops_c)

    need_a = max(0, int(target_each - orange_a))
    need_b = max(0, int(target_each - orange_b))
    need_c = max(0, int(target_each - orange_c))

    eta_a = eta_hours_for_target(rate_a, need_a)
    eta_b = eta_hours_for_target(rate_b, need_b)
    eta_c = eta_hours_for_target(rate_c, need_c)

    st.write(
        f"Assumption for v0: **1 shop continuously per material** (if you have ≥3 shops). "
        f"At Shop L{shop_level}, Orange r1 output per dedicated shop ≈ **{int(rate_a):,}/hour**."
    )

    m1, m2, m3 = st.columns(3)
    m1.metric(f"ETA {badge('orange')} Orange A", f"{eta_a:.1f} hours")
    m2.metric(f"ETA {badge('orange')} Orange B", f"{eta_b:.1f} hours")
    m3.metric(f"ETA {badge('orange')} Orange C", f"{eta_c:.1f} hours")

    st.subheader("Upstream sanity check (🟪 Purple needed, 🟦 Blue needed)")
    st.caption(
        "This checks if your current Purple/Blue inventories can support producing the missing Orange using "
        "Orange r1 + Purple r3. It’s a sanity check, not the full planner yet."
    )

    # Orange r1 ratio: Purple 1500 -> Orange 150  => 10 Purple per 1 Orange
    purple_needed_a = need_a * 10
    purple_needed_b = need_b * 10
    purple_needed_c = need_c * 10

    purple_def_a = max(0, purple_needed_a - int(purple_a))
    purple_def_b = max(0, purple_needed_b - int(purple_b))
    purple_def_c = max(0, purple_needed_c - int(purple_c))

    st.write(
        f"To make the missing Orange via {badge('orange')} r1 you need ~"
        f"**{badge('purple')} Purple**: A {purple_needed_a:,}, B {purple_needed_b:,}, C {purple_needed_c:,}."
    )
    st.write(f"Purple shortfall: A {purple_def_a:,}, B {purple_def_b:,}, C {purple_def_c:,}.")

    # Purple r3 effective batch @ L3 (assumed current shop level for throughput)
    # base: Blue 1000 each -> Purple 1500 in 1h
    # with shop mult (L3=4x): inputs 4000 each; output 6000 in 1h
    purple_r3 = {r.id: r for r in recipes if r.id.startswith("purple_r3_")}
    # any of A/B/C has same batch shape for inputs, output differs only by material label
    eff_purple_batch = apply_shop_bonus(purple_r3["purple_r3_A"], shop_lvl)
    purple_out_per_batch = eff_purple_batch.outputs[0].qty  # 6000 at L3
    blue_in_per_batch_each = next(
        x.qty for x in eff_purple_batch.inputs if x.tier == "blue" and x.material == "A"
    )

    batches_a = math.ceil(purple_def_a / purple_out_per_batch) if purple_def_a > 0 else 0
    batches_b = math.ceil(purple_def_b / purple_out_per_batch) if purple_def_b > 0 else 0
    batches_c = math.ceil(purple_def_c / purple_out_per_batch) if purple_def_c > 0 else 0

    total_batches = batches_a + batches_b + batches_c
    blue_need_each = (
        total_batches * blue_in_per_batch_each
    )  # Blue A, Blue B, Blue C each consumed equally

    blue_def_a = max(0, blue_need_each - int(blue_a))
    blue_def_b = max(0, blue_need_each - int(blue_b))
    blue_def_c = max(0, blue_need_each - int(blue_c))

    st.write(
        f"If you cover the Purple shortfall using {badge('purple')} Purple r3, you need "
        f"batches: A {batches_a}, B {batches_b}, C {batches_c} (total {total_batches})."
    )
    st.write(
        f"That consumes ~{badge('blue')} Blue per type: **{blue_need_each:,} each** (A, B, C)."
    )
    st.write(f"Blue shortfall: A {blue_def_a:,}, B {blue_def_b:,}, C {blue_def_c:,}.")

    # Hut production estimate for Blue (L3 huts produce 4000/h; one upgraded hut produces 8000/h)
    # This is a rough estimate assuming huts are producing BLUE (since you said blue herbalist is unlocked).
    base_per_hut_l3 = 4000
    extra_if_upgraded = 4000  # L4 hut adds +4000/h compared to L3

    blue_rate_a = huts_a * base_per_hut_l3
    blue_rate_b = huts_b * base_per_hut_l3
    blue_rate_c = huts_c * base_per_hut_l3

    if upgraded_hut_material in {"A", "B", "C"}:
        if upgraded_hut_material == "A" and huts_a > 0:
            blue_rate_a += extra_if_upgraded
        if upgraded_hut_material == "B" and huts_b > 0:
            blue_rate_b += extra_if_upgraded
        if upgraded_hut_material == "C" and huts_c > 0:
            blue_rate_c += extra_if_upgraded

    eta_blue_a = eta_hours_for_target(float(blue_rate_a), blue_def_a) if blue_def_a > 0 else 0.0
    eta_blue_b = eta_hours_for_target(float(blue_rate_b), blue_def_b) if blue_def_b > 0 else 0.0
    eta_blue_c = eta_hours_for_target(float(blue_rate_c), blue_def_c) if blue_def_c > 0 else 0.0

    s1, s2, s3 = st.columns(3)
    s1.metric(
        "🟦 Blue A rate",
        f"{blue_rate_a:,}/hour",
        help="Based on your hut split + optional L4 upgrade.",
    )
    s2.metric("🟦 Blue B rate", f"{blue_rate_b:,}/hour")
    s3.metric("🟦 Blue C rate", f"{blue_rate_c:,}/hour")

    t1, t2, t3 = st.columns(3)
    t1.metric("ETA to refill Blue A shortfall", f"{eta_blue_a:.1f} hours")
    t2.metric("ETA to refill Blue B shortfall", f"{eta_blue_b:.1f} hours")
    t3.metric("ETA to refill Blue C shortfall", f"{eta_blue_c:.1f} hours")

    with st.expander("Unlock costs loaded (sanity check)"):
        for u in unlocks:
            st.write(
                f"**{u.id}**:",
                ", ".join([f"{badge(x.tier)} {x.tier} {x.material} {x.qty:,}" for x in u.spend]),
            )


if __name__ == "__main__":
    main()
