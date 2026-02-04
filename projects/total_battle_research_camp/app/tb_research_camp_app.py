from __future__ import annotations

import math
from datetime import date, datetime, time, timedelta
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
from portfolio_starter.total_battle.models import ItemQty
from portfolio_starter.total_battle.planner_v1 import Goal, HasteConfig, PlannerConfig, PlannerV1

# -----------------------
# Paths / data loading
# -----------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RECIPES_PATH = DATA_DIR / "recipes.v1.json"
BUILDINGS_PATH = DATA_DIR / "buildings.v0.json"

RECIPES, UNLOCKS = load_recipes_and_unlocks(RECIPES_PATH)
BUILDING_LEVELS = load_building_levels(BUILDINGS_PATH)

# -----------------------
# UI helpers
# -----------------------
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


def list_sundays(start: datetime, end: datetime) -> list[datetime]:
    """
    Returns Sunday checkpoints between start and end (inclusive end if it is Sunday).
    Assumption: weekly rewards land on Sunday (local time).
    """
    cur = datetime.combine(start.date(), time(0, 0, 0))
    # Python weekday: Monday=0 ... Sunday=6
    days_ahead = (6 - cur.weekday()) % 7
    cur = cur + timedelta(days=days_ahead)

    sundays: list[datetime] = []
    while cur <= end:
        sundays.append(cur)
        cur = cur + timedelta(days=7)
    return sundays


def pack_plan_for_coins(shortfall: float) -> dict[str, float]:
    """
    Simple purchase planner for coins.
    You said:
      - Buy 9000 coins for Rs 500 anytime.
      - First-time pack: 18000 coins for Rs 1000 (optional).
    Returns: pack counts + INR estimate.
    """
    if shortfall <= 0:
        return {
            "need_extra_coins": 0.0,
            "pack_18k": 0.0,
            "pack_9k": 0.0,
            "coins_bought": 0.0,
            "inr": 0.0,
        }

    # Option A: only 9k packs
    p9 = int((shortfall + 9000 - 1) // 9000)
    inr_a = p9 * 500
    coins_a = p9 * 9000

    # Option B: one 18k pack + remaining 9k packs
    remain = max(0.0, shortfall - 18000.0)
    p9_b = int((remain + 9000 - 1) // 9000)
    inr_b = 1000 + p9_b * 500
    coins_b = 18000 + p9_b * 9000

    if inr_b < inr_a:
        return {
            "need_extra_coins": float(shortfall),
            "pack_18k": 1.0,
            "pack_9k": float(p9_b),
            "coins_bought": float(coins_b),
            "inr": float(inr_b),
        }

    return {
        "need_extra_coins": float(shortfall),
        "pack_18k": 0.0,
        "pack_9k": float(p9),
        "coins_bought": float(coins_a),
        "inr": float(inr_a),
    }


# -----------------------
# App
# -----------------------
def main() -> None:
    st.set_page_config(page_title="Total Battle – Research Camp", layout="wide")
    st.title("Total Battle – Research Camp Calculator")
    st.caption(
        "Tabs:\n"
        "- **Quick check**: fast ETA sanity checks (Orange r1 + Purple r3 assumptions)\n"
        "- **Planner v1**: feasibility + roadmap + weekly budgets (coins/supplies)"
    )

    tab_quick, tab_planner = st.tabs(["Quick check", "Planner v1 (roadmap + weekly budgets)"])

    # ============================================================
    # TAB 1 — QUICK CHECK
    # ============================================================
    with tab_quick:
        st.header("Quick goal check (assumes Orange r1 only + simple upstream sanity checks)")

        st.subheader("Buildings (quick scenario)")
        col1, col2 = st.columns(2)

        with col1:
            shop_level_q = st.selectbox(
                f"{badge('purple')} Transmutation Shop level",
                options=[3, 4],
                index=0,
                key="quick_shop_level",
            )
            num_shops_q = st.number_input(
                "Number of shops", min_value=0, max_value=9, value=3, step=1, key="quick_num_shops"
            )

        with col2:
            num_huts_q = st.number_input(
                f"{badge('blue')} Number of huts",
                min_value=0,
                max_value=9,
                value=5,
                step=1,
                key="quick_num_huts",
            )
            st.write("Hut split (how many huts produce each material type):")
            huts_a_q = st.number_input(
                "Huts on A", min_value=0, max_value=9, value=2, step=1, key="quick_huts_a"
            )
            huts_b_q = st.number_input(
                "Huts on B", min_value=0, max_value=9, value=2, step=1, key="quick_huts_b"
            )
            huts_c_q = st.number_input(
                "Huts on C", min_value=0, max_value=9, value=1, step=1, key="quick_huts_c"
            )

            upgraded_hut_material = st.selectbox(
                "Optional: Upgrade ONE hut to level 4 (800%) on material",
                options=["None", "A", "B", "C"],
                index=0,
                key="quick_upgraded_hut_mat",
            )

        if huts_a_q + huts_b_q + huts_c_q != num_huts_q:
            st.warning("Hut split must add up to total huts. Fix for accurate results.")

        st.subheader("Inventory (current)")
        inv_col1, inv_col2, inv_col3 = st.columns(3)
        with inv_col1:
            blue_a_q = st.number_input(
                f"{badge('blue')} Blue A",
                min_value=0.0,
                value=55_000.0,
                step=100.0,
                key="quick_blue_a",
            )
            purple_a_q = st.number_input(
                f"{badge('purple')} Purple A",
                min_value=0.0,
                value=135_000.0,
                step=100.0,
                key="quick_purple_a",
            )
            orange_a_q = st.number_input(
                f"{badge('orange')} Orange A",
                min_value=0.0,
                value=200.0,
                step=10.0,
                key="quick_orange_a",
            )
        with inv_col2:
            blue_b_q = st.number_input(
                f"{badge('blue')} Blue B",
                min_value=0.0,
                value=42_900.0,
                step=100.0,
                key="quick_blue_b",
            )
            purple_b_q = st.number_input(
                f"{badge('purple')} Purple B",
                min_value=0.0,
                value=122_000.0,
                step=100.0,
                key="quick_purple_b",
            )
            orange_b_q = st.number_input(
                f"{badge('orange')} Orange B",
                min_value=0.0,
                value=200.0,
                step=10.0,
                key="quick_orange_b",
            )
        with inv_col3:
            blue_c_q = st.number_input(
                f"{badge('blue')} Blue C",
                min_value=0.0,
                value=77_000.0,
                step=100.0,
                key="quick_blue_c",
            )
            purple_c_q = st.number_input(
                f"{badge('purple')} Purple C",
                min_value=0.0,
                value=109_000.0,
                step=100.0,
                key="quick_purple_c",
            )
            orange_c_q = st.number_input(
                f"{badge('orange')} Orange C",
                min_value=0.0,
                value=200.0,
                step=10.0,
                key="quick_orange_c",
            )

        st.subheader("Quick goal")
        goal_label = st.selectbox(
            "Goal",
            [
                f"{badge('orange')} Slot 9 unlock (Orange 50k each)",
                f"{badge('orange')} Unlock Purple r4 (Orange 54k each)",
            ],
            key="quick_goal",
        )
        target_each = 50_000 if "50k" in goal_label else 54_000
        st.write(f"Target: **{badge('orange')} Orange {target_each:,} each** (A, B, C).")

        # Load Orange r1 recipes
        r1 = {r.id: r for r in RECIPES if r.id.startswith("orange_r1_")}
        shop_lvl = BUILDING_LEVELS["shop"][int(shop_level_q)]

        # Shop allocation heuristic:
        # - If >=3 shops: assume 1 dedicated per material 24x7
        # - Else: split evenly (rough)
        if num_shops_q >= 3:
            shops_a = shops_b = shops_c = 1.0
        else:
            alloc = float(num_shops_q) / 3.0
            shops_a = shops_b = shops_c = alloc

        def rate_for(recipe_id: str, shops_alloc: float) -> float:
            eff = apply_shop_bonus(r1[recipe_id], shop_lvl)
            out_qty = eff.outputs[0].qty
            per_hour = items_per_hour_from_batch(out_qty, eff.time_hours)
            return per_hour * shops_alloc

        rate_a = rate_for("orange_r1_A", shops_a)
        rate_b = rate_for("orange_r1_B", shops_b)
        rate_c = rate_for("orange_r1_C", shops_c)

        need_a = max(0, int(target_each - orange_a_q))
        need_b = max(0, int(target_each - orange_b_q))
        need_c = max(0, int(target_each - orange_c_q))

        eta_a = eta_hours_for_target(rate_a, need_a)
        eta_b = eta_hours_for_target(rate_b, need_b)
        eta_c = eta_hours_for_target(rate_c, need_c)

        st.write(
            f"Assumption: **1 shop continuously per material** (if you have ≥3 shops). "
            f"At Shop L{shop_level_q}, Orange r1 output per dedicated shop ≈ **{int(rate_a):,}/hour**."
        )

        m1, m2, m3 = st.columns(3)
        m1.metric(f"ETA {badge('orange')} Orange A", f"{eta_a:.1f} hours")
        m2.metric(f"ETA {badge('orange')} Orange B", f"{eta_b:.1f} hours")
        m3.metric(f"ETA {badge('orange')} Orange C", f"{eta_c:.1f} hours")

        st.subheader("Upstream sanity check (🟪 Purple needed, 🟦 Blue needed)")
        st.caption(
            "Sanity check only: Orange r1 consumes Purple; Purple deficit estimated via Purple r3 consuming Blue."
        )

        # Orange r1 ratio: Purple 1500 -> Orange 150  => 10 Purple per 1 Orange
        purple_needed_a = need_a * 10
        purple_needed_b = need_b * 10
        purple_needed_c = need_c * 10

        purple_def_a = max(0, purple_needed_a - int(purple_a_q))
        purple_def_b = max(0, purple_needed_b - int(purple_b_q))
        purple_def_c = max(0, purple_needed_c - int(purple_c_q))

        st.write(
            f"To make missing Orange via {badge('orange')} r1 you need ~ {badge('purple')} Purple:\n"
            f"- A **{purple_needed_a:,}**, B **{purple_needed_b:,}**, C **{purple_needed_c:,}**"
        )
        st.write(
            f"Purple shortfall: A **{purple_def_a:,}**, B **{purple_def_b:,}**, C **{purple_def_c:,}**"
        )

        # Purple r3 effective batch
        purple_r3 = {r.id: r for r in RECIPES if r.id.startswith("purple_r3_")}
        eff_purple_batch = apply_shop_bonus(purple_r3["purple_r3_A"], shop_lvl)
        purple_out_per_batch = eff_purple_batch.outputs[0].qty
        blue_in_per_batch_each = next(
            x.qty for x in eff_purple_batch.inputs if x.tier == "blue" and x.material == "A"
        )

        batches_a = math.ceil(purple_def_a / purple_out_per_batch) if purple_def_a > 0 else 0
        batches_b = math.ceil(purple_def_b / purple_out_per_batch) if purple_def_b > 0 else 0
        batches_c = math.ceil(purple_def_c / purple_out_per_batch) if purple_def_c > 0 else 0

        total_batches = batches_a + batches_b + batches_c
        blue_need_each = total_batches * blue_in_per_batch_each

        blue_def_a = max(0, blue_need_each - int(blue_a_q))
        blue_def_b = max(0, blue_need_each - int(blue_b_q))
        blue_def_c = max(0, blue_need_each - int(blue_c_q))

        st.write(
            f"Purple r3 batches needed: A **{batches_a}**, B **{batches_b}**, C **{batches_c}** (total **{total_batches}**)."
        )
        st.write(f"Blue consumed per type: **{badge('blue')} {blue_need_each:,} each** (A, B, C).")
        st.write(
            f"Blue shortfall: A **{blue_def_a:,}**, B **{blue_def_b:,}**, C **{blue_def_c:,}**"
        )

        # Hut production for Blue (rough)
        base_per_hut_l3 = 4000
        extra_if_upgraded = 4000  # L4 hut adds +4000/h compared to L3

        blue_rate_a = huts_a_q * base_per_hut_l3
        blue_rate_b = huts_b_q * base_per_hut_l3
        blue_rate_c = huts_c_q * base_per_hut_l3

        if upgraded_hut_material in {"A", "B", "C"}:
            if upgraded_hut_material == "A" and huts_a_q > 0:
                blue_rate_a += extra_if_upgraded
            if upgraded_hut_material == "B" and huts_b_q > 0:
                blue_rate_b += extra_if_upgraded
            if upgraded_hut_material == "C" and huts_c_q > 0:
                blue_rate_c += extra_if_upgraded

        eta_blue_a = eta_hours_for_target(float(blue_rate_a), blue_def_a) if blue_def_a > 0 else 0.0
        eta_blue_b = eta_hours_for_target(float(blue_rate_b), blue_def_b) if blue_def_b > 0 else 0.0
        eta_blue_c = eta_hours_for_target(float(blue_rate_c), blue_def_c) if blue_def_c > 0 else 0.0

        s1, s2, s3 = st.columns(3)
        s1.metric("🟦 Blue A rate", f"{blue_rate_a:,}/hour")
        s2.metric("🟦 Blue B rate", f"{blue_rate_b:,}/hour")
        s3.metric("🟦 Blue C rate", f"{blue_rate_c:,}/hour")

        t1, t2, t3 = st.columns(3)
        t1.metric("ETA to refill Blue A shortfall", f"{eta_blue_a:.1f} hours")
        t2.metric("ETA to refill Blue B shortfall", f"{eta_blue_b:.1f} hours")
        t3.metric("ETA to refill Blue C shortfall", f"{eta_blue_c:.1f} hours")

        with st.expander("Unlock costs loaded (sanity check)"):
            for u in UNLOCKS:
                st.write(
                    f"**{u.id}**: "
                    + ", ".join(
                        [f"{badge(x.tier)} {x.tier} {x.material} {x.qty:,}" for x in u.spend]
                    )
                )

    # ============================================================
    # TAB 2 — PLANNER V1
    # ============================================================
    with tab_planner:
        st.header("Planner v1 — Feasibility, Roadmap, What-if + Weekly Budgets")

        # ---- Goal selection ----
        goal_choice = st.selectbox(
            "Select goal",
            [
                "Slot 9 unlock (🟠 Orange 50k each A/B/C)",
                "Unlock Purple r4 (🟠 Orange 54k each A/B/C)",
                "Chest target (🔴 Red 174k each A/B/C)",
            ],
            key="planner_goal_choice",
        )

        deadline_d = st.date_input(
            "Season deadline", value=date(2026, 2, 10), key="planner_deadline"
        )
        start_dt = datetime.now()
        deadline_dt = datetime.combine(deadline_d, time(23, 59, 0))

        if "Slot 9" in goal_choice:
            goal_obj = Goal(
                id="slot9_unlock",
                want=[
                    ItemQty("orange", "A", 50000),
                    ItemQty("orange", "B", 50000),
                    ItemQty("orange", "C", 50000),
                ],
            )
        elif "Purple r4" in goal_choice:
            goal_obj = Goal(
                id="unlock_purple_r4_materials",
                want=[
                    ItemQty("orange", "A", 54000),
                    ItemQty("orange", "B", 54000),
                    ItemQty("orange", "C", 54000),
                ],
            )
        else:
            goal_obj = Goal(
                id="red_chest_174k_each",
                want=[
                    ItemQty("red", "A", 174000),
                    ItemQty("red", "B", 174000),
                    ItemQty("red", "C", 174000),
                ],
            )

        # ---- Inventory ----
        st.subheader("Current inventory")
        inv_col1, inv_col2, inv_col3 = st.columns(3)

        with inv_col1:
            blue_a = st.number_input(
                "🔵 Blue A", min_value=0.0, value=55_000.0, step=100.0, key="inv_blue_a"
            )
            purple_a = st.number_input(
                "🟣 Purple A", min_value=0.0, value=135_000.0, step=100.0, key="inv_purple_a"
            )
            orange_a = st.number_input(
                "🟠 Orange A", min_value=0.0, value=200.0, step=10.0, key="inv_orange_a"
            )
            red_a = st.number_input(
                "🔴 Red A", min_value=0.0, value=0.0, step=10.0, key="inv_red_a"
            )
            yellow_a = st.number_input(
                "🟡 Yellow A", min_value=0.0, value=0.0, step=10.0, key="inv_yellow_a"
            )

        with inv_col2:
            blue_b = st.number_input(
                "🔵 Blue B", min_value=0.0, value=42_900.0, step=100.0, key="inv_blue_b"
            )
            purple_b = st.number_input(
                "🟣 Purple B", min_value=0.0, value=122_000.0, step=100.0, key="inv_purple_b"
            )
            orange_b = st.number_input(
                "🟠 Orange B", min_value=0.0, value=200.0, step=10.0, key="inv_orange_b"
            )
            red_b = st.number_input(
                "🔴 Red B", min_value=0.0, value=0.0, step=10.0, key="inv_red_b"
            )
            yellow_b = st.number_input(
                "🟡 Yellow B", min_value=0.0, value=0.0, step=10.0, key="inv_yellow_b"
            )

        with inv_col3:
            blue_c = st.number_input(
                "🔵 Blue C", min_value=0.0, value=77_000.0, step=100.0, key="inv_blue_c"
            )
            purple_c = st.number_input(
                "🟣 Purple C", min_value=0.0, value=109_000.0, step=100.0, key="inv_purple_c"
            )
            orange_c = st.number_input(
                "🟠 Orange C", min_value=0.0, value=200.0, step=10.0, key="inv_orange_c"
            )
            red_c = st.number_input(
                "🔴 Red C", min_value=0.0, value=0.0, step=10.0, key="inv_red_c"
            )
            yellow_c = st.number_input(
                "🟡 Yellow C", min_value=0.0, value=0.0, step=10.0, key="inv_yellow_c"
            )

        inventory = {
            ("blue", "A"): float(blue_a),
            ("blue", "B"): float(blue_b),
            ("blue", "C"): float(blue_c),
            ("purple", "A"): float(purple_a),
            ("purple", "B"): float(purple_b),
            ("purple", "C"): float(purple_c),
            ("orange", "A"): float(orange_a),
            ("orange", "B"): float(orange_b),
            ("orange", "C"): float(orange_c),
            ("red", "A"): float(red_a),
            ("red", "B"): float(red_b),
            ("red", "C"): float(red_c),
            ("yellow", "A"): float(yellow_a),
            ("yellow", "B"): float(yellow_b),
            ("yellow", "C"): float(yellow_c),
        }

        # ---- Buildings ----
        st.subheader("Buildings (current or what-if)")
        b1, b2 = st.columns(2)
        with b1:
            num_huts = st.number_input(
                "Herbalist huts", min_value=0, value=5, step=1, key="planner_num_huts"
            )
            hut_level = st.selectbox("Hut level", [3, 4, 5, 6], index=0, key="planner_hut_level")
        with b2:
            num_shops = st.number_input(
                "Transmutation shops", min_value=0, value=3, step=1, key="planner_num_shops"
            )
            shop_level = st.selectbox("Shop level", [3, 4, 5, 6], index=0, key="planner_shop_level")

        st.caption("Hut split must sum to number of huts.")
        s1, s2, s3 = st.columns(3)
        with s1:
            huts_a = st.number_input(
                "Huts producing Blue A", min_value=0, value=2, step=1, key="planner_huts_a"
            )
        with s2:
            huts_b = st.number_input(
                "Huts producing Blue B", min_value=0, value=2, step=1, key="planner_huts_b"
            )
        with s3:
            huts_c = st.number_input(
                "Huts producing Blue C", min_value=0, value=1, step=1, key="planner_huts_c"
            )

        if huts_a + huts_b + huts_c != num_huts:
            st.warning("⚠️ Hut split does not match total huts. Fix for accurate results.")

        # ---- Unlock state + roadmap ----
        st.subheader("Unlocks")
        unlock_ids = [u.id for u in UNLOCKS]

        already_unlocked = st.multiselect(
            "Already unlocked",
            options=unlock_ids,
            default=[],
            key="planner_already_unlocked",
        )
        already_unlocked_set: set[str] = set(already_unlocked)

        st.caption(
            "Roadmap: enter unlock IDs in order (one per line). Leave empty for no new unlocks."
        )
        unlock_order_text = st.text_area("Unlock sequence", value="", key="planner_unlock_sequence")
        unlock_sequence = [line.strip() for line in unlock_order_text.splitlines() if line.strip()]

        # ---- Haste coins ----
        st.subheader("Haste coins (current rules)")
        st.caption(
            "Default is 120 coins per 1 hour. We’ll make shop pro-rata smarter in a later version."
        )

        c1, c2, c3 = st.columns(3)
        with c1:
            hut_hours_instant = st.number_input(
                "Instant hut hours to claim now",
                min_value=0.0,
                value=0.0,
                step=1.0,
                key="planner_hut_hours_instant",
            )
        with c2:
            shop_jobs_instant = st.number_input(
                "Instant shop jobs (finish next N queued jobs)",
                min_value=0,
                value=0,
                step=1,
                key="planner_shop_jobs_instant",
            )
        with c3:
            haste_coins_per_hour = st.number_input(
                "Coins per hour (default 120)",
                min_value=0.0,
                value=120.0,
                step=10.0,
                key="planner_haste_coins_per_hour",
            )

        haste = HasteConfig(
            hut_hours_instant=float(hut_hours_instant),
            shop_jobs_instant=int(shop_jobs_instant),
            coins_per_hut_hour=float(haste_coins_per_hour) if haste_coins_per_hour > 0 else None,
            coins_per_shop_hour=float(haste_coins_per_hour) if haste_coins_per_hour > 0 else None,
        )

        cfg = PlannerConfig(
            start=start_dt,
            deadline=deadline_dt,
            num_huts=int(num_huts),
            hut_level=int(hut_level),
            hut_split={"A": int(huts_a), "B": int(huts_b), "C": int(huts_c)},
            num_shops=int(num_shops),
            shop_level=int(shop_level),
            unlocked_unlocks=already_unlocked_set,
            unlock_sequence=list(unlock_sequence),
            haste=haste,
        )

        # ---- Run / Clear ----
        run_col, clear_col = st.columns([1, 1])
        with run_col:
            run_clicked = st.button("Run planner", key="planner_run_btn")
        with clear_col:
            clear_clicked = st.button("Clear results", key="planner_clear_btn")

        if clear_clicked:
            st.session_state.pop("planner_res", None)

        if run_clicked:
            planner = PlannerV1(recipes=RECIPES, unlocks=UNLOCKS)
            st.session_state["planner_res"] = planner.run(
                cfg=cfg, inventory=inventory, goal=goal_obj
            )

        res = st.session_state.get("planner_res")

        if res is None:
            st.info("Click **Run planner** to generate results.")
            return

        # ---- Results ----
        st.subheader("Result")
        if res.feasible:
            st.success(
                f"✅ Goal achievable. ETA: {res.hours_needed:.1f} hours. Finish: {res.finished_at}"
            )
            slack = res.hours_available - float(res.hours_needed or 0.0)
            st.write(f"Slack before deadline: **{slack:.1f} hours**")
        else:
            st.error("❌ Goal NOT achievable by the deadline with the current scenario/roadmap.")

        if res.coins_estimate:
            st.subheader("Haste coins estimate")
            st.write(res.coins_estimate)

        st.subheader("Roadmap / milestones")
        rows = [
            {
                "Milestone": m.name,
                "Reached at": str(m.reached_at),
                "Hours from start": round(m.hours_from_start, 2),
                "Details": m.details,
            }
            for m in res.milestones
        ]
        st.dataframe(rows, use_container_width=True)

        # ============================================================
        # Weekly budgets (coins/supplies)
        # ============================================================
        st.subheader("Weekly forecast (coins/supplies budgets)")

        eco1, eco2, eco3 = st.columns(3)
        with eco1:
            start_coins = st.number_input(
                "Current coins", min_value=0.0, value=1690.0, step=50.0, key="eco_start_coins"
            )
            weekly_coins = st.number_input(
                "Coins earned every Sunday",
                min_value=0.0,
                value=10000.0,
                step=500.0,
                key="eco_weekly_coins",
            )
        with eco2:
            start_supplies = st.number_input(
                "Current camp supplies",
                min_value=0.0,
                value=360.0,
                step=10.0,
                key="eco_start_supplies",
            )
            weekly_supplies = st.number_input(
                "Camp supplies earned every Sunday",
                min_value=0.0,
                value=400.0,
                step=50.0,
                key="eco_weekly_supplies",
            )
        with eco3:
            econ_coins_per_hour = st.number_input(
                "Coins per 1 hour haste",
                min_value=0.0,
                value=120.0,
                step=10.0,
                key="eco_coins_per_hour",
            )
            pro_rata_factor = st.slider(
                "Shop pro-rata factor (1.0 worst-case, 0.5 assume half time already passed)",
                min_value=0.25,
                max_value=1.0,
                value=1.0,
                step=0.05,
                key="eco_prorata",
            )

        # Compute simulated end
        sim_end = res.finished_at if res.finished_at is not None else res.milestones[-1].reached_at
        late_hours = max(0.0, (sim_end - deadline_dt).total_seconds() / 3600.0)

        st.write(f"Simulated end: **{sim_end}**")
        st.write(f"Late by: **{late_hours:.1f} hours** (≈ {late_hours/24:.1f} days)")

        # Coins needed to eliminate lateness (rough)
        coins_needed = late_hours * float(econ_coins_per_hour) * float(pro_rata_factor)
        st.write(
            f"Estimated coins needed to finish by deadline (rough): **{coins_needed:,.0f} coins**"
        )

        sundays = list_sundays(start_dt, deadline_dt)

        week_rows: list[dict[str, object]] = []
        for i, wk in enumerate(sundays, start=1):
            coins_balance = start_coins + i * weekly_coins
            supplies_balance = start_supplies + i * weekly_supplies

            week_rows.append(
                {
                    "Sunday": wk.strftime("%Y-%m-%d"),
                    "Coins balance": round(coins_balance, 0),
                    "Supplies balance": round(supplies_balance, 0),
                    "Coins needed (deadline)": round(coins_needed, 0),
                    "Coin shortfall vs THIS week": round(max(0.0, coins_needed - coins_balance), 0),
                }
            )

        st.dataframe(week_rows, use_container_width=True)

        coins_available_by_deadline = start_coins + len(sundays) * weekly_coins
        shortfall_deadline = max(0.0, coins_needed - coins_available_by_deadline)

        st.subheader("Purchase recommendation (if needed)")
        st.write(
            f"Coins available by deadline (weekly income): **{coins_available_by_deadline:,.0f}**"
        )
        st.write(f"Coin shortfall by deadline: **{shortfall_deadline:,.0f}**")
        st.json(pack_plan_for_coins(shortfall_deadline))


if __name__ == "__main__":
    main()
