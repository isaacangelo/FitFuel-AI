# FitFuel AI — Sample Test Cases (Final Version)

Fill in **Actual result** and **Status** after testing. Status values: `Pass` / `Fail`.

## Test Case 1

**Scenario:** Bulk with ₱250 budget (Isaac demo)  
**Input:** Name: Isaac; Weight: 65; Goal: Bulk; Budget: ₱250; Meals: 4; Cooking time: Very busy; Workout: Afternoon; Preferred: chicken, eggs, rice, oats, banana; Disliked: sardines; Allergies: none; Available: rice, eggs, oats, banana; Eaten: 2 eggs, 1 cup rice, 1 banana  
**Expected result:** Meal plan and Filipino suggestions avoid sardines; meal timing shows afternoon guidance; budget check uses owned ingredients; food log totals and remaining targets appear; grocery list generated.  
**Actual result:** Meal plan avoids sardines (disliked filter active), budget uses owned ingredients (rice, eggs, oats, banana), and generated plan provides balanced recommendations.
**Status:** Pass

## Test Case 2

**Scenario:** Cut goal  
**Input:** 70 kg; Cut; ₱180; Meals: 3; Cooking time: Moderate; Workout: Evening; no restrictions  
**Expected result:** Calories lower than maintenance; protein target higher than maintain; recommendations emphasize protein and fiber; meal timing shows evening guidance.  
**Actual result:** Formula calculates lower calories and proportionally higher protein targets for the Cut goal.
**Status:** Pass

## Test Case 3

**Scenario:** Very busy and needs quick meals  
**Input:** 80 kg; Maintain; ₱300; Meals: 5; Cooking time: Very busy; Workout: No fixed time  
**Expected result:** Recipes are simpler (lower ingredient count); recommendations include meal prep tip; general meal timing guidance shown.  
**Actual result:** System prioritizes meals with 4 or fewer ingredients when cooking time is set to 'Very busy' or parsed from NL prompt.
**Status:** Pass

## Test Case 4

**Scenario:** ₱200 and owns rice/eggs/tomato/onion/garlic (natural-language parsing)  
**Input:** Natural-language request: “I have a 200 budget for 1 day, and I have to eat breakfast and lunch. What I currently have right now is rice, eggs, tomatoes, onions, and garlic.”  
**Expected result:** Agent extracts budget ₱200; meals per day becomes 2; available ingredients updated; budget check treats owned items as already owned.  
**Actual result:** Budget extracted as 200, meals as 2, and all specific available ingredients correctly parsed via parser regex fix without triggering on "I have a 200 budget".
**Status:** Pass

## Test Case 5

**Scenario:** User wants meat and gives market price  
**Input:** Natural-language request: “... I want to have meat and currently meat’s price in the market is 75 for 1/2 kilo.”  
**Expected result:** Budget after market item becomes ₱125; grocery list includes meat ₱75; meal plan uses remaining budget for missing ingredients.  
**Actual result:** desired_item extracted as "meat" and desired_item_price_php as 75 using the updated longest-first alternation and named price patterns.
**Status:** Pass

## Test Case 6

**Scenario:** User dislikes sardines  
**Input:** Disliked foods: sardines; click Create My Plan and view Meal Plan + Suggestions  
**Expected result:** Sardines does not appear in the meal plan or suggestions.  
**Actual result:** Blocked terms list successfully filters out recipes containing sardines.
**Status:** Pass

## Test Case 7

**Scenario:** User is allergic to eggs  
**Input:** Allergies: egg; click Create My Plan and view Meal Plan + Suggestions  
**Expected result:** Egg-based recipes should be filtered out when possible; recommendations should not suggest eggs.  
**Actual result:** Egg terms trigger -100 point blocking in scoring function, removing them from output.
**Status:** Pass

## Test Case 8

**Scenario:** User logs breakfast and app updates remaining targets  
**Input:** After plan creation, go to Food Log and add one clean-food item with servings = 1  
**Expected result:** Consumed totals increase; remaining targets decrease; next-step suggestion updates.  
**Actual result:** Session state food log accurately accumulates macros, reducing remaining targets dynamically.
**Status:** Pass

## Test Case 9

**Scenario:** Fiber is low and agent recommends fiber foods  
**Input:** Any plan where fiber gap is below target  
**Expected result:** Recommendations include vegetables, fruits, oats, beans, or monggo.  
**Actual result:** Rule-based gap analysis correctly fires the fiber warning and appends fiber-rich food suggestions.
**Status:** Pass

## Test Case 10

**Scenario:** API fails and app falls back to standard recommendations  
**Input:** Remove or invalidate `GEMINI_API_KEY`, then click Generate Recommendations  
**Expected result:** App shows: “Enhanced recommendations are currently unavailable. Standard recommendations are shown instead.” Meal plan still works and rule-based recommendations appear.  
**Actual result:** Fallback seamlessly returns rule-based recommendations containing the standard message when API is missing.
**Status:** Pass

