# MathonGo Student Feedback App

This repository contains a Streamlit-based application that ingests a student’s performance data (JSON), generates AI-powered feedback (using Groq’s LLM API), and produces a downloadable PDF report with personalized insights, actionable suggestions, and performance charts.

---

## Table of Contents

1. [APIs Used](#apis-used)  
2. [Prompt Logic](#prompt-logic)  
3. [Report Structure](#report-structure)  
4. [Project Overview](#project-overview)  
5. [Installation & Running](#installation--running)  

---

## APIs Used

- **Groq LLM API**  
  - **Endpoint**: `https://api.groq.com/v1/completions`  
  - **Purpose**: Given a detailed “system + task” prompt along with the student’s performance data, the Groq API returns a JSON object containing:  
    1. A heartfelt, personalized `intro` message.  
    2. A detailed `breakdown` of performance by subject and chapter.  
    3. A list of `suggestions` that include both academic tips and mental‐health/well‐being strategies.  
  - **Key Parameters**:  
    - `model`: `meta-llama/llama-4-scout-17b-16e-instruct`
    - `temperature`: 0.25  
    - `max_tokens`: 2000 (to accommodate long JSON output)  
    - `messages`:  
      - System message: instructs the LLM to act as a caring, experienced mentor.  
      - User message: injects the student’s performance data and detailed instructions on how to generate the JSON.  

- **ReportLab (reportlab.pdfgen.canvas)**  
  - **Purpose**: Generates a multi-page PDF report that includes:  
    1. A title and introductory paragraphs.  
    2. Performance breakdown text.  
    3. Actionable suggestions as bullet points.  
    4. Embedded Matplotlib-generated performance charts.  

- **Matplotlib**  
  - **Purpose**: Creates the following visualizations:  
    1. **Rolling Accuracy vs. Time** (line chart with shaded area) to show a student’s smoothed accuracy trend over time.  
    2. **Accuracy by Chapter** (bar chart)  
    3. **Accuracy by Subject** (bar chart)  

- **Streamlit**  
  - **Purpose**: Provides the web UI for:  
    1. Uploading a JSON file or using demo data.  
    2. Displaying a preview of the raw DataFrame.  
    3. Showing interactive charts.  
    4. Triggering the AI feedback generation.  
    5. Displaying the AI-generated text in the browser.  
    6. Offering a “Download PDF Report” button.  

---

## Prompt Logic

The core of our AI‐powered feedback resides in a carefully designed prompt template, located at `app/prompt/feedback_prompt.txt`. Below is the high‐level structure and rationale:

1. **SYSTEM Section**  
   - Instructs the LLM to behave as a caring, experienced mentor.  
   - Emphasizes a warm, empathic conversational tone, balancing academic guidance and mental‐health support.

2. **TASK Section**  
   - **Input**:  
     - `{JSON_DATA}` placeholder where the actual student performance data (parsed into a minimal JSON context) is injected.  
   - **Expected Output**: A JSON object with exactly three keys—`"intro"`, `"breakdown"`, and `"suggestions"`—each following strict formatting rules:  
     1. `"intro"`:  
        - Contains a single string, possibly with `\n` to indicate newlines (no raw line breaks).  
        - Must greet the student by name, highlight strengths and areas to improve, and convey genuine empathy.  
     2. `"breakdown"`:  
        - A multi‐paragraph, “walkthrough” style analysis of performance.  
        - Divided into subsections for **Subject** and **Chapter** assessments.  
        - Every line break inside this value must be escaped as `\n` to remain valid JSON.  
     3. `"suggestions"`:  
        - An array of 4–6 concise tips.  
        - Each tip begins with “Try…” or “Next time, consider…”, etc.  
        - Includes both academic strategies (e.g., targeted practice) and mental‐health advice (mindfulness breaks, sleep hygiene, short yoga/stretching routines).  
        - Any sub‐steps or bullet‐style newlines inside a suggestion must use `\n`.  

3. **IMPORTANT Section**  
   - Emphasizes:  
     - Returning _only_ valid JSON with those three keys.  
     - No extra commentary, no code fences (```), no additional keys.  
     - Maintaining a deeply caring, mentor‐like tone.  

4. **Sanitization & Parsing**  
   - The application strips any triple backticks if present and then calls `json.loads(...)`.  
   - If the JSON is malformed (e.g., raw newlines instead of `\n`), parsing fails. Hence the prompt explicitly instructs the LLM to escape line breaks.

5. **Rolling-Window Data Reduction**  
   - Downstream, the code builds a “slim context” containing only:  
     ```json
     {
       "student_name": "...",
       "subjects": [ { "subject_id": "...", "accuracy": 0.75, … }, … ],
       "chapters": [ { "chapter": "...", "accuracy": 0.6, … }, … ]
     }
     ```  
   - This minimal JSON is what gets interpolated into `{JSON_DATA}` before sending to the LLM.

---

## Report Structure

When you click **“Download PDF Report”**, the application assembles a PDF with the following layout:

1. **Title Page (first page)**  
   - **Title**: `“{student_name} – Performance Feedback”` (Helvetica-Bold, 18 pt)  
   - **Intro Paragraph**:  
     - Rendered in Helvetica 12 pt, wrapped to the page width.  
     - Text comes from the LLM’s `"intro"` field.  
     - Emotions, praise, and motivation are front‐and‐center here.  

2. **Performance Breakdown Section (continues on first page, possibly spilling to second)**  
   - **Section Header**: “Performance Breakdown” (Helvetica-Bold, 14 pt)  
   - **Body Text**:  
     - Rendered in Helvetica 12 pt, wrapped to fit within left/right margins.  
     - Sourced from the LLM’s `"breakdown"` field, which has explicit `\n` characters to indicate paragraphs.  
     - If the breakdown is too long to fit on one page, it automatically flows onto subsequent pages until finished.  

3. **Actionable Suggestions Section**  
   - **Section Header**: “Actionable Suggestions” (Helvetica-Bold, 14 pt)  
   - **Bullet Points**:  
     - Each suggestion is prefixed with a “• ” bullet.  
     - Long bullet text is wrapped and indented so it never exceeds the page width.  
     - These tips combine academic guidance and mental‐health/well‐being strategies.  
   - If the suggestions exceed the remaining space on a page, the next bullets continue on a new page.  

4. **Charts Section (each chart on its own page)**  
   - **Chart 1**: Rolling Accuracy vs. Time  
     - Large 8×4 in. Matplotlib figure showing the student’s smoothed accuracy (%) over time.  
     - X‐axis: timestamps (with rotated, human-readable labels).  
     - Y‐axis: accuracy from 0 to 100.  
   - **Chart 2**: Accuracy by Chapter  
     - Bar chart (6×4 in.) plotting each chapter’s percentage‐correct.  
   - **Chart 3**: Accuracy by Subject  
     - Bar chart (6×4 in.) plotting each subject’s percentage‐correct.  
   - Charts are inserted one per page, scaled to fit within the margins. If a chart’s height exceeds the printable area, it is proportionally resized.


