# import pandas as pd

# # Load the CSV only once to memory
# df = pd.read_csv("final.csv")

# def clean_ingredient_string(ingredient_string):
#     if pd.isna(ingredient_string):
#         return []
#     return [i.strip().lower() for i in ingredient_string.split(',')]

# # Search recipes containing ALL given ingredients
# def find_recipes_by_ingredients(user_ingredients):
#     user_ingredients = [i.strip().lower() for i in user_ingredients]

#     matched_recipes = []

#     for _, row in df.iterrows():
#         recipe_ingredients = clean_ingredient_string(row.get('ingredients'))
        
#         if all(ingredient in recipe_ingredients for ingredient in user_ingredients):
#             matched_recipes.append({
#                 'name': row.get('name'),
#                 'ingredients': recipe_ingredients,
#                 'instructions': row.get('instructions'),
#                 'prep_time': row.get('prep_time'),
#                 'serving': row.get('serving'),
#                 'image': row.get('image')
#             })

#     return matched_recipes
import pandas as pd
import math

# Load the CSV only once to memory
df = pd.read_csv("final.csv")

def clean_ingredient_string(ingredient_string):
    if pd.isna(ingredient_string):
        return []
    return [i.strip().lower() for i in str(ingredient_string).split(',')]

def safe_value(val):
    """Convert NaN, inf, or unsupported types to safe JSON-compatible values."""
    if pd.isna(val) or isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        return None
    return val

# Search recipes containing ALL given ingredients
def find_recipes_by_ingredients(user_ingredients):
    user_ingredients = [i.strip().lower() for i in user_ingredients]

    matched_recipes = []

    for _, row in df.iterrows():
        recipe_ingredients = clean_ingredient_string(row.get('ingredients'))
        recipe_ingredient_set = set(recipe_ingredients)
        
        if all(ingredient in recipe_ingredients for ingredient in user_ingredients):
            matched_recipes.append({
                'name': safe_value(row.get('name')),
                'ingredients': recipe_ingredients,
                'instructions': safe_value(row.get('instructions')),
                'prep_time': safe_value(row.get('prep_time')),
                'serving': safe_value(row.get('serving')),
                'image': safe_value(row.get('image')),
            })

    return matched_recipes
