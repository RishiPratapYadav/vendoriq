# 🚀 VendorIQ — Deploy in 3 Steps

## Files in this package

```
app.py              ← Main Streamlit web app
requirements.txt    ← Python dependencies
.streamlit/
  config.toml       ← App theme & server config
```

---

## Step 1 — Upload to GitHub (10 minutes)

1. Go to **github.com** and create a free account (if you don't have one)
2. Click the **+** button → **New repository**
3. Name it: `vendoriq` → click **Create repository**
4. Click **uploading an existing file**
5. Drag and drop ALL files from this package:
   - `app.py`
   - `requirements.txt`
   - `.streamlit/config.toml`
6. Click **Commit changes**

✅ Your code is now on GitHub.

---

## Step 2 — Deploy on Streamlit Cloud (5 minutes)

1. Go to **share.streamlit.io**
2. Click **Sign in with GitHub** → authorize
3. Click **New app**
4. Fill in:
   - Repository: `your-username/vendoriq`
   - Branch: `main`
   - Main file path: `app.py`
5. Click **Advanced settings** → **Secrets**
6. Add this (replace with your real key):
   ```
   ANTHROPIC_API_KEY = "sk-ant-your-key-here"
   ```
   Get your key from: https://console.anthropic.com
7. Click **Deploy!**

✅ In about 60 seconds you'll have a live URL like:
`https://your-username-vendoriq-app-xxxx.streamlit.app`

Share this URL with your team and clients.

---

## Step 3 — Share with Users

**For internal team:**
- Share the URL directly via email or Slack

**For external clients:**
- Add password protection (see below)
- Share the URL

### Adding a Password (Recommended for External Users)

Add this to the TOP of `app.py`, before anything else:

```python
import streamlit as st

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        st.title("VendorIQ — Login")
        pwd = st.text_input("Enter access password", type="password")
        if st.button("Login"):
            if pwd == st.secrets.get("APP_PASSWORD", "demo123"):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect password")
        st.stop()

check_password()
```

Then add `APP_PASSWORD = "yourpassword"` to your Streamlit Cloud Secrets.

---

## Running Locally (for testing)

```bash
pip install streamlit anthropic
export ANTHROPIC_API_KEY="sk-ant-your-key"
streamlit run app.py
```

Opens at: http://localhost:8501

---

## Updating Your App

1. Edit `app.py` on GitHub (click the pencil icon)
2. Click **Commit changes**
3. Streamlit Cloud automatically redeploys in ~30 seconds

No command line needed.
