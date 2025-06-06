# File: app/feedback_generator.py

import json
from app.llm_client import get_completion
import streamlit as st   # only used for debugging in the UI


def _strip_backticks(raw: str) -> str:
    """
    Remove leading/trailing triple-backticks if present.
    If there's no closing backticks, just return everything after the first line.
    """
    text = raw.strip()
    if text.startswith("```"):
        first_newline  = text.find("\n")
        closing_index  = text.find("```", first_newline + 1)
        if closing_index > first_newline:
            # Normal case: content between the first newline and the closing ```
            only = text[first_newline + 1 : closing_index]
        else:
            # No closing backticks→ everything after the first newline
            only = text[first_newline + 1 :]
    else:
        only = text
    return only.strip()


def _sanitize_str(val: str) -> str:
    """
    Ensure we have a string (no accidental None or non-str).
    """
    if not isinstance(val, str):
        return ""
    return val.strip()


def _debug_and_parse(raw_response: str) -> dict:
    """
    Show the LLM’s raw response (first 200 chars) in Streamlit,
    strip any backticks, then parse JSON. If parsing fails, raise an error.
    """

    stripped = _strip_backticks(raw_response)
    if not stripped:
        raise ValueError(
            "LLM returned an empty response (after stripping backticks). "
            f"repr(raw_response) = {repr(raw_response)}"
        )

    try:
        return json.loads(stripped)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON from LLM response: {e}\n\nPartial content:\n{stripped}")


def generate_feedback_sections(summary_dict: dict) -> dict:
    """
    Build a minimal JSON context (no DataFrames), send it to the LLM,
    parse the returned JSON, and return a dict with keys "intro", "breakdown", "suggestions".
    """

    # 1) Extract student name + DataFrames from summary_dict
    student_name = summary_dict.get("student_name", "Student")
    subj_df = summary_dict.get("subject_summary_df")   # pandas.DataFrame
    chap_df = summary_dict.get("chapter_summary_df")   # pandas.DataFrame

    # 2) Convert each DataFrame → list[dict] so nothing non-serializable ends up in JSON
    subjects = subj_df.to_dict(orient="records") if subj_df is not None else []
    chapters = chap_df.to_dict(orient="records") if chap_df is not None else []

    # 3) Build a “slim” context
    slim_context = {
        "student_name": student_name,
        "subjects":     subjects,
        "chapters":     chapters
    }

    # 4) Attempt to serialize slim_context
    try:
        json_data_str = json.dumps(slim_context, indent=2)
    except TypeError as e:
        st.error(f"DEBUG: Could not JSON-serialize slim_context: {e}")
        raise

    # 5) Load the prompt template (must contain a {JSON_DATA} placeholder)
    with open("app/prompt/feedback_prompt.txt", "r", encoding="utf-8") as f:
        template = f.read()

    # 6) Inject our JSON_DATA into the prompt
    final_prompt = template.format(JSON_DATA=json_data_str)

    # 7) Call the LLM
    raw_response = get_completion(final_prompt)
    if raw_response is None:
        # Instead of “return None”, raise an error so the frontend shows a clear message
        raise ValueError("LLM returned None instead of a string. Check your API key or network.")

    # 8) Strip backticks & parse JSON
    feedback = _debug_and_parse(raw_response)

    # 9) Safely extract each top-level field (use .get so missing keys don’t crash)
    intro_raw       = feedback.get("intro", "")
    breakdown_raw   = feedback.get("breakdown", "")
    suggestions_raw = feedback.get("suggestions", [])

    # 10) Sanitize each field
    intro     = _sanitize_str(intro_raw)
    breakdown = _sanitize_str(breakdown_raw)

    if isinstance(suggestions_raw, str):
        # If suggestions is a newline-separated string, split into list
        lines = suggestions_raw.splitlines()
        suggestions = [line.strip(" •-") for line in lines if line.strip()]
    elif isinstance(suggestions_raw, list):
        suggestions = [_sanitize_str(item) for item in suggestions_raw]
    else:
        suggestions = []

    return {
        "intro":       intro,
        "breakdown":   breakdown,
        "suggestions": suggestions
    }
