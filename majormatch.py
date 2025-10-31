import openai
import os
from utils.prompt_builder import build_prompt
import json
from pathlib import Path

# Insert your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY") or "sk-...your-key..."

def get_choice(prompt, options):
    print(prompt)
    for i, option in enumerate(options, 1):
        print(f"{i}) {option}")
    
    # Allow user to select a number
    while True:
        try:
            choice = int(input("> "))
            if 1 <= choice <= len(options):
                selected_option = options[choice - 1]
                
                # If the user selects "Other", prompt for additional input
                if "Other" in selected_option:
                    responses = []
                    print("You selected 'Other'. Please enter your choices one by one.")
                    print("Type 'done' when you're finished.")
                    while True:
                        response = input("Add another option (or type 'done' to finish): ")
                        if response.strip().lower() == "done":
                            break
                        elif response.strip():
                            responses.append(response.strip())
                    if responses:
                        return responses  # Return multiple responses as a list
                    else:
                        return [selected_option]  # Return just the "Other" option if nothing was entered
                else:
                    return [selected_option]  # Return the selected option
            else:
                print("Invalid choice. Please enter the number next to your selection.")
        except ValueError:
            print("Invalid choice. Please enter a valid number.")


print("Welcome to MajorMatch CLI!\n")

# Build profile based on the answers
profile = {}
# profile = {
#     "interests": [],
#     "work_style": [],
#     "strengths": [],
#     "academic_alignment": [],
#     "personality": [],
#     "workplace_setting": [],
#     "comfort_with_risk":[],
#     "natural_skills": []
# }

# Mapping helper function
def map_choices_to_profile(choices, rule_dict, profile_key):
    for keyword, mapped_value in rule_dict.items():
        if any(keyword in choice for choice in choices):
            profile.setdefault(profile_key, []).append(mapped_value)


with open("utils/career_match.json") as f:
    questions = json.load(f)

responses = {}
for q in questions:
    responses[q["key"]] = get_choice(q["question"], q["options"])
    profile[q["key"]] =responses[q["key"]] 

# Final profile output for clarity
print(profile)
print("that was profile")

# Build prompt
with open("prompts/major_prompt_template.txt") as f:
    template = f.read()
prompt = build_prompt(template, profile)

print(prompt)

#Query GPT
response = openai.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "system", "content": "You are a college guidance counselor."},
              {"role": "user", "content": prompt}]
)

print("\n> 🔍 Analyzing your profile...\n")
print(response.choices[0].message.content)
