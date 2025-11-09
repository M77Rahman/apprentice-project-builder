# 🧠 Apprentice Project Builder

A Streamlit app that analyzes your CV, extracts your skills, and generates **custom project ideas** to strengthen your apprenticeship applications.

## 🚀 Features
- Extracts skills directly from your uploaded CV (PDF)
- Identifies your current skill gaps vs. live job data
- Suggests tailored projects to help you fill those gaps
- Works offline using fallback or Ollama local generation

## 🧩 Tech Stack
- **Python**
- **Streamlit**
- **PyPDF2**
- **pandas**
- **Ollama (optional)** for offline AI generation

## 🧠 How to Run Locally
1. Clone the repo:
   ```bash
   git clone https://github.com/M77Rahman/apprentice-project-builder.git
   cd apprentice-project-builder

Create a virtual environment: python -m venv .venv
source .venv/bin/activate
Install dependencies:pip install -r requirements.txt

Run the app:streamlit run app.py
💬 AI Generation Modes

Online (Streamlit Cloud): Uses simple fallback project ideas (free)

Local (Ollama): Run ollama serve and get real AI-generated projects

📍 Live App

👉 Try it on Streamlit Cloud
https://apprentice-project-builder-etec9hnna67kqxywwjgks7.streamlit.app/
