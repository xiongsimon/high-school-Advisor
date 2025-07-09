import streamlit as st
from planner_agent.agent import StudyPlannerAgent
import os

st.title("🎓 High School Study Planner AI")

st.sidebar.header("Student Profile")

grade = st.sidebar.selectbox("Grade", ["9", "10", "11", "12"])
interests = st.sidebar.text_area("Interests (comma separated)", "Science, Engineering")
strengths = st.sidebar.text_area("Strengths (comma separated)", "Math, Problem-solving")
careers = st.sidebar.text_area("Career Goals", "Engineer, Researcher")
colleges = st.sidebar.text_area("Target Colleges", "MIT, Stanford")

api_key = st.sidebar.text_input("OpenAI API Key", type="password")

if st.button("Generate Plan") and api_key:
    profile = {
        "grade": grade,
        "interests": [i.strip() for i in interests.split(",")],
        "strengths": [s.strip() for s in strengths.split(",")],
        "career_goals": [c.strip() for c in careers.split(",")],
        "target_colleges": [c.strip() for c in colleges.split(",")],
    }

    agent = StudyPlannerAgent(api_key=api_key)
    with st.spinner("Thinking..."):
        plan = agent.get_plan(profile)
        st.subheader("📘 Your Personalized Plan:")
        st.markdown(plan)
