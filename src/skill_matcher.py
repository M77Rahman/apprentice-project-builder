from typing import List

def find_skill_gaps(cv_skills: List[str], market_skills: List[str]) -> List[str]:
    """Compare your skills to market skills and return what's missing."""
    return sorted(list(set(market_skills) - set(cv_skills)))
