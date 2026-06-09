"""
FitFuel AI: A Budget-Friendly Filipino Meal Planning and Nutrition Tracking Agent
for Busy Beginners

This Streamlit app demonstrates agentic behavior:
- planning (multi-step workflow)
- tool/data usage (CSV datasets)
- decision rules (goal, budget, restrictions, cooking time, workout time)
- session memory (food logging with session_state)
- external API usage (Google Gemini) with strict fallback and validation

Source of truth for nutrition + cost is the CSV datasets and Python calculations.
Gemini is only used for short natural-language explanations of already-calculated results.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from typing import Any, Optional

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

try:
    from google import genai as _genai_module
    _genai_module_available = True
except Exception:
    _genai_module = None
    _genai_module_available = False
# Keep a module-level alias used in the rest of the file for the availability check
genai = _genai_module


# ---------------------------------------------------------------------------
# Page configuration and theme
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="FitFuel AI",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)


def apply_custom_css() -> None:
    st.markdown(
        """
<style>
/* App background */
.stApp {
  background: #111820;
  color: #F5F7FA;
}

/* Sidebar */
section[data-testid="stSidebar"] {
  background: #151C24;
  border-right: 1px solid #2D3A46;
}

/* Headings */
h1, h2, h3, h4, h5, h6 {
  color: #F5F7FA;
  letter-spacing: 0.2px;
}

/* Text */
p, li, label, .stMarkdown {
  color: #F5F7FA;
}
.muted, .stCaption, small {
  color: #AAB4C0 !important;
}

/* Inputs */
div[data-baseweb="input"] > div,
div[data-baseweb="textarea"] > div,
div[data-baseweb="select"] > div {
  background: #1B2430 !important;
  border: 1px solid #2D3A46 !important;
  border-radius: 12px !important;
}

/* Buttons */
.stButton > button {
  background: #F25A2C;
  border: 1px solid #F25A2C;
  color: #F5F7FA;
  border-radius: 12px;
  padding: 0.55rem 0.85rem;
  font-weight: 600;
}
.stButton > button:hover {
  background: #FF7A45;
  border: 1px solid #FF7A45;
}
.stButton > button[kind="secondary"] {
  background: #151C24 !important;
  border: 1px solid #2D3A46 !important;
  color: #F5F7FA !important;
}
.stButton > button[kind="secondary"]:hover {
  border-color: #F25A2C !important;
  color: #F25A2C !important;
}
div[data-testid="stVerticalBlock"] > div:has(> div > .stButton > button[kind="primary"]) {
  margin-top: 4px;
}

/* Cards */
.ff-card {
  background: #1B2430;
  border: 1px solid #2D3A46;
  border-radius: 16px;
  padding: 16px 16px;
}
.ff-card-title {
  font-size: 14px;
  color: #AAB4C0;
  margin-bottom: 6px;
}
.ff-card-value {
  font-size: 20px;
  font-weight: 700;
  color: #F5F7FA;
}
.ff-accent {
  color: #F25A2C;
}

/* Workflow step cards */
.ff-workflow-card {
  background: #1B2430;
  border: 1px solid #2D3A46;
  border-left: 3px solid #F25A2C;
  border-radius: 12px;
  padding: 14px 14px;
  margin-bottom: 12px;
  min-height: 120px;
}
.ff-workflow-title {
  font-size: 14px;
  font-weight: 700;
  color: #F25A2C;
  margin-bottom: 8px;
}
.ff-workflow-desc {
  font-size: 13px;
  color: #AAB4C0;
  line-height: 1.45;
}
.ff-rec-box {
  background: #1B2430;
  border: 1px solid #2D3A46;
  border-radius: 12px;
  padding: 16px;
  margin-top: 8px;
}
.ff-footer {
  text-align: center;
  color: #AAB4C0;
  font-size: 12px;
  padding: 20px 0 8px 0;
  border-top: 1px solid #2D3A46;
  margin-top: 24px;
}
.ff-banner {
  background: #1B2430;
  border: 1px solid #2D3A46;
  border-left: 3px solid #F25A2C;
  border-radius: 12px;
  padding: 14px 16px;
  margin-top: 12px;
  line-height: 1.5;
}
.ff-banner-title {
  font-size: 15px;
  font-weight: 700;
  color: #F5F7FA;
  margin-bottom: 6px;
}
.ff-banner-line {
  font-size: 13px;
  color: #AAB4C0;
}
.ff-banner-workflow {
  font-size: 12px;
  color: #F25A2C;
  margin: 6px 0;
  font-weight: 600;
}
.ff-chat-assistant {
  background: #151C24;
  border: 1px solid #2D3A46;
  border-radius: 12px;
  padding: 12px 14px;
  margin-top: 10px;
  font-size: 14px;
  color: #AAB4C0;
}

/* Hero */
.ff-hero {
  padding: 36px 40px;
  border-radius: 18px;
  background: linear-gradient(135deg, rgba(30, 41, 59, 0.95), rgba(15, 23, 42, 0.95));
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-left: 5px solid #ff5a2a;
  margin-bottom: 24px;
}
.ff-kicker {
  color: #ff5a2a;
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  margin-bottom: 10px;
}
.ff-title {
  font-size: clamp(2.2rem, 5vw, 3.8rem);
  line-height: 1.02;
  font-weight: 900;
  margin: 0 0 14px 0;
  color: #f8fafc;
}
.ff-title .orange {
  color: #ff5a2a;
}
.ff-subtitle {
  color: #cbd5e1;
  font-size: 1.05rem;
  margin: 0 0 10px 0;
  max-width: 950px;
}
.ff-value {
  color: #f8fafc;
  font-size: 0.98rem;
  font-weight: 650;
  margin: 0;
  max-width: 950px;
}

/* Meal / menu cards */
.ff-meal-card {
  background: #1B2430;
  border: 1px solid #2D3A46;
  border-left: 4px solid #F25A2C;
  border-radius: 14px;
  padding: 16px 18px;
  margin-bottom: 14px;
}
.ff-meal-type {
  display: inline-block;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.6px;
  text-transform: uppercase;
  color: #F25A2C;
  margin-bottom: 6px;
}
.ff-meal-title {
  font-size: 20px;
  font-weight: 700;
  color: #F5F7FA;
  margin-bottom: 12px;
  line-height: 1.3;
}
.ff-macro-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 16px;
  margin-bottom: 10px;
}
.ff-macro-pill {
  font-size: 13px;
  color: #AAB4C0;
}
.ff-macro-pill strong {
  color: #F5F7FA;
  font-weight: 600;
}
.ff-meal-reason {
  font-size: 13px;
  color: #AAB4C0;
  margin-top: 8px;
  line-height: 1.45;
}
.ff-missing {
  font-size: 13px;
  color: #F25A2C;
  margin-top: 6px;
}

/* Grocery / prep list */
.ff-grocery-item {
  background: #151C24;
  border: 1px solid #2D3A46;
  border-radius: 10px;
  padding: 12px 14px;
  margin-bottom: 8px;
}
.ff-grocery-item-title {
  font-weight: 600;
  color: #F5F7FA;
  font-size: 15px;
}
.ff-grocery-item-meta {
  font-size: 12px;
  color: #AAB4C0;
  margin-top: 4px;
}

/* Gap analysis */
.ff-gap-card {
  background: #151C24;
  border: 1px solid #2D3A46;
  border-radius: 12px;
  padding: 12px 14px;
  margin-bottom: 10px;
}
.ff-gap-label {
  font-size: 13px;
  font-weight: 600;
  color: #F5F7FA;
  margin-bottom: 4px;
}
.ff-gap-status {
  font-size: 12px;
  color: #AAB4C0;
  margin-bottom: 6px;
}
.ff-status-on { color: #7DD3A8; }
.ff-status-warn { color: #F25A2C; }

/* Section headers */
.ff-section-title {
  font-size: 18px;
  font-weight: 700;
  color: #F5F7FA;
  margin: 0 0 4px 0;
}
.ff-section-sub {
  font-size: 13px;
  color: #AAB4C0;
  margin-bottom: 12px;
}

/* Ask FitFuel panel */
.ff-ask-panel {
  background: #1B2430;
  border: 1px solid #2D3A46;
  border-radius: 16px;
  padding: 18px 18px;
  margin-top: 12px;
}

/* Tables */
div[data-testid="stDataFrame"] {
  border: 1px solid #2D3A46;
  border-radius: 16px;
  overflow: hidden;
}

/* Tabs */
button[data-baseweb="tab"] {
  color: #AAB4C0 !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
  color: #F5F7FA !important;
  border-bottom: 2px solid #F25A2C !important;
}

/* Keep footer hidden but do not hide header/sidebar controls */
footer {visibility: hidden;}
</style>
        """,
        unsafe_allow_html=True,
    )


apply_custom_css()
load_dotenv()


# ---------------------------------------------------------------------------
# Dataset paths (defaults; override only when DEBUG_MODE is True)
# ---------------------------------------------------------------------------
RECIPES_PATH = os.path.join(os.path.dirname(__file__), "data", "filipino_recipes_100_dataset.csv")
CLEAN_FOODS_PATH = os.path.join(os.path.dirname(__file__), "data", "fitfuel_clean_daily_food_nutrition_dataset.csv")
CURATED_FOODS_PATH = os.path.join(os.path.dirname(__file__), "food_database.csv")

# Set True only for local development diagnostics (dataset paths, API debug).
DEBUG_MODE = False

GOAL_OPTIONS = ["Bulk", "Cut", "Maintain", "Beginner Recomposition"]
MEAL_COUNT_OPTIONS = [2, 3, 4, 5]
COOKING_TIME_OPTIONS = ["Very busy", "Moderate", "Flexible"]
WORKOUT_TIME_OPTIONS = ["Morning", "Afternoon", "Evening", "No fixed time"]

PROTEIN_MULTIPLIERS = {
    "Bulk": 2.0,
    "Cut": 2.2,
    "Maintain": 1.8,
    "Beginner Recomposition": 2.0,
}

MAX_INGREDIENTS_BY_COOKING = {
    "Very busy": 6,
    "Moderate": 10,
    "Flexible": 20,
}

VAGUE_INGREDIENT_PHRASES = (
    "traditional filipino ingredients",
    "traditional filipino ingredient",
    "viand",
    "assorted ingredients",
    "various ingredients",
    "mixed ingredients",
)

FISH_SEAFOOD_TERMS = (
    "bangus", "fish", "squid", "tuyo", "danggit", "sardine", "sardines", "shrimp",
    "crab", "seafood", "tilapia", "galunggong", "hipon", "pusit", "dilis",
)

QUICK_MEAL_KEYWORDS = (
    "silog", "sinangag", "fried rice", "garlic rice", "egg", "eggs", "oats", "oatmeal",
    "banana", "chicken rice", "tapa", "longganisa",
)


MEAL_SLOTS = {
    2: [("Meal 1", "breakfast"), ("Meal 2", "lunch")],
    3: [("Breakfast", "breakfast"), ("Lunch", "lunch"), ("Dinner", "dinner")],
    4: [("Breakfast", "breakfast"), ("Lunch", "lunch"), ("Snack", "snack"), ("Dinner", "dinner")],
    5: [("Breakfast", "breakfast"), ("Snack 1", "snack"), ("Lunch", "lunch"), ("Snack 2", "snack"), ("Dinner", "dinner")],
}


# ---------------------------------------------------------------------------
# Utility parsing / cleaning
# ---------------------------------------------------------------------------
def clean_text_input(text: str) -> str:
    if text is None:
        return ""
    return re.sub(r"\s+", " ", str(text)).strip()


def parse_list_input(text: str) -> list[str]:
    if not text or not str(text).strip():
        return []
    items = re.split(r"[,;\n]+", str(text))
    return [clean_text_input(item).lower() for item in items if clean_text_input(item)]


# Common serving/unit words to strip from food log entries before matching.
_UNIT_WORDS = {
    "cup", "cups", "pc", "pcs", "piece", "pieces",
    "serving", "servings", "slice", "slices",
    "tbsp", "tablespoon", "tablespoons", "tsp", "teaspoon", "teaspoons",
    "g", "gram", "grams", "kg", "kilo", "kilos",
    "can", "cans", "bowl", "bowls", "plate", "plates",
    "pack", "packs", "medium", "large", "small",
}


def parse_quantity_food(text: str) -> list[tuple[str, float]]:
    """Parse free-text food log input into (food_name, quantity) tuples.

    Handles:
    - Comma / semicolon / newline separation
    - Whole numbers, decimals, and fractions (e.g. 1/2)
    - Unit words (cup, pcs, grams, …) stripped before the food name
    - The word "of" after a unit word (e.g. "1 cup of rice" → "rice")
    """
    if not text or not str(text).strip():
        return []
    results: list[tuple[str, float]] = []
    parts = re.split(r"[,;\n]+", str(text))
    for part in parts:
        part = clean_text_input(part).lower()
        if not part:
            continue
        # Match a leading quantity: integer, decimal, or fraction (e.g. 1/2)
        match = re.match(
            r"^(\d+(?:\.\d+)?(?:\s*/\s*\d+)?|\d+/\d+)\s+(.+)$", part
        )
        if match:
            qty_str = match.group(1).strip()
            # Evaluate fraction like "1/2"
            if "/" in qty_str:
                num, denom = qty_str.split("/", 1)
                try:
                    qty = float(num.strip()) / float(denom.strip())
                except (ValueError, ZeroDivisionError):
                    qty = 1.0
            else:
                qty = float(qty_str)
            food = clean_text_input(match.group(2))
        else:
            qty = 1.0
            food = part

        # Strip leading unit words and optional "of"
        words = food.split()
        while words and words[0] in _UNIT_WORDS:
            words.pop(0)
            # Also strip "of" that may follow a unit word (e.g. "cup of rice")
            if words and words[0] == "of":
                words.pop(0)
        food = " ".join(words).strip() if words else food

        if food:
            results.append((food, qty))
    return results


def parse_natural_language_request(text: str) -> dict[str, Any]:
    """
    Heuristic extractor for messy natural-language requests.
    Extracts: budget_php, meals_count, meal_types, available_ingredients, desired_item, desired_item_price_php.
    """
    text = clean_text_input(text).lower()
    if not text:
        return {}

    out: dict[str, Any] = {}

    # Budget patterns: "200 budget", "budget for 1 day is 200", "₱200"
    budget_match = re.search(r"(?:₱\s*)?(\d{2,5})(?:\s*php)?\s*(?:budget|pesos|₱)?", text)
    if budget_match:
        out["budget_php"] = float(budget_match.group(1))

    # Meal mentions (breakfast/lunch/dinner/snack)
    meal_words = ["breakfast", "lunch", "dinner", "snack"]
    mentioned = [mw for mw in meal_words if re.search(rf"\b{mw}\b", text)]
    if mentioned:
        out["meal_types"] = mentioned
        out["meals_count"] = len(mentioned)

    # Available ingredients — TC4 fix:
    # Only fire on specific ownership phrases; plain "i have" is excluded because
    # it also appears in budget sentences like "I have a 200 budget".
    have_match = re.search(
        r"(?:"
        r"what i currently have right now is"
        r"|what i currently have"
        r"|i currently have"
        r"|currently have"
        r"|available ingredients are"
        r"|ingredients are"
        r"|what i have available is"
        r"|i have available"
        r")\s+(.*?)(?:\.|but i|and i|$)",
        text,
    )
    if have_match:
        raw = have_match.group(1)
        # Remove filler phrases and "and"
        raw = re.sub(r"(right now|at home|with me|available|\band\b)", "", raw).strip()
        out["available_ingredients"] = parse_list_input(raw)

    # Desired item — TC5 fix:
    # Longest phrase first so "i want to have" and "i want to buy" match before plain "i want".
    desired_item_match = re.search(
        r"\b(i want to have|i want to buy|i want|i need)\s+(.*?)\b(?:and|but|\.|$)",
        text,
    )
    if desired_item_match:
        item = clean_text_input(desired_item_match.group(2))
        # Keep only first word (strip leftover function words like "to buy")
        words = [w for w in item.split() if w not in ("to", "buy", "have", "get", "a", "an", "the", "some")]
        out["desired_item"] = words[0] if words else item.split()[0] if item else ""

    # Price: "75 for 1/2 kilo" or "75/half kilo"
    price_match = re.search(
        r"(\d{2,5})\s*(?:php|₱)?\s*(?:for|/)\s*(?:a\s*)?(1\/2|half)\s*(?:kilo|kg)",
        text,
    )
    if price_match:
        out["desired_item_price_php"] = float(price_match.group(1))
        out["desired_item_unit"] = "1/2 kilo"

    # Named-item price: "meat's price in the market is 75" / "meat costs 75" / "meat price is 75"
    named_price_match = re.search(
        r"(\w+)(?:'s)?\s*(?:price in the market|price|costs)\s*(?:is\s*)?(?:₱\s*)?(\d{2,5})",
        text,
    )
    if named_price_match and "desired_item_price_php" not in out:
        out["desired_item_price_php"] = float(named_price_match.group(2))
        if "desired_item" not in out:
            out["desired_item"] = named_price_match.group(1)

    # Final fallback price: "costs 75" / "price is 75" / "price 75"
    price_simple = re.search(r"(?:costs|price is|price)\s*(?:₱\s*)?(\d{2,5})", text)
    if "desired_item_price_php" not in out and price_simple:
        out["desired_item_price_php"] = float(price_simple.group(1))

    # Quick-meal intent detection
    quick_meal_phrases = [
        "very busy", "busy", "no time", "quick meals", "quick meal", "easy meals", "easy meal",
        "simple meals", "simple meal", "low prep", "low-prep", "fast meals", "fast meal",
        "quick to cook", "easy to cook", "meal prep", "meal-prep", "needs quick meals",
        "need quick meals", "no time to cook"
    ]
    if any(phrase in text for phrase in quick_meal_phrases):
        out["prefers_quick_meals"] = True

    return out


def build_nl_assistant_confirmation(
    nl_extracted: dict[str, Any],
    *,
    effective_budget: float,
    effective_meals: int,
    effective_available: list[str],
    desired_item: str | None,
    desired_item_price: float | None,
    original_budget: float | None,
) -> str:
    """User-friendly assistant confirmation after local NL parsing (no Gemini)."""
    found: list[str] = []
    if original_budget is not None:
        found.append(f"a ₱{original_budget:.0f} budget")
    elif nl_extracted.get("budget_php") is not None:
        found.append(f"a ₱{float(nl_extracted['budget_php']):.0f} budget")

    if effective_meals:
        found.append(f"{effective_meals} meal{'s' if effective_meals != 1 else ''}")

    if effective_available:
        found.append("available ingredients")

    if desired_item_price is not None:
        item_label = desired_item or "a market item"
        found.append(f"{item_label} worth ₱{desired_item_price:.0f}")

    prefers_quick_meals = nl_extracted.get("prefers_quick_meals", False)

    if not found and prefers_quick_meals:
        return "Got it. I detected that you are very busy and need quick meals. I’ll prioritize simple meals, available ingredients, and low-prep options."

    if not found:
        return None

    summary = ", ".join(found)
    msg = f"Got it. I found {summary}."

    if prefers_quick_meals:
        if desired_item_price is not None and original_budget is not None:
            msg += f" I also detected that you need quick meals, so I’ll prioritize simple low-prep options within the remaining ₱{effective_budget:.0f}."
        else:
            msg += " I also detected that you need quick meals, so I’ll prioritize simple low-prep options."
    else:
        if desired_item_price is not None and original_budget is not None:
            msg += (
                f" I'll treat your current ingredients as already owned and plan around "
                f"the remaining ₱{effective_budget:.0f}."
            )
        elif effective_available:
            msg += " I'll treat your current ingredients as already owned when planning meals."

    return msg


def recommendation_type_label(source: str | None) -> str:
    if source == "Gemini-enhanced":
        return "Enhanced"
    return "Standard"


def prepare_display_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Streamlit uses PyArrow under the hood; mixed-type columns can crash rendering.
    This helper creates a display-only copy and forces known mixed columns to string.
    """
    display_df = df.copy()
    mixed_cols = [
        "Target",
        "Status",
        "Notes",
        "Recommendation",
        "Target Range",
        "Actual",
        "Gap",
        "Reason",
        "Missing Ingredients",
    ]
    for col in mixed_cols:
        if col in display_df.columns:
            display_df[col] = display_df[col].astype(str)
    return display_df


# ---------------------------------------------------------------------------
# Dataset loading (tools)
# ---------------------------------------------------------------------------
def _safe_read_csv(path: str) -> tuple[pd.DataFrame, Optional[str]]:
    path = clean_text_input(path)
    if not path:
        return pd.DataFrame(), "No path provided."
    try:
        df = pd.read_csv(path)
        return df, None
    except FileNotFoundError:
        return pd.DataFrame(), f"File not found: {path}"
    except Exception as e:
        return pd.DataFrame(), f"Could not read CSV: {path}. Error: {e}"


def _empty_recipe_df() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "recipe_name",
            "serving_size",
            "calories",
            "protein_g",
            "carbs_g",
            "fats_g",
            "fiber_g",
            "estimated_cost_php",
            "main_ingredients",
            "meal_type",
            "recipe_name_lower",
            "meal_type_lower",
            "ingredients_lower",
        ]
    )


def _empty_clean_food_df() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "food_name",
            "category",
            "calories",
            "protein_g",
            "carbs_g",
            "fats_g",
            "fiber_g",
            "sugars_g",
            "sodium_mg",
            "cholesterol_mg",
            "meal_type",
            "water_intake_ml",
            "food_name_lower",
            "meal_type_lower",
            "category_lower",
        ]
    )


def _empty_curated_food_df() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "food_name",
            "category",
            "serving_size",
            "calories",
            "protein_g",
            "carbs_g",
            "fats_g",
            "fiber_g",
            "estimated_cost_php",
            "prep_time_minutes",
            "meal_type",
            "notes",
            "food_name_lower",
        ]
    )


def load_recipe_database(path: str) -> tuple[pd.DataFrame, Optional[str]]:
    df, err = _safe_read_csv(path)
    if df.empty:
        return _empty_recipe_df(), err
    required = {
        "recipe_name",
        "serving_size",
        "calories",
        "protein_g",
        "carbs_g",
        "fats_g",
        "fiber_g",
        "estimated_cost_php",
        "main_ingredients",
        "meal_type",
    }
    missing = required - set(df.columns)
    if missing:
        return _empty_recipe_df(), f"Recipe dataset missing columns: {', '.join(sorted(missing))}"
    df = df.copy()
    df["recipe_name_lower"] = df["recipe_name"].astype(str).str.lower()
    df["meal_type_lower"] = df["meal_type"].astype(str).str.lower()
    df["ingredients_lower"] = df["main_ingredients"].astype(str).str.lower()
    return df, None


def load_clean_food_database(path: str) -> tuple[pd.DataFrame, Optional[str]]:
    df, err = _safe_read_csv(path)
    if df.empty:
        return _empty_clean_food_df(), err
    required = {
        "food_name",
        "category",
        "calories",
        "protein_g",
        "carbs_g",
        "fats_g",
        "fiber_g",
        "sugars_g",
        "sodium_mg",
        "cholesterol_mg",
        "meal_type",
        "water_intake_ml",
    }
    missing = required - set(df.columns)
    if missing:
        return _empty_clean_food_df(), f"Clean food dataset missing columns: {', '.join(sorted(missing))}"
    df = df.copy()
    df["food_name_lower"] = df["food_name"].astype(str).str.lower()
    df["meal_type_lower"] = df["meal_type"].astype(str).str.lower()
    df["category_lower"] = df["category"].astype(str).str.lower()
    return df, None


def load_curated_food_database(path: str = CURATED_FOODS_PATH) -> tuple[pd.DataFrame, Optional[str]]:
    df, err = _safe_read_csv(path)
    if df.empty:
        return _empty_curated_food_df(), err
    required = {
        "food_name",
        "category",
        "serving_size",
        "calories",
        "protein_g",
        "carbs_g",
        "fats_g",
        "fiber_g",
        "estimated_cost_php",
        "prep_time_minutes",
        "meal_type",
        "notes",
    }
    missing = required - set(df.columns)
    if missing:
        return _empty_curated_food_df(), f"Curated food database missing columns: {', '.join(sorted(missing))}"
    df = df.copy()
    df["food_name_lower"] = df["food_name"].astype(str).str.lower()
    return df, None


def find_best_match(keyword: str, df: pd.DataFrame, name_col_lower: str) -> Optional[pd.Series]:
    if df.empty:
        return None
    kw = clean_text_input(keyword).lower()
    if not kw:
        return None
    exact = df[df[name_col_lower] == kw]
    if not exact.empty:
        return exact.iloc[0]
    partial = df[df[name_col_lower].str.contains(re.escape(kw), na=False)]
    if not partial.empty:
        return partial.iloc[0]
    # plural fallback
    kw2 = kw.rstrip("s")
    partial2 = df[df[name_col_lower].str.contains(re.escape(kw2), na=False)]
    if not partial2.empty:
        return partial2.iloc[0]
    return None


# ---------------------------------------------------------------------------
# Targets (source of truth: Python)
# ---------------------------------------------------------------------------
def estimate_targets(weight_kg: float, goal: str) -> dict[str, Any]:
    weight_kg = max(float(weight_kg), 40.0)
    maintenance = weight_kg * 33

    if goal == "Bulk":
        calories = maintenance + 250
    elif goal == "Cut":
        calories = maintenance - 300
    else:
        calories = maintenance

    calories = max(calories, 1400)
    protein_g = min(weight_kg * PROTEIN_MULTIPLIERS.get(goal, 1.8), weight_kg * 2.5)

    # Carbs range (avoid extremes)
    if goal == "Cut":
        carbs_low = (calories * 0.30) / 4
        carbs_high = (calories * 0.40) / 4
    elif goal == "Bulk":
        carbs_low = (calories * 0.40) / 4
        carbs_high = (calories * 0.50) / 4
    else:
        carbs_low = (calories * 0.35) / 4
        carbs_high = (calories * 0.45) / 4

    fats_low = (calories * 0.20) / 9
    fats_high = (calories * 0.30) / 9

    fiber_g = 28.0
    water_ml = round(weight_kg * 32.5)

    return {
        "maintenance_calories": round(maintenance),
        "calories": round(calories),
        "protein_g": round(protein_g, 1),
        "carbs_low_g": round(carbs_low, 1),
        "carbs_high_g": round(carbs_high, 1),
        "carbs_target_g": round((carbs_low + carbs_high) / 2, 1),
        "fats_low_g": round(fats_low, 1),
        "fats_high_g": round(fats_high, 1),
        "fats_target_g": round((fats_low + fats_high) / 2, 1),
        "fiber_g": fiber_g,
        "water_ml": water_ml,
    }


# ---------------------------------------------------------------------------
# Filtering and matching
# ---------------------------------------------------------------------------
def _blocked_terms(disliked: list[str], allergies: list[str]) -> set[str]:
    return {t.strip().lower() for t in (disliked + allergies) if t.strip()}


def _is_vague_ingredient(ingredient: str) -> bool:
    ing = clean_text_input(ingredient).lower()
    if not ing or len(ing) <= 2:
        return True
    if ing in ("protein", "seasoning", "spices"):
        return True
    return any(v in ing for v in VAGUE_INGREDIENT_PHRASES)


def _parse_ingredient_list(main_ingredients: str) -> list[str]:
    return [
        clean_text_input(x).lower()
        for x in str(main_ingredients).split(",")
        if clean_text_input(x) and not _is_vague_ingredient(x)
    ]


def _recipe_contains_term(recipe_row: pd.Series, term: str) -> bool:
    t = clean_text_input(term).lower()
    if not t:
        return False
    t_root = t.rstrip("s")
    hay = f"{recipe_row.get('recipe_name_lower', '')} {recipe_row.get('ingredients_lower', '')}"
    if t in hay or t_root in hay:
        return True
    if t == "eggs" and "egg" in hay:
        return True
    if t == "egg" and "eggs" in hay:
        return True
    return False


def _user_wants_seafood_or_processed_meat(preferred: list[str], available: list[str]) -> bool:
    terms = [clean_text_input(x).lower() for x in preferred + available if clean_text_input(x)]
    seafood = set(FISH_SEAFOOD_TERMS) | {"spam", "hotdog", "longganisa"}
    return any(any(s in t or t in s for s in seafood) for t in terms)


def _nutrition_confidence(row: pd.Series) -> float:
    """1.0 = reliable; lower = macro calories disagree with listed calories."""
    try:
        protein = float(row["protein_g"])
        carbs = float(row["carbs_g"])
        fats = float(row["fats_g"])
        calories = float(row["calories"])
    except Exception:
        return 0.3
    if calories <= 0:
        return 0.3
    macro_cals = protein * 4 + carbs * 4 + fats * 9
    if macro_cals <= 0:
        return 0.5
    ratio = macro_cals / calories
    if ratio > 1.35 or ratio < 0.65:
        return 0.35
    return 1.0


def _sanitize_missing_ingredients(missing: list[str]) -> list[str]:
    useful = [m for m in missing if not _is_vague_ingredient(m)]
    return useful


def _build_specific_missing(
    recipe_row: pd.Series,
    available: list[str],
    raw_missing: list[str],
) -> list[str]:
    """
    Return a human-readable 'still need to buy' list for the recipe.
    - Skips ingredients already owned by the user.
    - Keeps items specific (no vague phrases).
    - Capitalises each item for readability.
    """
    avail_lower = [a.lower() for a in available if a]
    result: list[str] = []
    for item in raw_missing:
        item_l = item.lower().strip()
        if not item_l or _is_vague_ingredient(item_l):
            continue
        # Skip if the user already has it
        if any(a in item_l or item_l in a for a in avail_lower):
            continue
        result.append(item.strip().capitalize())

    name_l = str(recipe_row.get("recipe_name_lower", ""))
    # Fallback check
    if "chicken" in name_l and not any("chicken" in a for a in avail_lower) and not any("chicken" in r.lower() for r in result):
        result.append("Chicken")

    if not result:
        return ["Missing ingredient details are unavailable."]
    return result


def match_available_ingredients(recipe_row: pd.Series, available: list[str]) -> dict[str, Any]:
    ingredients = _parse_ingredient_list(str(recipe_row["main_ingredients"]))
    avail = [a.lower() for a in available if a]
    missing: list[str] = []
    for ing in ingredients:
        if not any(a in ing or ing in a for a in avail):
            missing.append(ing)
    match_count = len(ingredients) - len(missing)
    ratio = match_count / max(len(ingredients), 1) if ingredients else 0.0
    return {
        "ingredients": ingredients,
        "missing_ingredients": _sanitize_missing_ingredients(missing),
        "match_ratio": ratio,
        "ingredient_count": len(ingredients),
        "has_vague_ingredients": _has_vague_ingredient_text(str(recipe_row["main_ingredients"])),
    }


def _has_vague_ingredient_text(main_ingredients: str) -> bool:
    text = str(main_ingredients).lower()
    return any(v in text for v in VAGUE_INGREDIENT_PHRASES)


def filter_recipes(
    recipes: pd.DataFrame,
    goal: str,
    cooking_time: str,
    meal_type: str | None,
    disliked: list[str],
    allergies: list[str],
) -> tuple[pd.DataFrame, list[str]]:
    decisions: list[str] = []
    if recipes.empty:
        return recipes, ["Recipe dataset not loaded."]

    df = recipes.copy()
    blocked = _blocked_terms(disliked, allergies)
    if blocked:
        before = len(df)
        df = df[~df["recipe_name_lower"].apply(lambda n: any(b in n for b in blocked))]
        df = df[~df["ingredients_lower"].apply(lambda n: any(b in n for b in blocked))]
        removed = before - len(df)
        if removed:
            decisions.append("Filtered recipes to remove items matching allergies or disliked foods.")

    if meal_type:
        mt = meal_type.lower()
        before = len(df)
        df = df[df["meal_type_lower"].str.contains(mt, na=False)]
        if len(df) < before:
            decisions.append(f"Filtered recipes to meal type: {meal_type}.")

    max_ings = MAX_INGREDIENTS_BY_COOKING.get(cooking_time, 10)
    df = df.copy()
    df["_ingredient_count"] = df["main_ingredients"].astype(str).apply(lambda s: len(_parse_ingredient_list(s)))
    before = len(df)
    df = df[df["_ingredient_count"] <= max_ings]
    if len(df) < before:
        decisions.append(f"Prioritized simpler recipes (≤ {max_ings} main ingredients) for your schedule.")
    df = df.drop(columns=["_ingredient_count"])

    return df, decisions


def filter_foods(
    clean_foods: pd.DataFrame,
    disliked: list[str],
    allergies: list[str],
) -> tuple[pd.DataFrame, list[str]]:
    decisions: list[str] = []
    if clean_foods.empty:
        return clean_foods, ["Clean food dataset not loaded."]
    df = clean_foods.copy()
    blocked = _blocked_terms(disliked, allergies)
    if blocked:
        before = len(df)
        df = df[~df["food_name_lower"].apply(lambda n: any(b in n for b in blocked))]
        removed = before - len(df)
        if removed:
            decisions.append("Filtered foods to remove items matching allergies or disliked foods.")
    return df, decisions


# ---------------------------------------------------------------------------
# Meal planning (source of truth: recipe dataset + Python)
# ---------------------------------------------------------------------------
def _goal_macro_bias(goal: str) -> dict[str, float]:
    # Simple scoring weights
    if goal == "Bulk":
        return {"protein": 1.2, "carbs": 1.1, "fiber": 1.0}
    if goal == "Cut":
        return {"protein": 1.3, "carbs": 0.9, "fiber": 1.2}
    if goal == "Beginner Recomposition":
        return {"protein": 1.3, "carbs": 1.0, "fiber": 1.1}
    return {"protein": 1.1, "carbs": 1.0, "fiber": 1.0}


def _adjusted_recipe_cost(recipe_row: pd.Series, available: list[str]) -> tuple[float, list[str]]:
    match = match_available_ingredients(recipe_row, available)
    base_cost = float(recipe_row["estimated_cost_php"])
    parsed = _parse_ingredient_list(str(recipe_row["main_ingredients"]))
    total_ings = max(len(parsed), 1)
    missing = match["missing_ingredients"]
    if match["has_vague_ingredients"] and not parsed:
        missing_ratio = 1.0
    else:
        missing_ratio = len(missing) / total_ings
    adjusted = base_cost * missing_ratio
    return round(adjusted, 1), missing


# Slot-specific preferred ingredients for scoring boosts
SLOT_BREAKFAST_KEYWORDS = ("oat", "oats", "banana", "egg", "eggs", "rice", "garlic rice", "sinangag")
SLOT_SNACK_KEYWORDS = ("banana", "oat", "oats", "egg", "eggs", "boil")
SLOT_LUNCH_DINNER_KEYWORDS = ("chicken", "pork", "beef", "tuna", "tilapia", "adobo", "rice")

# Terms that indicate the main protein in a recipe name
PROTEIN_CATEGORY_TERMS = [
    "chicken", "pork", "beef", "tuna", "sardine", "bangus", "tilapia",
    "squid", "shrimp", "spam", "corned", "tocino", "longganisa",
]

# Keywords that identify a real Filipino dish name — these get a scoring bonus so they beat
# generic fallback names like "Egg Rice Meal" or "Simple Chicken Rice Meal".
KNOWN_FILIPINO_DISH_KEYWORDS = (
    "adobo", "sinigang", "tinola", "afritada", "mechado", "menudo", "kaldereta",
    "bistek", "kare-kare", "nilaga", "pinakbet", "laing", "dinuguan", "paksiw",
    "ginataang", "ginisang", "silog", "sinangag", "tocino", "longganisa", "tapa",
    "sopas", "bulalo", "lomi", "palabok", "pancit", "lumpia", "kinilaw",
    "estofado", "igado", "dinakdakan", "barbecue", "inasal", "humba",
    "pares", "goto", "arroz caldo", "binagoongan", "tortang", "batchoy",
    "pochero", "morcon", "embutido", "pinoy", "pilipino", "filipino",
    "guisado", "nilagang", "tinolang", "itlog", "sinangag",
)

# Names of the generic fallback rows we added — penalised when a named Filipino dish
# could serve the same slot, so they only win when no real recipe matches.
GENERIC_FALLBACK_NAMES = (
    "egg rice meal",
    "simple chicken rice meal",
    "chicken and rice bowl",
    "boiled egg and rice",
    "scrambled egg rice bowl",
    "rice and egg bowl",
    "boiled eggs",
    "banana snack",
)


def _dominant_protein(recipe_row: pd.Series) -> str | None:
    """Return the first protein category keyword found in the recipe name, or None."""
    name = str(recipe_row.get("recipe_name_lower", ""))
    for term in PROTEIN_CATEGORY_TERMS:
        if term in name:
            return term
    return None


def score_recipe_for_meal(
    recipe_row: pd.Series,
    *,
    meal_type: str,
    goal: str,
    cooking_time: str,
    preferred: list[str],
    disliked: list[str],
    allergies: list[str],
    available: list[str],
    adj_cost: float,
    budget_per_meal: float,
    ing_match: dict[str, Any],
    # Diversity: count of how many times each protein already appears in plan
    protein_counts: dict[str, int] | None = None,
    prefers_quick_meals: bool = False,
) -> float:
    """
    Point-based scoring for recipe selection. Higher is better.
    Disliked/allergy hits should already be filtered out; -100 guards remain.
    """
    score = 0.0
    blocked = _blocked_terms(disliked, allergies)
    if protein_counts is None:
        protein_counts = {}

    for term in blocked:
        if _recipe_contains_term(recipe_row, term):
            return -100.0

    name_ing = f"{recipe_row.get('recipe_name_lower', '')} {recipe_row.get('ingredients_lower', '')}"
    name_l = str(recipe_row.get("recipe_name_lower", ""))

    # --- Preferred foods: base match ---
    pref_lower = {clean_text_input(p).lower() for p in preferred}
    avail_lower = {clean_text_input(a).lower() for a in available}
    for p in preferred:
        if _recipe_contains_term(recipe_row, p):
            score += 5.0

    # --- Available-ingredient boost ---
    avail_hits = 0
    for a in available:
        if _recipe_contains_term(recipe_row, a):
            score += 5.0
            avail_hits += 1

    # Bonus when already-owned ingredients are used
    if avail_hits >= 1:
        score += 2.0

    # --- Meal type match ---
    mt = meal_type.lower()
    row_mt = str(recipe_row.get("meal_type_lower", "")).lower()
    if mt and mt in row_mt:
        score += 3.0

    # --- Budget ---
    if budget_per_meal > 0 and adj_cost <= budget_per_meal:
        score += 3.0
    elif budget_per_meal > 0 and adj_cost <= budget_per_meal * 1.15:
        score += 1.0

    # --- Protein quality ---
    protein = float(recipe_row["protein_g"])
    if goal == "Bulk":
        if protein >= 20:
            score += 3.0
        elif protein >= 12:
            score += 2.0
    elif protein >= 12:
        score += 2.0

    # --- Cooking time (simplicity) ---
    ing_count = int(ing_match.get("ingredient_count", 0))
    if cooking_time == "Very busy":
        if ing_count <= 4:
            score += 2.0
        elif ing_count <= 6:
            score += 1.0

    if prefers_quick_meals and (ing_count <= 4 or any(k in name_ing for k in QUICK_MEAL_KEYWORDS)):
        score += 2.0

    # --- Ingredient match ratio ---
    if ing_match.get("match_ratio", 0) >= 0.6:
        score += 2.0

    # --- Penalise vague recipes ---
    if _has_vague_ingredient_text(str(recipe_row["main_ingredients"])):
        score -= 3.0
    vague_missing = [m for m in (ing_match.get("missing_ingredients") or []) if _is_vague_ingredient(m)]
    score -= 3.0 * len(vague_missing)

    # --- Nutrition confidence ---
    conf = _nutrition_confidence(recipe_row)
    if conf < 0.5:
        score -= 5.0

    # --- Seafood / processed-meat penalty ---
    if not _user_wants_seafood_or_processed_meat(preferred, available):
        for term in FISH_SEAFOOD_TERMS:
            if term in name_l:
                score -= 15.0
        if "spam" in name_l and "spam" not in pref_lower:
            score -= 15.0
        if "squid" in name_l or "pusit" in name_l:
            score -= 10.0

    # --- Filipino dish recognition: reward real Filipino dish names ---
    # This ensures Chicken Adobo / Tinola / Sinangag at Itlog beat generic
    # fallback names like "Egg Rice Meal" or "Simple Chicken Rice Meal".
    if any(k in name_l for k in KNOWN_FILIPINO_DISH_KEYWORDS):
        score += 2.0

    # --- Generic fallback penalty ---
    # Penalise our catch-all fallback rows so they only win when no named
    # Filipino recipe matches the slot requirements.
    if any(g == name_l for g in GENERIC_FALLBACK_NAMES):
        score -= 3.0

    # --- Slot-aware scoring ---
    user_gym = {clean_text_input(x).lower().rstrip("s") for x in preferred + available}

    if meal_type == "breakfast":
        # Breakfast: Filipino egg/rice dishes AND oats/banana both welcome.
        # Give Filipino breakfast dishes an extra lift over plain generic names.
        if any(k in name_ing for k in SLOT_BREAKFAST_KEYWORDS):
            score += 6.0
        if "oat" in user_gym and "oat" in name_ing:
            score += 4.0
        if "banana" in user_gym and "banana" in name_ing:
            score += 4.0
        if ("egg" in user_gym or "eggs" in pref_lower) and "egg" in name_ing:
            score += 4.0
        # Slightly de-emphasise chicken at breakfast unless it's the only preference
        if "chicken" in name_l and len(pref_lower - {"chicken"}) > 0:
            score -= 2.0

    elif meal_type in ("lunch", "dinner"):
        # Lunch/dinner: preferred chicken/protein Filipino dishes are top priority.
        # Give a strong explicit bonus when the user listed chicken as preferred
        # and the recipe actually uses it — this must beat a plain egg+rice dish
        # that only scores high from available-ingredient matches.
        if user_gym & {"chicken", "egg", "rice", "oat", "banana"}:
            if "chicken" in user_gym and "chicken" in name_ing:
                score += 10.0  # strong: preferred protein at the main meal
            if ("egg" in user_gym or "eggs" in pref_lower) and "egg" in name_ing:
                score += 3.0
            if "rice" in user_gym and "rice" in name_ing:
                score += 3.0
        # Extra signal: if chicken is preferred and this recipe has chicken in the name,
        # give an additional lift so it beats generic egg-rice fallbacks.
        if "chicken" in pref_lower and "chicken" in name_l:
            score += 5.0
        # Penalise breakfast-type dishes (silog, sinangag) appearing at lunch/dinner
        if any(bt in name_l for bt in ("silog", "sinangag", "tapsilog", "longsilog")):
            score -= 8.0

    elif meal_type == "snack":
        # Snack: banana/oats/egg — simple, real foods preferred
        snack_prefs = {clean_text_input(x).lower().rstrip("s") for x in preferred}
        if snack_prefs & {"oat", "banana", "egg"}:
            if "banana" in user_gym and "banana" in name_ing:
                score += 8.0
            if "oat" in user_gym and "oat" in name_ing:
                score += 8.0
            if ("egg" in user_gym or "eggs" in pref_lower) and "egg" in name_ing:
                score += 6.0
            # Penalise vague snacks that don't match available/preferred
            if _has_vague_ingredient_text(str(recipe_row["main_ingredients"])) and not any(
                _recipe_contains_term(recipe_row, p) for p in ("oats", "banana", "egg", "eggs", "rice")
            ):
                score -= 6.0
        # Silog / sinangag dishes are heavy breakfast/lunch items — penalise at snack
        if any(st in name_l for st in ("silog", "sinangag", "tapsilog", "longsilog", "porksilog")):
            score -= 12.0
        # Chicken snacks are fine but shouldn't dominate the plan
        if "chicken" in snack_prefs and "chicken" in name_l and not any(t in name_l for t in FISH_SEAFOOD_TERMS):
            score += 3.0

    # --- DIVERSITY PENALTY ---
    dominant = _dominant_protein(recipe_row)
    if dominant and dominant in protein_counts:
        count = protein_counts[dominant]
        if count == 1:
            score -= 6.0   # second instance: moderate penalty
        elif count >= 2:
            score -= 14.0  # third or more: heavy penalty

    return score


def enrich_recipe_name(recipe_row: pd.Series, available: list[str], preferred: list[str], meal_type: str) -> str:
    name_l = str(recipe_row.get("recipe_name_lower", ""))
    orig_name = str(recipe_row.get("recipe_name", ""))
    
    combined = {clean_text_input(x).lower().rstrip('s') for x in available + preferred}
    
    has_chicken = "chicken" in combined
    has_rice = "rice" in combined
    has_egg = "egg" in combined
    has_oat = "oat" in combined
    has_banana = "banana" in combined
    has_veg = "vegetable" in combined or "tomato" in combined or "onion" in combined
    has_tuna = "tuna" in combined
    has_tofu = "tofu" in combined
    has_monggo = "monggo" in combined or "mung" in combined

    if name_l in GENERIC_FALLBACK_NAMES:
        if ("chicken" in name_l or has_chicken) and ("rice" in name_l or has_rice):
            if has_veg:
                return "Chicken Ginisang Gulay with Rice or Chicken Tinola"
            if meal_type == "lunch":
                return "Chicken Adobo with Rice or Chicken Afritada with Rice"
            elif meal_type == "dinner":
                return "Chicken Tinola with Rice or another simple chicken Filipino meal"
            else:
                return "Chicken Rice Bowl (Adobo or Tinola style)"
        
        if ("tuna" in name_l or has_tuna) and ("rice" in name_l or has_rice):
            return "Tuna Rice Bowl or Tuna Silog-style Meal"

        if ("tofu" in name_l or has_tofu) and ("rice" in name_l or has_rice):
            return "Tofu Sisig-style Rice Meal or Tofu Rice Bowl"

        if ("monggo" in name_l or has_monggo) and ("rice" in name_l or has_rice):
            return "Ginisang Monggo with Rice"
        
        if ("egg" in name_l or has_egg) and ("rice" in name_l or has_rice):
            if has_veg:
                return "Ginisang Itlog with Tomato and Rice"
            return "Sinangag with Egg, Egg Silog-style Meal, or Ginisang Itlog with Rice"
            
        if ("oat" in name_l or has_oat) and ("banana" in name_l or has_banana):
            return "Oats with Banana or Banana Oats Snack"
            
        if ("egg" in name_l or has_egg) and not has_rice:
            return "Boiled Eggs or Simple Egg Meal"
            
    return orig_name


def generate_meal_plan(
    recipes: pd.DataFrame,
    targets: dict[str, Any],
    budget_php: float,
    num_meals: int,
    goal: str,
    cooking_time: str,
    workout_time: str,
    preferred: list[str],
    disliked: list[str],
    allergies: list[str],
    available: list[str],
    prefers_quick_meals: bool = False,
) -> tuple[list[dict[str, Any]], dict[str, Any], list[str]]:
    """
    Build a daily meal plan using filipino_recipes_100_dataset.csv.
    Costs are adjusted down when the user already owns ingredients.
    Diversity: tracks protein counts across slots to penalise repeats.
    """
    decisions: list[str] = []
    budget_php = max(float(budget_php), 0.0)
    slots = MEAL_SLOTS.get(num_meals, MEAL_SLOTS[4])

    plan: list[dict[str, Any]] = []
    remaining_budget = budget_php
    num_slots = len(slots)
    used_recipe_names: set[str] = set()
    # Diversity tracker: count how many times each dominant protein appeared
    protein_counts: dict[str, int] = {}

    for slot_idx, (meal_name, meal_type) in enumerate(slots):
        filtered, filter_decisions = filter_recipes(
            recipes=recipes,
            goal=goal,
            cooking_time=cooking_time,
            meal_type=meal_type,
            disliked=disliked,
            allergies=allergies,
        )
        # Snack slot: also allow simple breakfast options (e.g. silog, egg + rice) when dataset snacks are vague.
        if meal_type == "snack" and cooking_time == "Very busy":
            for extra_mt in ("breakfast", "lunch"):
                filtered_extra, extra_decisions = filter_recipes(
                    recipes=recipes,
                    goal=goal,
                    cooking_time=cooking_time,
                    meal_type=extra_mt,
                    disliked=disliked,
                    allergies=allergies,
                )
                if not filtered_extra.empty:
                    filtered = pd.concat([filtered, filtered_extra], ignore_index=True)
                    decisions.extend(extra_decisions)
            filtered = filtered.drop_duplicates(subset=["recipe_name"], keep="first")
        pref_lower = {clean_text_input(p).lower() for p in preferred}
        if meal_type == "snack" and "chicken" in pref_lower:
            if not _user_wants_seafood_or_processed_meat(preferred, available):
                filtered = filtered[
                    ~filtered["recipe_name_lower"].apply(lambda n: any(t in n for t in FISH_SEAFOOD_TERMS))
                ]
            if "spam" not in pref_lower:
                filtered = filtered[~filtered["recipe_name_lower"].str.contains("spam", na=False)]
        decisions.extend(filter_decisions)
        if filtered.empty:
            plan.append({
                "meal_name": meal_name,
                "meal_type": meal_type,
                "suggestion": "No matching recipe found (check datasets or restrictions).",
                "calories": 0.0,
                "protein_g": 0.0,
                "carbs_g": 0.0,
                "fats_g": 0.0,
                "fiber_g": 0.0,
                "estimated_cost_php": 0.0,
                "prep_notes": "Try loosening restrictions or adding more available ingredients.",
                "reason": "Fallback: recipe filtering removed all candidates.",
                "missing_ingredients": [],
            })
            continue

        slots_left = num_slots - slot_idx
        budget_per_meal = remaining_budget / max(slots_left, 1) if remaining_budget > 0 else budget_php / max(num_slots, 1)

        scored: list[tuple[float, pd.Series, float, list[str], dict[str, Any]]] = []
        for _, row in filtered.iterrows():
            if _nutrition_confidence(row) < 0.4:
                continue
            adj_cost, missing = _adjusted_recipe_cost(row, available)
            if adj_cost > remaining_budget and remaining_budget > 0:
                continue
            ing_match = match_available_ingredients(row, available)
            points = score_recipe_for_meal(
                row,
                meal_type=meal_type,
                goal=goal,
                cooking_time=cooking_time,
                preferred=preferred,
                disliked=disliked,
                allergies=allergies,
                available=available,
                adj_cost=adj_cost,
                budget_per_meal=budget_per_meal,
                ing_match=ing_match,
                protein_counts=protein_counts,
                prefers_quick_meals=prefers_quick_meals,
            )
            if points <= -50:
                continue
            scored.append((points, row, adj_cost, missing, ing_match))

        if not scored:
            fallback_rows: list[tuple[float, pd.Series, list[str], dict[str, Any]]] = []
            for _, row in filtered.iterrows():
                adj_cost, missing = _adjusted_recipe_cost(row, available)
                ing_match = match_available_ingredients(row, available)
                pts = score_recipe_for_meal(
                    row,
                    meal_type=meal_type,
                    goal=goal,
                    cooking_time=cooking_time,
                    preferred=preferred,
                    disliked=disliked,
                    allergies=allergies,
                    available=available,
                    adj_cost=adj_cost,
                    budget_per_meal=budget_per_meal,
                    ing_match=ing_match,
                    protein_counts=protein_counts,
                    prefers_quick_meals=prefers_quick_meals,
                )
                fallback_rows.append((pts, row, missing, ing_match))
            fallback_rows.sort(key=lambda x: x[0], reverse=True)
            if fallback_rows:
                _, best, missing, ing_match = fallback_rows[0]
                adj_cost, _ = _adjusted_recipe_cost(best, available)
            else:
                adj_cost, best, missing = 0.0, filtered.iloc[0], []
                ing_match = match_available_ingredients(best, available)
        else:
            scored.sort(key=lambda x: x[0], reverse=True)
            best = scored[0][1]
            adj_cost = scored[0][2]
            missing = scored[0][3]
            ing_match = scored[0][4]
            for pts, row, ac, miss, im in scored:
                rname = str(row["recipe_name"])
                if rname not in used_recipe_names:
                    best, adj_cost, missing, ing_match = row, ac, miss, im
                    break

        # Update diversity tracker
        dominant = _dominant_protein(best)
        if dominant:
            protein_counts[dominant] = protein_counts.get(dominant, 0) + 1

        ing_match_ratio = float(ing_match.get("match_ratio", 0))
        used_recipe_names.add(str(best["recipe_name"]))
        remaining_budget = max(remaining_budget - adj_cost, 0.0)

        # Moderation notes
        moderation_note = ""
        if float(best["fats_g"]) >= 20:
            moderation_note = "Moderation note: higher-fat dish; adjust portions if needed."

        # --- Build reason text as a single natural sentence ---
        avail_used = [a for a in available if _recipe_contains_term(best, a)]
        matched_prefs = [p for p in preferred if _recipe_contains_term(best, p)]
        
        reason_parts = []
        if avail_used:
            avail_str = " and ".join(avail_used[:2])
            reason_parts.append(f"Uses available {avail_str}")
        if matched_prefs:
            reason_parts.append("matches your preferred foods")
            
        if goal == "Bulk":
            reason_parts.append("supports your bulk goal")
        elif goal == "Cut":
            reason_parts.append("fits your cut goal")
        else:
            reason_parts.append("fits your maintenance goal")
            
        reason_parts.append("fits your budget")

        if cooking_time == "Very busy":
            last_part = "and is quick enough for a very busy schedule."
        elif cooking_time == "Moderate":
            last_part = "and fits a moderate cooking schedule."
        else:
            last_part = "and fits a flexible schedule."

        if not reason_parts:
            reason_parts.append("Selected for your profile")

        reason_text = ", ".join(reason_parts) + ", " + last_part
        reason_text = reason_text[0].upper() + reason_text[1:]

        reason_parts_final = [reason_text]
        if moderation_note:
            reason_parts_final.append(moderation_note)

        # --- Build missing-ingredients list (specific, not vague) ---
        specific_missing = _build_specific_missing(best, available, missing)

        suggestion_name = enrich_recipe_name(best, available, preferred, meal_type)

        plan.append({
            "meal_name": meal_name,
            "meal_type": meal_type,
            "suggestion": suggestion_name,
            "calories": float(best["calories"]),
            "protein_g": float(best["protein_g"]),
            "carbs_g": float(best["carbs_g"]),
            "fats_g": float(best["fats_g"]),
            "fiber_g": float(best["fiber_g"]),
            "estimated_cost_php": float(adj_cost),
            "prep_notes": (
                f"Main ingredients: {best['main_ingredients']}."
                if not _has_vague_ingredient_text(str(best["main_ingredients"]))
                else "Quick prep using your available staples where possible."
            ),
            "reason": " ".join(reason_parts_final) if reason_parts_final else "Selected based on your goal, budget, and ingredient match.",
            "missing_ingredients": specific_missing,
        })

    totals = calculate_totals(plan)
    gaps = analyze_gaps(totals, targets, budget_php)
    decisions.append("Selected Filipino recipes from the recipe dataset and adjusted cost using owned ingredients.")
    return plan, {"remaining_budget_php": remaining_budget, "totals": totals, "gaps": gaps}, decisions


def calculate_totals(items: list[dict[str, Any]]) -> dict[str, float]:
    def s(key: str) -> float:
        return float(sum(float(x.get(key, 0) or 0) for x in items))

    return {
        "calories": round(s("calories"), 1),
        "protein_g": round(s("protein_g"), 1),
        "carbs_g": round(s("carbs_g"), 1),
        "fats_g": round(s("fats_g"), 1),
        "fiber_g": round(s("fiber_g"), 1),
        "cost_php": round(s("estimated_cost_php"), 1),
    }


def analyze_gaps(totals: dict[str, float], targets: dict[str, Any], budget_php: float) -> dict[str, dict[str, Any]]:
    def range_status(actual: float, low: float, high: float) -> str:
        if actual < low:
            return "below"
        if actual > high:
            return "above"
        return "on_target"

    def simple_status(actual: float, target: float, tolerance: float = 0.10) -> str:
        if target <= 0:
            return "on_target"
        if abs(actual - target) <= target * tolerance:
            return "on_target"
        return "below" if actual < target else "above"

    budget_status = "on_target" if totals["cost_php"] <= budget_php else "over_budget"

    return {
        "calories": {"status": simple_status(totals["calories"], float(targets["calories"])), "actual": totals["calories"], "target": float(targets["calories"])},
        "protein": {"status": simple_status(totals["protein_g"], float(targets["protein_g"])), "actual": totals["protein_g"], "target": float(targets["protein_g"])},
        "carbs": {
            "status": range_status(totals["carbs_g"], float(targets["carbs_low_g"]), float(targets["carbs_high_g"])),
            "actual": totals["carbs_g"],
            "target_range": (float(targets["carbs_low_g"]), float(targets["carbs_high_g"])),
        },
        "fats": {
            "status": range_status(totals["fats_g"], float(targets["fats_low_g"]), float(targets["fats_high_g"])),
            "actual": totals["fats_g"],
            "target_range": (float(targets["fats_low_g"]), float(targets["fats_high_g"])),
        },
        "fiber": {"status": simple_status(totals["fiber_g"], float(targets["fiber_g"])), "actual": totals["fiber_g"], "target": float(targets["fiber_g"])},
        "budget": {"status": budget_status, "actual": totals["cost_php"], "target": float(budget_php)},
    }


def generate_meal_timing_guidance(workout_time: str) -> str:
    guidance = {
        "Morning": (
            "Since your workout is in the morning, keep the first meal lighter and focused on quick carbs "
            "before training. After training, prioritize protein for recovery."
        ),
        "Afternoon": (
            "Since your workout is in the afternoon, include carbs at lunch or a snack before training "
            "for energy. After training, prioritize protein for recovery."
        ),
        "Evening": (
            "Since your workout is in the evening, eat a balanced meal a few hours before training, "
            "and choose a lighter protein-based meal after training."
        ),
        "No fixed time": (
            "For general timing, eat carbs before training for energy and protein after training for recovery."
        ),
    }
    return guidance.get(workout_time, guidance["No fixed time"])


# ---------------------------------------------------------------------------
# Food logging (session memory)
# ---------------------------------------------------------------------------
def init_session_state() -> None:
    if "food_log" not in st.session_state:
        st.session_state.food_log = []
    if "agent_results" not in st.session_state:
        st.session_state.agent_results = None
    if "gemini_cache" not in st.session_state:
        st.session_state.gemini_cache = {}
    if "gemini_calls" not in st.session_state:
        st.session_state.gemini_calls = 0
    if "last_gemini_error" not in st.session_state:
        st.session_state.last_gemini_error = None
    if "last_gemini_model_used" not in st.session_state:
        st.session_state.last_gemini_model_used = None
    if "generated_recommendations" not in st.session_state:
        st.session_state.generated_recommendations = None
    if "recommendation_source" not in st.session_state:
        st.session_state.recommendation_source = None
    if "ask_fitfuel_nl" not in st.session_state:
        st.session_state.ask_fitfuel_nl = ""
    if "nl_assistant_confirmation" not in st.session_state:
        st.session_state.nl_assistant_confirmation = None


def _cost_from_fallback(food_name: str, fallback_db: pd.DataFrame) -> Optional[float]:
    if fallback_db.empty:
        return None
    row = find_best_match(food_name, fallback_db, "food_name_lower")
    if row is None:
        return None
    try:
        return float(row["estimated_cost_php"])
    except Exception:
        return None


def add_food_log(
    label: str,
    calories: float,
    protein_g: float,
    carbs_g: float,
    fats_g: float,
    fiber_g: float,
    estimated_cost_php: float | None,
    servings: float = 1.0,
) -> None:
    cost = float(estimated_cost_php) if estimated_cost_php is not None else 0.0
    st.session_state.food_log.append({
        "item": label,
        "servings": servings,
        "calories": round(float(calories) * servings, 1),
        "protein_g": round(float(protein_g) * servings, 1),
        "carbs_g": round(float(carbs_g) * servings, 1),
        "fats_g": round(float(fats_g) * servings, 1),
        "fiber_g": round(float(fiber_g) * servings, 1),
        "estimated_cost_php": round(cost * servings, 1),
        "cost_note": "" if estimated_cost_php is not None else "Cost not available for this item; budget totals may be understated.",
    })


def calculate_logged_totals(log: list[dict[str, Any]]) -> dict[str, float]:
    if not log:
        return {"calories": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fats_g": 0.0, "fiber_g": 0.0, "cost_php": 0.0}
    return {
        "calories": round(sum(float(e.get("calories", 0) or 0) for e in log), 1),
        "protein_g": round(sum(float(e.get("protein_g", 0) or 0) for e in log), 1),
        "carbs_g": round(sum(float(e.get("carbs_g", 0) or 0) for e in log), 1),
        "fats_g": round(sum(float(e.get("fats_g", 0) or 0) for e in log), 1),
        "fiber_g": round(sum(float(e.get("fiber_g", 0) or 0) for e in log), 1),
        "cost_php": round(sum(float(e.get("estimated_cost_php", 0) or 0) for e in log), 1),
    }


def remaining_targets(logged: dict[str, float], targets: dict[str, Any]) -> dict[str, float]:
    return {
        "calories": round(max(float(targets["calories"]) - logged["calories"], 0.0), 1),
        "protein_g": round(max(float(targets["protein_g"]) - logged["protein_g"], 0.0), 1),
        "carbs_g": round(max(float(targets["carbs_target_g"]) - logged["carbs_g"], 0.0), 1),
        "fats_g": round(max(float(targets["fats_target_g"]) - logged["fats_g"], 0.0), 1),
        "fiber_g": round(max(float(targets["fiber_g"]) - logged["fiber_g"], 0.0), 1),
    }


def recommend_next_food(remaining: dict[str, float]) -> str:
    suggestions: list[str] = []
    if remaining["protein_g"] > 15:
        suggestions.append("protein (chicken, eggs, tuna, tofu, milk, yogurt)")
    if remaining["carbs_g"] > 30:
        suggestions.append("carbs (rice, oats, banana, bread, sweet potato)")
    if remaining["fats_g"] > 10:
        suggestions.append("healthy fats (eggs, peanut butter, peanuts, milk)")
    if remaining["fiber_g"] > 5:
        suggestions.append("fiber-rich foods (vegetables, fruits, monggo, oats, beans)")
    if not suggestions:
        return "You are close to your daily targets. Focus on hydration and balanced portions."
    return "Based on your remaining targets, consider adding: " + "; ".join(suggestions) + "."


# ---------------------------------------------------------------------------
# Filipino meal suggestions (separate from the daily plan)
# ---------------------------------------------------------------------------
def suggest_filipino_recipes(
    recipes: pd.DataFrame,
    available: list[str],
    budget_remaining_php: float,
    meal_type: str | None,
    cooking_time: str,
    preferred: list[str],
    disliked: list[str],
    allergies: list[str],
    limit: int = 8,
) -> pd.DataFrame:
    if recipes.empty:
        return pd.DataFrame()

    filtered, _ = filter_recipes(
        recipes=recipes,
        goal="Maintain",
        cooking_time=cooking_time,
        meal_type=meal_type,
        disliked=disliked,
        allergies=allergies,
    )
    if filtered.empty:
        return pd.DataFrame()

    scored_rows: list[tuple[float, dict[str, Any]]] = []
    budget_per = budget_remaining_php / max(limit, 1) if budget_remaining_php > 0 else 9999.0

    for _, row in filtered.iterrows():
        if _nutrition_confidence(row) < 0.4:
            continue
        adj_cost, missing = _adjusted_recipe_cost(row, available)
        if budget_remaining_php > 0 and adj_cost > budget_remaining_php:
            continue
        ing_match = match_available_ingredients(row, available)
        mt = meal_type or str(row.get("meal_type", "")).lower()
        points = score_recipe_for_meal(
            row,
            meal_type=mt,
            goal="Maintain",
            cooking_time=cooking_time,
            preferred=preferred,
            disliked=disliked,
            allergies=allergies,
            available=available,
            adj_cost=adj_cost,
            budget_per_meal=budget_per,
            ing_match=ing_match,
        )
        if points <= -50:
            continue

        reason = []
        if ing_match["match_ratio"] >= 0.6:
            reason.append("Uses several of your available ingredients.")
        if preferred and any(_recipe_contains_term(row, p) for p in preferred):
            reason.append("Matches your preferred foods.")
        if cooking_time == "Very busy":
            reason.append("Quick prep friendly for a busy schedule.")
        if float(row["fats_g"]) >= 20:
            reason.append("Moderation note: higher-fat dish; adjust portions if needed.")

        missing_display = ", ".join(missing) if missing else "None"
        if _has_vague_ingredient_text(str(row["main_ingredients"])) and missing_display == "None":
            missing_display = "Missing ingredient details are unavailable."

        scored_rows.append((
            points,
            {
                "Recipe": row["recipe_name"],
                "Meal Type": row["meal_type"],
                "Main Ingredients": row["main_ingredients"],
                "Calories": float(row["calories"]),
                "Protein (g)": float(row["protein_g"]),
                "Carbs (g)": float(row["carbs_g"]),
                "Fats (g)": float(row["fats_g"]),
                "Fiber (g)": float(row["fiber_g"]),
                "Est. Cost to Buy Missing (₱)": float(adj_cost),
                "Missing Ingredients": missing_display,
                "Match Reason": " ".join(reason) if reason else "Filipino option matched to your profile.",
            },
        ))

    if not scored_rows:
        return pd.DataFrame()

    scored_rows.sort(key=lambda x: x[0], reverse=True)
    return pd.DataFrame([r[1] for r in scored_rows[:limit]])


# ---------------------------------------------------------------------------
# Grocery list (missing ingredients + optional custom market item)
# ---------------------------------------------------------------------------
def create_grocery_list(meal_plan: list[dict[str, Any]], custom_item: dict[str, Any] | None = None) -> tuple[pd.DataFrame, float]:
    items: dict[str, dict[str, Any]] = {}
    for meal in meal_plan:
        for ing in meal.get("missing_ingredients", []) or []:
            key = ing.strip().lower()
            if not key:
                continue
            if key not in items:
                items[key] = {"Item": ing, "Reason": "Missing ingredient for selected recipe.", "Est. Cost (₱)": None}

    if custom_item and custom_item.get("name") and custom_item.get("price_php") is not None:
        key = str(custom_item["name"]).strip().lower()
        items[key] = {
            "Item": custom_item["name"],
            "Reason": "User-requested market item.",
            "Est. Cost (₱)": float(custom_item["price_php"]),
        }

    rows = list(items.values())
    df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=["Item", "Reason", "Est. Cost (₱)"])
    total = float(df["Est. Cost (₱)"].fillna(0).sum()) if not df.empty else 0.0
    return df, round(total, 1)


# ---------------------------------------------------------------------------
# Rule-based recommendations (fallback and baseline)
# ---------------------------------------------------------------------------
def generate_rule_based_recommendations(
    gaps: dict[str, dict[str, Any]],
    goal: str,
    cooking_time: str,
    workout_time: str,
    remaining: dict[str, float],
) -> list[str]:
    recs: list[str] = []
    if gaps["protein"]["status"] == "below":
        recs.append("Protein is below target. Add eggs, tofu, chicken, tuna, sardines, milk, or yogurt.")
    if gaps["fiber"]["status"] == "below":
        recs.append("Fiber is low. Add vegetables, fruits, oats, monggo, beans, or cabbage.")
    if gaps["carbs"]["status"] == "below" and workout_time in ["Morning", "Afternoon"]:
        recs.append("Carbs may be low before training. Add rice, banana, oats, bread, or sweet potato.")
    if gaps["fats"]["status"] == "below":
        recs.append("Fats may be low. Add eggs, peanuts, peanut butter, milk, or fish in moderate portions.")
    if gaps["budget"]["status"] == "over_budget":
        recs.append("Cost is above budget. Replace expensive items with eggs, tofu, sardines, or monggo where possible.")
    if cooking_time == "Very busy":
        recs.append("Meal prep tip: batch-cook rice and a protein on your free day to reduce daily cooking time.")
    if goal == "Bulk" and gaps["calories"]["status"] == "below":
        recs.append("Calories are below your bulking target. Add a budget snack like oats or extra rice portions.")
    if goal == "Cut" and gaps["calories"]["status"] == "above":
        recs.append("Calories are above your cut target. Consider smaller portions and more vegetables.")

    recs.append("Hydration reminder: drink water before, during, and after training. Adjust for sweat and heat.")
    recs.append(recommend_next_food(remaining))
    return recs


# ---------------------------------------------------------------------------
# Gemini integration (external API layer)
# ---------------------------------------------------------------------------
FALLBACK_USER_MESSAGE = "Enhanced recommendations are currently unavailable. Standard recommendations are shown instead."

GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
]


def _summary_hash(payload: dict[str, Any]) -> str:
    s = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


def validate_gemini_output(
    text: str,
    blocked_terms: set[str],
) -> tuple[bool, Optional[str]]:
    t = clean_text_input(text)
    if not t:
        return False, "Empty output."

    # Word count check
    words = t.split()
    if len(words) < 80 or len(words) > 220:
        return False, "Output length outside expected range."

    # Block explicit macro-number claims
    if re.search(r"\b\d+\s*(kcal|calories)\b", t, re.IGNORECASE):
        return False, "Contains calorie numbers."
    if re.search(r"\b\d+\s*(g|grams)\s*(protein|carbs|fat|fats|fiber)\b", t, re.IGNORECASE):
        return False, "Contains macro numbers."

    # Block restricted foods mention
    tl = t.lower()
    for b in blocked_terms:
        if b and b in tl:
            return False, "Mentions restricted foods."

    return True, None


def _gemini_cache_key_from_payload(payload: dict[str, Any]) -> str:
    """
    Cache only stable parts so logging food doesn't invalidate the cache every time.
    Keep food log totals in the payload sent to Gemini, but exclude them from the hash.
    """
    stable = {
        "user_profile": payload.get("user_profile"),
        "meal_plan_summary": payload.get("meal_plan_summary"),
        "totals": payload.get("totals"),
        "gaps": payload.get("gaps"),
        "meal_timing_context": payload.get("meal_timing_context"),
    }
    return _summary_hash(stable)


def generate_gemini_recommendations(
    payload: dict[str, Any],
    blocked_terms: set[str],
) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Returns (recommendation_text, error_message, model_name_used).
    Must be called only when the user clicks Generate Recommendations.
    Tries multiple Gemini models in order to handle 404 / unavailable model errors.
    Uses the google-genai SDK (client-based API).
    """
    api_key = (os.getenv("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY") or "").strip()
    if not api_key:
        return None, "Missing API key.", None
    if not _genai_module_available or _genai_module is None:
        return None, "Gemini SDK not available.", None

    prompt = (
        "You are a helpful fitness nutrition assistant for a Filipino-context meal planning app.\n"
        "Use only the calculated data provided. Do not invent calories, macros, fiber, cost, or medical advice.\n"
        "Write a short recommendation (120–180 words) that:\n"
        "- Explains the plan choices and how to improve gaps\n"
        "- Includes meal timing guidance based on workout time\n"
        "- Includes one budget-friendly adjustment idea\n"
        "- Uses supportive, neutral language\n"
        "- Does NOT include exact nutrition numbers (no kcal, no grams)\n"
        "- Does NOT contradict restrictions\n"
        "- Does NOT guarantee outcomes\n\n"
        "Context (source of truth data):\n"
        f"{json.dumps(payload, ensure_ascii=False)}\n"
    )

    last_error: Optional[str] = None
    try:
        client = _genai_module.Client(api_key=api_key)
        for model_name in GEMINI_MODELS:
            try:
                resp = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config={
                        "temperature": 0.3,
                        "max_output_tokens": 300,
                    },
                )
                text = ""
                if hasattr(resp, "text"):
                    text = resp.text or ""
                elif hasattr(resp, "candidates") and resp.candidates:
                    text = getattr(resp.candidates[0].content.parts[0], "text", "") or ""
                ok, reason = validate_gemini_output(text, blocked_terms)
                if not ok:
                    last_error = f"{model_name}: Validation failed: {reason}"
                    continue
                return clean_text_input(text), None, model_name
            except Exception as e:
                last_error = f"{model_name}: {e}"
                continue
        return None, last_error or "All Gemini models failed.", None
    except Exception as e:
        return None, str(e), None


def _render_plan_status_steps(
    name: str,
    goal: str,
    recipes_count: int | None,
) -> Any:
    """
    Agent thinking steps UI. Uses st.status when available, otherwise falls back to a simple container.
    Returns a context object with `.update()` and `.write()` when using st.status; otherwise returns None.
    """
    if hasattr(st, "status"):
        label = "Creating your plan..."
        status = st.status(label, expanded=True)
        status.write("1. Reading your profile and constraints...")
        status.write(f"2. Estimating nutrition targets for {goal} goal...")
        if recipes_count is None:
            status.write("3. Loading Filipino recipe dataset... (not loaded)")
        else:
            status.write(f"3. Loading Filipino recipe dataset... ({recipes_count} recipes available)")
        status.write("4. Filtering recipes for your schedule and restrictions...")
        status.write("5. Selecting meals and calculating ingredient costs...")
        status.write("6. Running gap analysis and building grocery list...")
        status.write(f"7. Plan ready for {name}.")
        status.update(label=f"Plan ready for {name}.", state="complete")
        return status

    # Fallback
    box = st.container()
    with box:
        st.markdown('<div class="ff-card" style="margin-bottom: 12px;">', unsafe_allow_html=True)
        st.markdown("### Agent steps")
        st.write("1. Reading your profile and constraints...")
        st.write(f"2. Estimating nutrition targets for {goal} goal...")
        if recipes_count is None:
            st.write("3. Loading Filipino recipe dataset... (not loaded)")
        else:
            st.write(f"3. Loading Filipino recipe dataset... ({recipes_count} recipes available)")
        st.write("4. Filtering recipes for your schedule and restrictions...")
        st.write("5. Selecting meals and calculating ingredient costs...")
        st.write("6. Running gap analysis and building grocery list...")
        st.write(f"7. Plan ready for {name}.")
        st.markdown("</div>", unsafe_allow_html=True)
    return None


# ---------------------------------------------------------------------------
# Agent decision summary
# ---------------------------------------------------------------------------
def generate_agent_decision_summary(results: dict[str, Any]) -> list[str]:
    profile = results["profile"]
    summary = [
        "It read the user profile and constraints.",
        "It estimated nutrition targets using safe formulas (not medical advice).",
        "It checked available ingredients and treated them as already owned for budget calculations.",
        "It searched the Filipino recipe dataset to select meal suggestions.",
        "It searched the cleaned daily food dataset for food logging and extra options.",
        "It filtered out disliked foods and allergies.",
        "It selected meals based on goal, budget, workout time, and recipe simplicity.",
        "It calculated totals, remaining targets, and budget using Python (source of truth).",
        "It used session memory to store the food log during this session.",
        "It calls the external API only when Generate Recommendations is clicked, then validates the output.",
        "If the API is unavailable or conflicts with restrictions, it uses rule-based fallback recommendations.",
    ]

    if results.get("natural_language_request_used"):
        summary.insert(0, "It extracted structured details from the natural-language request and applied them to the profile.")

    return summary


# ---------------------------------------------------------------------------
# UI render helpers
# ---------------------------------------------------------------------------
def render_card(title: str, value: str, accent: bool = False) -> None:
    v_class = "ff-card-value ff-accent" if accent else "ff-card-value"
    st.markdown(
        f"""
<div class="ff-card">
  <div class="ff-card-title">{title}</div>
  <div class="{v_class}">{value}</div>
</div>
        """,
        unsafe_allow_html=True,
    )


def render_status_badge(status: str) -> str:
    # No icons/emojis: use short text
    mapping = {
        "on_target": "On target",
        "below": "Below target",
        "above": "Above target",
        "over_budget": "Over budget",
    }
    return mapping.get(status, status)


def _format_rule_recommendations(rule_recs: list[str]) -> str:
    return "\n".join(f"- {r}" for r in rule_recs)


def build_recommendations_payload(results: dict[str, Any], targets: dict[str, Any]) -> dict[str, Any]:
    logged = calculate_logged_totals(st.session_state.food_log)
    rem = remaining_targets(logged, targets)
    return {
        "user_profile": {
            "goal": results["profile"]["goal"],
            "workout_time": results["profile"]["workout_time"],
            "cooking_time": results["profile"]["cooking_time"],
            "budget_php": results["profile"]["budget_php"],
            "budget_after_market_item_php": results["profile"]["effective_budget_php"],
            "available_ingredients": results["profile"]["available_ingredients"][:20],
            "disliked": results["profile"]["disliked"][:20],
            "allergies": results["profile"]["allergies"][:20],
        },
        "meal_plan_summary": [
            {"meal": m["meal_name"], "type": m["meal_type"], "recipe": m["suggestion"], "cost_php": m["estimated_cost_php"]}
            for m in results["meal_plan"]
        ],
        "totals": results["plan_meta"]["totals"],
        "food_log_totals": logged,
        "gaps": results["plan_meta"]["gaps"],
        "remaining_targets_after_log": rem,
        "meal_timing_context": results["timing_guidance"],
    }


def process_generate_recommendations(results: dict[str, Any], targets: dict[str, Any], blocked: set[str]) -> None:
    """Run Gemini (with fallback) when user clicks Generate Recommendations."""
    payload = build_recommendations_payload(results, targets)
    fallback_text = _format_rule_recommendations(results.get("rule_recommendations", []))
    cache_key = _gemini_cache_key_from_payload(payload)

    cached = st.session_state.gemini_cache.get(cache_key)
    if cached:
        st.session_state.generated_recommendations = cached
        st.session_state.recommendation_source = "Gemini-enhanced"
        return

    text, err, model_used = generate_gemini_recommendations(payload, blocked_terms=blocked)
    st.session_state.gemini_calls += 1

    if text:
        st.session_state.gemini_cache[cache_key] = text
        st.session_state.generated_recommendations = text
        st.session_state.recommendation_source = "Gemini-enhanced"
        st.session_state.last_gemini_model_used = model_used
        st.session_state.last_gemini_error = None
    else:
        st.session_state.generated_recommendations = fallback_text
        st.session_state.recommendation_source = "Standard fallback"
        st.session_state.last_gemini_error = err


def render_hero() -> None:
    st.markdown(
        """
<div class="ff-hero">
  <div class="ff-kicker">AI MEAL PLANNING AGENT</div>
  <h1 class="ff-title"><span>Fit</span><span class="orange">Fuel</span><span> AI</span></h1>
  <p class="ff-subtitle">A Budget-Friendly Filipino Meal Planning and Nutrition Tracking Agent for Busy Beginners and Casual Fitness Users</p>
  <p class="ff-value">Plan meals, track nutrition, manage your food budget, and get Filipino-context recommendations using your available ingredients.</p>
</div>
        """,
        unsafe_allow_html=True,
    )


def render_how_it_works_tab() -> None:
    """Dedicated How It Works tab content."""
    st.markdown('<p class="ff-section-title">How FitFuel AI Works</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="ff-section-sub">FitFuel AI follows a structured process to create budget-friendly '
        "Filipino meal plans for busy beginners and casual fitness users.</p>",
        unsafe_allow_html=True,
    )
    st.markdown(
        """
<div class="ff-banner" style="margin-bottom: 16px;">
  <div class="ff-banner-workflow">
    User Input → Local Parser → Nutrition Targets → Food Data Lookup → Meal Scoring Logic → Recommendations/Fallback → Output
  </div>
  <div class="ff-banner-line">
    FitFuel AI uses your budget, goal, schedule, available ingredients, food preferences, and restrictions to generate Filipino-context meal plans with estimated nutrition, budget checks, and personalized recommendations.<br><br>CSV datasets and Python calculations remain the source of truth, while Gemini is used only to explain calculated recommendations in natural language.
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )

    steps = [
        ("1. User Input", "Reads the user’s goal, budget, workout time, cooking time, available ingredients, preferences, disliked foods, allergies, food log, and Ask FitFuel AI request."),
        ("2. Local Parser", "Extracts budget, meals needed, ingredients, desired market item, item price, and quick-meal intent from natural-language input."),
        ("3. Nutrition Targets", "Estimates calories, protein, carbs, fats, fiber, and hydration needs using safe general formulas."),
        ("4. Food Data Lookup", "Searches local CSV datasets for Filipino recipes and food nutrition values."),
        ("5. Meal Scoring Logic", "Selects meals based on budget, ingredients, meal count, prep time, goal, preferences, restrictions, and meal variety."),
        ("6. Recommendations / Output", "Uses Gemini only when Generate Recommendations is clicked. If the API fails, standard rule-based recommendations are shown. The app outputs meal plans, Filipino suggestions, food log, grocery list, budget check, and nutrition analysis."),
    ]
    row1 = st.columns(3)
    for col, (title, desc) in zip(row1, steps[:3]):
        with col:
            st.markdown(
                f'<div class="ff-workflow-card"><div class="ff-workflow-title">{title}</div>'
                f'<div class="ff-workflow-desc">{desc}</div></div>',
                unsafe_allow_html=True,
            )
    row2 = st.columns(3)
    for col, (title, desc) in zip(row2, steps[3:]):
        with col:
            st.markdown(
                f'<div class="ff-workflow-card"><div class="ff-workflow-title">{title}</div>'
                f'<div class="ff-workflow-desc">{desc}</div></div>',
                unsafe_allow_html=True,
            )

    st.caption(
        "If the external API is unavailable, FitFuel AI still uses local CSV data and rule-based "
        "recommendations so the user still receives a meal plan and nutrition guidance."
    )


def _macro_pills_html(cal: float, prot: float, carbs: float, fats: float, fiber: float, cost: float | None = None) -> str:
    cost_html = f'<span class="ff-macro-pill"><strong>₱{cost:.0f}</strong> est. cost</span>' if cost is not None else ""
    return (
        f'<div class="ff-macro-row">'
        f'<span class="ff-macro-pill"><strong>{cal:.0f}</strong> kcal</span>'
        f'<span class="ff-macro-pill"><strong>{prot:.0f}g</strong> protein</span>'
        f'<span class="ff-macro-pill"><strong>{carbs:.0f}g</strong> carbs</span>'
        f'<span class="ff-macro-pill"><strong>{fats:.0f}g</strong> fats</span>'
        f'<span class="ff-macro-pill"><strong>{fiber:.0f}g</strong> fiber</span>'
        f"{cost_html}"
        f"</div>"
    )


def render_meal_plan_card(meal: dict[str, Any]) -> None:
    slot = str(meal.get("meal_name", ""))
    meal_type = str(meal.get("meal_type", "")).title()
    type_label = f"{slot} · {meal_type}" if slot else meal_type
    title = str(meal.get("suggestion", "No suggestion"))
    macros = _macro_pills_html(
        float(meal.get("calories", 0)),
        float(meal.get("protein_g", 0)),
        float(meal.get("carbs_g", 0)),
        float(meal.get("fats_g", 0)),
        float(meal.get("fiber_g", 0)),
        float(meal.get("estimated_cost_php", 0)),
    )
    reason = clean_text_input(str(meal.get("reason", "")))
    prep = clean_text_input(str(meal.get("prep_notes", "")))
    missing = meal.get("missing_ingredients") or []
    missing_html = ""
    if missing:
        missing_html = f'<div class="ff-missing">Still need: {", ".join(missing[:12])}</div>'

    st.markdown(
        f"""
<div class="ff-meal-card">
  <div class="ff-meal-type">{type_label}</div>
  <div class="ff-meal-title">{title}</div>
  {macros}
  <div class="ff-meal-reason">{reason}</div>
  {"<div class='ff-meal-reason'>" + prep + "</div>" if prep else ""}
  {missing_html}
</div>
        """,
        unsafe_allow_html=True,
    )


def render_recipe_suggestion_card(row: pd.Series) -> None:
    macros = _macro_pills_html(
        float(row["Calories"]),
        float(row["Protein (g)"]),
        float(row["Carbs (g)"]),
        float(row["Fats (g)"]),
        float(row["Fiber (g)"]),
        float(row["Est. Cost to Buy Missing (₱)"]),
    )
    match_reason = str(row.get("Match Reason", ""))
    missing = str(row.get("Missing Ingredients", ""))
    missing_html = ""
    if missing and missing != "None":
        missing_html = f'<div class="ff-missing">Still need: {missing}</div>'

    st.markdown(
        f"""
<div class="ff-meal-card">
  <div class="ff-meal-type">{str(row["Meal Type"]).title()}</div>
  <div class="ff-meal-title">{row["Recipe"]}</div>
  {macros}
  <div class="ff-meal-reason">{match_reason}</div>
  {missing_html}
</div>
        """,
        unsafe_allow_html=True,
    )


def render_grocery_list_cards(grocery_df: pd.DataFrame, total: float) -> None:
    if grocery_df.empty:
        st.write("No missing ingredients to buy for this plan.")
        return
    for _, row in grocery_df.iterrows():
        item = str(row.get("Item", "Item"))
        reason = str(row.get("Reason", ""))
        cost_val = row.get("Est. Cost (₱)")
        cost_txt = f"₱{float(cost_val):.0f}" if pd.notna(cost_val) and cost_val != "" else "Included in plan estimate"
        st.markdown(
            f"""
<div class="ff-grocery-item">
  <div class="ff-grocery-item-title">{item}</div>
  <div class="ff-grocery-item-meta">{reason} · {cost_txt}</div>
</div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown(
        f'<div style="text-align: right; font-size: 16px; font-weight: 700; color: #F25A2C; margin-top: 12px;">'
        f"Estimated grocery total: ₱{total:.0f}</div>",
        unsafe_allow_html=True,
    )


def _gap_progress_value(gap: dict[str, Any], metric_key: str) -> float:
    actual = float(gap.get("actual", 0))
    if metric_key in ("carbs", "fats") and "target_range" in gap:
        low, high = gap["target_range"]
        mid = (float(low) + float(high)) / 2
        return min(actual / mid, 1.0) if mid > 0 else 0.0
    target = float(gap.get("target", 1))
    return min(actual / target, 1.0) if target > 0 else 0.0


def _gap_status_class(status: str) -> str:
    if status in ("on_target",):
        return "ff-status-on"
    return "ff-status-warn"


def render_nutrition_gap_cards(gaps: dict[str, dict[str, Any]]) -> None:
    labels = [
        ("calories", "Calories", False),
        ("protein", "Protein", False),
        ("carbs", "Carbs", True),
        ("fats", "Fats", True),
        ("fiber", "Fiber", False),
        ("budget", "Budget", False),
    ]
    cols = st.columns(2)
    for idx, (key, label, is_range) in enumerate(labels):
        gap = gaps[key]
        status = render_status_badge(gap["status"])
        status_cls = _gap_status_class(gap["status"])
        if is_range:
            low, high = gap["target_range"]
            target_txt = f"{low:.0f}–{high:.0f}"
        else:
            target_txt = f"{float(gap['target']):.0f}"
        actual = float(gap["actual"])
        if key == "budget":
            actual_txt = f"₱{actual:.0f}"
            target_txt = f"₱{float(gap['target']):.0f}"
        elif key == "calories":
            actual_txt = f"{actual:.0f} kcal"
            target_txt = f"{target_txt} kcal"
        else:
            actual_txt = f"{actual:.0f} g"
            target_txt = f"{target_txt} g"

        progress = _gap_progress_value(gap, key)
        with cols[idx % 2]:
            st.markdown(
                f'<div class="ff-gap-card"><div class="ff-gap-label">{label}</div>'
                f'<div class="ff-gap-status {status_cls}">{status} · {actual_txt} / {target_txt}</div></div>',
                unsafe_allow_html=True,
            )
            st.progress(min(max(progress, 0.0), 1.0))


def render_logged_food_cards(food_log: list[dict[str, Any]]) -> None:
    for entry in food_log:
        st.markdown(
            f"""
<div class="ff-grocery-item">
  <div class="ff-grocery-item-title">{entry.get("item", "Food")} × {entry.get("servings", 1)}</div>
  <div class="ff-grocery-item-meta">
    {entry.get("calories", 0):.0f} kcal · {entry.get("protein_g", 0):.0f}g protein ·
    {entry.get("carbs_g", 0):.0f}g carbs · {entry.get("fats_g", 0):.0f}g fats ·
    {entry.get("fiber_g", 0):.0f}g fiber
  </div>
</div>
            """,
            unsafe_allow_html=True,
        )


def render_personalized_recommendations(has_plan: bool, just_generated: bool = False) -> None:
    st.markdown('<div class="ff-ask-panel" style="margin-top: 12px;">', unsafe_allow_html=True)
    st.markdown('<p class="ff-section-title">Personalized Recommendations</p>', unsafe_allow_html=True)

    if not has_plan:
        st.write("Create a meal plan first before generating recommendations.")
    elif st.session_state.generated_recommendations is None:
        st.write("Click Generate Recommendations above to create personalized advice for this meal plan.")
    else:
        if just_generated and st.session_state.recommendation_source == "Gemini-enhanced":
            st.success("Recommendations generated.")
        elif just_generated and st.session_state.recommendation_source == "Standard fallback":
            st.info(FALLBACK_USER_MESSAGE)

        rec_type = recommendation_type_label(st.session_state.recommendation_source)
        st.caption(f"Recommendation type: {rec_type}")

        st.markdown('<div class="ff-rec-box">', unsafe_allow_html=True)
        st.write(st.session_state.generated_recommendations)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def render_footer_disclaimer() -> None:
    st.markdown(
        '<div class="ff-footer">FitFuel AI provides estimated meal planning and nutrition support only. '
        "It is not medical advice. Nutrition values and food prices are estimates.</div>",
        unsafe_allow_html=True,
    )


def render_developer_settings() -> None:
    with st.expander("Developer Settings", expanded=False):
        st.caption("These settings are for development and deployment only.")
        st.text_input("Recipe dataset path", value=st.session_state.get("recipes_path", RECIPES_PATH), key="recipes_path")
        st.text_input("Clean food dataset path", value=st.session_state.get("clean_foods_path", CLEAN_FOODS_PATH), key="clean_foods_path")
        st.text_input(
            "Curated fallback foods path",
            value=st.session_state.get("curated_foods_path", CURATED_FOODS_PATH),
            key="curated_foods_path",
        )


def render_developer_debug(
    recipes_df: pd.DataFrame,
    clean_foods_df: pd.DataFrame,
    curated_foods_df: pd.DataFrame,
) -> None:
    if not DEBUG_MODE:
        return
    api_key = (os.getenv("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY") or "").strip()
    with st.expander("Developer Debug", expanded=False):
        st.write(f"Gemini key loaded: {'Yes' if api_key else 'No'}")
        if api_key:
            st.write(f"Key length: {len(api_key)}")
        st.write(f"Gemini SDK available: {genai is not None}")
        st.write(f"Last Gemini model used: {st.session_state.last_gemini_model_used or 'None'}")
        st.write(f"Last Gemini error: {st.session_state.last_gemini_error or 'None'}")
        st.write(f"Gemini calls this session: {st.session_state.gemini_calls}")
        st.write(f"Filipino recipes loaded: {len(recipes_df)}")
        st.write(f"Clean foods loaded: {len(clean_foods_df)}")
        st.write(f"Curated fallback foods loaded: {len(curated_foods_df)}")
        st.write(f"Recommendation source: {st.session_state.recommendation_source or 'None'}")


def _request_create_plan() -> None:
    st.session_state.create_plan_requested = True


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------
def main() -> None:
    init_session_state()

    render_hero()

    # ---- Sidebar: Inputs ----
    with st.sidebar:
        # Live remaining targets (session memory)
        if st.session_state.agent_results is not None:
            ar = st.session_state.agent_results
            t = ar.get("targets") or estimate_targets(65.0, "Maintain")
            logged = calculate_logged_totals(st.session_state.food_log)
            rem = remaining_targets(logged, t)
            budget_after_market = float(ar["profile"].get("effective_budget_php", ar["profile"].get("budget_php", 0.0)))
            spent = float(logged.get("cost_php", 0.0))
            budget_remaining = round(max(budget_after_market - spent, 0.0), 1)

            st.markdown("## Today's Remaining Targets")
            st.metric("Calories remaining", f"{rem['calories']:.0f} kcal", delta=f"-{logged['calories']:.0f} kcal")
            st.metric("Protein remaining", f"{rem['protein_g']:.0f} g", delta=f"-{logged['protein_g']:.0f} g")
            st.metric("Budget remaining", f"₱{budget_remaining:.0f}", delta=f"-₱{spent:.0f}")
            st.divider()

        st.markdown("## Profile")

        st.markdown("### User inputs")
        name = st.text_input("Name or nickname", value="Isaac")
        weight_kg = st.number_input("Weight (kg)", min_value=40.0, max_value=200.0, value=65.0, step=0.5)
        goal = st.selectbox("Fitness goal", GOAL_OPTIONS, index=0)
        budget_php = st.number_input("Daily food budget (₱)", min_value=0.0, max_value=5000.0, value=250.0, step=10.0)
        meals_per_day = st.selectbox("Number of meals per day", MEAL_COUNT_OPTIONS, index=2)
        cooking_time = st.selectbox("Cooking time availability", COOKING_TIME_OPTIONS, index=0)
        workout_time = st.selectbox("Workout time", WORKOUT_TIME_OPTIONS, index=1)

        st.markdown("### Preferences and restrictions")
        preferred_text = st.text_area("Preferred foods or protein sources", value="chicken, eggs, rice, oats, banana")
        disliked_text = st.text_area("Disliked foods", value="sardines")
        allergies_text = st.text_area("Allergies or restrictions", value="none")
        available_text = st.text_area("Available ingredients", value="rice, eggs, oats, banana")
        eaten_today_text = st.text_area("Food already eaten today", value="2 eggs, 1 cup rice, 1 banana")

        st.markdown("---")
        st.button("Create My Plan", type="primary", use_container_width=True, on_click=_request_create_plan)
        clear_log = st.button("Clear Food Log", type="secondary", use_container_width=True)

        if DEBUG_MODE:
            render_developer_settings()

    if clear_log:
        st.session_state.food_log = []
        st.session_state.last_gemini_error = None
        st.session_state.generated_recommendations = None
        st.session_state.recommendation_source = None
        st.session_state.agent_results = None
        st.session_state.nl_assistant_confirmation = None
        st.rerun()

    # Load datasets (tool usage). Use friendly info messages; never crash if missing.
    recipes_path = st.session_state.get("recipes_path", RECIPES_PATH) if DEBUG_MODE else RECIPES_PATH
    clean_foods_path = st.session_state.get("clean_foods_path", CLEAN_FOODS_PATH) if DEBUG_MODE else CLEAN_FOODS_PATH
    curated_foods_path = st.session_state.get("curated_foods_path", CURATED_FOODS_PATH) if DEBUG_MODE else CURATED_FOODS_PATH
    recipes_df, recipes_err = load_recipe_database(recipes_path)
    clean_foods_df, clean_foods_err = load_clean_food_database(clean_foods_path)
    curated_foods_df, curated_err = load_curated_food_database(curated_foods_path)

    if recipes_err or clean_foods_err:
        st.info("Some food data is currently unavailable. The app will continue using available sources.")

    # Parse text inputs
    preferred = parse_list_input(preferred_text)
    disliked = [d for d in parse_list_input(disliked_text) if d != "none"]
    allergies = [a for a in parse_list_input(allergies_text) if a != "none"]
    available = [a for a in parse_list_input(available_text) if a != "none"]
    blocked = _blocked_terms(disliked, allergies)

    # No separate custom market item field; this is now handled entirely by Ask FitFuel AI.

    targets = estimate_targets(weight_kg, goal)
    timing_guidance = generate_meal_timing_guidance(workout_time)

    # Create plan before tabs so thinking steps appear above the dashboard
    if st.session_state.pop("create_plan_requested", False):
        natural_language_request = st.session_state.get("ask_fitfuel_nl", "")
        nl_extracted = parse_natural_language_request(natural_language_request)
        use_nl = bool(nl_extracted) and bool(natural_language_request.strip())

        effective_budget = float(budget_php)
        effective_meals = int(meals_per_day)
        effective_available = list(available)
        effective_cooking_time = cooking_time
        desired_item = None
        desired_item_price = None
        natural_language_request_used = False
        nl_caption = None
        original_budget_for_nl: float | None = None
        prefers_quick_meals = False

        if use_nl:
            natural_language_request_used = True
            if nl_extracted.get("budget_php") is not None:
                original_budget_for_nl = float(nl_extracted["budget_php"])
                effective_budget = original_budget_for_nl
            if nl_extracted.get("meals_count") in MEAL_COUNT_OPTIONS:
                effective_meals = int(nl_extracted["meals_count"])
            if nl_extracted.get("available_ingredients"):
                effective_available = list(dict.fromkeys([x for x in nl_extracted["available_ingredients"] if x]))
            if nl_extracted.get("desired_item"):
                desired_item = nl_extracted["desired_item"]
            if nl_extracted.get("desired_item_price_php") is not None:
                desired_item_price = float(nl_extracted["desired_item_price_php"])
            if nl_extracted.get("prefers_quick_meals"):
                prefers_quick_meals = True
                effective_cooking_time = "Very busy"

        if desired_item_price is not None:
            effective_budget = max(effective_budget - float(desired_item_price), 0.0)

        if use_nl:
            nl_caption = build_nl_assistant_confirmation(
                nl_extracted,
                effective_budget=effective_budget,
                effective_meals=effective_meals,
                effective_available=effective_available,
                desired_item=desired_item,
                desired_item_price=desired_item_price,
                original_budget=original_budget_for_nl,
            )
            st.session_state.nl_assistant_confirmation = nl_caption
        else:
            st.session_state.nl_assistant_confirmation = None

        recipes_count_for_status = None if recipes_df.empty else int(len(recipes_df))
        _render_plan_status_steps(name=clean_text_input(name) or "User", goal=goal, recipes_count=recipes_count_for_status)

        if recipes_df.empty:
            st.info("Some food data is currently unavailable. The app will continue using available sources.")
            meal_plan = []
            empty_totals = calculate_totals([])
            plan_meta = {
                "remaining_budget_php": effective_budget,
                "totals": empty_totals,
                "gaps": analyze_gaps(empty_totals, targets, effective_budget),
            }
            plan_decisions = ["Recipe dataset not loaded; plan generation skipped."]
        else:
            meal_plan, plan_meta, plan_decisions = generate_meal_plan(
                recipes=recipes_df,
                targets=targets,
                budget_php=effective_budget,
                num_meals=effective_meals,
                goal=goal,
                cooking_time=effective_cooking_time,
                workout_time=workout_time,
                preferred=preferred,
                disliked=disliked,
                allergies=allergies,
                available=effective_available,
                prefers_quick_meals=prefers_quick_meals,
            )

        log_messages: list[str] = []
        if st.session_state.agent_results is None and eaten_today_text.strip():
            for keyword, qty in parse_quantity_food(eaten_today_text):
                row = find_best_match(keyword, clean_foods_df, "food_name_lower")
                if row is not None:
                    cost = _cost_from_fallback(str(row["food_name"]), curated_foods_df)
                    add_food_log(
                        label=str(row["food_name"]),
                        calories=float(row["calories"]),
                        protein_g=float(row["protein_g"]),
                        carbs_g=float(row["carbs_g"]),
                        fats_g=float(row["fats_g"]),
                        fiber_g=float(row["fiber_g"]),
                        estimated_cost_php=cost,
                        servings=float(qty),
                    )
                    log_messages.append(f"Logged: {qty} x {row['food_name']}")
                else:
                    rrow = find_best_match(keyword, recipes_df, "recipe_name_lower")
                    if rrow is not None:
                        add_food_log(
                            label=str(rrow["recipe_name"]),
                            calories=float(rrow["calories"]),
                            protein_g=float(rrow["protein_g"]),
                            carbs_g=float(rrow["carbs_g"]),
                            fats_g=float(rrow["fats_g"]),
                            fiber_g=float(rrow["fiber_g"]),
                            estimated_cost_php=float(rrow["estimated_cost_php"]),
                            servings=float(qty),
                        )
                        log_messages.append(f"Logged: {qty} x {rrow['recipe_name']}")
                    else:
                        log_messages.append(f"Could not find '{keyword}' in the datasets. Try a simpler name.")

        logged_totals = calculate_logged_totals(st.session_state.food_log)
        remaining = remaining_targets(logged_totals, targets)
        rule_recs = generate_rule_based_recommendations(plan_meta["gaps"], goal, cooking_time, workout_time, remaining)
        grocery_df, grocery_total = create_grocery_list(
            meal_plan,
            custom_item={"name": desired_item, "price_php": desired_item_price} if desired_item_price is not None else None,
        )

        st.session_state.agent_results = {
            "profile": {
                "name": clean_text_input(name) or "User",
                "weight_kg": float(weight_kg),
                "goal": goal,
                "budget_php": float(budget_php),
                "effective_budget_php": float(effective_budget),
                "meals_per_day": int(effective_meals),
                "cooking_time": cooking_time,
                "workout_time": workout_time,
                "preferred": preferred,
                "disliked": disliked,
                "allergies": allergies,
                "available_ingredients": effective_available,
                "desired_item": desired_item,
                "desired_item_price_php": desired_item_price,
            },
            "targets": targets,
            "timing_guidance": timing_guidance,
            "meal_plan": meal_plan,
            "plan_meta": plan_meta,
            "plan_decisions": plan_decisions,
            "grocery_df": grocery_df,
            "grocery_total": grocery_total,
            "log_messages": log_messages,
            "rule_recommendations": rule_recs,
            "natural_language_request_used": natural_language_request_used,
            "nl_extraction_caption": nl_caption,
        }

        st.session_state.last_gemini_error = None
        st.session_state.generated_recommendations = None
        st.session_state.recommendation_source = None
        st.rerun()

    results = st.session_state.agent_results

    tab_overview, tab_how_it_works, tab_meal_plan, tab_suggestions, tab_food_log, tab_analysis = st.tabs(
        ["Overview", "How It Works", "Meal Plan", "Filipino Meal Suggestions", "Food Log", "Nutrition Analysis"]
    )

    generate_recs = False

    with tab_how_it_works:
        render_how_it_works_tab()

    with tab_overview:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            render_card("Goal", goal, accent=True)
        with c2:
            render_card("Meals per day", str(int(meals_per_day)))
        with c3:
            render_card("Budget (daily)", f"₱{float(budget_php):.0f}")
        with c4:
            eff = float(results["profile"]["effective_budget_php"]) if results else float(budget_php)
            render_card("Budget after market item", f"₱{eff:.0f}")

        st.markdown('<div class="ff-ask-panel">', unsafe_allow_html=True)
        st.markdown('<p class="ff-section-title">Ask FitFuel AI</p>', unsafe_allow_html=True)
        st.caption("Describe your budget, meals, ingredients, and market purchases. Parsed locally — not sent to the external API.")
        st.text_area(
            "Tell FitFuel AI what you need",
            key="ask_fitfuel_nl",
            placeholder=(
                "I have ₱200 for today. I need breakfast and lunch. I already have rice, eggs, tomatoes, "
                "onions, and garlic. I want to buy meat worth ₱75. Can you help me?"
            ),
            height=120,
        )
        if st.session_state.get("nl_assistant_confirmation"):
            st.markdown('<div class="ff-chat-assistant">', unsafe_allow_html=True)
            st.write(st.session_state.nl_assistant_confirmation)
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            st.button("Create My Plan", type="primary", use_container_width=True, on_click=_request_create_plan)
        with btn_col2:
            generate_recs = st.button("Generate Recommendations", type="secondary", use_container_width=True)

        just_generated = False
        if generate_recs:
            if results is None:
                st.warning("Create a meal plan first before generating recommendations.")
            else:
                process_generate_recommendations(results, targets, blocked)
                just_generated = True

        render_personalized_recommendations(has_plan=results is not None, just_generated=just_generated)

        st.markdown('<div class="ff-card" style="margin-top: 12px;">', unsafe_allow_html=True)
        st.markdown("### User Profile Summary")
        st.write(f"Name: {clean_text_input(name) or 'User'}")
        st.write(f"Weight: {float(weight_kg):.1f} kg")
        st.write(f"Workout time: {workout_time}")
        st.write(f"Cooking time availability: {cooking_time}")
        st.write(f"Available ingredients: {', '.join(available) if available else 'None provided'}")
        st.write(f"Preferred foods: {', '.join(preferred) if preferred else 'None provided'}")
        st.write(f"Disliked foods: {', '.join(disliked) if disliked else 'None'}")
        st.write(f"Allergies/restrictions: {', '.join(allergies) if allergies else 'None'}")
        if results and results["profile"].get("desired_item_price_php") is not None:
            st.write(
                f"Custom market item: {results['profile'].get('desired_item')} "
                f"(₱{float(results['profile'].get('desired_item_price_php')):.0f}, treated as purchase)"
            )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="ff-card" style="margin-top: 12px;">', unsafe_allow_html=True)
        st.markdown("### Estimated Nutrition Targets")
        st.caption("These targets are estimates only and are not medical advice.")
        tcols = st.columns(6)
        tcols[0].metric("Calories", f"{targets['calories']} kcal")
        tcols[1].metric("Protein", f"{targets['protein_g']} g")
        tcols[2].metric("Carbs", f"{targets['carbs_low_g']}–{targets['carbs_high_g']} g")
        tcols[3].metric("Fats", f"{targets['fats_low_g']}–{targets['fats_high_g']} g")
        tcols[4].metric("Fiber", f"{targets['fiber_g']} g")
        tcols[5].metric("Water", f"{targets['water_ml']} ml")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="ff-card" style="margin-top: 12px;">', unsafe_allow_html=True)
        st.markdown("### Meal Timing Guidance")
        st.write(timing_guidance)
        st.markdown("</div>", unsafe_allow_html=True)

        if results is None:
            st.info("Set your profile in the sidebar, describe your needs above, then click Create My Plan.")

    # Meal plan tab
    with tab_meal_plan:
        if results is None:
            st.info("No plan yet. Go to Overview and click Create My Plan.")
        else:
            st.markdown('<p class="ff-section-title">Your Meal Plan</p>', unsafe_allow_html=True)
            st.markdown('<p class="ff-section-sub">Filipino-context meals matched to your goal, budget, and available ingredients.</p>', unsafe_allow_html=True)

            for m in results["meal_plan"]:
                render_meal_plan_card(m)

            st.markdown('<div class="ff-card" style="margin-top: 12px;">', unsafe_allow_html=True)
            st.markdown("### Budget Check")
            total_cost = results["plan_meta"]["totals"]["cost_php"]
            st.write(f"Daily budget: ₱{results['profile']['budget_php']:.0f}")
            if results["profile"]["desired_item_price_php"] is not None:
                st.write(f"Market item purchase: ₱{results['profile']['desired_item_price_php']:.0f}")
                st.write(f"Budget remaining for missing ingredients: ₱{results['profile']['effective_budget_php']:.0f}")
            st.write(f"Total estimated cost to buy missing ingredients: ₱{total_cost:.0f}")
            if total_cost <= results["profile"]["effective_budget_php"]:
                st.write(f"Remaining budget: ₱{results['profile']['effective_budget_php'] - total_cost:.0f}")
            else:
                st.write(f"Over budget by: ₱{total_cost - results['profile']['effective_budget_php']:.0f}")
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown('<div class="ff-card" style="margin-top: 12px;">', unsafe_allow_html=True)
            st.markdown('<p class="ff-section-title">Grocery List</p>', unsafe_allow_html=True)
            st.markdown('<p class="ff-section-sub">Items to buy for missing ingredients and requested market purchases.</p>', unsafe_allow_html=True)
            render_grocery_list_cards(results["grocery_df"], float(results["grocery_total"]))
            st.markdown("</div>", unsafe_allow_html=True)

    # Suggestions tab
    with tab_suggestions:
        if recipes_df.empty:
            st.info("Some food data is currently unavailable. The app will continue using available sources.")
        else:
            st.markdown('<div class="ff-card">', unsafe_allow_html=True)
            st.markdown("### Filipino Meal Suggestions")
            st.caption("These suggestions use the recipe dataset and your available ingredients. Costs reflect only missing ingredients.")
            s_meal_type = st.selectbox("Filter by meal type", ["any", "breakfast", "lunch", "dinner", "snack"], index=0)
            mt = None if s_meal_type == "any" else s_meal_type
            budget_for_suggestions = (
                results.get("profile", {}).get("effective_budget_php", budget_php)
                if results
                else budget_php
            )
            available_for_suggestions = (
                results.get("profile", {}).get("available_ingredients", available)
                if results
                else available
            )
            suggestions_df = suggest_filipino_recipes(
                recipes=recipes_df,
                available=available_for_suggestions,
                budget_remaining_php=float(budget_for_suggestions),
                meal_type=mt,
                cooking_time=cooking_time,
                preferred=preferred,
                disliked=disliked,
                allergies=allergies,
                limit=10,
            )
            if suggestions_df.empty:
                st.write("No suggestions matched your current filters. Try changing meal type or loosening restrictions.")
            else:
                grid_cols = st.columns(2)
                for i, (_, srow) in enumerate(suggestions_df.iterrows()):
                    with grid_cols[i % 2]:
                        render_recipe_suggestion_card(srow)
            st.markdown("</div>", unsafe_allow_html=True)

    # Food log tab
    with tab_food_log:
        st.markdown('<div class="ff-card">', unsafe_allow_html=True)
        st.markdown("### Today’s Food Log (session only)")
        st.caption("Food logs are stored only during this session and are not saved permanently.")
        st.markdown("</div>", unsafe_allow_html=True)

        if clean_foods_df.empty and recipes_df.empty:
            st.info("Food log requires at least one dataset (clean foods or recipes).")
        else:
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                log_source = st.selectbox("Log source", ["Food item", "Filipino recipe"], index=0)
            with col2:
                servings = st.number_input("Servings", min_value=0.5, max_value=10.0, value=1.0, step=0.5)
            with col3:
                add_btn = st.button("Add to Food Log", type="secondary")

            search = st.text_input("Search item", value="")
            if log_source == "Food item" and not clean_foods_df.empty:
                options = clean_foods_df["food_name"].astype(str)
                if search.strip():
                    options = options[options.str.contains(search, case=False, na=False)]
                selected = st.selectbox("Select food", options.tolist()[:2000] if len(options) else [])
                if add_btn and selected:
                    row = clean_foods_df[clean_foods_df["food_name"] == selected].iloc[0]
                    cost = _cost_from_fallback(str(row["food_name"]), curated_foods_df)
                    add_food_log(
                        label=str(row["food_name"]),
                        calories=float(row["calories"]),
                        protein_g=float(row["protein_g"]),
                        carbs_g=float(row["carbs_g"]),
                        fats_g=float(row["fats_g"]),
                        fiber_g=float(row["fiber_g"]),
                        estimated_cost_php=cost,
                        servings=float(servings),
                    )
                    st.rerun()
            elif log_source == "Filipino recipe" and not recipes_df.empty:
                options = recipes_df["recipe_name"].astype(str)
                if search.strip():
                    options = options[options.str.contains(search, case=False, na=False)]
                selected = st.selectbox("Select recipe", options.tolist()[:2000] if len(options) else [])
                if add_btn and selected:
                    row = recipes_df[recipes_df["recipe_name"] == selected].iloc[0]
                    add_food_log(
                        label=str(row["recipe_name"]),
                        calories=float(row["calories"]),
                        protein_g=float(row["protein_g"]),
                        carbs_g=float(row["carbs_g"]),
                        fats_g=float(row["fats_g"]),
                        fiber_g=float(row["fiber_g"]),
                        estimated_cost_php=float(row["estimated_cost_php"]),
                        servings=float(servings),
                    )
                    st.rerun()

            if st.session_state.food_log:
                st.markdown('<div class="ff-card" style="margin-top: 12px;">', unsafe_allow_html=True)
                st.markdown('<p class="ff-section-title">Logged Items</p>', unsafe_allow_html=True)
                render_logged_food_cards(st.session_state.food_log)
                st.markdown("</div>", unsafe_allow_html=True)

                totals = calculate_logged_totals(st.session_state.food_log)
                rem = remaining_targets(totals, targets)
                m1, m2, m3, m4, m5, m6 = st.columns(6)
                m1.metric("Calories consumed", f"{totals['calories']} kcal")
                m2.metric("Protein consumed", f"{totals['protein_g']} g")
                m3.metric("Carbs consumed", f"{totals['carbs_g']} g")
                m4.metric("Fats consumed", f"{totals['fats_g']} g")
                m5.metric("Fiber consumed", f"{totals['fiber_g']} g")
                m6.metric("Est. cost (logged)", f"₱{totals['cost_php']:.0f}")

                r1, r2, r3, r4, r5 = st.columns(5)
                r1.metric("Calories remaining", f"{rem['calories']} kcal")
                r2.metric("Protein remaining", f"{rem['protein_g']} g")
                r3.metric("Carbs remaining", f"{rem['carbs_g']} g")
                r4.metric("Fats remaining", f"{rem['fats_g']} g")
                r5.metric("Fiber remaining", f"{rem['fiber_g']} g")

                st.markdown('<div class="ff-card" style="margin-top: 12px;">', unsafe_allow_html=True)
                st.markdown("### Next-step suggestion")
                st.write(recommend_next_food(rem))
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.info("No items logged yet. Add a food or recipe above.")

    # Nutrition analysis tab
    with tab_analysis:
        if results is None:
            st.info("Create a plan to see nutrition analysis.")
        else:
            plan_totals = results["plan_meta"]["totals"]
            gaps = results["plan_meta"]["gaps"]
            st.markdown('<div class="ff-card">', unsafe_allow_html=True)
            st.markdown("### Daily Nutrition Summary (Meal Plan)")
            a1, a2, a3, a4, a5, a6 = st.columns(6)
            a1.metric("Calories", f"{plan_totals['calories']} kcal")
            a2.metric("Protein", f"{plan_totals['protein_g']} g")
            a3.metric("Carbs", f"{plan_totals['carbs_g']} g")
            a4.metric("Fats", f"{plan_totals['fats_g']} g")
            a5.metric("Fiber", f"{plan_totals['fiber_g']} g")
            a6.metric("Est. cost", f"₱{plan_totals['cost_php']:.0f}")
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown('<div class="ff-card" style="margin-top: 12px;">', unsafe_allow_html=True)
            st.markdown('<p class="ff-section-title">Nutrition Gap Analysis</p>', unsafe_allow_html=True)
            st.markdown('<p class="ff-section-sub">Meal plan totals compared to your estimated daily targets.</p>', unsafe_allow_html=True)
            render_nutrition_gap_cards(gaps)
            st.markdown("</div>", unsafe_allow_html=True)

            if st.session_state.food_log:
                logged = calculate_logged_totals(st.session_state.food_log)
                rem = remaining_targets(logged, targets)
                st.markdown('<div class="ff-card" style="margin-top: 12px;">', unsafe_allow_html=True)
                st.markdown("### Logged Food vs Targets")
                l1, l2, l3, l4, l5 = st.columns(5)
                l1.metric("Calories remaining", f"{rem['calories']:.0f} kcal")
                l2.metric("Protein remaining", f"{rem['protein_g']:.0f} g")
                l3.metric("Carbs remaining", f"{rem['carbs_g']:.0f} g")
                l4.metric("Fats remaining", f"{rem['fats_g']:.0f} g")
                l5.metric("Fiber remaining", f"{rem['fiber_g']:.0f} g")
                st.markdown("</div>", unsafe_allow_html=True)

            st.caption("Personalized recommendations appear on the Overview tab after you click Generate Recommendations.")

    render_footer_disclaimer()
    render_developer_debug(recipes_df, clean_foods_df, curated_foods_df)


if __name__ == "__main__":
    main()
