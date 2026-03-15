import google.generativeai as genai
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
import platform
import matplotlib.pyplot as plt
import numpy as np
from utils.prompt_builder import *

# === CONFIG ===
GEMINI_MODEL = "gemini-2.5-pro"
DONE_KEYWORD = "done"
OTHER_KEYWORD = "Other"

# === LOGGING SETUP ===
log_stream = io.StringIO()
original_stdout = sys.stdout  # keep reference to terminal

def logged_input(prompt):
    """Input that logs both prompt and user response."""
    print(prompt, end="", flush=True, file=original_stdout)  # show prompt to user
    log_stream.write(prompt + "\n")  # log the prompt
    user_input = input()  # read user input from terminal
    log_stream.write(user_input + "\n")  # log user input
    return user_input

def user_print(*args, **kwargs):
    """Print to terminal and log everything."""
    print(*args, **kwargs, file=original_stdout)
    log_stream.write(" ".join(str(a) for a in args) + "\n")

# === GEMINI KEY CHECK ===
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("Missing GEMINI_API_KEY environment variable")
genai.configure(api_key=api_key)

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

def query_gemini(template_file, profile):
    """Build prompt from template + profile and query Gemini."""
    with open(template_file) as f:
        template = f.read()
    prompt = build_prompt(template, profile)
    print(prompt)

    try:
        response = genai.GenerativeModel(GEMINI_MODEL).generate_content(prompt)
    except Exception as e:
        print(f"❌ Gemini API error: {e}")
        return ""

    output = response.text
    print("\n> 🔍 Analyzing your profile...\n")
    print(output)
    return output

def query_geminibpc(template_file, profile):
    """Build prompt from template + profile and query Gemini."""
    with open(template_file) as f:
        template = f.read()
    prompt = bpc(template, profile)
    print(prompt)

    try:
        response = genai.GenerativeModel(GEMINI_MODEL).generate_content(prompt)
    except Exception as e:
        print(f"❌ Gemini API error: {e}")
        return ""

    output = response.text
    print("\n> 🔍 Analyzing your profile...\n")
    print(output)
    return output

# === RADAR CHART ===
def generate_radar_chart(scores, filename="radar_chart.png"):
    """Generates and saves a radar chart given a dict of scores."""
    categories = list(scores.keys())
    values = list(scores.values())

    # Close radar chart loop
    values += values[:1]
    N = len(categories)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    ax.plot(angles, values, linewidth=2, linestyle="solid")
    ax.fill(angles, values, alpha=0.3)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories)
    ax.set_yticks(range(0, 11, 2))
    ax.set_yticklabels(map(str, range(0, 11, 2)))
    ax.set_ylim(0, 10)
    ax.set_title("College Alignment Radar Chart", size=14, pad=20)

    plt.tight_layout()
    plt.savefig(filename, dpi=150)
    plt.close()
    print(f"📈 Radar chart saved as {filename}")
    return filename

def radar_chart_phase(profile):
    """Uses Gemini to score 5 dimensions and generate a radar chart."""
    with open("prompts/radar_prompt_template.txt") as f:
        template = f.read()

    prompt = template.format(
        college=", ".join(profile.get("college", [])),
        academics=", ".join(profile.get("academics", [])),
        leadership=", ".join(profile.get("leadership", [])),
        project_experience=", ".join(profile.get("project_experience", [])),
        passion=", ".join(profile.get("passion", [])),
        awards=", ".join(profile.get("awards", []))
    )

    try:
        response = genai.GenerativeModel(GEMINI_MODEL).generate_content(prompt)
    except Exception as e:
        print(f"❌ Gemini API error: {e}")
        return

    output = response.text
    print("\n> 📊 Gemini alignment scores & reasoning:\n")
    print(output)

    # Extract scores
    pattern = r"\*\*(?:Academic Achievements|Leadership|Project Experience|Character / Passion|Awards & Recognition)\*\*: (\d+)"
    matches = re.findall(pattern, output)
    categories = [
        "Academic Achievements",
        "Leadership",
        "Project Experience",
        "Character / Passion",
        "Awards & Recognition",
    ]

    if len(matches) != len(categories):
        print("⚠️ Could not parse all scores from Gemini output.")
        return

    scores = {cat: int(score) for cat, score in zip(categories, matches)}
    chart_file = generate_radar_chart(scores, filename="college_alignment_radar.png")
    return chart_file

def extract_majors(text):
    pattern = r"\d+\.\s*\*?Major\*?:\s*(.+)"
    return re.findall(pattern, text)

def save_log_to_pdf(filename, image_path=None):
    """Save all terminal interactions and optionally embed an image."""
    sys.stdout = original_stdout
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_text = f"Session started: {timestamp}\n\n" + log_stream.getvalue()

    c = canvas.Canvas(filename, pagesize=letter)
    text_obj = c.beginText(40, 750)
    text_obj.setFont("Courier", 9)

    for line in log_text.splitlines():
        for wrapped_line in textwrap.wrap(line, width=90):
            text_obj.textLine(wrapped_line)
            if text_obj.getY() < 150:
                c.drawText(text_obj)
                if image_path and os.path.exists(image_path):
                    c.drawImage(image_path, 150, 50, width=300, preserveAspectRatio=True, mask='auto')
                    image_path = None
                c.showPage()
                text_obj = c.beginText(40, 750)
                text_obj.setFont("Courier", 9)

    c.drawText(text_obj)
    if image_path and os.path.exists(image_path):
        c.drawImage(image_path, 150, 50, width=300, preserveAspectRatio=True, mask='auto')

    c.save()
    print(f"\n📄 All interactions logged to {filename}")

# === MAIN FLOW ===
if __name__ == "__main__":
    print("\nWelcome to MajorMatch CLI (Gemini Edition)!\n")

    profile = {}
    ask_questions("utils/career_match.json", profile)
    major_text = query_gemini("prompts/major_prompt_template.txt", profile)
    majors = extract_majors(major_text)
    personality = profile.get("personality", [])

    if logged_input("\nWould you like to continue with selecting a college? (Enter to continue): ") != "":
        save_log_to_pdf("session_log.pdf")
        exit()

    ask_questions("utils/college_match.json", college_profile)
    query_geminibpc("prompts/college_prompt_template.txt", college_profile)

    if logged_input("\nGenerate radar chart showing how well you align with your target college's expectations? (Enter to continue): ") != "":
        save_log_to_pdf("session_log.pdf")
        exit()

    chart_file = radar_chart_phase(college_profile)
    save_log_to_pdf("session_log.pdf", image_path=chart_file)
