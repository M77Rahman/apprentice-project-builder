import streamlit as st
from src.cv_parser import extract_text_from_pdf, extract_skills_from_text
from src.utils import load_json, top_skills_from_jobs
from src.skill_matcher import find_skill_gaps
from src.project_generator import generate_projects

st.set_page_config(page_title="Apprentice Project Builder", page_icon="🧠", layout="wide")

st.title("🧠 Apprentice Project Builder")
st.caption("Upload your CV, and we’ll generate custom project ideas based on live job skills and your missing gaps.")

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

    jobs = load_json("data/jobs_clean.json")
    job_skills = top_skills_from_jobs(jobs)
    gaps = find_skill_gaps(cv_skills, job_skills)

    st.subheader("🧩 Skill Gaps")
    st.write(", ".join(gaps) if gaps else "None detected — nice coverage!")

    if st.button("💡 Generate Custom Projects"):
        with st.spinner("🧠 Thinking... generating 3 tailored project ideas..."):
            projects = generate_projects(gaps, cv_skills, job_skills)

        if not projects:
            st.error("No projects generated — check your AI configuration.")
        else:
            st.success("✅ Here are your project ideas:")

            for p in projects:
                st.markdown(f"### 🚀 {p.get('title', 'Untitled Project')}")
                st.write(p.get("summary", ""))

                # Objectives
                st.markdown("**🎯 Objectives:**")
                for o in p.get("objectives", []):
                    st.write(f"- {o}")

                # Key skills and tools
                skills = ", ".join(p.get("key_skills", []))
                tools = ", ".join(p.get("tools", []))
                st.write(f"**🧠 Key skills:** {skills or 'N/A'}")
                st.write(f"**🧰 Tools:** {tools or 'N/A'}")
                st.write(f"**⚙️ Difficulty:** {p.get('difficulty', 'N/A')}")

                # Extra expandable sections
                with st.expander("✅ Acceptance Criteria"):
                    for a in p.get("acceptance_criteria", []):
                        st.write(f"- {a}")

                with st.expander("🧩 Starter Tasks"):
                    for t in p.get("starter_tasks", []):
                        st.write(f"- {t}")

                repo = p.get("github_repo_name", "apprentice-project")
                st.code(f"Repository: {repo}")
                st.divider()
else:
    st.info("👆 Upload a PDF CV to begin.")
