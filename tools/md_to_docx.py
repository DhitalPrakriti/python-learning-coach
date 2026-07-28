"""Render docs/ARCHITECTURE.md into a styled .docx.

Handles the subset of Markdown the document actually uses: ATX headings, fenced
code blocks, pipe tables, bullet and numbered lists, horizontal rules, and
inline **bold** / `code` spans.
"""
import re
import sys

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

SRC, OUT = sys.argv[1], sys.argv[2]

ACCENT = RGBColor(0x1F, 0x4E, 0x79)
CODE_BG = "F2F4F7"
MUTED = RGBColor(0x55, 0x5F, 0x6D)

doc = Document()

# --- base styles -----------------------------------------------------------
normal = doc.styles["Normal"]
normal.font.name = "Calibri"
normal.font.size = Pt(10.5)
normal.paragraph_format.space_after = Pt(7)
normal.paragraph_format.line_spacing = 1.13

for name, size, color, before, after in (
    ("Heading 1", 19, ACCENT, 20, 8),
    ("Heading 2", 14.5, ACCENT, 16, 6),
    ("Heading 3", 12, ACCENT, 12, 4),
):
    st = doc.styles[name]
    st.font.name = "Calibri Light"
    st.font.size = Pt(size)
    st.font.bold = True
    st.font.color.rgb = color
    st.paragraph_format.space_before = Pt(before)
    st.paragraph_format.space_after = Pt(after)
    st.paragraph_format.keep_with_next = True

code_style = doc.styles.add_style("CodeBlock", 1)  # WD_STYLE_TYPE.PARAGRAPH
code_style.font.name = "Consolas"
code_style.font.size = Pt(8.8)
code_style.paragraph_format.space_before = Pt(4)
code_style.paragraph_format.space_after = Pt(8)
code_style.paragraph_format.line_spacing = 1.0
code_style.paragraph_format.left_indent = Inches(0.16)


def shade(paragraph, fill):
    el = OxmlElement("w:shd")
    el.set(qn("w:val"), "clear")
    el.set(qn("w:fill"), fill)
    paragraph._p.get_or_add_pPr().append(el)


def add_inline(paragraph, text, bold=False, italic=False):
    """Emit runs, honouring **bold** and `code` spans."""
    for part in re.split(r"(\*\*[^*]+\*\*|`[^`]+`)", text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            run = paragraph.add_run(part[2:-2])
            run.bold = True
        elif part.startswith("`") and part.endswith("`"):
            run = paragraph.add_run(part[1:-1])
            run.font.name = "Consolas"
            run.font.size = Pt(9.2)
            run.font.color.rgb = RGBColor(0xA3, 0x1D, 0x4B)
        else:
            run = paragraph.add_run(part.replace("\\|", "|"))
        run.bold = run.bold or bold
        run.italic = italic


def split_row(line):
    line = line.strip().strip("|")
    return [c.strip() for c in re.split(r"(?<!\\)\|", line)]


lines = open(SRC, encoding="utf-8").read().split("\n")

# --- title page ------------------------------------------------------------
title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
title.paragraph_format.space_before = Pt(150)
run = title.add_run("Python Learning Coach")
run.font.name = "Calibri Light"
run.font.size = Pt(34)
run.font.bold = True
run.font.color.rgb = ACCENT

sub = doc.add_paragraph()
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = sub.add_run("Architecture Document")
run.font.size = Pt(17)
run.font.color.rgb = MUTED

for text in (
    "",
    "Multi-agent Python tutor  ·  Flask + Google Gemini",
    "Repository: DhitalPrakriti/python-learning-coach",
    "Branch: dev (merged to main via PR #1)",
    "28 July 2026",
):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(3)
    r = p.add_run(text)
    r.font.size = Pt(10.5)
    r.font.color.rgb = MUTED

doc.add_page_break()

# --- body ------------------------------------------------------------------
i = 0
skipped_h1 = False
while i < len(lines):
    line = lines[i]
    stripped = line.strip()

    # fenced code block
    if stripped.startswith("```"):
        i += 1
        body = []
        while i < len(lines) and not lines[i].strip().startswith("```"):
            body.append(lines[i])
            i += 1
        i += 1
        for n, code_line in enumerate(body):
            p = doc.add_paragraph(style="CodeBlock")
            p.paragraph_format.space_after = Pt(8 if n == len(body) - 1 else 0)
            p.paragraph_format.space_before = Pt(4 if n == 0 else 0)
            p.add_run(code_line if code_line.strip() else " ")
            shade(p, CODE_BG)
        continue

    # pipe table
    if (
        stripped.startswith("|")
        and i + 1 < len(lines)
        and re.match(r"^\|[\s:\-|]+\|$", lines[i + 1].strip())
    ):
        header = split_row(stripped)
        i += 2
        rows = []
        while i < len(lines) and lines[i].strip().startswith("|"):
            rows.append(split_row(lines[i]))
            i += 1

        table = doc.add_table(rows=1, cols=len(header))
        table.style = "Light Grid Accent 1"
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = True
        for cell, text in zip(table.rows[0].cells, header):
            cell.paragraphs[0].text = ""
            add_inline(cell.paragraphs[0], text, bold=True)
        for row in rows:
            cells = table.add_row().cells
            for cell, text in zip(cells, row[: len(header)]):
                cell.paragraphs[0].text = ""
                add_inline(cell.paragraphs[0], text)
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    p.paragraph_format.space_after = Pt(2)
                    p.paragraph_format.space_before = Pt(2)
                    for r in p.runs:
                        r.font.size = Pt(9.2)
        doc.add_paragraph().paragraph_format.space_after = Pt(4)
        continue

    # horizontal rule -> page break between major sections
    if stripped == "---":
        doc.add_page_break()
        i += 1
        continue

    # headings
    m = re.match(r"^(#{1,4})\s+(.*)$", stripped)
    if m:
        level, text = len(m.group(1)), m.group(2)
        if level == 1 and not skipped_h1:
            skipped_h1 = True  # already on the title page
            i += 1
            continue
        p = doc.add_paragraph(style=f"Heading {min(level, 3)}")
        add_inline(p, text)
        i += 1
        continue

    # bullets
    m = re.match(r"^[-*]\s+(.*)$", stripped)
    if m:
        p = doc.add_paragraph(style="List Bullet")
        p.paragraph_format.space_after = Pt(3)
        add_inline(p, m.group(1))
        i += 1
        continue

    # numbered
    m = re.match(r"^(\d+)\.\s+(.*)$", stripped)
    if m:
        p = doc.add_paragraph(style="List Number")
        p.paragraph_format.space_after = Pt(3)
        add_inline(p, m.group(2))
        i += 1
        continue

    # continuation of a list item (indented)
    if line.startswith("   ") and stripped:
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.5)
        p.paragraph_format.space_after = Pt(3)
        add_inline(p, stripped)
        i += 1
        continue

    if not stripped:
        i += 1
        continue

    p = doc.add_paragraph()
    add_inline(p, stripped)
    i += 1

doc.save(OUT)
print(f"wrote {OUT}")
