from src.cv_parser import extract_skills_from_text

SKILLS = ["Python", "SQL", "Java", "JavaScript", "TypeScript", "Power BI", "Docker", "C#", "TCP/IP"]


def test_known_text_yields_known_skills():
    text = "Experienced with Python, SQL, and Docker in production."
    found = extract_skills_from_text(text, SKILLS)
    assert found == ["Docker", "Python", "SQL"]


def test_no_matches_returns_empty_list():
    text = "I enjoy painting and long walks on the beach."
    assert extract_skills_from_text(text, SKILLS) == []


def test_java_does_not_match_inside_javascript():
    text = "Built several apps using JavaScript and TypeScript."
    found = extract_skills_from_text(text, SKILLS)
    assert "Java" not in found
    assert "JavaScript" in found
    assert "TypeScript" in found


def test_java_matches_when_genuinely_present():
    text = "Backend written in Java, frontend in JavaScript."
    found = extract_skills_from_text(text, SKILLS)
    assert "Java" in found
    assert "JavaScript" in found


def test_skill_at_end_of_sentence_still_matches():
    text = "My strongest language is Python."
    assert "Python" in extract_skills_from_text(text, SKILLS)


def test_symbol_bearing_skill_matches_at_sentence_end():
    text = "I have professional experience with C#."
    assert "C#" in extract_skills_from_text(text, SKILLS)


def test_synonym_and_punctuation_variants_are_detected():
    text = "Built dashboards in Power-BI and networked servers over TCP IP."
    found = extract_skills_from_text(text, SKILLS)
    assert "Power BI" in found
    assert "TCP/IP" in found


def test_result_is_sorted_and_deduplicated():
    text = "Python python PYTHON SQL sql"
    found = extract_skills_from_text(text, SKILLS)
    assert found == ["Python", "SQL"]
