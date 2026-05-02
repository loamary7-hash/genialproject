"""
Bullwhip Game – Interface Streamlit v2
Design : SaaS Dashboard moderne · ESLI Paris
Logique inchangée — redesign complet UI/UX
"""

import streamlit as st
import requests
import json
import pandas as pd
import plotly.graph_objects as go

# ── Configuration ─────────────────────────────────────────────────────────────
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbz_VmabDh4BVYLVIeHDKBmwcCykXsrM-LIr_hGxWd9Jp36-GGSXggiE59aQe1eIg7XqnQ/exec"
ROLES  = ["Détaillant", "Grossiste", "Distributeur", "Fabricant"]
CHAINS = ["A", "B", "C", "D", "E", "F"]

ROLE_META = {
    "Détaillant":   {"color": "#10B981", "bg": "#ECFDF5", "border": "#6EE7B7", "emoji": "🛒",
                     "desc": "Voit la demande client réelle"},
    "Grossiste":    {"color": "#3B82F6", "bg": "#EFF6FF", "border": "#93C5FD", "emoji": "📦",
                     "desc": "Reçoit les commandes du Détaillant"},
    "Distributeur": {"color": "#8B5CF6", "bg": "#F5F3FF", "border": "#C4B5FD", "emoji": "🏭",
                     "desc": "Deux échelons du client final"},
    "Fabricant":    {"color": "#F59E0B", "bg": "#FFFBEB", "border": "#FCD34D", "emoji": "🔧",
                     "desc": "Ressent le Bullwhip au maximum"},
}

# ── Helpers API ───────────────────────────────────────────────────────────────

def api_get(params: dict) -> dict:
    try:
        r = requests.get(APPS_SCRIPT_URL, params=params, timeout=15)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def api_post(payload: dict) -> dict:
    try:
        qp = {k: payload[k] for k in ("action", "sessionCode", "facilitatorKey") if k in payload}
        r  = requests.post(
            APPS_SCRIPT_URL, params=qp,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=15,
        )
        return r.json()
    except Exception as e:
        return {"error": str(e)}

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Bullwhip Game · ESLI",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Design System CSS ─────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

/* ── Reset & Base ── */
*, *::before, *::after { box-sizing: border-box; }
html, body, .stApp           { font-family: 'DM Sans', sans-serif !important; }
#MainMenu, footer, header    { visibility: hidden; }
.block-container             { padding: 2rem 2.5rem 3rem !important; max-width: 960px !important; margin: 0 auto !important; }
section[data-testid="stSidebar"] { display: none !important; }

/* ── Tokens ── */
:root {
  --c-bg:       #F8FAFC;
  --c-surface:  #FFFFFF;
  --c-border:   #E2E8F0;
  --c-text:     #0F172A;
  --c-muted:    #64748B;
  --c-green:    #10B981;
  --c-green-lt: #ECFDF5;
  --c-amber:    #F59E0B;
  --c-amber-lt: #FFFBEB;
  --c-red:      #EF4444;
  --c-red-lt:   #FEF2F2;
  --c-blue:     #3B82F6;
  --c-blue-lt:  #EFF6FF;
  --c-navy:     #1E293B;
  --shadow-sm:  0 1px 3px rgba(0,0,0,.08), 0 1px 2px rgba(0,0,0,.05);
  --shadow-md:  0 4px 12px rgba(0,0,0,.08), 0 2px 4px rgba(0,0,0,.05);
  --radius:     10px;
  --radius-sm:  6px;
}

/* ── Streamlit overrides ── */
.stApp { background: var(--c-bg) !important; }

.stButton > button {
  font-family: 'DM Sans', sans-serif !important;
  font-weight: 600 !important;
  font-size: .875rem !important;
  border-radius: var(--radius-sm) !important;
  padding: .5rem 1.25rem !important;
  border: 1.5px solid transparent !important;
  transition: all .18s ease !important;
  cursor: pointer !important;
}
.stButton > button[kind="primary"] {
  background: var(--c-navy) !important;
  color: #fff !important;
  border-color: var(--c-navy) !important;
}
.stButton > button[kind="primary"]:hover {
  background: #0F172A !important;
  box-shadow: 0 4px 14px rgba(30,41,59,.35) !important;
  transform: translateY(-1px) !important;
}
.stButton > button:not([kind="primary"]) {
  background: var(--c-surface) !important;
  color: var(--c-navy) !important;
  border-color: var(--c-border) !important;
}
.stButton > button:not([kind="primary"]):hover {
  border-color: var(--c-navy) !important;
  background: var(--c-bg) !important;
}

.stTextInput > div > div > input,
.stSelectbox > div > div,
.stNumberInput > div > div > input {
  font-family: 'DM Sans', sans-serif !important;
  border-radius: var(--radius-sm) !important;
  border: 1.5px solid var(--c-border) !important;
  font-size: .9rem !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus {
  border-color: var(--c-navy) !important;
  box-shadow: 0 0 0 3px rgba(30,41,59,.1) !important;
}

.stProgress > div > div > div {
  background: var(--c-green) !important;
  border-radius: 99px !important;
}
.stProgress > div > div {
  background: var(--c-border) !important;
  border-radius: 99px !important;
  height: 6px !important;
}

.stAlert { border-radius: var(--radius-sm) !important; font-family: 'DM Sans', sans-serif !important; }
.stDataFrame { border-radius: var(--radius) !important; border: 1px solid var(--c-border) !important; }
hr { border-color: var(--c-border) !important; margin: 1.5rem 0 !important; }

div[data-testid="stExpander"] {
  border: 1px solid var(--c-border) !important;
  border-radius: var(--radius) !important;
  background: var(--c-surface) !important;
}

/* ── Custom components ── */

/* Metric card */
.mcard {
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--radius);
  padding: 1rem 1.2rem 1rem;
  box-shadow: var(--shadow-sm);
  position: relative;
  overflow: hidden;
  height: 100%;
}
.mcard::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 3px;
  border-radius: var(--radius) var(--radius) 0 0;
}
.mcard-green::before  { background: var(--c-green); }
.mcard-amber::before  { background: var(--c-amber); }
.mcard-red::before    { background: var(--c-red); }
.mcard-blue::before   { background: var(--c-blue); }
.mcard-navy::before   { background: var(--c-navy); }

.mcard-label {
  font-size: .72rem;
  font-weight: 600;
  letter-spacing: .07em;
  text-transform: uppercase;
  color: var(--c-muted);
  margin-bottom: .5rem;
  display: flex;
  align-items: center;
  gap: .35rem;
}
.mcard-value {
  font-family: 'DM Mono', monospace;
  font-size: 1.9rem;
  font-weight: 500;
  color: var(--c-text);
  line-height: 1;
}
.mcard-value-green  { color: var(--c-green); }
.mcard-value-amber  { color: var(--c-amber); }
.mcard-value-red    { color: var(--c-red); }
.mcard-sub {
  font-size: .75rem;
  color: var(--c-muted);
  margin-top: .4rem;
}

/* Page header */
.page-header {
  margin-bottom: 1.75rem;
}
.page-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--c-text);
  letter-spacing: -.02em;
  margin: 0;
}
.page-sub {
  font-size: .875rem;
  color: var(--c-muted);
  margin-top: .25rem;
}

/* Section header */
.sect-hdr {
  font-size: .72rem;
  font-weight: 600;
  letter-spacing: .08em;
  text-transform: uppercase;
  color: var(--c-muted);
  margin: 1.5rem 0 .75rem;
  display: flex;
  align-items: center;
  gap: .5rem;
}
.sect-hdr::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--c-border);
}

/* Role badge */
.role-badge {
  display: inline-flex;
  align-items: center;
  gap: .4rem;
  padding: .3rem .75rem;
  border-radius: 99px;
  font-size: .8rem;
  font-weight: 600;
  border: 1.5px solid;
}

/* Chain visualization */
.chain-wrap {
  display: flex;
  align-items: center;
  gap: 0;
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--radius);
  padding: .75rem 1.25rem;
  box-shadow: var(--shadow-sm);
  flex-wrap: wrap;
  gap: .25rem;
}
.chain-node {
  display: flex;
  align-items: center;
  gap: .4rem;
  padding: .4rem .9rem;
  border-radius: var(--radius-sm);
  font-size: .82rem;
  font-weight: 500;
  background: var(--c-bg);
  color: var(--c-muted);
  border: 1px solid var(--c-border);
  white-space: nowrap;
}
.chain-node-active {
  color: #fff;
  border-color: transparent;
  box-shadow: 0 2px 8px rgba(0,0,0,.18);
}
.chain-arrow {
  color: var(--c-border);
  font-size: .9rem;
  padding: 0 .1rem;
  font-weight: 300;
}

/* Order card */
.order-card {
  background: var(--c-surface);
  border: 1.5px solid var(--c-border);
  border-radius: var(--radius);
  padding: 1.25rem 1.5rem;
  box-shadow: var(--shadow-sm);
}
.order-card-title {
  font-size: .9rem;
  font-weight: 600;
  color: var(--c-text);
  margin-bottom: .75rem;
  display: flex;
  align-items: center;
  gap: .5rem;
}
.order-incoming {
  background: var(--c-amber-lt);
  border: 1px solid #FDE68A;
  border-radius: var(--radius-sm);
  padding: .6rem 1rem;
  font-size: .875rem;
  color: #92400E;
  margin-bottom: .75rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.order-incoming strong {
  font-family: 'DM Mono', monospace;
  font-size: 1.1rem;
}
.cost-preview {
  background: var(--c-bg);
  border-radius: var(--radius-sm);
  padding: .6rem .9rem;
  font-size: .8rem;
  color: var(--c-muted);
  margin-top: .5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* Waiting state */
.wait-card {
  background: linear-gradient(135deg, #F0FDF4 0%, #ECFDF5 100%);
  border: 1.5px solid #86EFAC;
  border-radius: var(--radius);
  padding: 1.5rem;
  text-align: center;
}
.wait-title {
  font-size: 1rem;
  font-weight: 600;
  color: #166534;
  margin-bottom: .4rem;
}
.wait-sub {
  font-size: .85rem;
  color: #15803D;
}

/* Home hero cards */
.hero-card {
  background: var(--c-surface);
  border: 1.5px solid var(--c-border);
  border-radius: 14px;
  padding: 2rem;
  box-shadow: var(--shadow-md);
  transition: box-shadow .2s, transform .2s;
  height: 100%;
}
.hero-card:hover {
  box-shadow: 0 8px 24px rgba(0,0,0,.12);
  transform: translateY(-2px);
}
.hero-icon {
  font-size: 2.2rem;
  margin-bottom: .75rem;
}
.hero-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--c-text);
  margin-bottom: .4rem;
}
.hero-desc {
  font-size: .875rem;
  color: var(--c-muted);
  line-height: 1.6;
  margin-bottom: 1.25rem;
}

/* Dashboard player row */
.player-row {
  display: grid;
  grid-template-columns: 100px 130px 1fr 70px 70px 90px 70px;
  gap: .5rem;
  align-items: center;
  padding: .65rem .9rem;
  border-radius: var(--radius-sm);
  font-size: .85rem;
  margin-bottom: .35rem;
  background: var(--c-surface);
  border: 1px solid var(--c-border);
}
.player-row:hover { background: var(--c-bg); }
.player-row-hdr {
  font-size: .7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: .07em;
  color: var(--c-muted);
  padding: .4rem .9rem;
}

/* Results podium */
.podium-card {
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--radius);
  padding: 1rem 1.2rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: var(--shadow-sm);
  margin-bottom: .5rem;
  transition: box-shadow .15s;
}
.podium-card:hover { box-shadow: var(--shadow-md); }
.podium-rank { font-size: 1.3rem; }
.podium-name { font-weight: 600; font-size: .95rem; color: var(--c-text); }
.podium-cost { font-family: 'DM Mono', monospace; font-size: 1rem; color: var(--c-muted); }

/* Insight cards */
.insight-card {
  background: var(--c-surface);
  border-left: 3px solid;
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  padding: .9rem 1.1rem;
  margin-bottom: .6rem;
  box-shadow: var(--shadow-sm);
}
.insight-title {
  font-size: .82rem;
  font-weight: 700;
  margin-bottom: .3rem;
  text-transform: uppercase;
  letter-spacing: .06em;
}
.insight-body {
  font-size: .85rem;
  color: var(--c-muted);
  line-height: 1.6;
}

/* App header bar */
.app-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: .6rem 0 1.2rem;
  border-bottom: 1px solid var(--c-border);
  margin-bottom: 1.5rem;
}
.app-brand {
  font-size: 1rem;
  font-weight: 700;
  color: var(--c-text);
  letter-spacing: -.01em;
  display: flex;
  align-items: center;
  gap: .4rem;
}
.app-brand span { color: var(--c-muted); font-weight: 400; font-size: .85rem; }

/* Week badge */
.week-badge {
  background: var(--c-navy);
  color: #fff;
  font-size: .78rem;
  font-weight: 600;
  padding: .3rem .8rem;
  border-radius: 99px;
  font-family: 'DM Mono', monospace;
}

/* Status dot */
.dot { width:8px; height:8px; border-radius:50%; display:inline-block; margin-right:4px; }
.dot-green  { background: var(--c-green); }
.dot-amber  { background: var(--c-amber); }
.dot-red    { background: var(--c-red); }
.dot-grey   { background: var(--c-muted); }

</style>
""", unsafe_allow_html=True)

# ── State ─────────────────────────────────────────────────────────────────────

def init_state():
    defaults = {
        "page": "home",
        "player_id": None,
        "session_code": "",
        "player_name": "",
        "chain": "A",
        "role": "Détaillant",
        "is_facilitator": False,
        "facilitator_key": "",
        "order_history": [],
        "current_state": {},
        "order_sent": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()
ss = st.session_state

# ── UI Helpers ────────────────────────────────────────────────────────────────

def topbar(right_html=""):
    st.markdown(f"""
    <div class="app-topbar">
      <div class="app-brand">📦 Bullwhip Game <span>· ESLI Paris</span></div>
      <div>{right_html}</div>
    </div>""", unsafe_allow_html=True)

def sect(label, icon=""):
    st.markdown(f'<div class="sect-hdr">{icon + " " if icon else ""}{label}</div>', unsafe_allow_html=True)

def mcard(label, value, icon="", variant="navy", sub=""):
    val_class = f"mcard-value-{variant}" if variant in ("green","amber","red") else "mcard-value"
    sub_html  = f'<div class="mcard-sub">{sub}</div>' if sub else ""
    st.markdown(f"""
    <div class="mcard mcard-{variant}">
      <div class="mcard-label">{icon} {label}</div>
      <div class="{val_class}">{value}</div>
      {sub_html}
    </div>""", unsafe_allow_html=True)

def role_badge(role: str):
    m = ROLE_META.get(role, {})
    color  = m.get("color", "#666")
    bg     = m.get("bg", "#f5f5f5")
    border = m.get("border", "#ddd")
    emoji  = m.get("emoji", "")
    return (f'<span class="role-badge" style="background:{bg};color:{color};'
            f'border-color:{border}">{emoji} {role}</span>')

def chain_vis(active_role: str):
    all_nodes = [("👤", "Client", None)] + [(ROLE_META[r]["emoji"], r, r) for r in ROLES]
    html = '<div class="chain-wrap">'
    for i, (emoji, label, key) in enumerate(all_nodes):
        if i > 0:
            html += '<span class="chain-arrow">›</span>'
        if key == active_role:
            m = ROLE_META[key]
            html += (f'<div class="chain-node chain-node-active" '
                     f'style="background:{m["color"]}">{emoji} {label}</div>')
        else:
            html += f'<div class="chain-node">{emoji} {label}</div>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

def plotly_styled(fig, height=300):
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans, sans-serif", color="#64748B", size=12),
        margin=dict(l=0, r=0, t=16, b=0),
        xaxis=dict(showgrid=False, showline=False, tickfont=dict(size=11)),
        yaxis=dict(gridcolor="#F1F5F9", showline=False, tickfont=dict(size=11)),
        legend=dict(
            orientation="h", y=-0.25,
            font=dict(size=11), bgcolor="rgba(0,0,0,0)"
        ),
    )
    st.plotly_chart(fig, width="stretch")

# ── PAGE : Accueil ────────────────────────────────────────────────────────────

def page_home():
    topbar()
    st.markdown("""
    <div style="text-align:center; padding: 1rem 0 2rem;">
      <div style="font-size:3rem; margin-bottom:.5rem;">🌊</div>
      <div style="font-size:2rem; font-weight:800; color:#0F172A; letter-spacing:-.03em;">
        Bullwhip Game
      </div>
      <div style="font-size:1rem; color:#64748B; margin-top:.4rem;">
        Simulation pédagogique de la chaîne logistique · ESLI Paris
      </div>
    </div>""", unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown("""
        <div class="hero-card">
          <div class="hero-icon">🎓</div>
          <div class="hero-title">Je suis étudiant</div>
          <div class="hero-desc">Rejoins une session, choisis ton rôle dans la chaîne
          et joue en temps réel avec ton groupe.</div>
        </div>""", unsafe_allow_html=True)
        st.write("")
        if st.button("Rejoindre une session →", use_container_width=True, type="primary", key="btn_join"):
            ss["page"] = "join"; st.rerun()

    with col2:
        st.markdown("""
        <div class="hero-card">
          <div class="hero-icon">🎛️</div>
          <div class="hero-title">Je suis facilitateur</div>
          <div class="hero-desc">Crée une session, pilote la progression des équipes
          et visualise l'effet Bullwhip en direct.</div>
        </div>""", unsafe_allow_html=True)
        st.write("")
        if st.button("Espace facilitateur →", use_container_width=True, key="btn_fac"):
            ss["page"] = "facilitator_login"; st.rerun()

    st.write("")
    with st.expander("📖 Comment fonctionne ce jeu ?"):
        c1, c2 = st.columns(2, gap="large")
        with c1:
            st.markdown("""
**L'effet Bullwhip** est un phénomène clé en supply chain : de petites fluctuations
de la demande réelle créent des oscillations de plus en plus amplifiées en remontant
la chaîne, du Détaillant jusqu'au Fabricant.

**Ton rôle** : chaque semaine, tu reçois une commande de ton client aval et tu décides
combien commander à ton fournisseur amont. Ton seul objectif : **minimiser tes coûts**.
            """)
        with c2:
            st.markdown("""
**Structure des coûts :**
- 📦 **Stock excédentaire** : 0,15 €/unité/semaine
- ❌ **Rupture (backlog)** : 0,50 €/unité/semaine

**Durée** : 20 semaines simulées · ~45 minutes en salle

**Après la partie** : comparaison des indices Bullwhip par échelon,
discussion des causes et des solutions réelles (VMI, EDI, CPFR…).
            """)

# ── PAGE : Rejoindre ──────────────────────────────────────────────────────────

def page_join():
    topbar()
    if st.button("← Retour", key="back_join"):
        ss["page"] = "home"; st.rerun()

    st.markdown("""
    <div class="page-header" style="margin-top:.5rem">
      <div class="page-title">Rejoindre une session</div>
      <div class="page-sub">Entre le code donné par ton facilitateur et choisis ton rôle.</div>
    </div>""", unsafe_allow_html=True)

    col_form, col_info = st.columns([1.1, 1], gap="large")

    with col_form:
        with st.form("join_form"):
            code  = st.text_input("🔑 Code session", value="BW-2025",
                                   placeholder="ex. BW-2025")
            name  = st.text_input("👤 Ton prénom", placeholder="ex. Amary")
            chain = st.selectbox("⛓️ Chaîne", CHAINS[:6])
            role  = st.selectbox("🎯 Rôle", ROLES)
            st.write("")
            submitted = st.form_submit_button(
                "Rejoindre la session →", use_container_width=True, type="primary"
            )

    with col_info:
        sect("Détail des rôles", "📋")
        for r, m in ROLE_META.items():
            st.markdown(f"""
            <div style="background:{m['bg']};border:1px solid {m['border']};
                 border-radius:8px;padding:.7rem 1rem;margin-bottom:.5rem;">
              <div style="font-weight:600;color:{m['color']};font-size:.85rem;margin-bottom:.2rem;">
                {m['emoji']} {r}</div>
              <div style="font-size:.8rem;color:#64748B;">{m['desc']}</div>
            </div>""", unsafe_allow_html=True)

    if submitted:
        if not name.strip():
            st.error("⚠️ Entre ton prénom pour continuer.")
            return
        with st.spinner("Connexion à la session..."):
            resp = api_post({
                "action": "joinSession",
                "sessionCode": code.strip().upper(),
                "playerName":  name.strip(),
                "chain": chain, "role": role,
            })
        if "error" in resp:
            st.error(f"❌ {resp['error']}")
        else:
            ss.update({
                "player_id": resp["playerId"],
                "session_code": code.strip().upper(),
                "player_name": name.strip(),
                "chain": chain, "role": role,
                "page": "play", "order_sent": False,
            })
            st.rerun()

# ── PAGE : Jeu ────────────────────────────────────────────────────────────────

def page_play():
    state = api_get({
        "action": "getState",
        "playerId": ss["player_id"],
        "sessionCode": ss["session_code"],
    })
    if "error" in state:
        st.error(f"❌ Erreur serveur : {state['error']}"); return

    ss["current_state"] = state
    week        = state.get("currentWeek", 1)
    total       = state.get("totalWeeks", 20)
    game_status = state.get("gameStatus", "playing")
    role        = ss["role"]
    m           = ROLE_META.get(role, {})

    if game_status == "finished":
        ss["page"] = "results"; st.rerun()

    # Top bar
    week_badge = f'<span class="week-badge">S{week}/{total}</span>'
    topbar(right_html=f'{role_badge(role)}&nbsp;&nbsp;{week_badge}')

    # Progress bar
    pct = int(week / max(total, 1) * 100)
    st.markdown(f"""
    <div style="margin-bottom:1.5rem;">
      <div style="display:flex;justify-content:space-between;
           font-size:.75rem;color:#94A3B8;margin-bottom:.35rem;">
        <span>Progression</span>
        <span>{pct}% · {total - week} semaines restantes</span>
      </div>
      <div style="background:#E2E8F0;border-radius:99px;height:6px;">
        <div style="background:{m.get('color','#10B981')};width:{pct}%;
             height:6px;border-radius:99px;transition:width .4s;"></div>
      </div>
    </div>""", unsafe_allow_html=True)

    # Métriques
    stock   = state.get("stock", 0)
    backlog = state.get("backlog", 0)
    deliv   = state.get("pendingDelivery", 0)
    cost    = state.get("totalCost", 0.0)

    sect("Votre état actuel", "📊")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        v = "green" if stock >= 8 else "amber" if stock > 0 else "red"
        mcard("Stock", f"{stock} u", "📦", v, "unités disponibles")
    with c2:
        v = "green" if backlog == 0 else "amber" if backlog <= 3 else "red"
        mcard("Backlog", f"{backlog} u", "⚠️", v, "commandes en retard")
    with c3:
        mcard("Livraison prévue", f"{deliv} u", "🚚", "blue", "semaine prochaine")
    with c4:
        mcard("Coût cumulé", f"{cost:.2f}€", "💰", "navy", "depuis le début")

    st.write("")

    # Bloc commande ou attente
    if not ss["order_sent"]:
        sect("Décision de commande", "📋")
        hist = ss["order_history"]
        last_incoming = hist[-1]["incoming"] if hist else 4

        col_order, col_tip = st.columns([1.3, 1], gap="large")

        with col_order:
            upstream = ROLES[ROLES.index(role) + 1] if ROLES.index(role) < 3 else "Production"
            st.markdown(f"""
            <div class="order-card">
              <div class="order-card-title">📤 Commander à → {ROLE_META.get(upstream, {}).get('emoji','')}{upstream}</div>
              <div class="order-incoming">
                <span>Commande reçue ce tour :</span>
                <strong>{last_incoming} unités</strong>
              </div>
            </div>""", unsafe_allow_html=True)

            order_qty = st.number_input(
                "Quantité à commander", min_value=0, max_value=200,
                value=int(last_incoming), step=1, key=f"order_w{week}",
                label_visibility="visible"
            )

            proj_stock   = max(0, stock + deliv - last_incoming)
            proj_backlog = max(0, last_incoming - stock - deliv)
            est_cost     = proj_stock * 0.15 + proj_backlog * 0.50
            st.markdown(f"""
            <div class="cost-preview">
              <span>📦 Stock : <b>{proj_stock * 0.15:.2f} €</b> &nbsp;|&nbsp;
                    ⚠️ Rupture : <b>{proj_backlog * 0.50:.2f} €</b></span>
              <span style="font-weight:700;color:#0F172A;">Total : {est_cost:.2f} €</span>
            </div>""", unsafe_allow_html=True)
            st.write("")

            if st.button("✅ Valider ma commande", use_container_width=True, type="primary", key="validate"):
                with st.spinner("Envoi en cours..."):
                    resp = api_post({
                        "action": "submitOrder",
                        "sessionCode": ss["session_code"],
                        "playerId": ss["player_id"],
                        "orderQty": int(order_qty),
                    })
                if "error" in resp:
                    st.error(f"❌ {resp['error']}")
                else:
                    ss["order_history"].append({
                        "week":     resp.get("week", week),
                        "incoming": resp.get("incomingDemand", last_incoming),
                        "order":    resp.get("orderPlaced", order_qty),
                        "stock":    resp.get("newStock", stock),
                        "backlog":  resp.get("newBacklog", backlog),
                        "cost":     resp.get("weekCost", 0.0),
                    })
                    ss["order_sent"] = True
                    st.rerun()

        with col_tip:
            sect("Rappel des coûts", "💡")
            st.markdown(f"""
            <div style="background:#FFFBEB;border:1px solid #FDE68A;border-radius:8px;
                 padding:.9rem 1rem;margin-bottom:.6rem;">
              <div style="font-size:.78rem;font-weight:600;color:#92400E;margin-bottom:.3rem;">
                📦 STOCK EXCÉDENTAIRE</div>
              <div style="font-family:'DM Mono',monospace;font-size:1.1rem;color:#B45309;font-weight:500;">
                0,15 €/u/sem</div>
            </div>
            <div style="background:#FEF2F2;border:1px solid #FECACA;border-radius:8px;
                 padding:.9rem 1rem;">
              <div style="font-size:.78rem;font-weight:600;color:#991B1B;margin-bottom:.3rem;">
                ⚠️ RUPTURE (BACKLOG)</div>
              <div style="font-family:'DM Mono',monospace;font-size:1.1rem;color:#DC2626;font-weight:500;">
                0,50 €/u/sem</div>
            </div>""", unsafe_allow_html=True)

            if stock == 0 and backlog > 0:
                st.markdown("""
                <div style="background:#FEF2F2;border-left:3px solid #EF4444;border-radius:0 8px 8px 0;
                     padding:.7rem .9rem;margin-top:.75rem;font-size:.82rem;color:#991B1B;">
                  🔴 <b>Rupture de stock !</b> Tu paies 0,50€ par unité non livrée.
                  Pense à commander davantage pour les semaines suivantes.
                </div>""", unsafe_allow_html=True)
            elif stock > 15:
                st.markdown("""
                <div style="background:#FFFBEB;border-left:3px solid #F59E0B;border-radius:0 8px 8px 0;
                     padding:.7rem .9rem;margin-top:.75rem;font-size:.82rem;color:#92400E;">
                  🟡 <b>Stock élevé.</b> Tu paies 0,15€ par unité stockée.
                  Adapte ta commande à la demande réelle.
                </div>""", unsafe_allow_html=True)

    else:
        st.markdown("""
        <div class="wait-card">
          <div style="font-size:2rem;margin-bottom:.5rem;">⏳</div>
          <div class="wait-title">Commande envoyée avec succès !</div>
          <div class="wait-sub">En attente des autres joueurs et du facilitateur<br>
          pour passer à la semaine suivante.</div>
        </div>""", unsafe_allow_html=True)
        st.write("")
        if st.button("🔄 Rafraîchir le statut", use_container_width=True, key="refresh"):
            ss["order_sent"] = False; st.rerun()

    # Historique graphique
    if ss["order_history"]:
        st.write("")
        sect("Historique de vos commandes", "📈")
        df  = pd.DataFrame(ss["order_history"])
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df["week"], y=df["incoming"], name="Demande reçue",
            marker_color="#CBD5E1", opacity=.9, marker_line_width=0,
        ))
        fig.add_trace(go.Scatter(
            x=df["week"], y=df["order"], name="Vos commandes",
            mode="lines+markers",
            line=dict(color=m.get("color", "#10B981"), width=2.5),
            marker=dict(size=7, color=m.get("color", "#10B981"),
                        line=dict(color="#fff", width=2)),
        ))
        fig.update_layout(
            xaxis_title="Semaine", yaxis_title="Unités",
            legend=dict(orientation="h", y=-0.3),
            bargap=.35,
        )
        plotly_styled(fig, 250)

    # Chaîne visuelle
    st.write("")
    sect("Position dans la chaîne", "⛓️")
    chain_vis(role)

# ── PAGE : Facilitateur login ──────────────────────────────────────────────────

def page_facilitator_login():
    topbar()
    if st.button("← Retour", key="back_fac"):
        ss["page"] = "home"; st.rerun()

    st.markdown("""
    <div class="page-header">
      <div class="page-title">Espace Facilitateur</div>
      <div class="page-sub">Accède à une session existante ou crée-en une nouvelle.</div>
    </div>""", unsafe_allow_html=True)

    col_login, col_create = st.columns(2, gap="large")

    with col_login:
        sect("Accéder à une session", "🔐")
        with st.form("fac_form"):
            code = st.text_input("Code session", value="BW-2025")
            key  = st.text_input("Clé facilitateur", type="password", placeholder="ex. 1234")
            if st.form_submit_button("Accéder au dashboard →", type="primary", use_container_width=True):
                if code.strip() and key.strip():
                    ss.update({
                        "session_code": code.strip().upper(),
                        "facilitator_key": key.strip(),
                        "is_facilitator": True,
                        "page": "facilitator",
                    })
                    st.rerun()
                else:
                    st.error("Remplis les deux champs.")

    with col_create:
        sect("Créer une session", "✨")
        with st.form("create_form"):
            new_code  = st.text_input("Code session", placeholder="ex. BW-2025")
            new_key   = st.text_input("Clé facilitateur", placeholder="ex. 1234")
            nb_chains = st.slider("Nombre de chaînes", 1, 8, 5)
            if st.form_submit_button("Créer la session →", use_container_width=True):
                if new_code.strip() and new_key.strip():
                    resp = api_post({
                        "action": "createSession",
                        "sessionCode": new_code.strip().upper(),
                        "facilitatorKey": new_key.strip(),
                        "nbChains": nb_chains,
                    })
                    if "error" in resp:
                        st.error(f"❌ {resp['error']}")
                    else:
                        st.success(f"✅ Session **{new_code.upper()}** créée ! Partage ce code aux étudiants.")
                else:
                    st.error("Remplis tous les champs.")

# ── PAGE : Facilitateur dashboard ─────────────────────────────────────────────

def page_facilitator():
    # Garde clé
    if not ss.get("facilitator_key", "").strip():
        topbar()
        st.warning("⚠️ Clé facilitateur manquante — ressaisis-la pour continuer.")
        with st.form("reenter_key"):
            rekey = st.text_input("Clé facilitateur", type="password")
            if st.form_submit_button("Confirmer", type="primary"):
                if rekey.strip():
                    ss["facilitator_key"] = rekey.strip(); st.rerun()
                else:
                    st.error("La clé ne peut pas être vide.")
        return

    masked = ss["facilitator_key"][:2] + "••••"
    topbar(right_html=f'<span style="font-size:.78rem;color:#64748B">🔑 {masked} · {ss["session_code"]}</span>')

    data = api_get({"action": "getFacDashboard", "sessionCode": ss["session_code"]})
    if "error" in data:
        st.error(f"❌ {data['error']}"); return

    week      = data.get("currentWeek", 1)
    status    = data.get("status", "waiting")
    n_players = data.get("totalPlayers", 0)
    n_played  = data.get("playedThisRound", 0)
    bwi       = data.get("bullwhipIndex", {})

    # KPIs
    sect("Tableau de bord", "📊")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        mcard("Semaine", f"{week}/20", "📅", "navy")
    with c2:
        mcard("Joueurs", str(n_players), "👥", "blue")
    with c3:
        v = "green" if n_played == n_players else "amber"
        mcard("Ont joué", f"{n_played}/{n_players}", "✅", v)
    with c4:
        status_icons = {"waiting":"🟡","playing":"🟢","finished":"🔵"}
        mcard("Statut", status.capitalize(), status_icons.get(status,"⚪"), "navy")

    pct = int(n_played / max(n_players, 1) * 100)
    st.markdown(f"""
    <div style="margin:.75rem 0 1.5rem;">
      <div style="display:flex;justify-content:space-between;
           font-size:.75rem;color:#94A3B8;margin-bottom:.3rem;">
        <span>Soumissions ce tour</span><span>{pct}%</span>
      </div>
      <div style="background:#E2E8F0;border-radius:99px;height:6px;">
        <div style="background:{'#10B981' if pct==100 else '#F59E0B'};
             width:{pct}%;height:6px;border-radius:99px;"></div>
      </div>
    </div>""", unsafe_allow_html=True)

    # Tableau joueurs
    players = data.get("players", [])
    if players:
        sect("Joueurs connectés", "👥")
        records = []
        for p in players:
            if isinstance(p, dict):
                records.append({
                    "Chaîne": p.get("chain","—"), "Rôle": p.get("role","—"),
                    "Joueur": p.get("name","—"), "Stock": p.get("stock",0),
                    "Backlog": p.get("backlog",0), "Coût €": p.get("cost",p.get("totalCost",0.0)),
                })

        if records:
            df = pd.DataFrame(records).sort_values(["Chaîne","Rôle"])
            def add_bwi(row):
                v = bwi.get(f"{row['Chaîne']}-{row['Rôle']}")
                return f"{v:.2f}" if v else "—"
            df["BWI"] = df.apply(add_bwi, axis=1)
            st.dataframe(df, use_container_width=True, hide_index=True,
                         column_config={"Coût €": st.column_config.NumberColumn(format="%.2f €")})

    st.write("")
    col_adv, col_res, col_rst, col_ref = st.columns(4)

    with col_adv:
        if status != "finished":
            if st.button("▶ Semaine suivante", use_container_width=True, type="primary", key="advance"):
                resp = api_post({
                    "action": "advanceWeek",
                    "sessionCode": ss["session_code"],
                    "facilitatorKey": ss["facilitator_key"],
                })
                if "error" in resp:
                    err = resp["error"]
                    if any(w in err.lower() for w in ["clé","key","invalid"]):
                        st.error(f"❌ {err}")
                        if st.button("🔑 Réinitialiser la clé", key="reset_key"):
                            ss["facilitator_key"] = ""; st.rerun()
                    else:
                        st.error(err)
                else:
                    st.success(f"✅ Semaine {resp.get('newWeek','?')} démarrée !")
                    st.rerun()

    with col_res:
        if st.button("📊 Résultats", use_container_width=True, key="see_results"):
            ss["page"] = "results"; st.rerun()

    with col_rst:
        if st.button("🔄 Réinitialiser", use_container_width=True, key="reset_session"):
            resp = api_post({
                "action": "resetSession",
                "sessionCode": ss["session_code"],
                "facilitatorKey": ss["facilitator_key"],
            })
            if "error" in resp: st.error(resp["error"])
            else: st.success("Session réinitialisée."); st.rerun()

    with col_ref:
        if st.button("🔄 Rafraîchir", use_container_width=True, key="refresh_fac"):
            st.rerun()

# ── PAGE : Résultats ──────────────────────────────────────────────────────────

def page_results():
    topbar()
    st.markdown(f"""
    <div class="page-header">
      <div class="page-title">🏆 Résultats finaux</div>
      <div class="page-sub">Session {ss['session_code']} · Analyse de l'effet Bullwhip</div>
    </div>""", unsafe_allow_html=True)

    data = api_get({"action": "getResults", "sessionCode": ss["session_code"]})
    if "error" in data:
        st.error(f"❌ {data['error']}"); return

    bwi         = data.get("bullwhipIndex", {})
    chain_costs = data.get("chainCosts", {})
    players     = data.get("players", [])

    # ── Graphique BWI ──────────────────────────────────────────
    sect("Indice Bullwhip par échelon", "🌊")

    bwi_by_role: dict = {}
    for key, val in bwi.items():
        if "-" not in key or val is None: continue
        _, role = key.split("-", 1)
        if role not in bwi_by_role: bwi_by_role[role] = []
        try: bwi_by_role[role].append(float(val))
        except: pass

    roles_ordered = [r for r in ROLES if r in bwi_by_role and bwi_by_role[r]]
    avg_bwi = [sum(bwi_by_role[r]) / len(bwi_by_role[r])
               for r in roles_ordered if bwi_by_role[r]]

    if roles_ordered and avg_bwi:
        col_chart, col_legend = st.columns([2, 1], gap="large")
        with col_chart:
            colors = [ROLE_META.get(r, {}).get("color", "#888") for r in roles_ordered]
            fig = go.Figure(go.Bar(
                x=roles_ordered, y=avg_bwi,
                marker_color=colors,
                marker_line_width=0,
                text=[f"<b>{v:.2f}</b>" for v in avg_bwi],
                textposition="outside",
                textfont=dict(size=13),
            ))
            fig.add_hline(y=1, line_dash="dot", line_color="#94A3B8", line_width=1.5,
                          annotation_text="BWI = 1 · pas d'amplification",
                          annotation_font=dict(size=10, color="#94A3B8"))
            fig.update_layout(yaxis_title="Indice Bullwhip (BWI)", bargap=.4)
            plotly_styled(fig, 280)

        with col_legend:
            st.write("")
            for r, v in zip(roles_ordered, avg_bwi):
                m    = ROLE_META.get(r, {})
                sev  = "🟢" if v < 1.2 else "🟡" if v < 2 else "🔴"
                st.markdown(f"""
                <div style="background:{m.get('bg','#f5f5f5')};border:1px solid {m.get('border','#ddd')};
                     border-radius:8px;padding:.7rem 1rem;margin-bottom:.5rem;">
                  <div style="font-size:.78rem;font-weight:700;color:{m.get('color','#666')};margin-bottom:.2rem;">
                    {m.get('emoji','')} {r}</div>
                  <div style="font-family:'DM Mono',monospace;font-size:1.2rem;font-weight:500;color:{m.get('color','#666')};">
                    {sev} {v:.2f}x</div>
                </div>""", unsafe_allow_html=True)
    else:
        st.info("Les indices Bullwhip seront disponibles après au moins 3 semaines jouées.")

    # ── Classement chaînes ─────────────────────────────────────
    if chain_costs:
        sect("Classement des chaînes", "🏅")
        sorted_chains = sorted(chain_costs.items(), key=lambda x: x[1])
        medals = ["🥇","🥈","🥉"]
        col_pod, _ = st.columns([1.5, 1])
        with col_pod:
            for i, (chain, cost) in enumerate(sorted_chains):
                rank = medals[i] if i < 3 else f"#{i+1}"
                st.markdown(f"""
                <div class="podium-card">
                  <div style="display:flex;align-items:center;gap:.75rem">
                    <span class="podium-rank">{rank}</span>
                    <div>
                      <div class="podium-name">Chaîne {chain}</div>
                      <div style="font-size:.75rem;color:#94A3B8;">coût total de la chaîne</div>
                    </div>
                  </div>
                  <span class="podium-cost">{cost:.2f} €</span>
                </div>""", unsafe_allow_html=True)

    # ── Tableau joueurs ────────────────────────────────────────
    if players:
        sect("Détail par joueur", "👥")
        records = []
        for p in players:
            if isinstance(p, dict):
                records.append({"Chaîne": p.get("chain","—"), "Rôle": p.get("role","—"),
                                 "Joueur": p.get("name","—"), "Coût total (€)": p.get("totalCost",0.0)})
            elif isinstance(p, (list, tuple)) and len(p) >= 4:
                records.append({"Chaîne": p[0], "Rôle": p[1], "Joueur": p[2], "Coût total (€)": p[3]})
        if records:
            df = pd.DataFrame(records).sort_values("Coût total (€)")
            st.dataframe(df, use_container_width=True, hide_index=True,
                         column_config={"Coût total (€)": st.column_config.NumberColumn(format="%.2f €")})

    # ── Enseignements ──────────────────────────────────────────
    sect("Enseignements pédagogiques", "🎓")
    insights = [
        ("#EFF6FF", "#3B82F6", "🔍 Manque de visibilité",
         "Chaque maillon ne voit que la demande de son voisin direct, jamais la demande "
         "client réelle. L'information se déforme à chaque transmission."),
        ("#FFFBEB", "#F59E0B", "📦 Surcommande par précaution",
         "Face à l'incertitude, chaque acteur commande plus que nécessaire pour se "
         "prémunir contre les ruptures — ce qui amplifie le signal en amont."),
        ("#F5F3FF", "#8B5CF6", "⏱️ Délais de livraison",
         "Plus le lead time est long, plus l'incertitude est grande, plus on surcommande. "
         "Réduire les délais réduit mécaniquement le Bullwhip."),
        ("#ECFDF5", "#10B981", "✅ Solutions réelles",
         "VMI (Vendor Managed Inventory), partage d'information EDI en temps réel, "
         "CPFR (Collaborative Planning), flux tirés Kanban/JIT."),
    ]
    col_i1, col_i2 = st.columns(2, gap="large")
    for i, (bg, border, title, body) in enumerate(insights):
        col = col_i1 if i % 2 == 0 else col_i2
        with col:
            st.markdown(f"""
            <div class="insight-card" style="border-left-color:{border};background:{bg};">
              <div class="insight-title" style="color:{border};">{title}</div>
              <div class="insight-body">{body}</div>
            </div>""", unsafe_allow_html=True)

    st.write("")
    if st.button("← Retour à l'accueil", key="back_home"):
        for k in ["player_id", "page", "order_history", "order_sent", "current_state"]:
            st.session_state.pop(k, None)
        ss["page"] = "home"; st.rerun()

# ── Router ────────────────────────────────────────────────────────────────────

page = ss.get("page", "home")
if   page == "home":              page_home()
elif page == "join":              page_join()
elif page == "play":              page_play()
elif page == "facilitator_login": page_facilitator_login()
elif page == "facilitator":       page_facilitator()
elif page == "results":           page_results()
else:
    ss["page"] = "home"; st.rerun()
