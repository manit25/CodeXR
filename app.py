import os, time, base64, datetime, requests
import streamlit as st
from dotenv import load_dotenv

from codexr.utils_auth import signup_user, login_user, load_history, save_history as persist_history, clear_history
from codexr.llm import generate_structured_answer
from codexr.schema import Answer

load_dotenv()
st.set_page_config(page_title="CodeXR", layout="wide", page_icon="assets/logo.png")

ss = st.session_state
ss.setdefault("user", None)
ss.setdefault("last", None)
ss.setdefault("verbosity", "normal")
ss.setdefault("live_mode", False)
ss.setdefault("theme", "dark")
ss.setdefault("query", "")

# ----------------- Futuristic Theme -----------------
def inject_theme():
    dark = ss["theme"] == "dark"
    if dark:
        bg = "#05010a"
        text, sub = "#EAF2FF", "#9fb0c3"
        surface, border = "rgba(15,15,40,0.85)", "rgba(0,255,198,0.4)"
        btn_bg, btn_text, btn_border = "linear-gradient(90deg,#00FFC6,#7C3AED)", "#0c0f14", "transparent"
    else:
        bg = "#F7FAFF"
        text, sub = "#0E1624", "#516079"
        surface, border = "#FFFFFF", "rgba(0,0,0,0.1)"
        btn_bg, btn_text, btn_border = "linear-gradient(90deg,#7C3AED,#00FFC6)", "#FFFFFF", "transparent"

    st.markdown(f"""
    <style>
    /* Background with animated cyberpunk aura */
    [data-testid="stAppViewContainer"] {{
        background: {bg};
        color: {text};
        font-family: 'Roboto', sans-serif;
        background-image: radial-gradient(circle at 20% 20%, rgba(0,255,198,0.12) 0%, transparent 40%),
                          radial-gradient(circle at 80% 80%, rgba(124,58,237,0.12) 0%, transparent 40%);
        background-attachment: fixed;
        animation: bgmove 18s infinite alternate ease-in-out;
    }}
    @keyframes bgmove {{
        0% {{ background-position: 0% 0%; }}
        100% {{ background-position: 100% 100%; }}
    }}

    .cx-title {{
      font-weight:800; font-size:38px;
      background: linear-gradient(90deg,#00FFC6,#7C3AED);
      -webkit-background-clip: text;
      color: transparent;
      text-align:center; margin:20px 0;
      text-shadow: 0 0 20px rgba(0,255,198,0.6);
    }}

    .card {{
      background:{surface}; border:1px solid {border};
      border-radius:16px; padding:20px 25px;
      box-shadow:0 8px 32px rgba(0,0,0,.45);
      margin-bottom:18px;
      transition: all 0.3s ease;
    }}
    .card:hover {{
      transform: translateY(-3px);
      box-shadow:0 12px 36px rgba(0,255,198,0.4);
    }}

    .stButton button {{
      background: {btn_bg};
      color: {btn_text}; border:{btn_border};
      border-radius: 12px;
      padding: 0.6em 1.4em;
      font-weight: 600; font-size:16px;
      transition: all 0.25s ease;
      box-shadow: 0 0 12px rgba(124,58,237,0.6);
    }}
    .stButton button:hover {{
      transform: translateY(-2px) scale(1.03);
      box-shadow: 0 0 20px rgba(0,255,198,0.8);
    }}

    .google-btn {{
        display: inline-flex;
        align-items: center;
        background: {surface};
        color: {text};
        border: 1px solid {border};
        border-radius: 10px;
        padding: 12px 20px;
        font-size: 16px;
        font-weight: 600;
        font-family: 'Roboto', sans-serif;
        text-decoration: none;
        transition: all 0.3s ease;
        box-shadow: 0 0 15px rgba(0,255,198,0.3);
    }}
    .google-btn:hover {{
        transform: translateY(-2px) scale(1.02);
        box-shadow: 0 0 25px rgba(124,58,237,0.6);
    }}
    .google-btn img {{
        height: 20px;
        margin-right: 10px;
    }}
    </style>
    """, unsafe_allow_html=True)

inject_theme()

def get_image_as_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# ----------------- Login Panel -----------------
def login_panel():
    st.markdown(
        f"<div class='cx-title'><img src='data:image/png;base64,{get_image_as_base64('assets/logo.png')}' height='40'> CodeXR</div>",
        unsafe_allow_html=True
    )

    tabs = st.tabs(["🔑 Login", "🆕 Sign Up"])

    with tabs[0]:
        email = st.text_input("Email", key="login_email", placeholder="Enter your email")
        pw = st.text_input("Password", type="password", key="login_pw", placeholder="Enter your password")
        if st.button("Login", key="manual_login_btn"):
            if not email or not pw:
                st.error("Please enter both email and password.")
            else:
                ok, res = login_user(email, pw)
                if ok:
                    ss["user"] = {"email": email, "name": res.get("name", email.split('@')[0])}
                    st.rerun()
                else:
                    st.error(res)

    with tabs[1]:
        name = st.text_input("Name", key="signup_name", placeholder="Your Name")
        semail = st.text_input("Email", key="signup_email", placeholder="Enter your email")
        spw = st.text_input("Password", type="password", key="signup_pw", placeholder="Create a password")
        if st.button("Create account", key="create_account_btn"):
            if not name or not semail or not spw:
                st.error("Please fill in all fields.")
            else:
                ok, msg = signup_user(semail, name, spw)
                if ok:
                    st.success(msg)
                    st.info("You can now log in using your new account.")
                else:
                    st.error(msg)

    st.markdown("<h3 style='text-align:center; margin-top:30px;'>Or continue with Google</h3>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div style="display: flex; justify-content: center;">
            <a class="google-btn" href="http://localhost:5000/login">
                <img src='data:image/png;base64,{get_image_as_base64('assets/google.png')}' alt="Google">
                Continue with Google
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )

# ----------------- Google redirect handling -----------------
query_params = st.query_params.to_dict()
if not ss["user"] and "email" in query_params:
    ss["user"] = {
        "email": query_params.get("email"),
        "name": query_params.get("name", query_params["email"].split('@')[0])
    }
    st.rerun()

# ----------------- Auth Gate -----------------
if not ss["user"]:
    login_panel()
    st.stop()

user = ss["user"]

# ----------------- Header -----------------
st.markdown(
    f"<div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;'>"
    f"<div style='display: flex; align-items: center; gap: 10px;'>"
    f"<img src='data:image/png;base64,{get_image_as_base64('assets/logo.png')}' style='height: 40px;'>"
    f"<h1 style='margin:0; font-size:32px; color:{'#EAF2FF' if ss['theme']=='dark' else '#0E1624'};'>CodeXR</h1></div>"
    f"</div>",
    unsafe_allow_html=True
)

if st.toggle("🌙/☀️", value=(ss["theme"]=="light"), label_visibility="collapsed"):
    if ss["theme"] == "dark":
        ss["theme"] = "light"; st.rerun()
else:
    if ss["theme"] == "light":
        ss["theme"] = "dark"; st.rerun()

# ----------------- Layout -----------------
left, right = st.columns([1,2], gap="large")

with left:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("### 🎮 Input Gateway")
    q = st.text_area("Ask CodeXR", value=ss.get("query",""), height=150,
                     placeholder="Ask about Unity XR, Unreal, OpenXR, shaders...")
    ss["live_mode"] = st.checkbox("🌐 Live Mode", value=ss["live_mode"])
    v_opts = ["Concise","Normal","Detailed"]
    v_sel = st.selectbox("Response length", v_opts, index={"concise":0,"normal":1,"detailed":2}[ss["verbosity"]])
    ss["verbosity"] = {"Concise":"concise","Normal":"normal","Detailed":"detailed"}[v_sel]
    if st.button("⚡ Generate"):
        if q.strip():
            with st.spinner("Generating... ⚡"):
                try:
                    ans_dict = generate_structured_answer(q, verbosity=ss["verbosity"], live_mode=ss["live_mode"])
                    ans = Answer(**ans_dict)
                    ss["last"] = ans; ss["query"]=q
                    persist_history(user["email"], {"query":q,"answer":ans.model_dump()})
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("Enter a question first.")
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("### 📖 Knowledge Stream")
    if ss.get("last") and isinstance(ss["last"], Answer):
        res: Answer = ss["last"]
        st.markdown(f"**Context:** `{res.context}`")
        st.markdown(f"**Target:** `{res.target}`  |  **Difficulty:** `{res.difficulty}`")
        st.markdown("---")
        for i,s in enumerate(res.subtasks or []):
            st.subheader(f"{i+1}. {s.title}")
            if s.details: st.markdown(s.details)
            for step in s.steps: st.markdown(f"- {step}")
        if res.snippet and res.snippet.code.strip():
            st.code(res.snippet.code, language=res.snippet.language)
            if res.snippet.explanation: st.markdown(res.snippet.explanation)
        if res.best_practices:
            st.markdown("#### ✅ Best Practices"); [st.markdown(f"- {bp}") for bp in res.best_practices]
        if res.gotchas:
            st.markdown("#### ⚠️ Gotchas"); [st.markdown(f"- {g}") for g in res.gotchas]
        if res.docs:
            st.markdown("#### 📚 Docs"); [st.markdown(f"- [{d.title}]({d.url})") for d in res.docs]
        with st.expander("Raw JSON"): st.json(res.model_dump())
    else: st.info("Ask CodeXR something to see results.")
    st.markdown("</div>", unsafe_allow_html=True)

# ----------------- Sidebar -----------------
st.sidebar.markdown(f"**Signed in as:** {user['name']} ({user['email']})")
hist_raw = load_history(user["email"]) or []
if hist_raw:
    st.sidebar.subheader("📂 Chronicle Archive")
    if st.sidebar.button("🗑️ Clear All History"):
        if clear_history(user["email"]): st.success("History cleared."); st.rerun()
    for idx,h in enumerate(hist_raw[:8]):
        try:
            h["answer"]=Answer(**h["answer"])
            ts=time.strftime("%Y-%m-%d %H:%M",time.localtime(h.get("timestamp",0)))
            disp=h.get("query","")[:40]+"..." if len(h.get("query",""))>40 else h.get("query","")
            if st.sidebar.button(disp, key=f"h{idx}"):
                ss["query"]=h["query"]; ss["last"]=h["answer"]; st.rerun()
            st.sidebar.caption(f"({ts})")
        except: pass
else:
    st.sidebar.info("No history yet.")

if st.sidebar.button("Sign out"):
    try: requests.get("http://localhost:5000/logout",timeout=1)
    except: pass
    ss.clear(); st.rerun()

# ----------------- Footer -----------------
footer_color = "#9fb0c3" if ss["theme"]=="dark" else "#516079"
year = datetime.datetime.now().year
st.markdown(f"<hr><p style='text-align:center; color:{footer_color};'>© {year} CodeXR. Made with ❤️ - Manit Srivastava</p>", unsafe_allow_html=True)
