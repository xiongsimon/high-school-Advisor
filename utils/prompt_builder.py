def build_prompt(template: str, profile: dict) -> str:
    return template.format(
        interests=", ".join(profile["interests"]),
        work_style=profile["work_style"],
        strengths=", ".join(profile["strengths"]),
        academic_alignment=", ".join(profile["academic_alignment"])
    )