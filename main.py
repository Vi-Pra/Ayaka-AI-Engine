from fastapi import FastAPI, Query, HTTPException, Path as FastAPIPath, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from typing import List, Optional
import csv
import os
from pathlib import Path
from data_loader import find_recipes_by_ingredients, get_recipe_by_id
# from  data_loader import RecipeSearchRequest;
app = FastAPI(
    title="Recipe Finder API",
    description="Search and Get Recipes",
    version="1.0"
)

# ✅ CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Models
class RecipeSummary(BaseModel):
    id: int
    name: str
    image: Optional[str]
    prep_time: Optional[str]
    description: Optional[str]
    diet_type: Optional[str]

class RecipeDetail(BaseModel):
    id: int
    name: str
    ingredients: List[str]
    instructions: str
    prep_time: Optional[str]
    serving: Optional[str]
    image: Optional[str]
    description: Optional[str]
    detailed_ingredients: Optional[str]
    cuisine: Optional[str]
    course: Optional[str]
    diet_type: Optional[str]

class RecipeSearchRequest(BaseModel):
    ingredients: List[str]
    search_mode: str  # strict / fuzzy

# ✅ Dummy Root API
@app.get("/")
def read_root():
    return {"message": "Recipe Generator API is running!"}

# ✅ Get Ingredients API with Caching
CSV_FILE = Path("final.csv")
ingredient_cache = {
    "ingredients": set(),
    "last_file_size": 0,
    "last_modified_time": 0
}

#  def extract_unique_ingredients():
#      unique_ingredients = set()
#      try:
#          with open(CSV_FILE, mode='r', encoding='utf-8') as file:
#              reader = csv.DictReader(file)
#              print(reader)
#              for row in reader:
#                  ingredients_raw = row.get("ingredients", "")
#                  print(ingredients_raw)
#                  ingredients = [item.strip().lower() for item in ingredients_raw.split(",") if item.strip()]
                
#                  unique_ingredients.update(ingredients)
#      except Exception as e:
#          print("Error reading CSV:", e)
#      return unique_ingredients

import csv
import ast  # For safe string to list conversion

def extract_unique_ingredients():
    ingredients = set()
    with open('final.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            raw_data = row.get('ingredients', '')
            if raw_data:
                try:
                    # ✅ Safely parse string list to Python list
                    parsed_data = ast.literal_eval(raw_data)
                    if isinstance(parsed_data, list):
                        ingredients.update(parsed_data)
                except (ValueError, SyntaxError) as e:
                    print(f"Skipping invalid row: {e} | Data: {raw_data}")
    return sorted(ingredients)

@app.get("/ingredients", response_model=List[str])
def get_ingredients():
    file_stats = os.stat(CSV_FILE)
    current_size = file_stats.st_size
    current_modified = file_stats.st_mtime

    if (
        current_size != ingredient_cache["last_file_size"]
        or current_modified != ingredient_cache["last_modified_time"]
        or not ingredient_cache["ingredients"]
    ):
        print("Reloading ingredients...")
        ingredient_cache["ingredients"] = extract_unique_ingredients()
        print('done')
        ingredient_cache["last_file_size"] = current_size
        ingredient_cache["last_modified_time"] = current_modified

    return sorted(list(ingredient_cache["ingredients"]))

# ✅ Search Recipes by Name API
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

all_recipes = load_recipes()

@app.get("/search", response_model=List[RecipeSummary])
def search_recipe(query: str = Query(..., min_length=2)):
    query_lower = query.strip().lower()
    matches = [r for r in all_recipes if query_lower in r.get("name", "").lower()]

    if not matches:
        raise HTTPException(status_code=404, detail="Recipe not found")

    results = []
    for match in matches:
        results.append({
            "id": int(match.get("id")),
            "name": match.get("name", ""),
            "image": match.get("image") or "",
            "prep_time": match.get("prep_time") or "",
            "description": match.get("description") or "",
            "diet_type": match.get("diet") or ""
        })

    return jsonable_encoder(results)

# ✅ Find Recipes by Ingredients API (using query params)
# @app.post("/find_recipes", response_model=List[RecipeSummary])
@app.post("/find_recipes")
def find_recipes(request: RecipeSearchRequest):
    # Normalize input ingredients (lowercase + strip spaces)
    ingredients = [ingredient.strip().lower() for ingredient in request.ingredients]
    search_mode = request.search_mode.lower()

    if search_mode not in ["strict", "fuzzy"]:
        raise HTTPException(status_code=400, detail="Invalid search_mode. Use 'strict' or 'fuzzy'.")

    recipes = find_recipes_by_ingredients(ingredients, search_mode)
    return JSONResponse(content=jsonable_encoder({"recipes": recipes}))

    ingredient_list = [ing.strip() for ing in request.ingredients if ing.strip()]
    search_mode = request.search_mode

    recipes = find_recipes_by_ingredients(ingredient_list, search_mode)
    if not recipes:
        raise HTTPException(status_code=404, detail="No matching recipes found")

    results = []
    for recipe in recipes:
        results.append({
            "id": int(recipe.get("id", 0)),
            "name": recipe.get("name", ""),
            "image": recipe.get("image") or "",
            "prep_time": recipe.get("prep_time") or "",
            "description": recipe.get("description") or "",
            "diet_type": recipe.get("diet") or ""
        })

    return jsonable_encoder(results)

# ✅ Get Full Recipe by ID API
@app.get("/recipe/{id}", response_model=RecipeDetail)
def get_recipe_detail(id: int = FastAPIPath(..., description="Unique Recipe ID")):
    recipe = get_recipe_by_id(id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    return jsonable_encoder({
        "id": int(recipe.get("id")),
        "name": recipe.get("name", ""),
        "ingredients": [i.strip().lower() for i in (recipe.get("ingredients") or "").split(",")],
        "instructions": recipe.get("instructions") or "",
        "prep_time": str(recipe.get("prep_time")) or "",
        "serving": str(recipe.get("serving")) or "",
        "image": recipe.get("image") or "",
        "description": recipe.get("description") or "",
        "detailed_ingredients": recipe.get("detailed_ingredients") or "",
        "cuisine": recipe.get("cuisine" ) or "",
        "course": recipe.get("course") or "",
        "diet_type": recipe.get("diet") or ""
    })
