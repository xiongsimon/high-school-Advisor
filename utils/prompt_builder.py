def build_prompt(template: str, profile: dict) -> str:
    def join_or_default(key):
        return ", ".join(profile.get(key, [])) or "Not specified"

    return template.format(
        interests=join_or_default("interests"),
        work_style=join_or_default("work_style"),
        strengths=join_or_default("strengths"),
        academic_alignment=join_or_default("academic_alignment"),
        personality=join_or_default("personality"),
        workplace_setting=join_or_default("workplace_setting"),
        comfort_with_risk=join_or_default("comfort_with_risk"),
    )

def bpc(template: str, profile: dict) -> str:
    def join_or_default(key):
        return ", ".join(profile.get(key, [])) or "Not specified"

    return template.format(
        location=join_or_default("location"),
        budget=join_or_default("budget"),
        campus_size=join_or_default("campus_size"),
        admission_risk_tolerance=join_or_default("admission_risk_tolerance"),
        class_size_preference=join_or_default("class_size_preference"),
        campus_culture=join_or_default("campus_culture"),
        learning_preference=join_or_default("learning_preference"),
        extracurricular_interest=join_or_default("extracurricular_interest"),
        financial_aid_priority=join_or_default("financial_aid_priority"),
        career_services_importance=join_or_default("career_services_importance"),
        institution_type=join_or_default("institution_type"),
    )
