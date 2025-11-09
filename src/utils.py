import json
from collections import Counter


def load_json(path: str):
    """Load any JSON file safely."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def top_skills_from_jobs(jobs, n: int = 20):
    """Return the top N most common skills from job data."""
    c = Counter()
    for j in jobs:
        c.update(j.get("skills", []))
    return [s for s, _ in c.most_common(n)]
