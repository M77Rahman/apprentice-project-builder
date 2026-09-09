from typing import List

from .utils import top_skills_from_jobs


def find_skill_gaps(cv_skills: List[str], market_skills: List[str]) -> List[str]:
    """Return the skills present in market_skills but missing from cv_skills.

    Plain set difference, alphabetically sorted — use rank_skill_gaps() when
    the gaps need to be prioritised by how in-demand each one is.
    """
    return sorted(set(market_skills) - set(cv_skills))


def rank_skill_gaps(cv_skills: List[str], jobs: List[dict]) -> List[str]:
    """Return every skill gap across `jobs`, ranked most in-demand first.

    "In demand" means how many job listings require the skill, computed via
    utils.top_skills_from_jobs(). This is what should decide which gaps
    become generated projects, rather than an arbitrary/alphabetical slice.
    """
    ranked_all = top_skills_from_jobs(jobs, n=None)
    cv_set = set(cv_skills)
    return [skill for skill in ranked_all if skill not in cv_set]


def top_skill_gaps(cv_skills: List[str], jobs: List[dict], n: int = 3) -> List[str]:
    """Return the top `n` highest-priority skill gaps for `cv_skills` vs `jobs`."""
    return rank_skill_gaps(cv_skills, jobs)[:n]
