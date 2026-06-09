import sys, unittest.mock as mock
sys.modules['streamlit'] = mock.MagicMock()

from app import (
    load_recipe_database, estimate_targets, filter_recipes,
    _adjusted_recipe_cost, match_available_ingredients, score_recipe_for_meal,
    RECIPES_PATH
)

recipes, err = load_recipe_database(RECIPES_PATH)
preferred = ["chicken", "eggs", "rice", "oats", "banana"]
available = ["rice", "eggs", "oats", "banana"]
disliked = ["sardines"]

filtered, _ = filter_recipes(recipes, "Bulk", "Very busy", "lunch", disliked, [])
budget_per_meal = 62.5
protein_counts = {}

print("=== TOP 10 LUNCH CANDIDATES (scored) ===")
scored = []
for _, row in filtered.iterrows():
    adj_cost, missing = _adjusted_recipe_cost(row, available)
    ing_match = match_available_ingredients(row, available)
    pts = score_recipe_for_meal(
        row, meal_type="lunch", goal="Bulk", cooking_time="Very busy",
        preferred=preferred, disliked=disliked, allergies=[],
        available=available, adj_cost=adj_cost, budget_per_meal=budget_per_meal,
        ing_match=ing_match, protein_counts=protein_counts
    )
    scored.append((pts, str(row["recipe_name"]), adj_cost, ing_match["match_ratio"],
                   str(row.get("main_ingredients", ""))))

scored.sort(reverse=True)
for pts, name, cost, ratio, ings in scored[:12]:
    print(f"  {pts:6.1f}  {name:<40s}  ratio={ratio:.2f}  ings={ings[:50]}")
