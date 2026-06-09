"""
FitFuel AI — Smoke Tests
Covers:
  - TC1: Meal plan quality (Filipino dishes, diversity, no generics)
  - TC4: NL ingredients regex (must not fire on plain "I have a 200 budget")
  - TC5: Desired item regex (longest-first alternation: "I want to have meat" → meat)
  - Parser edge cases: all 8 specified scenarios
"""

import sys
import unittest.mock as mock

sys.modules["streamlit"] = mock.MagicMock()

from app import (
    load_recipe_database,
    generate_meal_plan,
    estimate_targets,
    parse_natural_language_request,
    parse_quantity_food,
    RECIPES_PATH,
    KNOWN_FILIPINO_DISH_KEYWORDS,
)

# ---------------------------------------------------------------------------
# TC1: Meal plan quality check
# ---------------------------------------------------------------------------
recipes, err = load_recipe_database(RECIPES_PATH)
print("Recipes loaded:", len(recipes), "| Error:", err)

targets = estimate_targets(65, "Bulk")
preferred = ["chicken", "eggs", "rice", "oats", "banana"]
available = ["rice", "eggs", "oats", "banana"]
disliked = ["sardines"]

plan, summary, decisions = generate_meal_plan(
    recipes, targets, 250, 4, "Bulk", "Very busy", "Afternoon",
    preferred, disliked, [], available
)

print()
print("=== TC1: MEAL PLAN QUALITY CHECK ===")
for meal in plan:
    print(f"\n{meal['meal_name']:10s} -> {meal['suggestion']}")
    print(f"  Reason : {meal['reason']}")
    print(f"  Missing: {meal['missing_ingredients']}")

chicken_count = sum(1 for m in plan if "chicken" in m["suggestion"].lower())
generic_names = [
    "egg rice meal", "simple chicken rice meal", "chicken and rice bowl",
    "boiled egg and rice", "scrambled egg rice bowl", "rice and egg bowl",
]
generic_count = sum(1 for m in plan if m["suggestion"].lower() in generic_names)
filipino_count = sum(
    1 for m in plan
    if any(k in m["suggestion"].lower() for k in KNOWN_FILIPINO_DISH_KEYWORDS)
)

print("\n--- Quality results ---")
print(f"Chicken meals : {chicken_count}/4", "PASS" if chicken_count <= 2 else "FAIL - too many chicken")
print(f"Generic fallbacks: {generic_count}/4", "PASS" if generic_count <= 1 else "WARN - too many generics")
print(f"Filipino dishes  : {filipino_count}/4", "PASS" if filipino_count >= 2 else "WARN - few Filipino dishes")

# ---------------------------------------------------------------------------
# TC4 & TC5: Parser unit tests
# ---------------------------------------------------------------------------
PASS = "PASS"
FAIL = "FAIL"

def check(label, condition):
    status = PASS if condition else FAIL
    print(f"  [{status}] {label}")
    return condition

all_pass = True

print()
print("=== TC4 / TC5: NL PARSER UNIT TESTS ===")

# --- Test 1: Full combined TC4+TC5 prompt ---
print()
print("Test 1: Full TC4+TC5 combined prompt")
t1 = (
    "I have a 200 budget for 1 day, and I have to eat breakfast and lunch. "
    "What I currently have right now is rice, eggs, tomatoes, onions, and garlic. "
    "But I want to have meat and currently meat's price in the market is 75 for 1/2 kilo. "
    "Can you help me with my meal plan?"
)
r1 = parse_natural_language_request(t1)
all_pass &= check("budget == 200",          r1.get("budget_php") == 200.0)
all_pass &= check("meals_count == 2",       r1.get("meals_count") == 2)
all_pass &= check("breakfast in meal_types", "breakfast" in (r1.get("meal_types") or []))
all_pass &= check("lunch in meal_types",     "lunch" in (r1.get("meal_types") or []))
avail = r1.get("available_ingredients", [])
all_pass &= check("rice in available",      "rice" in avail)
all_pass &= check("eggs in available",      "eggs" in avail)
all_pass &= check("tomatoes in available",  "tomatoes" in avail)
all_pass &= check("onions in available",    "onions" in avail)
all_pass &= check("garlic in available",    "garlic" in avail)
all_pass &= check("desired_item == 'meat'", r1.get("desired_item") == "meat")
all_pass &= check("desired_item_price == 75", r1.get("desired_item_price_php") == 75.0)
# Budget sentence must NOT bleed into available_ingredients
all_pass &= check("'budget' not in available_ingredients",
                  not any("budget" in x for x in avail))
all_pass &= check("'a 200' not in available_ingredients",
                  not any("200" in x for x in avail))

# --- Test 2: "I want to have meat" ---
print()
print("Test 2: 'I want to have meat'")
r2 = parse_natural_language_request("I want to have meat")
all_pass &= check("desired_item == 'meat'", r2.get("desired_item") == "meat")

# --- Test 3: "I want to buy meat" ---
print()
print("Test 3: 'I want to buy meat'")
r3 = parse_natural_language_request("I want to buy meat")
all_pass &= check("desired_item == 'meat'", r3.get("desired_item") == "meat")

# --- Test 4: "I want meat" ---
print()
print("Test 4: 'I want meat'")
r4 = parse_natural_language_request("I want meat")
all_pass &= check("desired_item == 'meat'", r4.get("desired_item") == "meat")

# --- Test 5: "I need meat" ---
print()
print("Test 5: 'I need meat'")
r5 = parse_natural_language_request("I need meat")
all_pass &= check("desired_item == 'meat'", r5.get("desired_item") == "meat")

# --- Test 6: "meat costs 75" ---
print()
print("Test 6: 'meat costs 75'")
r6 = parse_natural_language_request("meat costs 75")
all_pass &= check("desired_item_price == 75", r6.get("desired_item_price_php") == 75.0)

# --- Test 7: "currently have rice, eggs, tomatoes, onions, garlic" ---
print()
print("Test 7: 'currently have rice, eggs, tomatoes, onions, garlic'")
r7 = parse_natural_language_request("currently have rice, eggs, tomatoes, onions, garlic")
avail7 = r7.get("available_ingredients", [])
all_pass &= check("rice in available",     "rice" in avail7)
all_pass &= check("eggs in available",     "eggs" in avail7)
all_pass &= check("tomatoes in available", "tomatoes" in avail7)
all_pass &= check("onions in available",   "onions" in avail7)
all_pass &= check("garlic in available",   "garlic" in avail7)

# --- Test 8: "I have a 200 budget" must NOT parse as ingredients ---
print()
print("Test 8: 'I have a 200 budget' — must NOT produce available_ingredients")
r8 = parse_natural_language_request("I have a 200 budget")
avail8 = r8.get("available_ingredients", [])
all_pass &= check("No available_ingredients extracted", not avail8)
all_pass &= check("budget == 200", r8.get("budget_php") == 200.0)

# --- Summary ---
print()
print("=== PARSER TEST SUMMARY ===")
print("Overall:", PASS if all_pass else FAIL)

# ---------------------------------------------------------------------------
# FOOD LOG PARSER (parse_quantity_food) TESTS
# ---------------------------------------------------------------------------
print()
print("=== FOOD LOG PARSER TESTS ===")

food_log_pass = True

# Test FL1: "2 eggs, 1 cup rice, 1 banana"
print()
print("Test FL1: '2 eggs, 1 cup rice, 1 banana'")
fl1 = parse_quantity_food("2 eggs, 1 cup rice, 1 banana")
fl1_foods = {f: q for f, q in fl1}
food_log_pass &= check("eggs with qty 2",    fl1_foods.get("eggs") == 2.0)
food_log_pass &= check("rice with qty 1",    fl1_foods.get("rice") == 1.0)
food_log_pass &= check("banana with qty 1",  fl1_foods.get("banana") == 1.0)
food_log_pass &= check("'cup rice' NOT in results", "cup rice" not in fl1_foods)

# Test FL2: "1 cup of rice"
print()
print("Test FL2: '1 cup of rice'")
fl2 = parse_quantity_food("1 cup of rice")
fl2_foods = {f: q for f, q in fl2}
food_log_pass &= check("rice with qty 1",    fl2_foods.get("rice") == 1.0)
food_log_pass &= check("'cup of rice' NOT in results", "cup of rice" not in fl2_foods)

# Test FL3: "2 pcs egg"
print()
print("Test FL3: '2 pcs egg'")
fl3 = parse_quantity_food("2 pcs egg")
fl3_foods = {f: q for f, q in fl3}
food_log_pass &= check("egg with qty 2",     fl3_foods.get("egg") == 2.0)
food_log_pass &= check("'pcs egg' NOT in results", "pcs egg" not in fl3_foods)

# Test FL4: "1/2 cup oats"
print()
print("Test FL4: '1/2 cup oats'")
fl4 = parse_quantity_food("1/2 cup oats")
fl4_foods = {f: q for f, q in fl4}
food_log_pass &= check("oats with qty 0.5",  fl4_foods.get("oats") == 0.5)
food_log_pass &= check("'cup oats' NOT in results", "cup oats" not in fl4_foods)

# Test FL5: "1 serving chicken adobo"
print()
print("Test FL5: '1 serving chicken adobo'")
fl5 = parse_quantity_food("1 serving chicken adobo")
fl5_foods = {f: q for f, q in fl5}
food_log_pass &= check("'chicken adobo' with qty 1", fl5_foods.get("chicken adobo") == 1.0)
food_log_pass &= check("'serving chicken adobo' NOT in results", "serving chicken adobo" not in fl5_foods)

# Test FL6: "100 grams chicken"
print()
print("Test FL6: '100 grams chicken'")
fl6 = parse_quantity_food("100 grams chicken")
fl6_foods = {f: q for f, q in fl6}
food_log_pass &= check("'chicken' with qty 100", fl6_foods.get("chicken") == 100.0)
food_log_pass &= check("'grams chicken' NOT in results", "grams chicken" not in fl6_foods)

# Test FL7: "1 bowl oatmeal"
print()
print("Test FL7: '1 bowl oatmeal'")
fl7 = parse_quantity_food("1 bowl oatmeal")
fl7_foods = {f: q for f, q in fl7}
food_log_pass &= check("'oatmeal' with qty 1", fl7_foods.get("oatmeal") == 1.0)

# Test FL8: "1 can tuna, 1 plate rice"
print()
print("Test FL8: '1 can tuna, 1 plate rice'")
fl8 = parse_quantity_food("1 can tuna, 1 plate rice")
fl8_foods = {f: q for f, q in fl8}
food_log_pass &= check("'tuna' with qty 1",  fl8_foods.get("tuna") == 1.0)
food_log_pass &= check("'rice' with qty 1",  fl8_foods.get("rice") == 1.0)

# Test FL9: "2 pieces eggs"
print()
print("Test FL9: '2 pieces eggs'")
fl9 = parse_quantity_food("2 pieces eggs")
fl9_foods = {f: q for f, q in fl9}
food_log_pass &= check("'eggs' with qty 2",  fl9_foods.get("eggs") == 2.0)
food_log_pass &= check("'pieces eggs' NOT in results", "pieces eggs" not in fl9_foods)

print()
print("=== FOOD LOG PARSER TEST SUMMARY ===")
print("Overall:", PASS if food_log_pass else FAIL)

# ---------------------------------------------------------------------------
# COMBINED FINAL SUMMARY
# ---------------------------------------------------------------------------
print()
print("=== ALL TESTS FINAL SUMMARY ===")
overall = all_pass and food_log_pass
print("Overall:", PASS if overall else FAIL)

