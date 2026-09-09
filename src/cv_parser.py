import re

from pypdf import PdfReader
from rapidfuzz import fuzz

# Canonical skill -> alternate spellings/abbreviations seen on real CVs.
# Keys must match a skill name in data/skills_list.json.
SYNONYMS = {
    "Power BI": ["powerbi", "power-bi"],
    "JavaScript": ["js"],
    "TypeScript": ["ts"],
    "CI/CD": ["ci cd", "continuous integration", "continuous deployment"],
    "Node.js": ["nodejs", "node js"],
    "Vue.js": ["vuejs", "vue"],
    "Machine Learning": ["ml"],
    "Deep Learning": ["dl"],
    "NLP": ["natural language processing"],
    "scikit-learn": ["sklearn", "scikit learn"],
    "TensorFlow": ["tensor flow"],
    "PyTorch": ["torch"],
    ".NET": ["dot net", "dotnet"],
    "C#": ["c sharp", "csharp"],
    "C++": ["cpp", "c plus plus"],
    "REST": ["restful", "rest api", "rest apis"],
    "REST APIs": ["restful api", "restful apis"],
    "GraphQL": ["graph ql"],
    "GraphQL APIs": ["graphql api"],
    "SQL Server": ["mssql", "ms sql"],
    "PostgreSQL": ["postgres"],
    "Active Directory": ["ad "],
    "Windows Server Administration": ["windows server admin"],
    "Cyber Security": ["cybersecurity", "cyber-security", "infosec"],
    "Penetration Testing": ["pen testing", "pentesting", "pen-testing"],
    "Network Security": ["network sec"],
    "TCP/IP": ["tcp ip"],
    "GitHub Actions": ["github actions ci"],
    "AWS": ["amazon web services"],
    "GCP": ["google cloud platform", "google cloud"],
    "Azure": ["microsoft azure"],
    "Microsoft 365": ["office 365", "m365"],
    "Data Protection (GDPR)": ["gdpr"],
    "UX Design": ["user experience design"],
    "UI Design": ["user interface design"],
    "Object-Oriented Programming": ["oop"],
    "Shell Scripting": ["shell script", "bash scripting"],
    "PowerShell": ["power shell"],
}

# Skills that are short/common substrings of other skills in the list and
# therefore need whole-word matching only (no fuzzy match), to avoid false
# positives such as "Java" matching inside "JavaScript".
EXACT_ONLY = {"Java", "Go", "R", "C", "C++", "C#"}

FUZZY_THRESHOLD = 88


def extract_text_from_pdf(file) -> str:
    """Read all text from a PDF file."""
    reader = PdfReader(file)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _word_boundary_match(term: str, text_lower: str) -> bool:
    """True if `term` appears in `text_lower` without being embedded inside a
    larger alphanumeric word (so "Java" won't match inside "JavaScript").

    Only alphanumeric neighbours break the match — punctuation like a
    trailing "." or "," (sentence/list delimiters) does not, which lets
    symbol-bearing terms like "C#", "C++" and ".NET" match normally at the
    end of a sentence or list item.
    """
    pattern = r"(?<![a-z0-9])" + re.escape(term.lower()) + r"(?![a-z0-9])"
    return re.search(pattern, text_lower) is not None


def _fuzzy_match(term: str, text_lower: str) -> bool:
    """Fuzzy-match a multi-word/long term against sliding windows of the text."""
    words = text_lower.split()
    term_word_count = max(len(term.split()), 1)
    window = term_word_count + 1
    for i in range(len(words)):
        candidate = " ".join(words[i:i + window])
        if not candidate:
            continue
        if fuzz.partial_ratio(term.lower(), candidate) >= FUZZY_THRESHOLD:
            return True
    return False


def extract_skills_from_text(text: str, skills_list: list) -> list:
    """Return the canonical skills detected in `text`.

    Matching order per skill:
    1. Exact whole-word/phrase match on the canonical name.
    2. Exact whole-word/phrase match on any known synonym.
    3. Fuzzy match against the canonical name (skipped for short skills in
       EXACT_ONLY, which would otherwise false-positive on longer skills).
    """
    found = []
    text_lower = text.lower()

    for skill in skills_list:
        if _word_boundary_match(skill, text_lower):
            found.append(skill)
            continue

        matched = False
        for synonym in SYNONYMS.get(skill, []):
            if _word_boundary_match(synonym, text_lower):
                matched = True
                break
        if matched:
            found.append(skill)
            continue

        if skill not in EXACT_ONLY and _fuzzy_match(skill, text_lower):
            found.append(skill)

    return sorted(set(found))
