# app/data_processor.py

import json
import pandas as pd
from datetime import datetime

def parse_json_to_df(raw_bytes: bytes):
    """
    Adapted to handle the sample JSON structure you provided (a list with one dict).
    This function returns:
      - df_questions: a pandas DataFrame with one row per question attempt, containing:
          ['timestamp', 'chapter', 'subject', 'accuracy', 'time_spent', 'difficulty', 'concepts']
      - summary_dict: {
            "student_name": str,                   # default "Student"
            "subject_summary_df": DataFrame,       # per-subject metrics
            "chapter_summary_df": DataFrame,       # per-chapter metrics
            "raw_json": Python dict                # the full parsed JSON dict
        }
    """

    parsed = json.loads(raw_bytes.decode("utf-8"))

    # 1) If parsed is a list (as in your sample), extract the first element
    if isinstance(parsed, list) and len(parsed) > 0:
        parsed = parsed[0]
    elif isinstance(parsed, list) and len(parsed) == 0:
        raise ValueError("Uploaded JSON list is empty.")

    # At this point, parsed should be a dict with keys: "test", "subjects", "sections", etc.
    raw_json = parsed.copy()
    student_name = parsed.get("student_name", "Student")

    # 2) Build subject-level summary DataFrame (if "subjects" key exists)
    subject_summary_df = pd.DataFrame()
    if "subjects" in parsed and isinstance(parsed["subjects"], list):
        subjects_list = parsed["subjects"]
        # For each subject entry, we expect keys: totalTimeTaken, totalMarkScored, totalAttempted, totalCorrect, accuracy
        # We also need some identifier for subject name: in your sample, each subject has a subjectId, but no "name" field.
        # If you have a separate mapping from subjectId to subject name, you could inject it here.
        # For now, we’ll simply label them "Subject 1", "Subject 2", … or use subjectId["$oid"] as name.
        records = []
        for i, subj in enumerate(subjects_list, start=1):
            subj_id = subj.get("subjectId", {}).get("$oid", f"subj_{i}")
            accuracy = subj.get("accuracy", None)
            total_time = subj.get("totalTimeTaken", None)
            total_attempted = subj.get("totalAttempted", None)
            total_correct = subj.get("totalCorrect", None)
            total_marks = subj.get("totalMarkScored", None)
            records.append({
                "subject_id": subj_id,
                "accuracy": round(accuracy, 1) if accuracy is not None else None,
                "total_time_spent": total_time,
                "total_attempted": total_attempted,
                "total_correct": total_correct,
                "total_marks": total_marks
            })
        subject_summary_df = pd.DataFrame(records)
    else:
        # No "subjects" key → empty DataFrame
        subject_summary_df = pd.DataFrame(
            columns=[
                "subject_id",
                "accuracy",
                "total_time_spent",
                "total_attempted",
                "total_correct",
                "total_marks"
            ]
        )

    # 3) Build a flat DataFrame of all question‐level entries by iterating through sections→questions
    questions_data = []
    sections = parsed.get("sections", [])
    for section in sections:
        # Each section has keys: "sectionId", "questions" (list)
        questions = section.get("questions", [])
        for q in questions:
            qid = q.get("questionId", {})
            # Extract chapter titles (list of dicts with "title")
            chapters = qid.get("chapters", [])
            # We’ll assume each question belongs to exactly one chapter; if multiple, take the first
            chapter_title = chapters[0].get("title") if chapters else "Unknown Chapter"

            # Extract topic list (if needed)
            topics = qid.get("topics", [])
            # Combine topic titles (just for reference; not currently used in summary)
            topic_titles = [t.get("title") for t in topics if "title" in t]

            # Extract concept list
            concepts = qid.get("concepts", [])
            concept_titles = [c.get("title") for c in concepts if "title" in c]

            # Difficulty (level)
            difficulty = qid.get("level", None)

            # Status & accuracy: if any markedOption has isCorrect==true, we treat accuracy=1; else 0.
            marked_options = q.get("markedOptions", [])
            input_value = q.get("inputValue", {})
            accuracy_flag = 0
            # If markedOptions contain {"isCorrect": true}, set accuracy 1
            for mo in marked_options:
                if mo.get("isCorrect", False):
                    accuracy_flag = 1
                    break
            # Or if inputValue["isCorrect"] is True (for numeric inputs)
            if input_value.get("isCorrect", False):
                accuracy_flag = 1

            # Time spent on this question
            time_spent = q.get("timeTaken", None)

            # There is no timestamp per question in this JSON. We'll create a dummy ordinal timestamp
            # based on the order we encounter them. We'll fill real timestamp later if needed.
            timestamp = None  # placeholder; we’ll fill a sequential int index after building list

            questions_data.append({
                "timestamp": timestamp,
                "chapter": chapter_title,
                "topics": topic_titles,
                "concepts": concept_titles,
                "difficulty": difficulty,
                "accuracy": accuracy_flag,
                "time_spent": time_spent
            })

    if len(questions_data) == 0:
        # No question entries → return empty DataFrame
        df_questions = pd.DataFrame(
            columns=[
                "timestamp", "chapter", "topics", "concepts",
                "difficulty", "accuracy", "time_spent"
            ]
        )
    else:
        # Create DataFrame
        df_questions = pd.DataFrame(questions_data)
        # Since there is no real timestamp, assign a sequential index (0,1,2,…)
        df_questions["timestamp"] = pd.date_range(
            start=datetime.now(), periods=len(df_questions), freq="T"
        )

    # 4) Compute per‐chapter summary: average accuracy, average time_spent, count of questions per chapter
    if "chapter" in df_questions.columns and "accuracy" in df_questions.columns and "time_spent" in df_questions.columns:
        chapter_summary_df = (
            df_questions
            .groupby("chapter", as_index=False)
            .agg(
                accuracy=("accuracy", "mean"),
                avg_time_spent=("time_spent", "mean"),
                num_questions=("accuracy", "count")
            )
        )
        chapter_summary_df["accuracy"] = chapter_summary_df["accuracy"].round(1)
        chapter_summary_df["avg_time_spent"] = chapter_summary_df["avg_time_spent"].round(1)
    else:
        chapter_summary_df = pd.DataFrame(
            columns=["chapter", "accuracy", "avg_time_spent", "num_questions"]
        )

    # 5) Package everything into summary_dict
    summary_dict = {
        "student_name": student_name,
        "subject_summary_df": subject_summary_df,
        "chapter_summary_df": chapter_summary_df,
        "raw_json": raw_json
    }

    return df_questions, summary_dict
