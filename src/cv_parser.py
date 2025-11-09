import re
from PyPDF2 import PdfReader


def extract_text_from_pdf(file) -> str:
    """Read all text from a PDF file."""
    reader = PdfReader(file)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def extract_skills_from_text(text: str, skills_list: list):
    """Return a list of matching skills from text."""
    found = []
    text_lower = text.lower()
    for skill in skills_list:
        pattern = r"\b" + re.escape(skill.lower()) + r"\b"
        if re.search(pattern, text_lower):
            found.append(skill)
    return sorted(list(set(found)))
