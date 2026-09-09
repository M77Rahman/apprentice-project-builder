from src.skill_matcher import find_skill_gaps, rank_skill_gaps, top_skill_gaps

JOBS = [
    {"title": "A", "skills": ["Python", "SQL", "Docker"]},
    {"title": "B", "skills": ["Python", "SQL", "Excel"]},
    {"title": "C", "skills": ["SQL", "Docker", "Linux"]},
    {"title": "D", "skills": ["Linux"]},
]


def test_find_skill_gaps_is_a_plain_set_difference():
    cv_skills = ["Python"]
    market_skills = ["Python", "SQL", "Docker", "Excel"]
    assert find_skill_gaps(cv_skills, market_skills) == ["Docker", "Excel", "SQL"]


def test_find_skill_gaps_empty_when_cv_covers_everything():
    assert find_skill_gaps(["Python", "SQL"], ["Python", "SQL"]) == []


def test_rank_skill_gaps_orders_by_job_frequency():
    # SQL appears in 3 jobs, Docker in 2, Excel in 1, Linux in 2 -> SQL first
    cv_skills = []
    ranked = rank_skill_gaps(cv_skills, JOBS)
    assert ranked[0] == "SQL"
    assert ranked.index("Docker") < ranked.index("Excel")


def test_rank_skill_gaps_excludes_known_skills():
    ranked = rank_skill_gaps(["SQL", "Python"], JOBS)
    assert "SQL" not in ranked
    assert "Python" not in ranked
    assert "Docker" in ranked


def test_top_skill_gaps_respects_n():
    top = top_skill_gaps([], JOBS, n=2)
    assert len(top) == 2
    assert top[0] == "SQL"
