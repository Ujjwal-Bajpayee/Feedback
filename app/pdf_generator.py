# File: app/pdf_generator.py

import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.utils import simpleSplit
from PIL import Image


def _sanitize_pdf_text(s: str) -> str:
    """
    Replace any Unicode punctuation that Helvetica cannot render:
      – (en-dash)  → -
      — (em-dash)  → -
      “ ” (curly quotes) → "
      ‘ ’ (curly quotes) → '
    Remove any control character in U+0000–U+001F except \n, \r, \t.
    """
    if not isinstance(s, str):
        s = str(s)

    s = s.replace("–", "-").replace("—", "-")
    s = s.replace("“", '"').replace("”", '"')
    s = s.replace("‘", "'").replace("’", "'")

    sanitized = []
    for ch in s:
        code = ord(ch)
        if 0x00 <= code <= 0x1F and ch not in ("\n", "\r", "\t"):
            continue
        sanitized.append(ch)
    return "".join(sanitized)


def create_pdf_report(
    student_name: str,
    feedback: dict,
    chart_figs: list
) -> bytes:
    """
    Build a PDF report using only standard PDF fonts (Helvetica / Helvetica-Bold).
    Wraps and paginates long text so content does not overflow. Inserts charts
    on separate pages after text.
    """

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    # Margins and layout constants
    left_margin = 0.75 * inch
    right_margin = 0.75 * inch
    top_margin = 0.75 * inch
    bottom_margin = 0.75 * inch
    page_width, page_height = letter
    max_text_width = page_width - left_margin - right_margin
    leading = 14  # line height

    def _move_to_next_line(y):
        return y - leading

    def _start_new_page():
        c.showPage()
        return page_height - top_margin

    def _draw_wrapped_text(text: str, start_x: float, start_y: float, font_name: str, font_size: int):
        """
        Draws wrapped text starting at (start_x, start_y). If text exceeds bottom_margin,
        starts a new page and continues. Returns the final y position after drawing.
        """
        sanitized = _sanitize_pdf_text(text)
        wrapped_lines = simpleSplit(sanitized, font_name, font_size, max_text_width)
        y = start_y
        c.setFont(font_name, font_size)
        for line in wrapped_lines:
            if y < bottom_margin + leading:
                y = _start_new_page()
                c.setFont(font_name, font_size)
            c.drawString(start_x, y, line)
            y = _move_to_next_line(y)
        return y

    # 1) Title
    y = page_height - top_margin
    c.setFont("Helvetica-Bold", 18)
    title_text = _sanitize_pdf_text(f"{student_name} - Performance Feedback")
    c.drawString(left_margin, y, title_text)
    y = _move_to_next_line(y) - 10  # extra space after title

    # 2) Intro paragraph
    intro = feedback.get("intro", "")
    y = _draw_wrapped_text(intro, left_margin, y, "Helvetica", 12)
    y -= 20  # extra space before next section

    # 3) “Performance Breakdown” section
    c.setFont("Helvetica-Bold", 14)
    if y < bottom_margin + leading + 20:
        y = _start_new_page()
    c.drawString(left_margin, y, _sanitize_pdf_text("Performance Breakdown"))
    y -= leading + 10  # move below heading

    breakdown = feedback.get("breakdown", "")
    y = _draw_wrapped_text(breakdown, left_margin, y, "Helvetica", 12)
    y -= 20  # extra space

    # 4) “Actionable Suggestions” section
    c.setFont("Helvetica-Bold", 14)
    if y < bottom_margin + leading + 20:
        y = _start_new_page()
    c.drawString(left_margin, y, _sanitize_pdf_text("Actionable Suggestions"))
    y -= leading + 10

    suggestions = feedback.get("suggestions", [])
    for sugg in suggestions:
        # Draw bullet point
        bullet_text = "• " + sugg
        y = _draw_wrapped_text(bullet_text, left_margin, y, "Helvetica", 12)
        y -= 5  # slight gap between bullets
        if y < bottom_margin + leading:
            y = _start_new_page()

    # 5) Insert charts (each on its own page)
    for fig in chart_figs:
        y = _start_new_page()
        # Save chart to buffer
        img_buffer = io.BytesIO()
        fig.savefig(img_buffer, format="png", bbox_inches="tight")
        img_buffer.seek(0)
        img = Image.open(img_buffer)
        orig_width, orig_height = img.size

        max_img_width = page_width - left_margin - right_margin
        display_width = max_img_width
        display_height = orig_height * (display_width / orig_width)

        # If the display height exceeds printable area, scale down
        max_display_height = page_height - top_margin - bottom_margin
        if display_height > max_display_height:
            scale = max_display_height / display_height
            display_height = max_display_height
            display_width = display_width * scale

        c.drawInlineImage(
            img,
            left_margin,
            page_height - top_margin - display_height,
            width=display_width,
            height=display_height
        )

    # 6) Finalize
    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
