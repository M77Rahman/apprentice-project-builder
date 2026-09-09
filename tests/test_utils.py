from collections import Counter

from src.utils import skill_frequency, top_skills_from_jobs

JOBS = [
    {"title": "A", "skills": ["Python", "SQL"]},
    {"title": "B", "skills": ["Python", "Excel"]},
    {"title": "C", "skills": ["SQL"]},
]


def test_top_skills_from_jobs_counts_correctly():
    top = top_skills_from_jobs(JOBS, n=10)
    assert top[0] in ("Python", "SQL")  # both appear twice, tie is fine
    assert set(top) == {"Python", "SQL", "Excel"}


def test_top_skills_from_jobs_respects_n():
    top = top_skills_from_jobs(JOBS, n=1)
    assert len(top) == 1
    assert top[0] in ("Python", "SQL")


def test_top_skills_from_jobs_n_none_returns_everything():
    top = top_skills_from_jobs(JOBS, n=None)
    assert set(top) == {"Python", "SQL", "Excel"}
    assert len(top) == 3


def test_skill_frequency_counts_match_manual_counter():
    freq = skill_frequency(JOBS)
    expected = Counter({"Python": 2, "SQL": 2, "Excel": 1})
    assert freq == expected


def test_skill_frequency_handles_jobs_without_skills_key():
    freq = skill_frequency([{"title": "X"}])
    assert freq == Counter()
