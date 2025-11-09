import json
from typing import List
import streamlit as st

def _fallback_projects(skill_gaps: List[str]):
    """Offline fallback generator — makes simple briefs for each missing skill."""
    if not skill_gaps:
        skill_gaps = ["Python", "SQL", "APIs"]

    projects = []
    for g in skill_gaps[:3]:
        projects.append({
            "title": f"{g} Practice Project",
            "summary": f"Build a short project to strengthen your {g} skills.",
            "objectives": [
                f"Implement a core feature using {g}.",
                "Document progress and lessons learned.",
                "Add screenshots or a short demo video."
            ],
            "key_skills": [g],
            "tools": ["Python"],
            "difficulty": "Medium",
            "github_repo_name": f"{g.lower().replace(' ', '-')}-practice"
        })
    return projects


def generate_projects(skill_gaps: list, cv_skills: list, job_skills: list):
    """Return 3 project briefs (offline only — Ollama version)."""
    st.info("Using local generator (Ollama / fallback mode).")
    return _fallback_projects(skill_gaps)
