import json
from typing import List
import streamlit as st

def _fallback_projects(skill_gaps: List[str]):
    """Offline fallback generator — makes simple briefs for each missing skill."""
    if not skill_gaps:
        skill_gaps = ["APIs", "Power BI", "Linux"]

    projects = []
    for g in skill_gaps[:3]:
        projects.append({
            "title": f"{g} Practice Project",
            "summary": f"Build a hands-on mini project to strengthen {g} skills.",
            "objectives": [
                f"Implement a small feature using {g}.",
                "Document progress and key learnings.",
                "Add screenshots or a short demo."
            ],
            "key_skills": [g],
            "tools": ["Python"],
            "difficulty": "Intermediate",
            "github_repo_name": f"{g.lower().replace(' ', '-')}-practice",
            "acceptance_criteria": [
                "All main features function correctly.",
                "Project runs without errors.",
                "README clearly documents setup and usage."
            ],
            "starter_tasks": [
                "Set up project folder and virtual environment.",
                "Initialize a GitHub repository.",
                f"Implement one basic {g}-related feature."
            ]
        })
    return projects


def generate_projects(skill_gaps: list, cv_skills: list, job_skills: list):
    """Return 3 detailed project briefs (prefers local Ollama)."""
    try:
        # use local AI generator (Gemma via Ollama)
        from src.ai_generator import generate_ai_projects
        return generate_ai_projects(cv_skills, skill_gaps, job_skills)

    except Exception as e:
        st.warning(f"AI generation failed ({e}); using fallback.")
        return _fallback_projects(skill_gaps)
