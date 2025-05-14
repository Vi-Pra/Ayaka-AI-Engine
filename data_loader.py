import pandas as pd
import math
import ast
from typing import List, Dict, Optional
from rapidfuzz import process, fuzz

# ✅ Load CSV once
try:
    df = pd.read_csv("final.csv")
except FileNotFoundError:
    raise FileNotFoundError("Error: 'final.csv' file not found. Please check the path.")

# ✅ Utility to clean ingredients string safely
def clean_ingredient_string(ingredient_data) -> List[str]:
    if pd.isna(ingredient_data):
        return []

    # Fix: If stringified list, parse it back to real list
    if isinstance(ingredient_data, str):
        try:
            ingredient_data = ast.literal_eval(ingredient_data)
        except (ValueError, SyntaxError):
            ingredient_data = ingredient_data.split(',')

    if not isinstance(ingredient_data, list):
        return []

    return [ing.strip().lower() for ing in ingredient_data if isinstance(ing, str) and ing.strip() != '']

# ✅ Safe value extraction
def safe_value(value, default=None):
    if pd.isna(value) or (isinstance(value, float) and (math.isinf(value) or math.isnan(value))):
        return default
    return value

# ✅ Fuzzy Strict Match Helper
def fuzzy_strict_match(user_ingredients: List[str], recipe_ingredients: List[str], threshold: int = 90) -> bool:
    if not recipe_ingredients:
        return False  # Nothing to match with

    for user_ing in user_ingredients:
        match_result = process.extractOne(user_ing, recipe_ingredients, scorer=fuzz.partial_ratio)
        if match_result is None:
            return False  # Can't match, so recipe is not a fit

        match, score = match_result[0], match_result[1]
        if score < threshold:
            return False  # this ingredient didn't match well enough

    return True  # All ingredients matched well


# ✅ Find recipes by ingredients (strict/fuzzy)
def find_recipes_by_ingredients(user_ingredients: List[str], search_mode: str) -> List[Dict]:
    print(user_ingredients, search_mode)
    if not user_ingredients:
        return []

    user_ingredients = [ing.strip().lower() for ing in user_ingredients]
    results = []

    for _, row in df.iterrows():
        ingredients_raw = row.get('ingredients')
        recipe_ingredients = clean_ingredient_string(ingredients_raw)

        print(recipe_ingredients)

        if search_mode == "strict":
            if fuzzy_strict_match(user_ingredients, recipe_ingredients):
                results.append({
                    "id": safe_value(row.get("id")),
                    "name": safe_value(row.get("name"), ""),
                    "image": safe_value(row.get("image"), ""),
                    "prep_time": str(safe_value(row.get("prep_time"), "")),
                    "description": safe_value(row.get("description"), ""),
                    "diet_type": safe_value(row.get("diet"), ""),
                })

        elif search_mode == "fuzzy":
            common_ingredients = set(user_ingredients) & set(recipe_ingredients)
            match_score = (len(common_ingredients) / len(user_ingredients)) * 100

            if match_score >= 30:
                results.append({
                    "score": match_score,
                    "recipe": {
                        "id": safe_value(row.get("id")),
                        "name": safe_value(row.get("name"), ""),
                        "image": safe_value(row.get("image"), ""),
                        "prep_time": safe_value(row.get("prep_time"), ""),
                        "description": safe_value(row.get("description"), ""),
                        "diet_type": safe_value(row.get("diet"), ""),
                    }
                })

        else:
            raise ValueError(f"Invalid search_mode '{search_mode}'. Use 'strict' or 'fuzzy'.")

    if search_mode == "fuzzy":
        results.sort(key=lambda x: x['score'], reverse=True)
        results = [item['recipe'] for item in results]

    return results

# ✅ Get detailed recipe by ID
def get_recipe_by_id(recipe_id: int) -> Optional[Dict]:
    recipe_row = df[df['id'] == recipe_id]
    if recipe_row.empty:
        return None

    row = recipe_row.iloc[0]

    return {
        "id": safe_value(row.get("id")),
        "name": safe_value(row.get("name"), ""),
        "ingredients": safe_value(row.get("ingredients"), ""),
        "instructions": safe_value(row.get("instructions"), ""),
        "prep_time": safe_value(row.get("prep_time"), ""),
        "serving": safe_value(row.get("serving"), ""),
        "image": safe_value(row.get("image"), ""),
        "description": safe_value(row.get("description"), ""),
        "detailed_ingredients": safe_value(row.get("detailed_ingredients"), ""),
        "cuisine": safe_value(row.get("cuisine"), ""),
        "course": safe_value(row.get("course"), ""),
        "diet": safe_value(row.get("diet"), ""),
    }
