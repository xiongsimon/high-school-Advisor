import openai
import os
from utils.prompt_builder import build_prompt

# Insert your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY") or "sk-...your-key..."

def get_choice(prompt, options):
    print(prompt)
    for i, option in enumerate(options, 1):
        print(f"{i}) {option}")
    while True:
        try:
            choice = int(input("> "))
            if 1 <= choice <= len(options):
                return options[choice - 1]
        except ValueError:
            pass
        print("Invalid choice. Please enter the number next to your selection.")

print("Welcome to MajorMatch CLI!\n")

# Collect user responses
activity = input("What's something you've done recently that felt fun or rewarding?\n")
work_style = get_choice("Do you prefer working with people or solo?", ["With people", "Solo"])
appeal = get_choice("Which of these appeals most?", ["Design", "Persuasive writing", "Building things", "Logic puzzles"])

# Build profile (in real use, enhance with NLP or more logic)
profile = {
    "interests": ["visual communication" if "Design" in appeal else "problem-solving"],
    "work_style": "collaborative leader" if "people" in work_style.lower() else "independent thinker",
    "strengths": ["organization", "creativity"] if "prom" in activity.lower() else ["analysis", "focus"],
    "academic_alignment": ["marketing", "design"] if "Design" in appeal else ["engineering", "computer science"]
}

# Build prompt
with open("prompts/major_prompt_template.txt") as f:
    template = f.read()
prompt = build_prompt(template, profile)

# Query GPT
response = openai.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a college guidance counselor."},
        {"role": "user", "content": prompt}
    ]
)

print("\n> 🔍 Analyzing your profile...\n")
print(response.choices[0].message.content)
