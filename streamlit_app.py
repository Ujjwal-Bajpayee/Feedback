# streamlit_app.py

import os
from dotenv import load_dotenv

# ─── Step 1) Load environment variables before anything else ───────────────────────
load_dotenv()  # This reads your .env file and puts GROQ_API_KEY into os.environ

# ─── Step 2) Now import everything else ────────────────────────────────────────────
import streamlit as st
import pandas as pd
import json

from app.data_processor import parse_json_to_df
from app.charts import plot_accuracy_over_time, plot_chapter_breakdown, plot_subject_breakdown
from app.feedback_generator import generate_feedback_sections
from app.pdf_generator import create_pdf_report

# ─── Step 3) Configure the Streamlit page ─────────────────────────────────────────
st.set_page_config(
    page_title="MathonGo AI Feedback",
    layout="wide",
    page_icon="🧠"
)

# ─── Step 4) (Optional) Inject custom CSS for MathonGo brand colors ────────────────
st.markdown(
    """
    <style>
    /* Change button hover to accent orange */
    .stButton>button:hover {
        background-color: #FF7F00 !important;
        color: #FFFFFF !important;
    }
    /* Force H1/H2 in primary blue */
    h1, h2, h3 {
        color: #0033A0 !important;
    }
    /* Sidebar background to light gray */
    [data-testid="stSidebar"] {
        background-color: #F5F5F5;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ─── Step 5) Sidebar: Logo + Data Source Selection ─────────────────────────────────
st.sidebar.markdown(
    """
    <div style="text-align:Left; padding: 10px;">
      <h2 style="color: #0033A0;">MathonGo</h2>
    </div>
    """,
    unsafe_allow_html=True
)

logo_path = os.path.join("assets", "logo.png")
if os.path.exists(logo_path):
    st.sidebar.image(logo_path, width=200)
else:
    st.sidebar.markdown("### MathonGo")

st.sidebar.title("Student Feedback")

data_source = st.sidebar.radio(
    "Choose Data Source:",
    ("Use Demo Data", "Upload Your Own JSON")
)

# ─── Step 6) Load raw bytes from Demo or Uploaded JSON ─────────────────────────────
raw_bytes = None
demo_loaded = False

if data_source == "Use Demo Data":
    demo_path = os.path.join("data", "submission1.json")
    try:
        with open(demo_path, "rb") as f:
            raw_bytes = f.read()
            demo_loaded = True
    except FileNotFoundError:
        st.sidebar.error(f"Demo file not found at {demo_path}.")
elif data_source == "Upload Your Own JSON":
    uploaded_file = st.sidebar.file_uploader("Upload your JSON file", type=["json"])
    if uploaded_file is not None:
        raw_bytes = uploaded_file.read()

# ─── Step 7) If we have JSON bytes, process and display ────────────────────────────
if raw_bytes is not None:
    try:
        # 1) Parse JSON → DataFrames + summary dict
        df_all, summary_dict = parse_json_to_df(raw_bytes)

        # 2) Show a preview of the question‐level DataFrame
        st.subheader("🔍 Raw Data Preview")
        st.dataframe(df_all.head(10), use_container_width=True)

        # 3) Generate & display charts: accuracy vs time, chapter breakdown, subject breakdown
        st.subheader("📊 Performance Charts")
        fig1 = plot_accuracy_over_time(df_all)
        fig2 = plot_chapter_breakdown(summary_dict["chapter_summary_df"])
        fig3 = plot_subject_breakdown(summary_dict["subject_summary_df"])

        col1, col2 = st.columns(2)
        with col1:
            st.pyplot(fig1, use_container_width=True)
        with col2:
            st.pyplot(fig2, use_container_width=True)

        # Show the subject‐level chart below
        st.pyplot(fig3, use_container_width=True)

        # 4) Button to trigger AI feedback generation
        if st.button("🧠 Generate Feedback"):
            with st.spinner("Generating AI‐powered feedback..."):
                feedback_sections = generate_feedback_sections(summary_dict)

            # 5) Display the AI feedback
            st.subheader("🤖 AI‐Generated Feedback")
            st.markdown("")
            st.markdown(feedback_sections["intro"])
            st.markdown("*Performance Breakdown*")
            st.markdown(feedback_sections["breakdown"])
            st.markdown("*Actionable Suggestions*")
            for bullet in feedback_sections["suggestions"]:
                st.markdown(f"- {bullet}")

            # 6) Build PDF & offer download
            student_name = summary_dict.get("student_name", "Student")
            pdf_bytes = create_pdf_report(
                student_name=student_name,
                feedback=feedback_sections,
                chart_figs=[fig1, fig2, fig3]
            )
            st.download_button(
                label="📄 Download PDF Report",
                data=pdf_bytes,
                file_name="student_performance_report.pdf",
                mime="application/pdf"
            )

    except Exception as e:
        st.error(f"Error processing data: {e}")

else:
    st.info("Select *Use Demo Data* or *Upload Your Own JSON* from the sidebar.")