"""
generate_rfp.py — Standalone RFP Generator
==========================================
Run independently to generate an RFP for any healthcare vendor category.

Usage:
    python generate_rfp.py

Or import and call directly:
    from generate_rfp import run
    run(category="EHR / Electronic Health Records", org_name="My Hospital")
"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from rfp_engine import generate_rfp, template_exists, CATEGORY_KEYS

CATEGORIES = list(CATEGORY_KEYS.keys())

DEFAULT_CRITERIA = {
    "HIPAA Compliance":     {"weight": 25, "desc": "Full HIPAA/HITECH compliance, BAA availability"},
    "Data Security":        {"weight": 20, "desc": "Encryption, access controls, SOC2/ISO 27001"},
    "EHR Integration":      {"weight": 15, "desc": "Epic, Cerner, HL7 FHIR support"},
    "Pricing & TCO":        {"weight": 15, "desc": "Transparent pricing, ROI potential"},
    "Customer Support":     {"weight": 10, "desc": "24/7 healthcare-specific SLA"},
    "Scalability":          {"weight": 10, "desc": "Growth and enterprise readiness"},
    "Implementation Time":  {"weight": 5,  "desc": "Time to go-live and onboarding"},
}

DEFAULT_RESTRICTIONS = [
    "Must be HIPAA compliant with signed BAA",
    "Must have 3+ years healthcare experience",
    "Must support HL7 FHIR standards",
    "No vendors under active FDA warning letters",
]


def run(
    category: str = None,
    org_name: str = None,
    top_vendors: list = None,
    criteria: dict = None,
    restrictions: list = None,
    output_dir: str = "generated/"
) -> str:
    """
    Generate an RFP document. If called without arguments, runs interactively.
    Returns the path to the generated .docx file.
    """

    # ── Interactive mode if run directly ──────────────────────
    if category is None:
        print("\n" + "═"*55)
        print("  📋 HEALTHCARE RFP GENERATOR")
        print("═"*55)

        print("\nAvailable Categories:")
        for i, cat in enumerate(CATEGORIES, 1):
            status = "✅ Template" if template_exists(cat) else "⚡ AI Generate"
            print(f"  [{i}] {cat:<42} {status}")

        while True:
            choice = input("\nSelect category (number): ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(CATEGORIES):
                category = CATEGORIES[int(choice) - 1]
                break
            print("  Invalid choice. Try again.")

        org_name = input("Your organisation name: ").strip() or "[Your Organisation]"

        vendors_input = input("Top vendor names (comma-separated, or press Enter to skip): ").strip()
        top_vendors = [v.strip() for v in vendors_input.split(",") if v.strip()] if vendors_input else []

    # ── Use defaults if not provided ──────────────────────────
    criteria     = criteria     or DEFAULT_CRITERIA
    restrictions = restrictions or DEFAULT_RESTRICTIONS
    top_vendors  = top_vendors  or []

    # ── Show what will happen ─────────────────────────────────
    source = "Pre-built template" if template_exists(category) else "Claude AI (no template found)"
    print(f"\n  Category:    {category}")
    print(f"  Organisation: {org_name}")
    print(f"  Source:      {source}")
    print(f"  Vendors:     {', '.join(top_vendors) if top_vendors else 'None specified'}")
    print(f"  Output dir:  {output_dir}")

    # ── Generate ──────────────────────────────────────────────
    print("\n  Generating RFP document...\n")
    out_path = generate_rfp(
        category       = category,
        org_name       = org_name,
        top_vendors    = top_vendors,
        criteria       = criteria,
        restrictions   = restrictions,
        output_dir     = output_dir,
        deadline_weeks = "2-4"
    )

    print(f"\n  ✅ RFP generated successfully!")
    print(f"  📄 File: {out_path}")
    print("═"*55 + "\n")
    return out_path


if __name__ == "__main__":
    run()
