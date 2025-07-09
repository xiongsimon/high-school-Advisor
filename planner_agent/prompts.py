def build_student_prompt(profile: dict) -> str:
    return f"""
Student Profile:
- Grade: {profile.get("grade")}
- Interests: {", ".join(profile.get("interests", []))}
- Strengths: {", ".join(profile.get("strengths", []))}
- Preferred colleges: {", ".join(profile.get("target_colleges", []))}
- Career goals: {", ".join(profile.get("career_goals", []))}

Please provide a detailed study plan including:
1. Recommended subjects and electives
2. Suggested extracurricular activities
3. Relevant AP or IB courses
4. Matching college majors
5. Career preparation steps
"""
