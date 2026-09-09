import matplotlib.pyplot as plt
import streamlit as st

from src.cv_parser import extract_skills_from_text, extract_text_from_pdf
from src.project_generator import ai_available, generate_projects
from src.skill_matcher import find_skill_gaps, top_skill_gaps
from src.utils import load_json, skill_frequency, top_skills_from_jobs

st.set_page_config(page_title="Apprentice Project Builder", page_icon="🧠", layout="wide")

st.title("🧠 Apprentice Project Builder")
st.caption(
    "Upload your CV and we'll compare your skills against a curated apprenticeship "
    "listings dataset, find your biggest gaps, and generate project ideas to close them."
)

TRACKS = {
    "All tracks": None,
    "Data & AI": "data_ai",
    "Network & Infrastructure": "network_infra",
    "Digital Support & Dev": "digital_support",
}

with st.sidebar:
    st.header("Settings")
    track_label = st.selectbox("Compare against job track", list(TRACKS.keys()))
    selected_track = TRACKS[track_label]

    st.divider()
    if ai_available():
        st.success("🤖 AI generation mode: an API key is configured, so project briefs will be written by Claude.")
    else:
        st.warning(
            "📋 Template mode: no ANTHROPIC_API_KEY is configured, so project briefs come from "
            "an offline template generator. Add the key as a Streamlit secret or environment "
            "variable for tailored AI-generated suggestions."
        )

all_jobs = load_json("data/jobs_clean.json")
jobs = [j for j in all_jobs if selected_track is None or j.get("track") == selected_track]

uploaded_file = st.file_uploader("📄 Upload your CV (PDF only)", type=["pdf"])

if uploaded_file:
    with st.spinner("🔍 Extracting skills from your CV..."):
        skills_list = load_json("data/skills_list.json")
        text = extract_text_from_pdf(uploaded_file)
        cv_skills = extract_skills_from_text(text, skills_list)

    if cv_skills:
        st.success(f"✅ Found {len(cv_skills)} skills in your CV")
        st.write(", ".join(cv_skills))
    else:
        st.warning("⚠️ No known skills found — try another CV or update your skill list.")
        st.stop()

    job_skills = top_skills_from_jobs(jobs)
    gaps = find_skill_gaps(cv_skills, job_skills)
    ranked_gaps = top_skill_gaps(cv_skills, jobs, n=3)

    st.subheader("🧩 Skill Gaps")
    st.caption(f"Compared against {len(jobs)} listings in the {track_label} track.")
    st.write(", ".join(gaps) if gaps else "None detected — nice coverage!")

    if gaps:
        freq = skill_frequency(jobs)
        gap_freq = sorted(
            ((skill, freq[skill]) for skill in gaps if freq[skill] > 0),
            key=lambda item: item[1],
            reverse=True,
        )[:10]
        if gap_freq:
            with st.expander("📊 Most in-demand skill gaps in this dataset"):
                labels = [s for s, _ in gap_freq][::-1]
                counts = [c for _, c in gap_freq][::-1]
                fig, ax = plt.subplots(figsize=(6, max(2, 0.4 * len(labels))))
                ax.barh(labels, counts, color="#4C72B0")
                ax.set_xlabel("Listings requiring this skill")
                ax.set_title(f"Skill gap frequency — {track_label}")
                fig.tight_layout()
                st.pyplot(fig)

    if not ranked_gaps:
        st.info("You already cover every skill in this track's listings — nothing to generate projects for.")
    elif st.button("💡 Generate Custom Projects"):
        with st.spinner("🧠 Generating tailored project ideas for your top skill gaps..."):
            projects, mode = generate_projects(ranked_gaps, cv_skills, jobs)

        if not projects:
            st.error("No projects generated — check your AI configuration.")
        else:
            if mode == "ai":
                st.success("✅ AI-generated project ideas (via Claude), tailored to your CV and these listings:")
            else:
                st.success("✅ Template-mode project ideas (not AI-generated — see sidebar to enable AI):")

            briefs_markdown = [f"# Project Briefs ({'AI-generated' if mode == 'ai' else 'Template mode'})\n"]

            for p in projects:
                st.markdown(f"### 🚀 {p.get('title', 'Untitled Project')}")
                st.write(p.get("summary", ""))

                st.markdown("**🎯 Objectives:**")
                for o in p.get("objectives", []):
                    st.write(f"- {o}")

                skills = ", ".join(p.get("key_skills", []))
                tools = ", ".join(p.get("tools", []))
                st.write(f"**🧠 Key skills:** {skills or 'N/A'}")
                st.write(f"**🧰 Tools:** {tools or 'N/A'}")
                st.write(f"**⚙️ Difficulty:** {p.get('difficulty', 'N/A')}")

                with st.expander("✅ Acceptance Criteria"):
                    for a in p.get("acceptance_criteria", []):
                        st.write(f"- {a}")

                with st.expander("🧩 Starter Tasks"):
                    for t in p.get("starter_tasks", []):
                        st.write(f"- {t}")

                repo = p.get("github_repo_name", "apprentice-project")
                st.code(f"Repository: {repo}")
                st.divider()

                briefs_markdown.append(f"## {p.get('title', 'Untitled Project')}\n")
                briefs_markdown.append(f"{p.get('summary', '')}\n")
                briefs_markdown.append("**Objectives:**")
                briefs_markdown += [f"- {o}" for o in p.get("objectives", [])]
                briefs_markdown.append(f"\n**Key skills:** {skills or 'N/A'}")
                briefs_markdown.append(f"**Tools:** {tools or 'N/A'}")
                briefs_markdown.append(f"**Difficulty:** {p.get('difficulty', 'N/A')}\n")
                briefs_markdown.append("**Acceptance criteria:**")
                briefs_markdown += [f"- {a}" for a in p.get("acceptance_criteria", [])]
                briefs_markdown.append("\n**Starter tasks:**")
                briefs_markdown += [f"- {t}" for t in p.get("starter_tasks", [])]
                briefs_markdown.append(f"\nRepository: `{repo}`\n\n---\n")

            st.download_button(
                "⬇️ Download project briefs (Markdown)",
                data="\n".join(briefs_markdown),
                file_name="project_briefs.md",
                mime="text/markdown",
            )
else:
    st.info("👆 Upload a PDF CV to begin.")
