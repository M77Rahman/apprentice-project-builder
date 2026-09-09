import json
from collections import Counter


def load_json(path: str):
    """Load any JSON file safely."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def top_skills_from_jobs(jobs, n: int = 20):
    """Return the most common skills from job data, most frequent first.

    Pass n=None to get every skill that appears, fully ranked by frequency
    (useful when a caller needs to rank a larger set, not just a top slice).
    """
    c = Counter()
    for j in jobs:
        c.update(j.get("skills", []))
    if n is None:
        return [s for s, _ in c.most_common()]
    return [s for s, _ in c.most_common(n)]


def skill_frequency(jobs) -> Counter:
    """Return a Counter of how many jobs list each skill."""
    c = Counter()
    for j in jobs:
        c.update(j.get("skills", []))
    return c
