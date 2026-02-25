"""
RFP Engine
===========
Generates category-aware RFP Word documents.

Priority:
  1. Load from /templates/<category_key>.json  (Option 2 — pre-built template)
  2. Generate via Claude API                   (Option 3 — AI fallback)

Usage:
    from rfp_engine import generate_rfp
    path = generate_rfp(
        category       = "EHR / Electronic Health Records",
        org_name       = "St. Mary's Hospital",
        top_vendors    = ["Epic", "Cerner", "athenahealth"],
        criteria       = {"HIPAA Compliance": {"weight": 25}, ...},
        restrictions   = ["Must be HIPAA compliant", ...],
        output_dir     = "generated/"
    )
"""

import os
import json
import re
import anthropic
from datetime import datetime
from docx_builder import build_rfp_docx   # see docx_builder.py

# ── PATHS ─────────────────────────────────────────────────────
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")

# ── CATEGORY → TEMPLATE FILE MAPPING ─────────────────────────
CATEGORY_KEYS = {
    "EHR / Electronic Health Records":       "ehr",
    "Medical Billing & Revenue Cycle":       "medical_billing",
    "Telemedicine / Virtual Care Platform":  "telemedicine",
    "Healthcare Analytics & AI":             "healthcare_analytics",
    "Medical Device Software":               "medical_device_software",
}

# ── PUBLIC ENTRY POINT ────────────────────────────────────────

def generate_rfp(
    category: str,
    org_name: str,
    top_vendors: list,
    criteria: dict,
    restrictions: list,
    output_dir: str = "generated/",
    deadline_weeks: str = "2-4"
) -> str:
    """
    Generate an RFP Word document for the given category.
    Returns the path to the generated .docx file.
    """
    print(f"\n[RFP Engine] Category: {category}")

    # Step 1 — Try to load pre-built template
    template = _load_template(category)

    if template:
        print(f"[RFP Engine] ✅ Template found: {_template_path(category)}")
        source = "template"
    else:
        print(f"[RFP Engine] ⚠️  No template found. Generating via Claude API...")
        template = _generate_via_claude(category, criteria, restrictions)
        source = "ai_generated"

    # Step 2 — Merge runtime context into template
    context = {
        "org_name":       org_name,
        "category":       category,
        "top_vendors":    top_vendors,
        "criteria":       criteria,
        "restrictions":   restrictions,
        "deadline_weeks": deadline_weeks,
        "issue_date":     datetime.now().strftime("%B %d, %Y"),
        "ref_number":     _ref_number(category),
        "source":         source,
    }
    template["context"] = context

    # Step 3 — Build the Word document
    os.makedirs(output_dir, exist_ok=True)
    safe_name = re.sub(r'[^a-zA-Z0-9]', '_', category)
    filename  = f"RFP_{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
    out_path  = os.path.join(output_dir, filename)

    build_rfp_docx(template, context, out_path)
    print(f"[RFP Engine] 📄 Document saved: {out_path}")
    return out_path


# ── TEMPLATE LOADER ───────────────────────────────────────────

def _template_path(category: str) -> str:
    key = CATEGORY_KEYS.get(category)
    if not key:
        return None
    return os.path.join(TEMPLATES_DIR, f"{key}.json")

def _load_template(category: str) -> dict:
    path = _template_path(category)
    if path and os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return None

def template_exists(category: str) -> bool:
    path = _template_path(category)
    return bool(path and os.path.exists(path))


# ── AI FALLBACK (Option 3) ────────────────────────────────────

def _generate_via_claude(category: str, criteria: dict, restrictions: list) -> dict:
    """
    Use Claude API to generate a full RFP template structure
    for any category that doesn't have a pre-built template.
    """
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    criteria_list = "\n".join(
        f"- {k} (weight: {v.get('weight', '?')}%)" for k, v in criteria.items()
    )
    restrictions_list = "\n".join(f"- {r}" for r in restrictions)

    prompt = f"""You are a healthcare procurement expert. Generate a comprehensive RFP template 
for the vendor category: "{category}"

Evaluation criteria being used:
{criteria_list}

Hard restrictions / disqualifiers:
{restrictions_list}

Return ONLY a valid JSON object with this exact structure:
{{
  "category": "{category}",
  "short_description": "One sentence describing what this RFP is for",
  "mandatory_requirements": [
    "List 4-6 absolute must-have compliance or regulatory requirements specific to this category"
  ],
  "sections": [
    {{
      "number": "01",
      "title": "Section Title",
      "description": "Brief intro paragraph for this section",
      "questions": [
        "Question 1 for vendors to answer",
        "Question 2 for vendors to answer"
      ]
    }}
  ]
}}

Include these 7 sections in order:
1. Company Background & History (10 questions)
2. Technical Specifications & Integrations (12 questions specific to {category})
3. Compliance & Security (12 questions - include category-specific regulations)
4. Pricing & Licensing Model (12 questions)
5. Implementation Timeline & Support (12 questions)
6. References & Case Studies (6 questions)
7. SLA & Performance Guarantees (10 questions)

Make all questions highly specific to "{category}" — not generic.
Return ONLY the JSON. No preamble, no explanation, no markdown backticks."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text.strip()
    # Strip markdown code fences if present
    raw = re.sub(r'^```json\s*', '', raw)
    raw = re.sub(r'^```\s*',     '', raw)
    raw = re.sub(r'\s*```$',     '', raw)

    template = json.loads(raw)
    print(f"[RFP Engine] ✅ Claude generated template with {len(template.get('sections', []))} sections")
    return template


# ── HELPERS ───────────────────────────────────────────────────

def _ref_number(category: str) -> str:
    key = CATEGORY_KEYS.get(category, "GEN")
    prefix = key.upper().replace("_", "")[:6]
    year = datetime.now().strftime("%Y")
    return f"RFP-{prefix}-{year}-001"
