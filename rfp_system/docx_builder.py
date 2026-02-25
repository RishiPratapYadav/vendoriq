"""
DOCX Builder
=============
Renders an RFP template dictionary into a professional .docx Word document.
Works with both pre-built templates and AI-generated ones — same output quality.
"""

import os
import sys
sys.path.insert(0, '/home/claude/.npm-global/lib/node_modules')

from docx import Document
from docx.shared import Pt, RGBColor, Inches, Twips
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import subprocess, json, tempfile

# We use docx-js (node) for generation — consistent with SKILL.md
# This module writes the JS, runs node, and outputs the .docx

def build_rfp_docx(template: dict, context: dict, output_path: str):
    """
    Generate a .docx RFP document from template + context.
    Uses docx-js via Node.js for maximum formatting quality.
    """
    context["_output_path"] = output_path
    js_code = _render_js(template, context)

    # Write temp JS file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
        f.write(js_code)
        tmp_js = f.name

    try:
        result = subprocess.run(
            ['node', tmp_js],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            raise RuntimeError(f"Node.js error:\n{result.stderr}")
        print(f"[DOCX Builder] {result.stdout.strip()}")
    finally:
        os.unlink(tmp_js)


def _esc(text: str) -> str:
    """Escape text for safe embedding in JS template literals."""
    return (text or "").\
        replace("\\", "\\\\").\
        replace("`",  "\\`").\
        replace("$",  "\\$").\
        replace("\n", " ").\
        replace('"',  '\\"')


def _render_js(template: dict, context: dict) -> str:
    """Render the full Node.js docx-generation script."""

    category        = _esc(context["category"])
    org_name        = _esc(context["org_name"])
    issue_date      = _esc(context["issue_date"])
    ref_number      = _esc(context["ref_number"])
    deadline_weeks  = _esc(context["deadline_weeks"])
    short_desc      = _esc(template.get("short_description", category))
    source          = context.get("source", "template")
    source_note     = "" if source == "template" else "AI-Generated Template"

    # Top vendors list
    vendors_js = json.dumps(context.get("top_vendors", []))

    # Restrictions
    restrictions_js = json.dumps(context.get("restrictions", []))

    # Criteria rows for scoring table
    criteria_rows = ""
    for i, (crit, info) in enumerate(context.get("criteria", {}).items()):
        w    = info.get("weight", 0)
        desc = info.get("desc", "")
        fill = "FFFFFF" if i % 2 == 0 else "F2F4F6"
        criteria_rows += f"""
    new TableRow({{ children: [
      _cell({json.dumps(crit)},  4000, "{fill}", true,  "1B2E45"),
      _cell("{w}%",              1200, "{fill}", true,  "0D7A6B", WD_CENTER),
      _cell({json.dumps(desc)},  4160, "{fill}", false, "1A1A2E"),
    ]}}),"""

    # Mandatory requirements bullets
    mandatory = template.get("mandatory_requirements", [])
    mandatory_bullets = "\n".join(
        f'    _bullet({json.dumps(r)}),' for r in mandatory
    )

    # Sections
    sections_js = ""
    for sec in template.get("sections", []):
        num   = _esc(sec.get("number", ""))
        title = _esc(sec.get("title", ""))
        desc  = _esc(sec.get("description", ""))
        questions = sec.get("questions", [])
        q_rows = ""
        for qi, q in enumerate(questions):
            fill = "FFFFFF" if qi % 2 == 0 else "F2F4F6"
            q_rows += f"""
      new TableRow({{ children: [
        _cell({json.dumps(q)}, 5500, "{fill}", false, "1A1A2E"),
        _cell("",              3860, "{fill}", false, "1A1A2E"),
      ]}}),"""

        sections_js += f"""
  // ── Section {num}: {title} ──
  _pageBreak(),
  _banner("{num}", "{title}"),
  _spacer(160),
  _para("{desc}", {{ size: 22 }}),
  _spacer(120),
  new Table({{
    width: {{ size: 9360, type: WidthType.DXA }},
    columnWidths: [5500, 3860],
    rows: [
      new TableRow({{ children: [
        _headerCell("Question / Requirement", 5500),
        _headerCell("Vendor Response",        3860),
      ]}}),{q_rows}
    ]
  }}),"""

    output_path_escaped = _esc(context.get("_output_path", "/tmp/rfp_output.docx"))

    return f"""
const {{
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, VerticalAlign, PageBreak, LevelFormat,
  TabStopType, TabStopPosition
}} = require('docx');
const fs = require('fs');

const NAVY    = "1B2E45";
const TEAL    = "0D7A6B";
const LTGRAY  = "F2F4F6";
const MIDGRAY = "D0D5DD";
const WHITE   = "FFFFFF";
const DKTEXT  = "1A1A2E";
const WD_CENTER = AlignmentType.CENTER;
const WD_RIGHT  = AlignmentType.RIGHT;

const OUTPUT_PATH = {json.dumps(output_path_escaped)};

// ── Helpers ───────────────────────────────────────────────────
const _b  = (c="D0D5DD") => ({{ style: BorderStyle.SINGLE, size: 1, color: c }});
const _ab = (c="D0D5DD") => ({{ top: _b(c), bottom: _b(c), left: _b(c), right: _b(c) }});
const _nb = () => ({{ style: BorderStyle.NONE, size: 0, color: "FFFFFF" }});
const _nbs = () => ({{ top: _nb(), bottom: _nb(), left: _nb(), right: _nb() }});

function _para(text, opts={{}}) {{
  return new Paragraph({{
    alignment: opts.align || AlignmentType.LEFT,
    spacing: {{ before: opts.before ?? 80, after: opts.after ?? 80 }},
    children: [new TextRun({{ text, bold: opts.bold||false, italics: opts.italic||false,
      size: opts.size||22, color: opts.color||DKTEXT, font: "Arial" }})]
  }});
}}

function _spacer(before=160) {{
  return new Paragraph({{ spacing: {{ before, after: 0 }}, children: [new TextRun("")] }});
}}

function _pageBreak() {{
  return new Paragraph({{ children: [new PageBreak()] }});
}}

function _bullet(text) {{
  return new Paragraph({{
    numbering: {{ reference: "bullets", level: 0 }},
    spacing: {{ before: 60, after: 60 }},
    children: [new TextRun({{ text, size: 22, color: DKTEXT, font: "Arial" }})]
  }});
}}

function _cell(text, width, fill, bold=false, color=DKTEXT, align=AlignmentType.LEFT) {{
  return new TableCell({{
    width: {{ size: width, type: WidthType.DXA }},
    shading: {{ fill, type: ShadingType.CLEAR }},
    margins: {{ top: 100, bottom: 100, left: 160, right: 160 }},
    borders: _ab(MIDGRAY),
    verticalAlign: VerticalAlign.CENTER,
    children: [new Paragraph({{ alignment: align,
      children: [new TextRun({{ text: text||"", bold, size: 20, color, font: "Arial" }})] }})]
  }});
}}

function _headerCell(text, width) {{
  return new TableCell({{
    width: {{ size: width, type: WidthType.DXA }},
    shading: {{ fill: NAVY, type: ShadingType.CLEAR }},
    margins: {{ top: 100, bottom: 100, left: 160, right: 160 }},
    borders: _ab(NAVY),
    children: [new Paragraph({{
      children: [new TextRun({{ text, bold: true, size: 20, color: WHITE, font: "Arial" }})]
    }})]
  }});
}}

function _infoRow(label, value, i) {{
  const fill = i % 2 === 0 ? LTGRAY : WHITE;
  return new TableRow({{ children: [
    _cell(label, 2800, fill, true,  NAVY),
    _cell(value, 6560, fill, false, DKTEXT),
  ]}});
}}

function _banner(number, title) {{
  return new Table({{
    width: {{ size: 9360, type: WidthType.DXA }},
    columnWidths: [800, 8560],
    borders: {{ top: _nb(), bottom: _nb(), left: _nb(), right: _nb(), insideH: _nb(), insideV: _nb() }},
    rows: [new TableRow({{ children: [
      new TableCell({{
        width: {{ size: 800, type: WidthType.DXA }},
        shading: {{ fill: TEAL, type: ShadingType.CLEAR }},
        margins: {{ top: 120, bottom: 120, left: 160, right: 160 }},
        borders: _nbs(), verticalAlign: VerticalAlign.CENTER,
        children: [new Paragraph({{ alignment: AlignmentType.CENTER,
          children: [new TextRun({{ text: number, bold: true, size: 28, color: WHITE, font: "Arial" }})] }})]
      }}),
      new TableCell({{
        width: {{ size: 8560, type: WidthType.DXA }},
        shading: {{ fill: NAVY, type: ShadingType.CLEAR }},
        margins: {{ top: 120, bottom: 120, left: 200, right: 160 }},
        borders: _nbs(), verticalAlign: VerticalAlign.CENTER,
        children: [new Paragraph({{
          children: [new TextRun({{ text: title, bold: true, size: 26, color: WHITE, font: "Arial" }})] }})]
      }}),
    ]}})]
  }});
}}

// ── Document ──────────────────────────────────────────────────
const topVendors  = {vendors_js};
const restrictions = {restrictions_js};
const sourceNote  = "{source_note}";

const doc = new Document({{
  numbering: {{ config: [
    {{ reference: "bullets",
       levels: [{{ level: 0, format: LevelFormat.BULLET, text: "\\u2022",
         alignment: AlignmentType.LEFT,
         style: {{ paragraph: {{ indent: {{ left: 720, hanging: 360 }} }} }} }}] }},
    {{ reference: "numbers",
       levels: [{{ level: 0, format: LevelFormat.DECIMAL, text: "%1.",
         alignment: AlignmentType.LEFT,
         style: {{ paragraph: {{ indent: {{ left: 720, hanging: 360 }} }} }} }}] }},
  ]}},
  styles: {{
    default: {{ document: {{ run: {{ font: "Arial", size: 22, color: DKTEXT }} }} }},
    paragraphStyles: [
      {{ id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: {{ size: 32, bold: true, font: "Arial", color: NAVY }},
        paragraph: {{ spacing: {{ before: 320, after: 160 }}, outlineLevel: 0 }} }},
      {{ id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: {{ size: 26, bold: true, font: "Arial", color: TEAL }},
        paragraph: {{ spacing: {{ before: 240, after: 120 }}, outlineLevel: 1 }} }},
    ]
  }},
  sections: [{{
    properties: {{
      page: {{
        size: {{ width: 12240, height: 15840 }},
        margin: {{ top: 1440, right: 1260, bottom: 1440, left: 1260 }}
      }}
    }},
    headers: {{
      default: new Header({{ children: [
        new Table({{
          width: {{ size: 9720, type: WidthType.DXA }},
          columnWidths: [6200, 3520],
          borders: {{ top: _nb(), bottom: _b(TEAL), left: _nb(), right: _nb(), insideH: _nb(), insideV: _nb() }},
          rows: [new TableRow({{ children: [
            new TableCell({{ width: {{ size: 6200, type: WidthType.DXA }}, borders: _nbs(), margins: {{ bottom: 80 }},
              children: [new Paragraph({{ children: [new TextRun({{ text: "REQUEST FOR PROPOSAL — {category.upper()}", bold: true, size: 18, color: NAVY, font: "Arial" }})] }})] }}),
            new TableCell({{ width: {{ size: 3520, type: WidthType.DXA }}, borders: _nbs(), margins: {{ bottom: 80 }},
              children: [new Paragraph({{ alignment: AlignmentType.RIGHT, children: [new TextRun({{ text: "CONFIDENTIAL", size: 18, color: TEAL, bold: true, font: "Arial" }})] }})] }}),
          ]}})]
        }})
      ]}})
    }},
    footers: {{
      default: new Footer({{ children: [
        new Paragraph({{
          spacing: {{ before: 80 }},
          border: {{ top: {{ style: BorderStyle.SINGLE, size: 4, color: MIDGRAY, space: 4 }} }},
          tabStops: [{{ type: TabStopType.RIGHT, position: 9360 }}],
          children: [
            new TextRun({{ text: "{org_name} \\u2014 Confidential & Proprietary", size: 18, color: "888888", font: "Arial" }}),
            new TextRun({{ text: "\\t{ref_number}", size: 18, color: "888888", font: "Arial" }}),
          ]
        }})
      ]}})
    }},

    children: [

      // ── Cover Page ───────────────────────────────────────────
      _spacer(2880),
      new Paragraph({{ alignment: AlignmentType.CENTER, spacing: {{ before: 0, after: 0 }},
        children: [new TextRun({{ text: "REQUEST FOR PROPOSAL", bold: true, size: 56, color: NAVY, font: "Arial" }})] }}),
      new Paragraph({{ alignment: AlignmentType.CENTER, spacing: {{ before: 120, after: 0 }},
        children: [new TextRun({{ text: "{category}", size: 40, color: TEAL, font: "Arial" }})] }}),
      _spacer(80),
      new Paragraph({{ alignment: AlignmentType.CENTER, spacing: {{ before: 0, after: 80 }},
        children: [new TextRun({{ text: "{short_desc}", size: 22, color: "888888", italics: true, font: "Arial" }})] }}),
      _spacer(320),
      new Paragraph({{ alignment: AlignmentType.CENTER, spacing: {{ before: 0, after: 80 }},
        border: {{ top: {{ style: BorderStyle.SINGLE, size: 8, color: TEAL, space: 4 }},
                   bottom: {{ style: BorderStyle.SINGLE, size: 8, color: TEAL, space: 4 }} }},
        children: [new TextRun({{ text: "  ", size: 8, font: "Arial" }})] }}),
      _spacer(240),
      new Paragraph({{ alignment: AlignmentType.CENTER, spacing: {{ before: 0, after: 80 }},
        children: [new TextRun({{ text: "Issued by: {org_name}", size: 24, color: DKTEXT, font: "Arial" }})] }}),
      new Paragraph({{ alignment: AlignmentType.CENTER, spacing: {{ before: 0, after: 80 }},
        children: [new TextRun({{ text: "Issue Date: {issue_date}", size: 24, color: DKTEXT, font: "Arial" }})] }}),
      new Paragraph({{ alignment: AlignmentType.CENTER, spacing: {{ before: 0, after: 80 }},
        children: [new TextRun({{ text: "Response Deadline: [Insert Date \\u2014 {deadline_weeks} weeks from issue]", size: 24, color: "CC0000", bold: true, font: "Arial" }})] }}),
      new Paragraph({{ alignment: AlignmentType.CENTER, spacing: {{ before: 0, after: 80 }},
        children: [new TextRun({{ text: "RFP Reference: {ref_number}", size: 24, color: DKTEXT, font: "Arial" }})] }}),
      ...(sourceNote ? [new Paragraph({{ alignment: AlignmentType.CENTER, spacing: {{ before: 80, after: 0 }},
        children: [new TextRun({{ text: "\\u26A1 " + sourceNote, size: 18, color: TEAL, font: "Arial" }})] }})] : []),
      _spacer(400),
      ...(topVendors.length > 0 ? [
        new Paragraph({{ alignment: AlignmentType.CENTER, spacing: {{ before: 0, after: 80 }},
          children: [new TextRun({{ text: "Shortlisted Vendors: " + topVendors.join(" \\u2022 "), size: 20, color: "555555", font: "Arial" }})] }}),
      ] : []),
      _spacer(200),
      new Paragraph({{ alignment: AlignmentType.CENTER,
        children: [new TextRun({{ text: "CONFIDENTIAL \\u2014 FOR NAMED RECIPIENTS ONLY", bold: true, size: 20, color: "888888", font: "Arial" }})] }}),

      // ── Section 00: Overview ─────────────────────────────────
      _pageBreak(),
      _banner("00", "Overview & Submission Details"),
      _spacer(160),
      _para("This Request for Proposal invites qualified vendors to submit proposals for: {short_desc}"),
      _spacer(),
      new Table({{
        width: {{ size: 9360, type: WidthType.DXA }},
        columnWidths: [2800, 6560],
        borders: {{ ...Object.fromEntries(["top","bottom","left","right","insideH","insideV"].map(k => [k, _b()])) }},
        rows: [
          _infoRow("RFP Reference",       "{ref_number}",  0),
          _infoRow("Category",            "{category}",    1),
          _infoRow("Issuing Organisation","{org_name}",    0),
          _infoRow("Issue Date",          "{issue_date}",  1),
          _infoRow("Response Deadline",   "[Insert Date \\u2014 {deadline_weeks} weeks from above]", 0),
          _infoRow("Submission Email",    "[procurement@yourorganisation.com]", 1),
          _infoRow("Questions Deadline",  "[Insert Date \\u2014 5 business days after issue]", 0),
          _infoRow("RFP Contact",         "[Name, Title, Email, Phone]", 1),
        ]
      }}),
      _spacer(),
      _para("Mandatory Requirements — vendors failing any item below are automatically disqualified:", {{ bold: true, color: "CC0000" }}),
      _spacer(80),
      ...restrictions.map(r => _bullet(r)),

      // ── Dynamic Sections ─────────────────────────────────────
      {sections_js}

      // ── Scoring Criteria ─────────────────────────────────────
      _pageBreak(),
      _banner("EV", "Evaluation Criteria & Scoring"),
      _spacer(160),
      _para("All proposals will be scored by the Vendor Selection Committee using the weighted criteria below. Scores are 0\\u201310 per criterion, multiplied by the weight to produce a total out of 100."),
      _spacer(120),
      new Table({{
        width: {{ size: 9360, type: WidthType.DXA }},
        columnWidths: [4000, 1200, 4160],
        rows: [
          new TableRow({{ children: [
            _headerCell("Criterion",          4000),
            _headerCell("Weight",             1200),
            _headerCell("Key Evaluation Focus", 4160),
          ]}}),
          {criteria_rows}
        ]
      }}),
      _spacer(),
      _para("Submission Instructions", {{ bold: true, size: 24, color: NAVY }}),
      _spacer(80),
      _bullet("Submit as a single PDF: [CompanyName]_{ref_number}.pdf"),
      _bullet("Email to: [procurement@yourorganisation.com] — Subject: {ref_number} Proposal"),
      _bullet("Proposals must arrive by the deadline date at 5:00 PM local time."),
      _bullet("All questions in writing only to the procurement contact above."),
      _bullet("Proposals valid for minimum 90 days from submission deadline."),
      _bullet("The Organisation reserves the right to reject any or all proposals without obligation."),
      _spacer(400),
      new Paragraph({{ alignment: AlignmentType.CENTER, spacing: {{ before: 160, after: 80 }},
        children: [new TextRun({{ text: "\\u2014 End of Request for Proposal \\u2014", bold: true, size: 22, color: NAVY, font: "Arial" }})] }}),
      new Paragraph({{ alignment: AlignmentType.CENTER,
        children: [new TextRun({{ text: "Thank you for your interest. We look forward to reviewing your proposal.", size: 20, color: "888888", font: "Arial" }})] }}),

    ]
  }}]
}});

Packer.toBuffer(doc).then(buffer => {{
  fs.writeFileSync(OUTPUT_PATH, buffer);
  console.log("RFP document generated: " + OUTPUT_PATH);
}});
"""
