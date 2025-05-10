from fastapi import FastAPI, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from data_loader import find_recipes_by_ingredients
from typing import List
import csv
import os
from pathlib import Path


app = FastAPI()

# Allow all origins (not recommended for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Use specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Recipe Generator API is running!"}

@app.post("/find-recipes/")
def find_recipes(ingredients: str = Form(...)):
    """
    Accepts a comma-separated string of ingredients and returns matching recipes.
    """
    user_ingredients = [item.strip() for item in ingredients.split(',')]
    recipes = find_recipes_by_ingredients(user_ingredients)
    return {"matches": recipes}


CSV_FILE = Path("final.csv")

# Ingredient cache to avoid redundant parsing
ingredient_cache = {
    "ingredients": set(),
    "last_file_size": 0,
    "last_modified_time": 0
}

def extract_unique_ingredients():
    """
    Read ingredients column from CSV and return a deduplicated set.
    """
    unique_ingredients = set()

    try:
        with open(CSV_FILE, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                ingredients_raw = row.get("ingredients", "")
                ingredients = [item.strip().lower() for item in ingredients_raw.split(",") if item.strip()]
                unique_ingredients.update(ingredients)
    except Exception as e:
        print("Error reading CSV:", e)

    return unique_ingredients

@app.get("/ingredients", response_model=List[str])
def get_ingredients():
    """
    Return unique ingredients from CSV. Refreshes only if file changes.
    """
    file_stats = os.stat(CSV_FILE)
    current_size = file_stats.st_size
    current_modified = file_stats.st_mtime

    if (
        current_size != ingredient_cache["last_file_size"]
        or current_modified != ingredient_cache["last_modified_time"]
        or not ingredient_cache["ingredients"]
    ):
        print("Change detected in CSV. Reloading ingredients...")
        new_ingredients = extract_unique_ingredients()
        ingredient_cache["ingredients"] = new_ingredients
        ingredient_cache["last_file_size"] = current_size
        ingredient_cache["last_modified_time"] = current_modified
    else:
        print("Using cached ingredient list.")
        
    return sorted(list(ingredient_cache["ingredients"]))



# Load all recipes from the CSV
def load_recipes():
    recipes = []
    try:
        with open(CSV_FILE, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                recipes.append(row)
    except Exception as e:
        print("Error reading CSV:", e)
    return recipes

# Load the recipes once at startup
all_recipes = load_recipes()

@app.get("/search")
def search_recipe(query: str = Query(..., min_length=2, description="Name of the recipe to search")):
    query_lower = query.strip().lower()
    matches = [r for r in all_recipes if query_lower in r.get("name", "").lower()]

    if not matches:
        raise HTTPException(status_code=404, detail="Recipe not found")

    results = []
    for match in matches:
        results.append({
            "name": match.get("name", ""),
            "description": match.get("description", ""),
            "ingredients": match.get("ingredients", ""),
            "detailed_ingredients": match.get("detailed_ingredients", ""),
            "instructions": match.get("instructions", ""),
            "cuisine": match.get("cuisine", ""),
            "course": match.get("course", ""),
            "diet": match.get("diet", "")
        })

    return results

