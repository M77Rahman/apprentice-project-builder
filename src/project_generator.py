"""Generate tailored project-brief ideas for a candidate's skill gaps.

Two generation modes:
- "ai": calls the Anthropic API with the candidate's actual CV skills, the
  specific skill gap, and the job context it's relevant to, so each brief
  is genuinely written for that person. Requires ANTHROPIC_API_KEY.
- "template": an offline generator used when no API key is configured (or
  the API call fails). It's not AI-generated and the UI must say so.
"""

import json
import os
import re
from typing import Dict, List, Tuple

import streamlit as st

DEFAULT_MODEL = "claude-sonnet-5"
REQUIRED_KEYS = [
    "title", "summary", "objectives", "key_skills", "tools",
    "difficulty", "acceptance_criteria", "starter_tasks", "github_repo_name",
]


# ---------------------------------------------------------------------------
# API key / mode helpers
# ---------------------------------------------------------------------------

def get_api_key() -> str:
    """Read the Anthropic API key from Streamlit secrets or the environment."""
    try:
        if "ANTHROPIC_API_KEY" in st.secrets:
            return st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        pass
    return os.environ.get("ANTHROPIC_API_KEY", "")


def ai_available() -> bool:
    return bool(get_api_key())


# ---------------------------------------------------------------------------
# AI generation path
# ---------------------------------------------------------------------------

def _job_context_for_gaps(skill_gaps: List[str], jobs: List[dict]) -> Dict[str, dict]:
    """For each gap, collect the job titles that need it and the other
    skills those jobs also require, so the prompt can tailor projects to
    real roles rather than the skill in isolation."""
    context = {}
    for gap in skill_gaps:
        matching = [j for j in jobs if gap in j.get("skills", [])]
        titles = sorted({j["title"] for j in matching})
        co_skills = sorted({s for j in matching for s in j.get("skills", []) if s != gap})
        context[gap] = {"job_titles": titles[:5], "related_skills": co_skills[:8]}
    return context


def _build_prompt(skill_gaps: List[str], cv_skills: List[str], jobs: List[dict]) -> str:
    gap_context = _job_context_for_gaps(skill_gaps, jobs)
    return f"""You are helping a UK apprenticeship candidate build a portfolio that closes specific skill gaps.

Candidate's current CV skills: {json.dumps(cv_skills)}

Skill gaps to address, ranked by how many apprenticeship listings require them (most in-demand first),
along with the job titles and co-required skills that make each gap relevant:
{json.dumps(gap_context, indent=2)}

Generate exactly {len(skill_gaps)} project briefs, one per skill gap listed above, in the same order.
Each brief must be genuinely tailored: reference the specific job titles/related skills for that gap,
and where sensible build on the candidate's existing CV skills rather than starting from zero.

Return ONLY a JSON array (no markdown code fences, no commentary before or after) where each element
has exactly these keys:
- "title": short project title (string)
- "summary": 1-2 sentence description (string)
- "objectives": 3-5 learning objectives (array of strings)
- "key_skills": skills the project demonstrates, must include the target gap skill (array of strings)
- "tools": 3-5 concrete tools/libraries specific to the target skill (array of strings)
- "difficulty": one of "Easy", "Medium", "Hard" (string)
- "acceptance_criteria": 3-5 concrete, testable criteria (array of strings)
- "starter_tasks": 3-5 ordered first steps to begin the project (array of strings)
- "github_repo_name": kebab-case repo name (string)
"""


def _extract_json_array(text: str) -> list:
    text = text.strip()
    text = re.sub(r"^```(json)?", "", text.strip()).strip()
    text = re.sub(r"```$", "", text.strip()).strip()
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1:
        raise ValueError("No JSON array found in model response")
    return json.loads(text[start:end + 1])


def _validate_projects(projects: list) -> None:
    if not isinstance(projects, list) or not projects:
        raise ValueError("Model response was not a non-empty JSON array")
    for p in projects:
        if not isinstance(p, dict):
            raise ValueError("Project entry was not a JSON object")
        for key in REQUIRED_KEYS:
            if key not in p or p[key] in (None, "", []):
                raise ValueError(f"Project missing required field: {key}")


def _ai_generate(skill_gaps: List[str], cv_skills: List[str], jobs: List[dict], api_key: str) -> list:
    import anthropic

    client = anthropic.Anthropic(api_key=api_key, timeout=30.0)
    model = os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL)
    prompt = _build_prompt(skill_gaps, cv_skills, jobs)

    response = client.messages.create(
        model=model,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(block.text for block in response.content if hasattr(block, "text"))
    projects = _extract_json_array(text)
    _validate_projects(projects)
    return projects


# ---------------------------------------------------------------------------
# Offline fallback (template) path
# ---------------------------------------------------------------------------

# Tools associated with specific skills. Skills not listed here fall back to
# a category guess (see _CATEGORY_TOOLS) so suggestions still stay relevant
# to the actual skill gap instead of defaulting to generic Python tooling.
_SKILL_TOOLS: Dict[str, List[str]] = {
    "SQL": ["PostgreSQL", "DBeaver", "pgAdmin"],
    "SQL Server": ["SQL Server Management Studio", "T-SQL", "Azure Data Studio"],
    "PostgreSQL": ["psql", "pgAdmin", "SQLAlchemy"],
    "MongoDB": ["MongoDB Compass", "Mongoose", "PyMongo"],
    "Docker": ["Docker Desktop", "Docker Compose", "Docker Hub"],
    "Kubernetes": ["kubectl", "Minikube", "Helm"],
    "Terraform": ["Terraform CLI", "AWS/Azure provider", "Terraform Cloud"],
    "Power BI": ["Power BI Desktop", "Power Query", "DAX"],
    "Tableau": ["Tableau Public", "Tableau Prep"],
    "Excel": ["Excel", "Power Query", "Excel VBA"],
    "Python": ["VS Code", "pytest", "virtualenv"],
    "Machine Learning": ["scikit-learn", "Jupyter Notebook", "pandas"],
    "Deep Learning": ["PyTorch", "TensorFlow", "Jupyter Notebook"],
    "TensorFlow": ["TensorFlow", "Keras", "Jupyter Notebook"],
    "PyTorch": ["PyTorch", "Jupyter Notebook", "NumPy"],
    "NLP": ["spaCy", "Hugging Face Transformers", "NLTK"],
    "Computer Vision": ["OpenCV", "PyTorch", "Jupyter Notebook"],
    "scikit-learn": ["scikit-learn", "pandas", "Jupyter Notebook"],
    "Pandas": ["pandas", "Jupyter Notebook", "NumPy"],
    "NumPy": ["NumPy", "Jupyter Notebook", "pandas"],
    "ETL": ["Apache Airflow", "dbt", "SQL"],
    "Airflow": ["Apache Airflow", "Docker", "PostgreSQL"],
    "dbt": ["dbt Core", "Snowflake/BigQuery", "SQL"],
    "Data Warehousing": ["Snowflake", "BigQuery", "dbt"],
    "Data Modelling": ["dbdiagram.io", "SQL", "dbt"],
    "Data Visualization": ["Matplotlib", "Power BI", "Tableau"],
    "Data Cleaning": ["pandas", "OpenRefine", "Jupyter Notebook"],
    "Statistics": ["Python (SciPy)", "Jupyter Notebook", "Excel"],
    "Snowflake": ["Snowflake", "SQL", "dbt"],
    "BigQuery": ["BigQuery", "SQL", "Looker"],
    "Looker": ["Looker Studio", "SQL", "BigQuery"],
    "MLOps": ["MLflow", "Docker", "GitHub Actions"],
    "Networking": ["Wireshark", "Cisco Packet Tracer", "GNS3"],
    "TCP/IP": ["Wireshark", "GNS3", "Cisco Packet Tracer"],
    "Subnetting": ["Cisco Packet Tracer", "Subnet calculator", "GNS3"],
    "Routing": ["Cisco Packet Tracer", "GNS3", "pfSense"],
    "Switching": ["Cisco Packet Tracer", "GNS3", "pfSense"],
    "Cisco": ["Cisco Packet Tracer", "GNS3", "Cisco IOS"],
    "DNS": ["BIND", "pfSense", "Wireshark"],
    "DHCP": ["pfSense", "Windows Server DHCP role", "Wireshark"],
    "VPN": ["OpenVPN", "WireGuard", "pfSense"],
    "Firewalls": ["pfSense", "iptables", "Cisco ASA"],
    "Network Security": ["Wireshark", "Nmap", "pfSense"],
    "Network Monitoring": ["Nagios", "Zabbix", "Wireshark"],
    "Cloud Networking": ["AWS VPC", "Azure Virtual Network", "Terraform"],
    "Load Balancing": ["NGINX", "HAProxy", "AWS ELB"],
    "Cyber Security": ["Kali Linux", "Nmap", "Wireshark"],
    "Penetration Testing": ["Kali Linux", "Metasploit", "Burp Suite"],
    "SIEM": ["Splunk", "ELK Stack", "Wazuh"],
    "Wireshark": ["Wireshark", "tcpdump", "GNS3"],
    "Active Directory": ["Windows Server", "PowerShell", "Group Policy"],
    "Windows Server": ["Windows Server", "Hyper-V", "PowerShell"],
    "Windows Server Administration": ["Windows Server", "PowerShell", "Active Directory"],
    "Linux": ["Ubuntu Server", "Bash", "systemd"],
    "Virtualization": ["VirtualBox", "VMware Workstation", "Hyper-V"],
    "VMware": ["VMware Workstation", "vSphere", "ESXi"],
    "Hyper-V": ["Hyper-V Manager", "PowerShell", "Windows Server"],
    "Server Administration": ["Linux/Windows Server", "PowerShell/Bash", "Ansible"],
    "Backup and Recovery": ["Veeam", "Windows Server Backup", "rsync"],
    "IT Support": ["Ticketing system (Zendesk/Jira)", "Remote desktop tools", "Windows/Linux"],
    "Helpdesk": ["Zendesk", "Freshservice", "Windows/macOS"],
    "Ticketing Systems": ["Jira Service Management", "Zendesk", "Freshservice"],
    "ITIL": ["ServiceNow", "Jira Service Management", "ITIL process docs"],
    "Git": ["Git", "GitHub", "GitHub Desktop"],
    "GitHub": ["GitHub", "GitHub Actions", "Git"],
    "GitHub Actions": ["GitHub Actions", "Docker", "YAML"],
    "CI/CD": ["GitHub Actions", "Jenkins", "Docker"],
    "Jenkins": ["Jenkins", "Docker", "Git"],
    "Ansible": ["Ansible", "YAML playbooks", "Linux"],
    "REST": ["Postman", "Flask/Express", "curl"],
    "REST APIs": ["Postman", "FastAPI/Express", "curl"],
    "GraphQL": ["Apollo", "GraphiQL", "Postman"],
    "GraphQL APIs": ["Apollo Server", "GraphiQL", "Postman"],
    "Flask": ["Flask", "SQLAlchemy", "Postman"],
    "Django": ["Django", "Django REST Framework", "SQLite/PostgreSQL"],
    "FastAPI": ["FastAPI", "Pydantic", "Uvicorn"],
    "React": ["React", "Vite", "npm"],
    "Vue.js": ["Vue.js", "Vite", "npm"],
    "Angular": ["Angular CLI", "TypeScript", "npm"],
    "Node.js": ["Node.js", "Express", "npm"],
    "JavaScript": ["VS Code", "Node.js", "npm"],
    "TypeScript": ["TypeScript", "VS Code", "npm"],
    "HTML": ["VS Code", "Chrome DevTools", "HTML validator"],
    "CSS": ["VS Code", "Chrome DevTools", "Flexbox/Grid"],
    "Java": ["IntelliJ IDEA", "Maven", "JUnit"],
    "C#": ["Visual Studio", ".NET CLI", "NUnit"],
    ".NET": ["Visual Studio", "ASP.NET Core", "Entity Framework"],
    "C++": ["CLion/VS Code", "CMake", "GDB"],
    "Object-Oriented Programming": ["UML diagrams", "IDE of choice", "Design pattern references"],
    "Design Patterns": ["UML diagrams", "Refactoring guru reference", "IDE of choice"],
    "Test Automation": ["Selenium", "pytest", "Postman"],
    "Selenium": ["Selenium WebDriver", "pytest", "ChromeDriver"],
    "pytest": ["pytest", "pytest-cov", "GitHub Actions"],
    "Software Testing": ["pytest/JUnit", "Postman", "GitHub Actions"],
    "Postman": ["Postman", "Newman", "REST API"],
    "Agile": ["Jira", "Trello", "Confluence"],
    "Scrum": ["Jira", "Confluence", "Miro"],
    "Jira": ["Jira", "Confluence", "Trello"],
    "Confluence": ["Confluence", "Jira", "Miro"],
    "Project Management": ["Jira", "Trello", "MS Project"],
    "Technical Documentation": ["Markdown", "Confluence", "MkDocs"],
    "Figma": ["Figma", "FigJam"],
    "UX Design": ["Figma", "Miro", "user testing notes"],
    "UI Design": ["Figma", "Adobe XD", "design system"],
    "Web Accessibility": ["axe DevTools", "WAVE", "Lighthouse"],
    "Salesforce": ["Salesforce Trailhead org", "Apex", "Salesforce Flow"],
    "SharePoint": ["SharePoint Online", "Power Automate", "Microsoft Lists"],
    "Microsoft 365": ["Microsoft 365 admin center", "Power Automate", "Teams"],
    "Customer Service": ["Zendesk", "CRM tool", "knowledge base"],
    "Data Protection (GDPR)": ["Data mapping template", "Privacy impact assessment", "policy docs"],
    "Azure": ["Azure Portal", "Azure CLI", "Azure DevOps"],
    "AWS": ["AWS Console", "AWS CLI", "AWS Free Tier"],
    "GCP": ["Google Cloud Console", "gcloud CLI", "Cloud Shell"],
    "APIs": ["Postman", "Flask/Express", "curl"],
    "Apache Spark": ["PySpark", "Jupyter Notebook", "Hadoop"],
    "Bash": ["Bash", "Linux terminal", "shellcheck"],
    "Shell Scripting": ["Bash", "shellcheck", "cron"],
    "PowerShell": ["PowerShell", "Windows Terminal", "PowerShell ISE"],
    "Regex": ["regex101.com", "Python re module", "VS Code"],
    "Jupyter Notebook": ["Jupyter Notebook", "pandas", "Matplotlib"],
    "Matplotlib": ["Matplotlib", "Jupyter Notebook", "pandas"],
    "Seaborn": ["Seaborn", "Matplotlib", "pandas"],
    "A/B Testing": ["Python (SciPy)", "Google Optimize", "Jupyter Notebook"],
    "Excel VBA": ["Excel", "VBA editor", "Macro recorder"],
    "Big Data": ["Apache Spark", "Hadoop", "PySpark"],
    "Hadoop": ["Hadoop", "PySpark", "HDFS"],
    "Monitoring (Grafana/Prometheus)": ["Grafana", "Prometheus", "Docker"],
    "DevOps": ["Docker", "GitHub Actions", "Terraform"],
    "Endpoint Security": ["CrowdStrike/Defender", "Wireshark", "SIEM"],
    "LAN": ["Cisco Packet Tracer", "GNS3", "Wireshark"],
    "WAN": ["GNS3", "Cisco Packet Tracer", "Wireshark"],
}

_CATEGORY_KEYWORDS: List[Tuple[str, List[str]]] = [
    ("data", ["data", "sql", "analytics", "warehous", "etl", "spark", "hadoop", "ml", "learning", "statist", "vision", "nlp"]),
    ("network", ["network", "cisco", "dns", "dhcp", "vpn", "firewall", "lan", "wan", "routing", "switch", "security", "vpn"]),
    ("cloud", ["cloud", "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "devops", "ci/cd"]),
    ("web", ["java", "script", "react", "vue", "angular", "html", "css", "api", "rest", "graphql", "flask", "django", "node"]),
    ("support", ["support", "helpdesk", "ticket", "itil", "customer", "documentation", "office", "365", "sharepoint"]),
]

_CATEGORY_TOOLS = {
    "data": ["Jupyter Notebook", "pandas", "SQL"],
    "network": ["Wireshark", "Cisco Packet Tracer", "GNS3"],
    "cloud": ["Docker", "Terraform", "AWS/Azure Free Tier"],
    "web": ["VS Code", "Git", "Postman"],
    "support": ["Jira Service Management", "Confluence", "Windows/Linux"],
}


def _tools_for_skill(skill: str) -> List[str]:
    if skill in _SKILL_TOOLS:
        return _SKILL_TOOLS[skill]
    skill_lower = skill.lower()
    for category, keywords in _CATEGORY_KEYWORDS:
        if any(kw in skill_lower for kw in keywords):
            return _CATEGORY_TOOLS[category]
    return ["Git", "VS Code", skill]


def _difficulty_for_gap(skill: str, cv_skills: List[str], jobs: List[dict]) -> str:
    """Base difficulty on how much of the job's other required skillset the
    candidate already has: lots of overlap -> Easy, little overlap -> Hard."""
    relevant_jobs = [j for j in jobs if skill in j.get("skills", [])]
    cv_set = set(cv_skills)
    ratios = []
    for job in relevant_jobs:
        other_skills = set(job.get("skills", [])) - {skill}
        if not other_skills:
            continue
        ratios.append(len(other_skills & cv_set) / len(other_skills))

    if not ratios:
        return "Medium"
    avg_overlap = sum(ratios) / len(ratios)
    if avg_overlap >= 0.6:
        return "Easy"
    if avg_overlap >= 0.3:
        return "Medium"
    return "Hard"


def _fallback_project_for_gap(skill: str, cv_skills: List[str], jobs: List[dict]) -> dict:
    tools = _tools_for_skill(skill)
    difficulty = _difficulty_for_gap(skill, cv_skills, jobs)
    relevant_jobs = sorted({j["title"] for j in jobs if skill in j.get("skills", [])})[:3]
    leverage_skill = next((s for s in cv_skills if s != skill), None)

    title = f"{skill} Portfolio Project"
    summary_role_hint = f" ready for roles like {', '.join(relevant_jobs)}" if relevant_jobs else ""
    summary = (
        f"Build a small, demonstrable project that gives you hands-on {skill} experience"
        f"{summary_role_hint}."
    )

    objectives = [
        f"Apply {skill} to solve a real, scoped problem end-to-end.",
        f"Practise the core workflow of {tools[0]} in a realistic setting.",
    ]
    if leverage_skill:
        objectives.append(f"Combine {skill} with {leverage_skill}, which you already know, to build something integrated.")
    objectives.append("Document your approach, decisions, and what you'd improve with more time.")

    key_skills = [skill] + ([leverage_skill] if leverage_skill else [])

    acceptance_criteria = [
        f"The project clearly demonstrates working, non-trivial use of {skill}.",
        f"A README explains the problem, your approach, and how to run it using {tools[0]}.",
        "The repository has a clean commit history showing incremental progress.",
    ]

    starter_tasks = [
        f"Set up your environment and install/configure {tools[0]}.",
        f"Define a small, concrete problem that requires {skill} to solve.",
        "Build a minimal working version, then iterate.",
        "Write the README and add a short demo (screenshots or a short recording).",
    ]

    return {
        "title": title,
        "summary": summary,
        "objectives": objectives,
        "key_skills": key_skills,
        "tools": tools,
        "difficulty": difficulty,
        "acceptance_criteria": acceptance_criteria,
        "starter_tasks": starter_tasks,
        "github_repo_name": re.sub(r"[^a-z0-9]+", "-", skill.lower()).strip("-") + "-project",
    }


def _fallback_projects(skill_gaps: List[str], cv_skills: List[str], jobs: List[dict]) -> list:
    gaps = skill_gaps if skill_gaps else ["Python", "SQL", "Git"]
    return [_fallback_project_for_gap(gap, cv_skills, jobs) for gap in gaps[:3]]


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def generate_projects(skill_gaps: List[str], cv_skills: List[str], jobs: List[dict]) -> Tuple[list, str]:
    """Return (projects, mode). mode is "ai" when the Anthropic API produced
    the briefs, "template" when the offline fallback generator was used
    (no API key configured, or the API call failed)."""
    gaps = skill_gaps[:3] if skill_gaps else ["Python", "SQL", "Git"]

    api_key = get_api_key()
    if api_key:
        try:
            projects = _ai_generate(gaps, cv_skills, jobs, api_key)
            return projects, "ai"
        except Exception:
            pass

    return _fallback_projects(gaps, cv_skills, jobs), "template"
