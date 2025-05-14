from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer

# Local model path
model_path = "/home/vivek/Major_Project/fastapi/Project/fine-tuned-gpt2-recipes"

# Load model & tokenizer from local path
model = AutoModelForCausalLM.from_pretrained(model_path)
tokenizer = AutoTokenizer.from_pretrained(model_path)

generator = pipeline("text-generation", model=model_path, tokenizer=model_path)

def generate_ai_recipe(ingredients: list[str]) -> str:
    # Prepare the prompt string from ingredients
    prompt = f"Ingredients: {', '.join(ingredients)}"
    print(f"Prompt for AI: {prompt}")
    # Generate recipe text
    output = generator(prompt, max_length=300, truncation=True, do_sample=True, temperature=0.8)
    
    # Return the generated recipe text
    return output[0]['generated_text']
        
# print(generate_ai_recipe(["chicken", "rice", "broccoli"]))

