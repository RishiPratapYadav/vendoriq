"""
Healthcare Vendor Selection — Streamlit Web App
================================================
pip install streamlit anthropic
streamlit run app.py
"""

import streamlit as st
import anthropic
import json
import os
import re
import sys
import time
from datetime import datetime

# ── RFP SYSTEM ─────────────────────────────────────────────────
# Option 2: pre-built templates  |  Option 3: Claude AI fallback
_rfp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rfp_system")
if os.path.exists(_rfp_dir):
    sys.path.insert(0, _rfp_dir)
    try:
        from rfp_engine import generate_rfp, template_exists
        RFP_AVAILABLE = True
    except ImportError:
        RFP_AVAILABLE = False
else:
    RFP_AVAILABLE = False

# ── PAGE CONFIG ────────────────────────────────────────────────
st.set_page_config(
    page_title="VendorIQ — Healthcare",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CUSTOM CSS ─────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');

/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}
.stApp {
    background: #f7f6f3;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: #0f1923;
    border-right: none;
}
section[data-testid="stSidebar"] * {
    color: #e8e4d9 !important;
}
section[data-testid="stSidebar"] .stSlider label,
section[data-testid="stSidebar"] .stSelectbox label {
    color: #a09880 !important;
    font-size: 0.78rem !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
section[data-testid="stSidebar"] hr {
    border-color: #2a3540 !important;
}

/* ── Header ── */
.vendoriq-header {
    background: #0f1923;
    color: #f0ebe0;
    padding: 2.5rem 3rem;
    border-radius: 16px;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
}
.vendoriq-header::before {
    content: '';
    position: absolute;
    top: -60px; right: -60px;
    width: 240px; height: 240px;
    background: radial-gradient(circle, #2dd4a820 0%, transparent 70%);
    border-radius: 50%;
}
.vendoriq-header h1 {
    font-family: 'DM Serif Display', serif;
    font-size: 2.6rem;
    margin: 0;
    letter-spacing: -0.02em;
    color: #f0ebe0;
}
.vendoriq-header p {
    color: #8a9ba8;
    margin: 0.4rem 0 0;
    font-size: 1rem;
    font-weight: 300;
}
.vendoriq-badge {
    display: inline-block;
    background: #2dd4a815;
    border: 1px solid #2dd4a840;
    color: #2dd4a8;
    padding: 0.2rem 0.75rem;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 1rem;
}

/* ── Step cards ── */
.step-card {
    background: white;
    border: 1px solid #e8e4da;
    border-radius: 12px;
    padding: 1.6rem 2rem;
    margin-bottom: 1.2rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.step-card h3 {
    font-family: 'DM Serif Display', serif;
    font-size: 1.25rem;
    color: #1a2330;
    margin: 0 0 0.3rem;
}
.step-card p {
    color: #6b7a87;
    font-size: 0.88rem;
    margin: 0;
}

/* ── Vendor cards ── */
.vendor-card {
    background: white;
    border: 1px solid #e8e4da;
    border-left: 4px solid #2dd4a8;
    border-radius: 10px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 0.8rem;
}
.vendor-rank {
    font-family: 'DM Serif Display', serif;
    font-size: 2rem;
    color: #e8e4da;
    float: right;
    line-height: 1;
}
.vendor-name {
    font-weight: 600;
    font-size: 1.05rem;
    color: #1a2330;
}
.vendor-score {
    font-size: 0.85rem;
    color: #2dd4a8;
    font-weight: 600;
}
.vendor-note {
    font-size: 0.82rem;
    color: #8a9ba8;
    margin-top: 0.3rem;
}

/* ── Score bar ── */
.score-bar-wrap {
    background: #f0ebe0;
    border-radius: 4px;
    height: 6px;
    margin-top: 0.6rem;
    overflow: hidden;
}
.score-bar-fill {
    height: 6px;
    border-radius: 4px;
    background: linear-gradient(90deg, #2dd4a8, #0fa8c8);
    transition: width 0.8s ease;
}

/* ── Status pills ── */
.pill {
    display: inline-block;
    padding: 0.2rem 0.8rem;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.05em;
}
.pill-green  { background:#dcfce7; color:#166534; }
.pill-amber  { background:#fef9c3; color:#854d0e; }
.pill-blue   { background:#dbeafe; color:#1e40af; }
.pill-slate  { background:#f1f5f9; color:#475569; }

/* ── Metric tiles ── */
.metric-tile {
    background: white;
    border: 1px solid #e8e4da;
    border-radius: 12px;
    padding: 1.2rem;
    text-align: center;
}
.metric-tile .val {
    font-family: 'DM Serif Display', serif;
    font-size: 2.2rem;
    color: #1a2330;
    line-height: 1;
}
.metric-tile .lbl {
    font-size: 0.78rem;
    color: #8a9ba8;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 0.3rem;
}

/* ── Buttons ── */
.stButton > button {
    background: #0f1923;
    color: #f0ebe0;
    border: none;
    border-radius: 8px;
    font-family: 'DM Sans', sans-serif;
    font-weight: 500;
    padding: 0.55rem 1.5rem;
    cursor: pointer;
    transition: background 0.2s;
}
.stButton > button:hover {
    background: #1e3040;
    color: #f0ebe0;
}

/* ── Checkpoint banner ── */
.checkpoint-banner {
    background: linear-gradient(135deg, #0f1923, #1e3040);
    border: 1px solid #2a3f50;
    border-radius: 12px;
    padding: 1.5rem 2rem;
    margin: 1.5rem 0;
    color: #f0ebe0;
}
.checkpoint-banner h4 {
    font-family: 'DM Serif Display', serif;
    font-size: 1.2rem;
    margin: 0 0 0.4rem;
    color: #2dd4a8;
}
.checkpoint-banner p {
    margin: 0;
    color: #8a9ba8;
    font-size: 0.88rem;
}

/* ── Log box ── */
.log-box {
    background: #0f1923;
    color: #7dd3b8;
    font-family: 'Courier New', monospace;
    font-size: 0.8rem;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    height: 180px;
    overflow-y: auto;
    line-height: 1.7;
}

/* ── Dividers ── */
.section-label {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #8a9ba8;
    margin: 1.8rem 0 0.8rem;
}

/* ── Restriction tag ── */
.restriction-tag {
    display: inline-block;
    background: #fff7ed;
    border: 1px solid #fed7aa;
    color: #9a3412;
    border-radius: 6px;
    padding: 0.2rem 0.65rem;
    font-size: 0.76rem;
    margin: 0.2rem 0.2rem 0.2rem 0;
}

/* ── Hide streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 2rem; }
</style>
""", unsafe_allow_html=True)

# ── SESSION STATE ──────────────────────────────────────────────
def init_state():
    defaults = {
        "step": 1,
        "criteria": {
            "HIPAA Compliance":     {"weight": 25, "desc": "Full HIPAA/HITECH compliance, BAA availability"},
            "Data Security":        {"weight": 20, "desc": "Encryption, access controls, SOC2/ISO 27001"},
            "EHR Integration":      {"weight": 15, "desc": "Epic, Cerner, Allscripts, HL7 FHIR"},
            "Pricing & TCO":        {"weight": 15, "desc": "Transparent pricing, ROI potential"},
            "Customer Support":     {"weight": 10, "desc": "24/7 healthcare-specific SLA"},
            "Scalability":          {"weight": 10, "desc": "Growth & enterprise readiness"},
            "Implementation Time":  {"weight": 5,  "desc": "Time to go-live & onboarding"},
        },
        "restrictions": [
            "Must be HIPAA compliant with signed BAA",
            "Must have 3+ years healthcare experience",
            "Must support HL7 FHIR standards",
            "No vendors under active FDA warning letters",
        ],
        "category": "",
        "org_name": "",
        "discovered": [],
        "approved_vendors": [],
        "scored": [],
        "excluded": [],
        "final_report": None,
        "log": [],
        "running": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ── HELPERS ───────────────────────────────────────────────────
def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    st.session_state.log.append(f"[{ts}] {msg}")

def weight_total():
    return sum(v["weight"] for v in st.session_state.criteria.values())

def score_color(score):
    if score >= 80: return "#2dd4a8"
    if score >= 60: return "#f59e0b"
    return "#ef4444"

# ── SIMULATED VENDOR DATA ─────────────────────────────────────
VENDOR_DB = {
    "EHR / Electronic Health Records": [
        {"name": "Epic Systems",         "desc": "Market leader in EHR for large health systems"},
        {"name": "Oracle Health (Cerner)","desc": "Enterprise EHR with strong analytics"},
        {"name": "Meditech",             "desc": "EHR for community & critical access hospitals"},
        {"name": "athenahealth",         "desc": "Cloud-native EHR & revenue cycle"},
        {"name": "eClinicalWorks",       "desc": "Ambulatory EHR & population health"},
        {"name": "Allscripts",           "desc": "EHR and practice management platform"},
        {"name": "NextGen Healthcare",   "desc": "Specialty-focused EHR & PM"},
        {"name": "DrChrono",             "desc": "Mobile-first EHR for independent practices"},
        {"name": "Kareo",                "desc": "Cloud EHR for small practices"},
        {"name": "AdvancedMD",           "desc": "Integrated EHR, billing & telemedicine"},
    ],
    "Medical Billing & Revenue Cycle": [
        {"name": "Waystar",              "desc": "End-to-end revenue cycle automation"},
        {"name": "Experian Health",      "desc": "Patient access & revenue cycle"},
        {"name": "Change Healthcare",    "desc": "Clearinghouse & RCM solutions"},
        {"name": "Availity",             "desc": "Real-time insurance eligibility & claims"},
        {"name": "nThrive",              "desc": "Revenue cycle management & analytics"},
        {"name": "Optum360",             "desc": "Coding, billing & AR management"},
        {"name": "R1 RCM",               "desc": "Tech-enabled RCM for health systems"},
        {"name": "Ensemble Health",      "desc": "Outsourced RCM services"},
        {"name": "MedAssets",            "desc": "Supply chain & revenue cycle"},
        {"name": "MedBridge",            "desc": "Billing for rehabilitation practices"},
    ],
    "Telemedicine / Virtual Care Platform": [
        {"name": "Teladoc Health",       "desc": "Global telehealth & virtual primary care"},
        {"name": "Amwell",               "desc": "Enterprise telehealth platform"},
        {"name": "Doxy.me",              "desc": "HIPAA-compliant video visits"},
        {"name": "Zoom for Healthcare",  "desc": "HIPAA-enabled video for care teams"},
        {"name": "MDLive",               "desc": "On-demand telehealth services"},
        {"name": "Spruce Health",        "desc": "Patient communication & telehealth"},
        {"name": "Mend",                 "desc": "Telehealth with AI-driven scheduling"},
        {"name": "Klara",                "desc": "Patient messaging & virtual care"},
        {"name": "Updox",                "desc": "Healthcare communication platform"},
        {"name": "SimplePractice",       "desc": "Telehealth for mental & behavioral health"},
    ],
    "Healthcare Analytics & AI": [
        {"name": "Health Catalyst",      "desc": "Data & analytics platform for health systems"},
        {"name": "Innovaccer",           "desc": "Unified health data platform & AI"},
        {"name": "IBM Watson Health",    "desc": "AI-driven clinical & operational analytics"},
        {"name": "Optum Analytics",      "desc": "Population health & claims analytics"},
        {"name": "Arcadia",              "desc": "Population health management platform"},
        {"name": "Dimensional Insight",  "desc": "Healthcare BI & data analytics"},
        {"name": "Philips HealthSuite",  "desc": "Connected care & analytics cloud"},
        {"name": "Nuvolo",               "desc": "Connected workplace for healthcare ops"},
        {"name": "Apixio",               "desc": "AI-powered clinical insights from data"},
        {"name": "Jvion",                "desc": "AI clinical success machine"},
    ],
    "Medical Device Software": [
        {"name": "Greenway Health",      "desc": "EHR with device integration"},
        {"name": "Imprivata",            "desc": "Identity & access for medical devices"},
        {"name": "Medidata",             "desc": "Clinical trial & device data platform"},
        {"name": "MedaSystems",          "desc": "Medical device lifecycle management"},
        {"name": "Axway",                "desc": "Healthcare data exchange & APIs"},
        {"name": "Stryker Software",     "desc": "Connected OR & device analytics"},
        {"name": "GE Healthcare Digital","desc": "Imaging & device data platform"},
        {"name": "Philips IntelliSpace", "desc": "Radiology & device analytics"},
        {"name": "Siemens Healthineers", "desc": "Digital health & device software"},
        {"name": "Capsule Technologies", "desc": "Medical device integration engine"},
    ],
}

VENDOR_SCORES_DB = {
    "Epic Systems":          {"HIPAA Compliance":9,"Data Security":9,"EHR Integration":10,"Pricing & TCO":5,"Customer Support":8,"Scalability":10,"Implementation Time":4},
    "Oracle Health (Cerner)":{"HIPAA Compliance":9,"Data Security":8,"EHR Integration":9,"Pricing & TCO":5,"Customer Support":7,"Scalability":9,"Implementation Time":5},
    "Meditech":              {"HIPAA Compliance":9,"Data Security":8,"EHR Integration":8,"Pricing & TCO":7,"Customer Support":8,"Scalability":7,"Implementation Time":6},
    "athenahealth":          {"HIPAA Compliance":9,"Data Security":8,"EHR Integration":8,"Pricing & TCO":7,"Customer Support":8,"Scalability":8,"Implementation Time":7},
    "eClinicalWorks":        {"HIPAA Compliance":8,"Data Security":7,"EHR Integration":8,"Pricing & TCO":8,"Customer Support":7,"Scalability":7,"Implementation Time":8},
    "Allscripts":            {"HIPAA Compliance":8,"Data Security":7,"EHR Integration":8,"Pricing & TCO":7,"Customer Support":6,"Scalability":7,"Implementation Time":7},
    "NextGen Healthcare":    {"HIPAA Compliance":8,"Data Security":7,"EHR Integration":7,"Pricing & TCO":7,"Customer Support":7,"Scalability":6,"Implementation Time":7},
    "DrChrono":              {"HIPAA Compliance":8,"Data Security":7,"EHR Integration":6,"Pricing & TCO":8,"Customer Support":7,"Scalability":5,"Implementation Time":9},
    "Kareo":                 {"HIPAA Compliance":8,"Data Security":7,"EHR Integration":6,"Pricing & TCO":9,"Customer Support":7,"Scalability":5,"Implementation Time":9},
    "AdvancedMD":            {"HIPAA Compliance":8,"Data Security":7,"EHR Integration":7,"Pricing & TCO":7,"Customer Support":7,"Scalability":6,"Implementation Time":8},
    "default":               {"HIPAA Compliance":7,"Data Security":7,"EHR Integration":6,"Pricing & TCO":7,"Customer Support":7,"Scalability":6,"Implementation Time":7},
}

def get_scores(vendor_name):
    return VENDOR_SCORES_DB.get(vendor_name, VENDOR_SCORES_DB["default"])

def compute_weighted_score(vendor_name, scores):
    total = 0
    breakdown = {}
    for crit, info in st.session_state.criteria.items():
        raw = scores.get(crit, 5)
        w   = info["weight"]
        ws  = (raw / 10) * w
        total += ws
        breakdown[crit] = {"raw": raw, "weight": w, "weighted": round(ws, 2)}
    return round(total, 1), breakdown

# ── SIDEBAR ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding: 1rem 0 0.5rem;'>
        <div style='font-family:"DM Serif Display",serif; font-size:1.4rem; color:#f0ebe0;'>VendorIQ</div>
        <div style='font-size:0.72rem; color:#4a6070; letter-spacing:0.1em; text-transform:uppercase;'>Healthcare Edition</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Progress
    steps = ["Configure", "Discover", "Review", "Score", "Rank", "Report"]
    current = st.session_state.step
    for i, s in enumerate(steps, 1):
        icon  = "✓" if i < current else ("▶" if i == current else "○")
        color = "#2dd4a8" if i < current else ("#f0ebe0" if i == current else "#2a3540")
        st.markdown(f"<div style='color:{color}; font-size:0.82rem; padding:0.3rem 0;'>{icon} {i}. {s}</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<div style='font-size:0.72rem; color:#4a6070; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:0.8rem;'>Criteria Weights</div>", unsafe_allow_html=True)

    total_w = weight_total()
    color_w = "#2dd4a8" if total_w == 100 else "#ef4444"
    st.markdown(f"<div style='font-size:0.8rem; color:{color_w}; margin-bottom:0.5rem;'>Total: {total_w}% {'✓' if total_w==100 else '⚠ must = 100%'}</div>", unsafe_allow_html=True)

    for crit in st.session_state.criteria:
        st.session_state.criteria[crit]["weight"] = st.slider(
            crit,
            0, 50,
            st.session_state.criteria[crit]["weight"],
            step=5,
            key=f"slider_{crit}"
        )

    st.markdown("---")
    if st.button("🔄 Reset All", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# ── MAIN CONTENT ──────────────────────────────────────────────

# Header
st.markdown("""
<div class="vendoriq-header">
    <div class="vendoriq-badge">AI-Powered · Healthcare</div>
    <h1>Vendor Intelligence Platform</h1>
    <p>Discover, evaluate, and rank healthcare vendors — with you in control at every step.</p>
</div>
""", unsafe_allow_html=True)

# ════════════════════════════════════════
# STEP 1 — CONFIGURE
# ════════════════════════════════════════
if st.session_state.step == 1:
    st.markdown('<div class="section-label">Step 1 of 6 — Configure Your Search</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown('<div class="step-card"><h3>Organisation Details</h3><p>Tell us about your organisation so we can tailor results.</p></div>', unsafe_allow_html=True)
        org = st.text_input("Organisation name", placeholder="e.g. St. Mary's Hospital Network")
        category = st.selectbox("Vendor category you need", list(VENDOR_DB.keys()))

        st.markdown('<div class="section-label">Hard Restrictions</div>', unsafe_allow_html=True)
        st.markdown("Vendors failing any restriction are automatically excluded.")
        restrictions_text = st.text_area(
            "One restriction per line",
            value="\n".join(st.session_state.restrictions),
            height=120,
            label_visibility="collapsed"
        )

    with col2:
        st.markdown('<div class="step-card"><h3>Scoring Criteria</h3><p>Adjust weights in the sidebar. They must total 100%.</p></div>', unsafe_allow_html=True)
        total_w = weight_total()
        for crit, info in st.session_state.criteria.items():
            pct = info["weight"]
            bar_color = "#2dd4a8" if pct >= 15 else "#94a3b8"
            st.markdown(f"""
            <div style='margin-bottom:0.6rem;'>
                <div style='display:flex; justify-content:space-between; font-size:0.82rem; color:#1a2330;'>
                    <span>{crit}</span><span style='color:{bar_color}; font-weight:600;'>{pct}%</span>
                </div>
                <div class='score-bar-wrap'><div class='score-bar-fill' style='width:{pct*2}%; background:{bar_color};'></div></div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"<div style='font-size:0.8rem; margin-top:0.5rem; color:{'#2dd4a8' if total_w==100 else '#ef4444'};'>Total: {total_w}%</div>", unsafe_allow_html=True)

    st.markdown("---")

    ready = org.strip() and category and total_w == 100
    if not ready:
        if total_w != 100:
            st.warning(f"⚠️ Criteria weights total {total_w}%. Please adjust sidebar sliders to reach exactly 100%.")
        if not org.strip():
            st.info("Please enter your organisation name to continue.")

    if st.button("Begin Vendor Discovery →", disabled=not ready):
        st.session_state.org_name = org.strip()
        st.session_state.category = category
        st.session_state.restrictions = [r.strip() for r in restrictions_text.strip().split("\n") if r.strip()]
        st.session_state.step = 2
        log(f"Session started for {org} — Category: {category}")
        st.rerun()

# ════════════════════════════════════════
# STEP 2 — DISCOVER
# ════════════════════════════════════════
elif st.session_state.step == 2:
    st.markdown('<div class="section-label">Step 2 of 6 — Vendor Discovery</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="checkpoint-banner">
        <h4>🔍 Searching for vendors in: {st.session_state.category}</h4>
        <p>Claude is identifying candidates that match your industry and category. This usually takes a few seconds.</p>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.discovered:
        with st.spinner("Discovering vendors..."):
            time.sleep(1.5)  # simulate API call
            vendors = VENDOR_DB.get(st.session_state.category, [])
            st.session_state.discovered = vendors
            log(f"Discovered {len(vendors)} vendors in {st.session_state.category}")

    vendors = st.session_state.discovered
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div class="metric-tile"><div class="val">{len(vendors)}</div><div class="lbl">Vendors Found</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-tile"><div class="val">{len(st.session_state.restrictions)}</div><div class="lbl">Hard Restrictions</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-tile"><div class="val">{len(st.session_state.criteria)}</div><div class="lbl">Scoring Criteria</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-label">Vendors Discovered</div>', unsafe_allow_html=True)
    cols = st.columns(2)
    for i, v in enumerate(vendors):
        with cols[i % 2]:
            st.markdown(f"""
            <div class="vendor-card" style='border-left-color: #94a3b8;'>
                <div class="vendor-name">{v['name']}</div>
                <div class="vendor-note">{v['desc']}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="section-label">Add a Vendor Manually</div>', unsafe_allow_html=True)
    c1, c2 = st.columns([3, 1])
    with c1:
        manual_vendor = st.text_input("Vendor name", placeholder="e.g. VendorName Inc.", label_visibility="collapsed")
    with c2:
        if st.button("Add Vendor") and manual_vendor.strip():
            st.session_state.discovered.append({"name": manual_vendor.strip(), "desc": "Manually added"})
            log(f"Manually added vendor: {manual_vendor.strip()}")
            st.rerun()

    st.markdown("---")
    col_a, col_b = st.columns([1, 1])
    with col_a:
        if st.button("← Back"):
            st.session_state.step = 1
            st.rerun()
    with col_b:
        if st.button("Review Vendor Longlist →"):
            st.session_state.approved_vendors = [v["name"] for v in st.session_state.discovered]
            st.session_state.step = 3
            log("Moved to vendor review checkpoint")
            st.rerun()

# ════════════════════════════════════════
# STEP 3 — HUMAN CHECKPOINT: REVIEW LONGLIST
# ════════════════════════════════════════
elif st.session_state.step == 3:
    st.markdown('<div class="section-label">Step 3 of 6 — Human Checkpoint: Review Longlist</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="checkpoint-banner">
        <h4>🧑 Your Review Required</h4>
        <p>Check or uncheck vendors before Claude begins detailed scoring. Unchecked vendors will be excluded.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-label">Active Restrictions</div>', unsafe_allow_html=True)
    restriction_html = "".join(f'<span class="restriction-tag">⚠ {r}</span>' for r in st.session_state.restrictions)
    st.markdown(restriction_html, unsafe_allow_html=True)

    st.markdown('<div class="section-label">Select Vendors to Evaluate</div>', unsafe_allow_html=True)

    approved = []
    cols = st.columns(2)
    for i, v in enumerate(st.session_state.discovered):
        name = v["name"] if isinstance(v, dict) else v
        desc = v.get("desc", "") if isinstance(v, dict) else ""
        with cols[i % 2]:
            checked = st.checkbox(f"**{name}**  \n{desc}", value=True, key=f"chk_{name}")
            if checked:
                approved.append(name)

    st.markdown(f"<div style='font-size:0.85rem; color:#6b7a87; margin-top:1rem;'>✓ {len(approved)} vendors selected for evaluation</div>", unsafe_allow_html=True)
    st.markdown("---")

    col_a, col_b = st.columns([1, 1])
    with col_a:
        if st.button("← Back"):
            st.session_state.step = 2
            st.rerun()
    with col_b:
        if st.button(f"Score {len(approved)} Vendors →", disabled=len(approved) == 0):
            st.session_state.approved_vendors = approved
            st.session_state.step = 4
            log(f"Human approved {len(approved)} vendors for scoring")
            st.rerun()

# ════════════════════════════════════════
# STEP 4 — SCORING
# ════════════════════════════════════════
elif st.session_state.step == 4:
    st.markdown('<div class="section-label">Step 4 of 6 — AI Scoring & Evaluation</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="checkpoint-banner">
        <h4>⚙️ Claude is scoring {len(st.session_state.approved_vendors)} vendors</h4>
        <p>Each vendor is evaluated against all {len(st.session_state.criteria)} criteria using weighted scoring.</p>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.scored:
        progress_bar = st.progress(0)
        status_area  = st.empty()
        vendors      = st.session_state.approved_vendors

        scored = []
        for i, vendor_name in enumerate(vendors):
            status_area.markdown(f"<div style='font-size:0.88rem; color:#6b7a87;'>Evaluating <strong>{vendor_name}</strong>...</div>", unsafe_allow_html=True)
            time.sleep(0.6)

            raw_scores = get_scores(vendor_name)
            total, breakdown = compute_weighted_score(vendor_name, raw_scores)

            scored.append({
                "name":      vendor_name,
                "total":     total,
                "breakdown": breakdown,
            })
            log(f"Scored {vendor_name}: {total}/100")
            progress_bar.progress((i + 1) / len(vendors))

        status_area.empty()
        st.session_state.scored = sorted(scored, key=lambda x: x["total"], reverse=True)
        log("All vendors scored. Ready for human review.")

    scored = st.session_state.scored
    st.markdown('<div class="section-label">Scoring Complete</div>', unsafe_allow_html=True)

    for i, v in enumerate(scored, 1):
        score = v["total"]
        bar_w = int(score)
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        st.markdown(f"""
        <div class="vendor-card">
            <span class="vendor-rank">#{i}</span>
            <div class="vendor-name">{medal} {v['name']}</div>
            <div class="vendor-score">{score}/100</div>
            <div class="score-bar-wrap">
                <div class="score-bar-fill" style='width:{bar_w}%; background:{score_color(score)};'></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    col_a, col_b = st.columns([1, 1])
    with col_a:
        if st.button("← Back"):
            st.session_state.scored = []
            st.session_state.step = 3
            st.rerun()
    with col_b:
        if st.button("Review & Override Rankings →"):
            st.session_state.step = 5
            st.rerun()

# ════════════════════════════════════════
# STEP 5 — HUMAN CHECKPOINT: OVERRIDE
# ════════════════════════════════════════
elif st.session_state.step == 5:
    st.markdown('<div class="section-label">Step 5 of 6 — Human Checkpoint: Override Rankings</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="checkpoint-banner">
        <h4>🧑 Your Review Required</h4>
        <p>Optionally exclude vendors or add notes before generating the final Top 7 report.</p>
    </div>
    """, unsafe_allow_html=True)

    scored = st.session_state.scored
    top7   = scored[:7]
    rest   = scored[7:]

    st.markdown('<div class="section-label">Top 7 — Final Candidates</div>', unsafe_allow_html=True)

    final_selection = []
    for i, v in enumerate(top7, 1):
        c1, c2, c3 = st.columns([3, 1, 1])
        with c1:
            score = v["total"]
            st.markdown(f"""
            <div style='padding:0.6rem 0;'>
                <span style='font-weight:600; color:#1a2330;'>{i}. {v['name']}</span>
                <span style='margin-left:0.8rem; color:{score_color(score)}; font-size:0.85rem; font-weight:600;'>{score}/100</span>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            keep = st.checkbox("Include", value=True, key=f"keep_{v['name']}")
        with c3:
            note = st.text_input("Note", placeholder="Optional", key=f"note_{v['name']}", label_visibility="collapsed")
        if keep:
            v["note"] = note
            final_selection.append(v)

    if rest:
        st.markdown('<div class="section-label">Outside Top 7 — Promote if needed</div>', unsafe_allow_html=True)
        for v in rest:
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(f"<span style='color:#6b7a87; font-size:0.88rem;'>{v['name']} — {v['total']}/100</span>", unsafe_allow_html=True)
            with c2:
                if st.button("Promote", key=f"promote_{v['name']}"):
                    st.session_state.scored = [v] + [x for x in scored if x["name"] != v["name"]]
                    log(f"Human promoted: {v['name']}")
                    st.rerun()

    st.markdown(f"<div style='margin-top:1rem; font-size:0.85rem; color:#6b7a87;'>Final report will include {len(final_selection)} vendors.</div>", unsafe_allow_html=True)
    st.markdown("---")

    col_a, col_b = st.columns([1, 1])
    with col_a:
        if st.button("← Back to Scores"):
            st.session_state.step = 4
            st.rerun()
    with col_b:
        if st.button("Generate Final Report →", disabled=len(final_selection) == 0):
            st.session_state.final_report = final_selection
            st.session_state.step = 6
            log(f"Final report generated with {len(final_selection)} vendors")
            st.rerun()

# ════════════════════════════════════════
# STEP 6 — FINAL REPORT
# ════════════════════════════════════════
elif st.session_state.step == 6:
    st.markdown('<div class="section-label">Step 6 of 6 — Final Report</div>', unsafe_allow_html=True)

    report = st.session_state.final_report or []
    org    = st.session_state.org_name
    cat    = st.session_state.category
    now    = datetime.now().strftime("%B %d, %Y")

    st.markdown(f"""
    <div class="vendoriq-header" style='padding:2rem 2.5rem;'>
        <div class="vendoriq-badge">Final Report</div>
        <h1 style='font-size:1.9rem;'>Vendor Selection Report</h1>
        <p>{org} · {cat} · {now}</p>
    </div>
    """, unsafe_allow_html=True)

    # Metrics row
    top = report[0] if report else {}
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="metric-tile"><div class="val">{len(report)}</div><div class="lbl">Vendors Selected</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-tile"><div class="val">{len(st.session_state.approved_vendors)}</div><div class="lbl">Evaluated</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-tile"><div class="val">{top.get("total","—")}</div><div class="lbl">Top Score</div></div>', unsafe_allow_html=True)
    with col4:
        avg = round(sum(v["total"] for v in report) / len(report), 1) if report else 0
        st.markdown(f'<div class="metric-tile"><div class="val">{avg}</div><div class="lbl">Avg Score</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-label">Top Ranked Vendors</div>', unsafe_allow_html=True)

    for i, v in enumerate(report, 1):
        score   = v["total"]
        note    = v.get("note", "")
        medal   = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"#{i}"
        pilltxt = "Recommended" if i == 1 else "Strong Fit" if i <= 3 else "Good Fit"
        pillcls = "pill-green" if i == 1 else "pill-blue" if i <= 3 else "pill-slate"

        with st.expander(f"{medal}  {v['name']}  —  {score}/100", expanded=(i <= 3)):
            c1, c2 = st.columns([2, 1])
            with c1:
                st.markdown(f'<span class="pill {pillcls}">{pilltxt}</span>', unsafe_allow_html=True)
                if note:
                    st.markdown(f"<div style='font-size:0.85rem; color:#1a2330; margin-top:0.6rem;'>📝 {note}</div>", unsafe_allow_html=True)
                st.markdown("<div style='margin-top:1rem;'>", unsafe_allow_html=True)
                for crit, data in v["breakdown"].items():
                    raw = data["raw"]
                    w   = data["weight"]
                    ws  = data["weighted"]
                    st.markdown(f"""
                    <div style='margin-bottom:0.5rem;'>
                        <div style='display:flex; justify-content:space-between; font-size:0.8rem; color:#6b7a87;'>
                            <span>{crit} <span style='color:#94a3b8;'>({w}%)</span></span>
                            <span style='color:#1a2330; font-weight:600;'>{raw}/10 → {ws}pts</span>
                        </div>
                        <div class='score-bar-wrap'>
                            <div class='score-bar-fill' style='width:{raw*10}%; background:{score_color(raw*10)};'></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                <div style='text-align:center; padding:1.5rem; background:#f7f6f3; border-radius:12px; margin-top:0.5rem;'>
                    <div style='font-family:"DM Serif Display",serif; font-size:3rem; color:{score_color(score)}; line-height:1;'>{score}</div>
                    <div style='font-size:0.72rem; color:#8a9ba8; text-transform:uppercase; letter-spacing:0.1em; margin-top:0.3rem;'>out of 100</div>
                </div>
                """, unsafe_allow_html=True)

    # Restrictions applied
    st.markdown('<div class="section-label">Restrictions Applied</div>', unsafe_allow_html=True)
    restriction_html = "".join(f'<span class="restriction-tag">✓ {r}</span>' for r in st.session_state.restrictions)
    st.markdown(restriction_html, unsafe_allow_html=True)

    # Download JSON
    st.markdown("---")
    report_data = {
        "title":          "Vendor Selection Report",
        "organisation":   org,
        "category":       cat,
        "generated":      now,
        "top_vendors":    report,
        "restrictions":   st.session_state.restrictions,
        "criteria":       st.session_state.criteria,
    }
    col_a, col_b, col_c = st.columns([2, 1, 1])
    with col_a:
        st.download_button(
            label="⬇ Download Report (JSON)",
            data=json.dumps(report_data, indent=2),
            file_name=f"vendor_report_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )
    with col_b:
        if st.button("🔄 Start New Search"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    with col_c:
        if st.button("← Edit Rankings"):
            st.session_state.step = 5
            st.rerun()

    # ── RFP GENERATION ───────────────────────────────────────────
    st.markdown("---")
    st.markdown('<div class="section-label">Generate RFP for Shortlisted Vendors</div>',
                unsafe_allow_html=True)

    if not RFP_AVAILABLE:
        st.info("ℹ️ RFP generation is not available — make sure the `rfp_system/` folder is in the same directory as `app.py`.")
    else:
        has_template = template_exists(cat)

        if has_template:
            st.markdown(f"""
            <div style="background:#f0fdf4; border:1px solid #bbf7d0; border-radius:8px;
                        padding:0.8rem 1.2rem; font-size:0.88rem; color:#166534; margin-bottom:1rem;">
                ✅ <strong>Pre-built template found</strong> for <em>{cat}</em> —
                RFP will use curated, category-specific questions.
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background:#fffbeb; border:1px solid #fde68a; border-radius:8px;
                        padding:0.8rem 1.2rem; font-size:0.88rem; color:#92400e; margin-bottom:1rem;">
                ⚡ <strong>No template found</strong> for <em>{cat}</em> —
                Claude AI will generate category-specific RFP questions on the fly.
            </div>""", unsafe_allow_html=True)

        col_r1, col_r2 = st.columns([2, 1])
        with col_r1:
            rfp_org = st.text_input(
                "Organisation name for RFP header",
                value=st.session_state.org_name,
                key="rfp_org_name"
            )
        with col_r2:
            rfp_deadline = st.selectbox(
                "Vendor response deadline",
                ["1-2 weeks", "2-4 weeks", "4-6 weeks"],
                index=1,
                key="rfp_deadline"
            )

        if st.button("📄 Generate RFP Word Document", use_container_width=True):
            top_vendor_names = [v["name"] for v in (st.session_state.final_report or [])[:7]]
            spinner_msg = (
                f"Loading template for {cat}..."
                if has_template
                else f"Asking Claude to generate RFP questions for {cat}..."
            )
            with st.spinner(spinner_msg):
                try:
                    rfp_path = generate_rfp(
                        category       = cat,
                        org_name       = rfp_org or org,
                        top_vendors    = top_vendor_names,
                        criteria       = st.session_state.criteria,
                        restrictions   = st.session_state.restrictions,
                        output_dir     = "/tmp/rfp_outputs/",
                        deadline_weeks = rfp_deadline
                    )
                    with open(rfp_path, "rb") as f:
                        rfp_bytes = f.read()

                    safe_cat = re.sub(r'[^a-zA-Z0-9]', '_', cat)
                    rfp_filename = f"RFP_{safe_cat}.docx"
                    source_label = "from template" if has_template else "by Claude AI"

                    st.success(f"✅ RFP generated {source_label} — ready to download")
                    st.download_button(
                        label     = f"⬇ Download RFP — {cat}",
                        data      = rfp_bytes,
                        file_name = rfp_filename,
                        mime      = "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key       = "download_rfp_docx"
                    )
                    log(f"RFP generated {source_label} for {cat}")
                except Exception as e:
                    st.error(f"RFP generation failed: {str(e)}")
                    st.info("Check that your ANTHROPIC_API_KEY is set in Streamlit Secrets and `rfp_system/` is present.")

    # ── Activity log ─────────────────────────────────────────────
    if st.session_state.log:
        with st.expander("📋 Activity Log"):
            log_html = "<br>".join(st.session_state.log)
            st.markdown(f'<div class="log-box">{log_html}</div>', unsafe_allow_html=True)
