from openai import OpenAI
import json, re

REQUIRED_FIELDS = [
    "title", "summary", "objectives", "key_skills", "tools",
    "difficulty", "github_repo_name", "acceptance_criteria", "starter_tasks"
]


def _coerce_list(x, n=None):
    if isinstance(x, list):
        return [i for i in x if i][:n] if n else [i for i in x if i]
    if isinstance(x, str):
        items = [i.strip("-• ").strip() for i in x.split("\n") if i.strip()]
        return items[:n] if n else items
    return []


def _default_acceptance_criteria(gap):
    templates = {
        "ci/cd": [
            "Pipeline triggers on commit and passes tests.",
            "Deploys to staging automatically.",
            "Logs visible in CI dashboard."
        ],
        "react": [
            "No console errors on load.",
            "State updates without page reload.",
            "At least one component test passes."
        ],
        "regex": [
            "Correctly filters target text.",
            "No false positives on sample set.",
            "User can edit regex and see live results."
        ],
        "sql": [
            "CRUD operations supported.",
            "Queries complete quickly on sample data.",
            "Integrity constraints prevent duplicates."
        ],
        "api": [
            "Endpoints return correct status and schema.",
            "Auth and basic rate limit in place.",
            "Docs include working examples."
        ],
    }
    return templates.get(gap.lower(), [
        "Core features meet requirements.",
        "Project runs without runtime errors.",
        "README explains setup and usage."
    ])


def _default_starter_tasks(gap):
    templates = {
        "ci/cd": [
            "Init repo + branch protection.",
            "Add CI workflow (build/test).",
            "Add deploy step to staging."
        ],
        "react": [
            "Scaffold with Vite/CRA.",
            "Create core components + routes.",
            "Bind to mock API and render list."
        ],
        "regex": [
            "Create sample dataset.",
            "Draft initial regex patterns.",
            "Add filter preview UI/CLI."
        ],
        "sql": [
            "Design ERD.",
            "Create tables + FKs.",
            "Write SELECT/JOIN examples."
        ],
        "api": [
            "Init FastAPI/Flask app.",
            "Add GET/POST endpoints.",
            "Test with curl/Postman."
        ],
    }
    return templates.get(gap.lower(), [
        "Create repo & venv.",
        "Install deps.",
        "Write README goals + run steps."
    ])


def generate_ai_projects(cv_skills, gaps, job_snippets_or_skills):
    """
    Calls local Ollama model (gemma:2b) via OpenAI-compatible API.
    """
    client = OpenAI(api_key="ollama", base_url="http://localhost:11434/v1")

    if job_snippets_or_skills and isinstance(job_snippets_or_skills[0], dict):
        job_snips = "\n".join(
            f"- {j.get('title','Apprentice role')}: {(j.get('description','') or '')[:150]}..."
            for j in job_snippets_or_skills[:5]
        )
    else:
        job_snips = "\n".join(f"- {str(s)}" for s in job_snippets_or_skills[:10])

    prompt = f"""
Generate exactly 3 JSON objects describing apprenticeship-ready projects.

User skills: {", ".join(cv_skills)}
Skill gaps: {", ".join(gaps)}
Job context:
{job_snips}

Each project MUST include:
- title
- summary (2 sentences)
- objectives (array of 3)
- key_skills (include one of the gaps)
- tools
- difficulty (Easy|Medium|Hard)
- github_repo_name (kebab-case)
- acceptance_criteria (array of 3)
- starter_tasks (array of 3)

Return ONLY valid JSON (no markdown).
""".strip()

    resp = client.chat.completions.create(
        model="gemma:2b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )

    raw = resp.choices[0].message.content.strip()
    clean = raw.replace("```json", "").replace("```", "").strip()

    # --- NEW FIX: wrap multiple objects in an array if needed ---
    if clean.count("{") > 1 and not clean.startswith("["):
        # ensure commas between objects
        clean = "[" + re.sub(r"}\s*{", "},{", clean) + "]"

    try:
        data = json.loads(clean)
    except json.JSONDecodeError:
        cleaned = clean
        if not cleaned.endswith("]"):
            cleaned += "]"
        cleaned = re.sub(r"([}\]])\s*([{\[])", r"\1,\2", cleaned)
        try:
            data = json.loads(cleaned)
        except Exception:
            print("RAW OUTPUT >>>\n", raw, "\n<<< END RAW")
            return [{
                "title": "Parse error",
                "summary": f"Returned text:\n{raw}",
                "objectives": [],
                "key_skills": [],
                "tools": [],
                "difficulty": "N/A",
                "github_repo_name": "apprentice-project",
                "acceptance_criteria": ["Manual validation required."],
                "starter_tasks": ["Inspect output and re-run."]
            }]

    if isinstance(data, dict):
        data = [data]

    # --- Normalize projects ---
    fixed = []
    for d in data:
        for k in REQUIRED_FIELDS:
            d.setdefault(k, "N/A")

        d["objectives"] = _coerce_list(d["objectives"], n=3)
        d["key_skills"] = _coerce_list(d["key_skills"])
        d["tools"] = _coerce_list(d["tools"])
        d["acceptance_criteria"] = _coerce_list(d["acceptance_criteria"], n=3)
        d["starter_tasks"] = _coerce_list(d["starter_tasks"], n=3)

        gap_match = next(
            (g for g in gaps if any(g.lower() in str(s).lower() for s in d["key_skills"])),
            gaps[0] if gaps else "general"
        )

        if len(d["acceptance_criteria"]) < 3:
            d["acceptance_criteria"] = _default_acceptance_criteria(gap_match)
        if len(d["starter_tasks"]) < 3:
            d["starter_tasks"] = _default_starter_tasks(gap_match)

        rn = str(d["github_repo_name"]).strip().lower()
        rn = re.sub(r"[^a-z0-9\-]", "-", rn)
        rn = re.sub(r"-+", "-", rn).strip("-") or "apprentice-project"
        d["github_repo_name"] = rn

        fixed.append(d)

    return fixed[:3] if fixed else [{
        "title": "Parse error",
        "summary": "Empty result after parsing.",
        "objectives": [],
        "key_skills": [],
        "tools": [],
        "difficulty": "N/A",
        "github_repo_name": "apprentice-project",
        "acceptance_criteria": ["Project builds successfully."],
        "starter_tasks": ["Initialize repository."]
    }]

