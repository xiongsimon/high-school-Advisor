import openai
from planner_agent.prompts import build_student_prompt

class StudyPlannerAgent:
    def __init__(self, api_key):
        openai.api_key = api_key

    def get_plan(self, student_profile: dict) -> str:
        prompt = build_student_prompt(student_profile)
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert academic advisor."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        return response['choices'][0]['message']['content']
