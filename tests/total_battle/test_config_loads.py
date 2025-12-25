from pathlib import Path

from portfolio_starter.total_battle.config_io import load_building_levels, load_recipes_and_unlocks


def test_configs_load() -> None:
    root = Path(__file__).resolve().parents[2]
    recipes_path = root / "projects" / "total_battle_research_camp" / "data" / "recipes.v0.json"
    buildings_path = root / "projects" / "total_battle_research_camp" / "data" / "buildings.v0.json"

    recipes, unlocks = load_recipes_and_unlocks(recipes_path)
    b = load_building_levels(buildings_path)

    assert len(recipes) > 0
    assert len(unlocks) > 0
    assert 3 in b["shop"]
    assert 3 in b["hut"]
