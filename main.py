import openai
import os
import json
from pathlib import Path
import re
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime
import textwrap
import sys
#import matplotlib.pyplot as plt
import platform
from utils.prompt_builder import *


# === CONFIG ===
OPENAI_MODEL = "gpt-4"
DONE_KEYWORD = "done"
OTHER_KEYWORD = "Other"

# === LOGGING SETUP ===
log_stream = io.StringIO()
original_stdout = sys.stdout
sys.stdout = log_stream  # capture all print output

def logged_input(prompt):
    """Input that logs both prompt and user response."""
    print(prompt, end="", flush=True)
    log_stream.write(prompt + "\n")
    user_input = input()
    log_stream.write(user_input + "\n")
    return user_input

# === OPENAI KEY CHECK ===
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("Missing OPENAI_API_KEY environment variable")
openai.api_key = api_key

# === CLI FUNCTIONS ===
def get_choice(prompt, options):
    print(prompt)
    if not options:
        return _get_freeform_list()

    for i, option in enumerate(options, 1):
        print(f"{i}) {option}")

    while True:
        try:
            choice = int(logged_input("> "))
            if 1 <= choice <= len(options):
                selected_option = options[choice - 1]
                if OTHER_KEYWORD in selected_option:
                    return _get_freeform_list()
                return [selected_option]
            else:
                print("Invalid choice. Please enter the number next to your selection.")
        except ValueError:
            print("Invalid choice. Please enter a valid number.")

def _get_freeform_list():
    responses = []
    print(f"Please enter your choices one by one. Type '{DONE_KEYWORD}' when finished.")
    while True:
        response = logged_input("Add another option: ")
        if response.strip().lower() == DONE_KEYWORD:
            break
        elif response.strip():
            responses.append(response.strip())
    return responses if responses else []

def ask_questions(json_file, profile):
    """Load questions from JSON and append answers to profile."""
    with open(json_file) as f:
        questions = json.load(f)
    for q in questions:
        profile[q["key"]] = get_choice(q["question"], q["options"])
    return profile

def query_gpt(template_file, profile):
    """Build prompt from template + profile and query GPT."""
    with open(template_file) as f:
        template = f.read()
    prompt = build_prompt(template, profile)  # from utils.prompt_builder
    print(prompt)

    try:
        response = openai.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a college guidance counselor."},
                {"role": "user", "content": prompt}
            ]
        )
    except Exception as e:
        print(f"❌ OpenAI API error: {e}")
        return ""

    output = response.choices[0].message.content
    print("\n> 🔍 Analyzing your profile...\n")
    print(output)
    return output

def generate_radar_chart(scores, filename="radar_chart.png"):
    """Generates and saves a radar chart given a dict of scores."""
    categories = list(scores.keys())
    values = list(scores.values())

    # Close the radar chart loop
    values += values[:1]
    angles = [n / float(len(categories)) * 2 * 3.14159 for n in range(len(categories))]
    angles += angles[:1]


def radar_chart_phase(profile):
    """
    Uses the radar prompt template to get 5 scores + reasoning from GPT,
    then generates a radar chart from the scores.
    """
    # Load your radar chart scoring template
    with open("prompts/radar_prompt_template.txt") as f:
        template = f.read()

    # Fill in the template with profile data
    prompt = template.format(
        college=", ".join(profile.get("college", [])),
        academics=", ".join(profile.get("academics", [])),
        leadership=", ".join(profile.get("leadership", [])),
        project_experience=", ".join(profile.get("project_experience", [])),
        passion=", ".join(profile.get("passion", [])),
        awards=", ".join(profile.get("awards", []))
    )

    try:
        response = openai.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert in U.S. college admissions and can assess how a student's achievements align with a college's expectations."},
                {"role": "user", "content": prompt}
            ]
        )
    except Exception as e:
        print(f"❌ OpenAI API error: {e}")
        return

    output = response.choices[0].message.content
    print("\n> 📊 GPT alignment scores & reasoning:\n")
    print(output)

    # Extract numbers for radar chart
    pattern = r"\*\*(?:Academic Achievements|Leadership|Project Experience|Character / Passion|Awards & Recognition)\*\*: (\d+)"
    matches = re.findall(pattern, output)
    categories = ["Academic Achievements", "Leadership", "Project Experience", "Character / Passion", "Awards & Recognition"]

    if len(matches) != len(categories):
        print("⚠️ Could not parse all scores from GPT output.")
        return

    scores = {cat: int(score) for cat, score in zip(categories, matches)}
    generate_radar_chart(scores, filename="college_alignment_radar.png")


def extract_majors(text):
    """Extract majors from GPT output using regex."""
    pattern = r"\d+\.\s*\*?Major\*?:\s*(.+)"
    return re.findall(pattern, text)

def save_log_to_pdf(filename):
    """Save full log output to PDF."""
    sys.stdout = original_stdout  # restore stdout
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_text = f"Session started: {timestamp}\n\n" + log_stream.getvalue()

    c = canvas.Canvas(filename, pagesize=letter)
    text_obj = c.beginText(40, 750)
    text_obj.setFont("Courier", 9)

    for line in log_text.splitlines():
        for wrapped_line in textwrap.wrap(line, width=90):
            text_obj.textLine(wrapped_line)
            if text_obj.getY() < 40:
                c.drawText(text_obj)
                c.showPage()
                text_obj = c.beginText(40, 750)
                text_obj.setFont("Courier", 9)

    c.drawText(text_obj)
    c.save()
    print(f"\n📄 All interactions logged to {filename}")

# === MAIN RUN FLOW ===
if __name__ == "__main__":
    print("Welcome to MajorMatch CLI!\n")

    # Phase 1: Majors
    profile = {}
    ask_questions("utils/career_match.json", profile)
    major_text = query_gpt("prompts/major_prompt_template.txt", profile)
    majors = extract_majors(major_text)
    personality = profile.get("personality", [])

    if logged_input("\nWould you like to continue with selecting a college? (Enter to continue): ") != "":
        save_log_to_pdf("session_log.pdf")
        exit()

    # Phase 2: Colleges
    college_profile = {"major": majors, "personality": personality}
    ask_questions("utils/college_match.json", college_profile)
    query_gpt("prompts/college_prompt_template.txt", college_profile)


    # Phase 3: Radar Chart of College Alignment
    if logged_input("\nGenerate radar chart showing how well you align with your target college's expectations? (Enter to continue): ") != "":
        save_log_to_pdf("session_log.pdf")
        exit()

    radar_chart_phase(college_profile)


    # Save session log
    save_log_to_pdf("session_log.pdf")
