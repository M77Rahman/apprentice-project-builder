from src.project_generator import generate_projects, REQUIRED_KEYS

JOBS = [
    {"title": "Data Analyst Apprentice", "skills": ["SQL", "Excel", "Power BI", "Python"]},
    {"title": "Cyber Security Apprentice", "skills": ["Linux", "Networking", "Python"]},
    {"title": "Software Engineering Apprentice", "skills": ["Git", "CI/CD", "JavaScript"]},
]


def test_fallback_mode_used_without_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    projects, mode = generate_projects(["SQL", "Networking", "Git"], ["Python"], JOBS)
    assert mode == "template"
    assert len(projects) == 3


def test_fallback_projects_have_every_required_field_populated(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    projects, _ = generate_projects(["SQL", "Docker", "Excel"], ["Python", "Git"], JOBS)
    for project in projects:
        for key in REQUIRED_KEYS:
            assert key in project, f"missing key {key}"
            assert project[key], f"empty value for {key}"


def test_fallback_tools_vary_by_skill(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    sql_projects, _ = generate_projects(["SQL"], ["Python"], JOBS)
    docker_projects, _ = generate_projects(["Networking"], ["Python"], JOBS)
    assert sql_projects[0]["tools"] != docker_projects[0]["tools"]


def test_fallback_difficulty_reflects_skill_overlap(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    # candidate already has every other skill the Power BI-needing job wants
    high_overlap_projects, _ = generate_projects(
        ["Power BI"], ["SQL", "Excel", "Python"], JOBS
    )
    # candidate has none of the other skills required alongside SQL
    low_overlap_projects, _ = generate_projects(["SQL"], [], JOBS)
    assert high_overlap_projects[0]["difficulty"] == "Easy"
    assert low_overlap_projects[0]["difficulty"] == "Hard"


def test_generate_projects_falls_back_to_defaults_when_no_gaps(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    projects, mode = generate_projects([], ["Python"], JOBS)
    assert mode == "template"
    assert len(projects) == 3
