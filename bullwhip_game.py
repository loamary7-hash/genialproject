"""
Bullwhip Game – Interface Streamlit
Design : Light Clean · Outfit · ESLI Paris
"""

import streamlit as st
from game_engine import PedagogyEngine, CALENDAR_EVENTS, LEAD_TIMES
import requests
import json
import pandas as pd
import plotly.graph_objects as go

# ── Config ────────────────────────────────────────────────────────────────────
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbz_VmabDh4BVYLVIeHDKBmwcCykXsrM-LIr_hGxWd9Jp36-GGSXggiE59aQe1eIg7XqnQ/exec"
ROLES  = ["Détaillant", "Grossiste", "Distributeur", "Fabricant"]
CHAINS = ["A", "B", "C", "D", "E", "F"]

ROLE_META = {
    "Détaillant":   {"dot":"#10B981","bg":"#ECFDF5","border":"#6EE7B7","dk":"#065F46","light":"#F0FDF4","emoji":"🛒","hint":"Tu vois la demande client réelle — le moins exposé au Bullwhip.","alert":"green"},
    "Grossiste":    {"dot":"#3B82F6","bg":"#EFF6FF","border":"#93C5FD","dk":"#1E40AF","light":"#F0F7FF","emoji":"📦","hint":"Reçois les commandes du Détaillant uniquement — un échelon de distance.","alert":"blue"},
    "Distributeur": {"dot":"#8B5CF6","bg":"#F5F3FF","border":"#C4B5FD","dk":"#4C1D95","light":"#F8F5FF","emoji":"🏭","hint":"Deux échelons du client — la variabilité s'amplifie déjà.","alert":"amber"},
    "Fabricant":    {"dot":"#F59E0B","bg":"#FFFBEB","border":"#FCD34D","dk":"#78350F","light":"#FFFDF0","emoji":"🔧","hint":"Ressens le Bullwhip au maximum — sois prudent dans tes commandes !","alert":"red"},
}

# ── API ───────────────────────────────────────────────────────────────────────
def api_get(params: dict) -> dict:
    try:
        r = requests.get(APPS_SCRIPT_URL, params=params, timeout=15)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def api_post(payload: dict) -> dict:
    try:
        qp = {k: payload[k] for k in ("action","sessionCode","facilitatorKey") if k in payload}
        r  = requests.post(APPS_SCRIPT_URL, params=qp,
                           data=json.dumps(payload),
                           headers={"Content-Type":"application/json"}, timeout=15)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

# ── Page setup ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Bullwhip Game · ESLI",
    page_icon="📦", layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

*, *::before, *::after { box-sizing: border-box; }
html, body, .stApp { font-family: 'Outfit', sans-serif !important; background: #F0F4F8 !important; color: #1E293B !important; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 2.5rem 4rem !important; max-width: 960px !important; margin: 0 auto !important; }
section[data-testid="stSidebar"] { display: none !important; }

/* ── Streamlit overrides ── */
.stButton > button {
  font-family: 'Outfit', sans-serif !important;
  font-weight: 700 !important; font-size: .875rem !important;
  border-radius: 10px !important; padding: .6rem 1.4rem !important;
  border: 1.5px solid !important; transition: all .15s ease !important;
}
.stButton > button[kind="primary"] {
  background: #10B981 !important; color: #fff !important; border-color: #10B981 !important;
}
.stButton > button[kind="primary"]:hover {
  background: #059669 !important; border-color: #059669 !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 14px rgba(16,185,129,.3) !important;
}
.stButton > button:not([kind="primary"]) {
  background: #fff !important; color: #334155 !important; border-color: #E2E8F0 !important;
}
.stButton > button:not([kind="primary"]):hover {
  border-color: #94A3B8 !important; background: #F8FAFC !important;
}
.stTextInput > div > div > input,
.stSelectbox > div > div,
.stNumberInput > div > div > input {
  font-family: 'Outfit', sans-serif !important;
  border-radius: 10px !important; border: 1.5px solid #E2E8F0 !important;
  font-size: .875rem !important; background: #fff !important; color: #1E293B !important;
}
.stTextInput > div > div > input:focus, .stNumberInput > div > div > input:focus {
  border-color: #10B981 !important; box-shadow: 0 0 0 3px rgba(16,185,129,.12) !important;
}
.stProgress > div > div { background: #E2E8F0 !important; border-radius: 99px !important; height: 8px !important; }
.stProgress > div > div > div { border-radius: 99px !important; background: #10B981 !important; }
div[data-testid="stExpander"] { border: 1.5px solid #E2E8F0 !important; border-radius: 12px !important; background: #fff !important; }
.stAlert { border-radius: 10px !important; font-family: 'Outfit', sans-serif !important; }
hr { border-color: #E2E8F0 !important; margin: 1.25rem 0 !important; }

/* ── Topbar ── */
.topbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 0 20px; border-bottom: 2px solid #E2E8F0; margin-bottom: 24px;
}
.brand { font-size: 15px; font-weight: 800; color: #0F172A; letter-spacing: -.02em; display:flex; align-items:center; gap:7px; }
.brand-sub { color: #94A3B8; font-weight: 400; font-size: 13px; }

/* ── Section header ── */
.sh {
  font-size: 11px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase;
  color: #94A3B8; margin: 22px 0 12px; display: flex; align-items: center; gap: 8px;
}
.sh::after { content: ''; flex: 1; height: 1.5px; background: #E2E8F0; }

/* ── Card ── */
.card {
  background: #fff; border: 1.5px solid #E2E8F0; border-radius: 14px;
  padding: 20px 22px; box-shadow: 0 1px 4px rgba(0,0,0,.04);
}

/* ── Metric cards ── */
.mcg { display: grid; grid-template-columns: repeat(4,1fr); gap: 11px; margin-bottom: 20px; }
.mc {
  background: #fff; border: 1.5px solid #E2E8F0; border-radius: 13px;
  padding: 16px 18px; box-shadow: 0 1px 4px rgba(0,0,0,.04); position: relative;
}
.mc-dot { width: 9px; height: 9px; border-radius: 50%; margin-bottom: 10px; }
.mc-label { font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: .08em; color: #94A3B8; margin-bottom: 7px; }
.mc-value { font-family: 'JetBrains Mono', monospace; font-size: 26px; font-weight: 700; color: #1E293B; line-height: 1; }
.mc-sub { font-size: 10px; color: #CBD5E1; margin-top: 5px; }

/* ── Progress ── */
.pb-wrap { margin: 4px 0 20px; }
.pb-top { display: flex; justify-content: space-between; font-size: 11px; color: #94A3B8; margin-bottom: 5px; font-weight: 500; }
.pb-track { height: 8px; background: #E2E8F0; border-radius: 99px; overflow: hidden; }
.pb-fill { height: 8px; border-radius: 99px; transition: width .4s; }

/* ── Role badge ── */
.rb { display: inline-flex; align-items: center; gap: 5px; padding: 4px 12px; border-radius: 99px; font-size: 12px; font-weight: 700; border: 1.5px solid; }
.wb { background: #1E293B; color: #fff; font-size: 11px; font-weight: 700; padding: 4px 11px; border-radius: 7px; font-family: 'JetBrains Mono', monospace; }

/* ── Chain visual ── */
.chain { display: flex; align-items: center; gap: 5px; flex-wrap: wrap; background: #F8FAFC; border: 1.5px solid #E2E8F0; border-radius: 11px; padding: 10px 14px; }
.cn { padding: 5px 11px; border-radius: 7px; font-size: 11px; font-weight: 600; background: #fff; color: #94A3B8; border: 1.5px solid #E2E8F0; white-space: nowrap; }
.cn-active { color: #fff !important; border-color: transparent; }
.ca { color: #CBD5E1; font-size: 11px; }

/* ── Order panel ── */
.order-panel { background: #F8FAFC; border: 1.5px solid #E2E8F0; border-radius: 13px; padding: 18px 20px; }
.inc-box { background: #FFFBEB; border: 1.5px solid #FCD34D; border-radius: 9px; padding: 10px 14px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 13px; }
.inc-label { font-size: 11px; color: #92400E; font-weight: 600; }
.inc-val { font-family: 'JetBrains Mono', monospace; font-size: 18px; font-weight: 700; color: #B45309; }
.cost-row { background: #fff; border: 1.5px solid #E2E8F0; border-radius: 9px; padding: 9px 13px; display: flex; justify-content: space-between; font-size: 11px; color: #94A3B8; margin-top: 9px; }

/* ── Alert tips ── */
.alt { border-radius: 0 9px 9px 0; padding: 10px 14px; font-size: 12px; margin-top: 11px; line-height: 1.65; border-left: 3px solid; }
.alt-green  { background: #F0FDF4; border-color: #10B981; color: #065F46; }
.alt-red    { background: #FFF1F2; border-color: #F43F5E; color: #9F1239; }
.alt-amber  { background: #FFFBEB; border-color: #F59E0B; color: #92400E; }
.alt-blue   { background: #EFF6FF; border-color: #3B82F6; color: #1E40AF; }
.alt-purple { background: #F5F3FF; border-color: #8B5CF6; color: #4C1D95; }

/* ── Wait card ── */
.wait { background: linear-gradient(135deg, #F0FDF4, #ECFDF5); border: 1.5px solid #86EFAC; border-radius: 14px; padding: 34px; text-align: center; }

/* ── Hero cards ── */
.hcard { background: #fff; border: 1.5px solid #E2E8F0; border-radius: 16px; padding: 28px; box-shadow: 0 2px 10px rgba(0,0,0,.05); transition: all .2s; }
.hcard:hover { box-shadow: 0 8px 28px rgba(0,0,0,.1); transform: translateY(-2px); border-color: #CBD5E1; }

/* ── Podium ── */
.pod { display: flex; align-items: center; justify-content: space-between; padding: 13px 17px; background: #fff; border: 1.5px solid #E2E8F0; border-radius: 11px; margin-bottom: 9px; box-shadow: 0 1px 4px rgba(0,0,0,.04); }
.pod-rank { font-size: 20px; width: 30px; }
.pod-name { font-size: 14px; font-weight: 700; color: #1E293B; }
.pod-cost { font-family: 'JetBrains Mono', monospace; font-size: 14px; color: #64748B; }

/* ── Insight cards ── */
.ins { border-radius: 0 10px 10px 0; padding: 13px 16px; margin-bottom: 10px; border-left: 3px solid; }
.ins-title { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .07em; margin-bottom: 5px; }
.ins-body  { font-size: 12px; color: #64748B; line-height: 1.7; }

/* ── Cost info tiles ── */
.cost-tile { border-radius: 10px; padding: 12px 14px; margin-bottom: 8px; }

/* ── Role cards ── */
.rcard { border-radius: 9px; padding: 11px 14px; margin-bottom: 8px; border: 1.5px solid; }

/* ── Table ── */
.stDataFrame { border-radius: 12px !important; border: 1.5px solid #E2E8F0 !important; }
</style>
""", unsafe_allow_html=True)

# ── State ─────────────────────────────────────────────────────────────────────
def init_state():
    for k, v in {
        "page":"home","player_id":None,"session_code":"","player_name":"",
        "chain":"A","role":"Détaillant","is_facilitator":False,"facilitator_key":"",
        "order_history":[],"current_state":{},"order_sent":False,
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()
ss = st.session_state

# ── Helpers ───────────────────────────────────────────────────────────────────
def topbar(right="", show_home=False):
    st.markdown(f"""
    <div class="topbar">
      <div class="brand">📦 Bullwhip Game <span class="brand-sub">· ESLI Paris</span></div>
      <div style="display:flex;align-items:center;gap:9px">{right}</div>
    </div>""", unsafe_allow_html=True)
    if show_home:
        col_h, _ = st.columns([1, 5])
        with col_h:
            if st.button("🏠 Accueil", key="topbar_home_btn", use_container_width=True):
                for k in ["player_id","page","order_history","order_sent","current_state"]:
                    st.session_state.pop(k, None)
                st.session_state["page"] = "home"
                st.rerun()

def sh(label, icon=""):
    st.markdown(f'<div class="sh">{icon+" " if icon else ""}{label}</div>', unsafe_allow_html=True)

def mcard(label, value, dot_color, sub=""):
    st.markdown(f"""
    <div class="mc">
      <div class="mc-dot" style="background:{dot_color}"></div>
      <div class="mc-label">{label}</div>
      <div class="mc-value">{value}</div>
      {"<div class='mc-sub'>"+sub+"</div>" if sub else ""}
    </div>""", unsafe_allow_html=True)

def pb(pct, color, left="Progression", right=""):
    st.markdown(f"""
    <div class="pb-wrap">
      <div class="pb-top"><span>{left}</span><span style="color:{color};font-weight:700">{right}</span></div>
      <div class="pb-track"><div class="pb-fill" style="width:{pct}%;background:{color}"></div></div>
    </div>""", unsafe_allow_html=True)

def rb_html(role):
    m = ROLE_META.get(role, {})
    return (f'<span class="rb" style="background:{m["bg"]};color:{m["dk"]};'
            f'border-color:{m["border"]}">{m["emoji"]} {role}</span>')

def chain_vis(active):
    nodes = [("👤","Client",None)] + [(ROLE_META[r]["emoji"],r,r) for r in ROLES]
    html = '<div class="chain">'
    for i,(e,label,key) in enumerate(nodes):
        if i: html += '<span class="ca">›</span>'
        if key == active:
            m = ROLE_META[key]
            html += f'<div class="cn cn-active" style="background:{m["dot"]}">{e} {label}</div>'
        else:
            html += f'<div class="cn">{e} {label}</div>'
    st.markdown(html+"</div>", unsafe_allow_html=True)

def plotly_clean(fig, h=260):
    fig.update_layout(
        height=h, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Outfit, sans-serif", color="#94A3B8", size=11),
        margin=dict(l=0, r=0, t=16, b=0),
        xaxis=dict(showgrid=False, showline=False, tickfont=dict(size=10, color="#CBD5E1")),
        yaxis=dict(gridcolor="#F1F5F9", showline=False, tickfont=dict(size=10, color="#CBD5E1")),
        legend=dict(orientation="h", y=-0.28, bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
    )
    st.plotly_chart(fig, width="stretch")

# ── PAGE : HOME ───────────────────────────────────────────────────────────────
def page_home():
    topbar()
    st.markdown("""
    <div style="text-align:center;padding:12px 0 30px">
      <div style="font-size:44px;margin-bottom:10px">🌊</div>
      <div style="font-size:28px;font-weight:800;color:#0F172A;letter-spacing:-.03em">Bullwhip Game</div>
      <div style="font-size:14px;color:#94A3B8;margin-top:6px;font-weight:500">Simulation pédagogique · Chaîne logistique · ESLI Paris</div>
    </div>""", unsafe_allow_html=True)

    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown("""
        <div class="hcard">
          <div style="font-size:32px;margin-bottom:12px">🎓</div>
          <div style="font-size:16px;font-weight:800;color:#0F172A;margin-bottom:7px">Je suis étudiant</div>
          <div style="font-size:13px;color:#64748B;line-height:1.7;margin-bottom:20px">
            Rejoins une session, choisis ton rôle dans la chaîne et joue en temps réel avec ton groupe.
          </div>
        </div>""", unsafe_allow_html=True)
        if st.button("Rejoindre une session →", use_container_width=True, type="primary"):
            ss["page"]="join"; st.rerun()

    with c2:
        st.markdown("""
        <div class="hcard">
          <div style="font-size:32px;margin-bottom:12px">🎛️</div>
          <div style="font-size:16px;font-weight:800;color:#0F172A;margin-bottom:7px">Je suis facilitateur</div>
          <div style="font-size:13px;color:#64748B;line-height:1.7;margin-bottom:20px">
            Crée une session, pilote la progression des équipes et visualise l'effet Bullwhip en direct.
          </div>
        </div>""", unsafe_allow_html=True)
        if st.button("Espace facilitateur →", use_container_width=True):
            ss["page"]="facilitator_login"; st.rerun()

    st.write("")
    with st.expander("📖 Comment fonctionne ce jeu ?"):
        c1, c2 = st.columns(2, gap="large")
        with c1:
            st.markdown("""
**L'effet Bullwhip** est un phénomène clé en supply chain : de petites fluctuations
de la demande réelle créent des oscillations de plus en plus amplifiées en remontant
la chaîne, du Détaillant jusqu'au Fabricant.

**Ton rôle** : chaque semaine, tu reçois une commande de ton client aval et tu décides
combien commander à ton fournisseur amont. Objectif : **minimiser tes coûts**.
            """)
        with c2:
            st.markdown("""
**Structure des coûts :**
- 📦 Stock excédentaire : **0,15 €/unité/semaine**
- ❌ Rupture (backlog) : **0,50 €/unité/semaine**

**Durée** : 20 semaines simulées · ~45 min

**Après la partie** : analyse des indices Bullwhip, discussion
des causes et solutions réelles (VMI, EDI, CPFR…).
            """)

# ── PAGE : JOIN ───────────────────────────────────────────────────────────────
def page_join():
    topbar()
    if st.button("← Retour"): ss["page"]="home"; st.rerun()
    st.markdown("""
    <div style="font-size:22px;font-weight:800;color:#0F172A;letter-spacing:-.02em;margin-bottom:4px">Rejoindre une session</div>
    <div style="font-size:13px;color:#64748B;margin-bottom:24px">Entre le code donné par ton facilitateur et choisis ton rôle.</div>
    """, unsafe_allow_html=True)

    col_form, col_roles = st.columns([1.1, 1], gap="large")

    with col_form:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        with st.form("join_form"):
            code  = st.text_input("🔑 Code session", value="BW-2025", placeholder="ex. BW-2025")
            name  = st.text_input("👤 Ton prénom", placeholder="ex. Amary")
            c1,c2 = st.columns(2)
            with c1: chain = st.selectbox("⛓️ Chaîne", CHAINS[:6])
            with c2: role  = st.selectbox("🎯 Rôle", ROLES)
            st.write("")
            ok = st.form_submit_button("Rejoindre →", use_container_width=True, type="primary")
        m = ROLE_META.get(role, ROLE_META["Détaillant"])
        st.markdown(f'<div class="alt alt-{m["alert"]}">{m["emoji"]} <b>{role}</b> — {m["hint"]}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_roles:
        sh("Les rôles", "📋")
        for r, m in ROLE_META.items():
            st.markdown(f"""
            <div class="rcard" style="background:{m['bg']};border-color:{m['border']}">
              <div style="font-size:12px;font-weight:700;color:{m['dk']};margin-bottom:3px">{m['emoji']} {r}</div>
              <div style="font-size:11px;color:#64748B">{m['hint']}</div>
            </div>""", unsafe_allow_html=True)

    if ok:
        if not name.strip(): st.error("⚠️ Entre ton prénom."); return

        session_code_clean = code.strip().upper()

        with st.spinner("Connexion en cours..."):
            resp = api_post({
                "action":      "joinSession",
                "sessionCode": session_code_clean,
                "playerName":  name.strip(),
                "chain":       chain,
                "role":        role,
            })

        # ── Rôle déjà pris → tentative de reconnexion ──────────────────────
        if resp.get("error","").lower().find("déjà pris") != -1 or            resp.get("error","").lower().find("already") != -1:

            with st.spinner("Rôle existant détecté — reconnexion..."):
                resp2 = api_post({
                    "action":      "reconnectPlayer",
                    "sessionCode": session_code_clean,
                    "playerName":  name.strip(),
                    "chain":       chain,
                    "role":        role,
                })

            if "error" in resp2:
                err_msg = resp2["error"]
                st.error(f"❌ {err_msg}")
                # Guide précis selon le type d'erreur
                if "introuvable" in err_msg.lower() or "not found" in err_msg.lower():
                    st.markdown("""
                    <div class="alt alt-amber">
                      ⚠️ <b>Reconnexion impossible.</b> Vérifie ces 3 points :<br>
                      &nbsp;&nbsp;• <b>Prénom</b> : exactement le même qu'à l'inscription (majuscules comprises)<br>
                      &nbsp;&nbsp;• <b>Chaîne</b> : la même lettre qu'à l'inscription<br>
                      &nbsp;&nbsp;• <b>Rôle</b> : exactement le même rôle qu'à l'inscription
                    </div>""", unsafe_allow_html=True)
            else:
                st.success(f"✅ Reconnexion réussie ! Bienvenue {resp2.get('playerName', name.strip())} 👋")
                ss.update({
                    "player_id":    resp2["playerId"],
                    "session_code": session_code_clean,
                    "player_name":  name.strip(),
                    "chain":        chain,
                    "role":         role,
                    "page":         "play",
                    "order_sent":   resp2.get("orderSentThisRound", False),
                    "order_history": resp2.get("orderHistory", []),
                })
                st.rerun()

        elif "error" in resp:
            st.error(f"❌ {resp['error']}")

        else:
            ss.update({
                "player_id":    resp["playerId"],
                "session_code": session_code_clean,
                "player_name":  name.strip(),
                "chain":        chain,
                "role":         role,
                "page":         "play",
                "order_sent":   False,
            })
            st.rerun()

# ── PAGE : PLAY ───────────────────────────────────────────────────────────────
def page_play():
    state = api_get({"action":"getState","playerId":ss["player_id"],"sessionCode":ss["session_code"]})
    if "error" in state: st.error(f"❌ {state['error']}"); return

    ss["current_state"] = state
    week   = state.get("currentWeek", 1)
    total  = state.get("totalWeeks", 20)
    status = state.get("gameStatus", "playing")
    role   = ss["role"]
    m      = ROLE_META.get(role, {})

    if status == "finished": ss["page"]="results"; st.rerun()

    pct = int(week / max(total,1) * 100)
    topbar(right=f'{rb_html(role)}&nbsp;&nbsp;<span class="wb">S{week}/{total}</span>', show_home=True)

    pb(pct, m["dot"], f"Chaîne {ss['chain']} · Semaine {week}", f"{pct}% — {total-week} sem. restantes")

    stock   = state.get("stock", 0)
    backlog = state.get("backlog", 0)
    deliv   = state.get("pendingDelivery", 0)
    cost    = state.get("totalCost", 0.0)

    sh("État actuel", "📊")
    c1,c2,c3,c4 = st.columns(4)
    with c1:
        dot = "#10B981" if stock>=8 else "#F59E0B" if stock>0 else "#EF4444"
        mcard("Stock", f"{stock} u", dot, "unités disponibles")
    with c2:
        dot = "#10B981" if backlog==0 else "#F59E0B" if backlog<=3 else "#EF4444"
        mcard("Backlog", f"{backlog} u", dot, "commandes en retard")
    with c3:
        mcard("Livraison S+1", f"{deliv} u", "#3B82F6", "semaine prochaine")
    with c4:
        mcard("Coût cumulé", f"{cost:.0f}€", "#8B5CF6", "depuis le début")

    st.write("")

    if not ss["order_sent"]:
        col_order, col_side = st.columns([1.3, 1], gap="large")
        hist = ss["order_history"]
        last_in = hist[-1]["incoming"] if hist else 4

        with col_order:
            sh("Décision de commande", "📋")
            up_idx = ROLES.index(role)
            upstream = ROLES[up_idx+1] if up_idx < 3 else "Production"
            up_m = ROLE_META.get(upstream, {})
            st.markdown(f"""
            <div class="order-panel">
              <div style="font-size:13px;font-weight:700;color:#334155;margin-bottom:13px">
                📤 Commander à → {up_m.get("emoji","")} {upstream}
              </div>
              <div class="inc-box">
                <span class="inc-label">Commande reçue ce tour :</span>
                <span class="inc-val">{last_in} u</span>
              </div>
            </div>""", unsafe_allow_html=True)

            qty = st.number_input("Quantité à commander (unités)", min_value=0, max_value=200,
                                  value=int(last_in), step=1, key=f"q{week}")
            proj_s = max(0, stock+deliv-last_in)
            proj_b = max(0, last_in-stock-deliv)
            est    = proj_s*0.15 + proj_b*0.50
            st.markdown(f"""
            <div class="cost-row">
              <span>📦 {proj_s*0.15:.2f}€ stock &nbsp;|&nbsp; ⚠️ {proj_b*0.50:.2f}€ rupture</span>
              <span style="font-weight:700;color:#1E293B">= {est:.2f} €</span>
            </div>""", unsafe_allow_html=True)
            st.write("")

            if st.button("✅ Valider ma commande", use_container_width=True, type="primary"):
                with st.spinner("Envoi..."):
                    resp = api_post({"action":"submitOrder","sessionCode":ss["session_code"],
                                     "playerId":ss["player_id"],"orderQty":int(qty)})
                if "error" in resp: st.error(f"❌ {resp['error']}")
                else:
                    ss["order_history"].append({
                        "week":resp.get("week",week),"incoming":resp.get("incomingDemand",last_in),
                        "order":resp.get("orderPlaced",qty),"stock":resp.get("newStock",stock),
                        "backlog":resp.get("newBacklog",backlog),"cost":resp.get("weekCost",0.0),
                    })
                    ss["order_sent"]=True; st.rerun()

        with col_side:
            sh("Coûts & conseils", "💡")
            st.markdown(f"""
            <div class="cost-tile" style="background:#FFFBEB;border:1.5px solid #FDE68A">
              <div style="font-size:10px;font-weight:700;color:#92400E;text-transform:uppercase;letter-spacing:.07em;margin-bottom:4px">📦 Stock excédentaire</div>
              <div style="font-family:'JetBrains Mono',monospace;font-size:18px;font-weight:700;color:#D97706">0,15 €/u/sem</div>
            </div>
            <div class="cost-tile" style="background:#FFF1F2;border:1.5px solid #FECACA">
              <div style="font-size:10px;font-weight:700;color:#9F1239;text-transform:uppercase;letter-spacing:.07em;margin-bottom:4px">⚠️ Rupture (backlog)</div>
              <div style="font-family:'JetBrains Mono',monospace;font-size:18px;font-weight:700;color:#E11D48">0,50 €/u/sem</div>
            </div>""", unsafe_allow_html=True)

            if stock==0 and backlog>0:
                st.markdown('<div class="alt alt-red">🔴 <b>Rupture !</b> Tu paies 0,50€/u non livrée. Commande davantage.</div>', unsafe_allow_html=True)
            elif stock>15:
                st.markdown('<div class="alt alt-amber">🟡 <b>Stock élevé.</b> Tu paies 0,15€/u. Adapte ta commande à la demande réelle.</div>', unsafe_allow_html=True)
            elif stock>=4 and backlog==0:
                st.markdown('<div class="alt alt-green">🟢 <b>Bonne gestion !</b> Stock équilibré, pas de rupture.</div>', unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="wait">
          <div style="font-size:38px;margin-bottom:10px">⏳</div>
          <div style="font-size:17px;font-weight:800;color:#166534;margin-bottom:6px">Commande envoyée !</div>
          <div style="font-size:13px;color:#16A34A">En attente des autres joueurs et du facilitateur.</div>
        </div>""", unsafe_allow_html=True)
        st.write("")
        if st.button("🔄 Rafraîchir", use_container_width=True):
            ss["order_sent"]=False; st.rerun()

    if ss["order_history"]:
        st.write("")
        sh("Historique des commandes", "📈")
        df = pd.DataFrame(ss["order_history"])
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df["week"], y=df["incoming"], name="Demande reçue",
                             marker_color="#E2E8F0", marker_line_width=0, opacity=.9))
        fig.add_trace(go.Scatter(x=df["week"], y=df["order"], name="Vos commandes",
                                 mode="lines+markers",
                                 line=dict(color=m["dot"], width=2.5),
                                 marker=dict(size=7, color=m["dot"], line=dict(color="#fff", width=2))))
        fig.update_layout(xaxis_title="Semaine", yaxis_title="Unités", bargap=.4)
        plotly_clean(fig, 240)

    st.write("")
    sh("Position dans la chaîne", "⛓️")
    chain_vis(role)

# ── PAGE : FACILITATOR LOGIN ───────────────────────────────────────────────────
def page_facilitator_login():
    topbar()
    if st.button("← Retour"): ss["page"]="home"; st.rerun()
    st.markdown("""
    <div style="font-size:22px;font-weight:800;color:#0F172A;letter-spacing:-.02em;margin-bottom:4px">Espace Facilitateur</div>
    <div style="font-size:13px;color:#64748B;margin-bottom:24px">Accède à une session existante ou crée-en une nouvelle.</div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2, gap="large")
    with c1:
        sh("Accéder à une session", "🔐")
        st.markdown('<div class="card">', unsafe_allow_html=True)
        with st.form("fac_form"):
            code = st.text_input("Code session", value="BW-2025")
            key  = st.text_input("Clé facilitateur", type="password", placeholder="ex. 1234")
            if st.form_submit_button("Accéder au dashboard →", type="primary", use_container_width=True):
                if code.strip() and key.strip():
                    ss.update({"session_code":code.strip().upper(),"facilitator_key":key.strip(),
                               "is_facilitator":True,"page":"facilitator"}); st.rerun()
                else: st.error("Remplis les deux champs.")
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        sh("Créer une session", "✨")
        st.markdown('<div class="card">', unsafe_allow_html=True)
        with st.form("create_form"):
            nc = st.text_input("Code session", placeholder="ex. BW-2025")
            nk = st.text_input("Clé facilitateur", placeholder="ex. 1234")
            nb = st.slider("Nombre de chaînes", 1, 8, 5)
            if st.form_submit_button("Créer →", use_container_width=True):
                if nc.strip() and nk.strip():
                    resp = api_post({"action":"createSession","sessionCode":nc.strip().upper(),
                                     "facilitatorKey":nk.strip(),"nbChains":nb})
                    if "error" in resp: st.error(f"❌ {resp['error']}")
                    else: st.success(f"✅ Session **{nc.upper()}** créée !")
                else: st.error("Remplis tous les champs.")
        st.markdown('</div>', unsafe_allow_html=True)

# ── PAGE : FACILITATOR ────────────────────────────────────────────────────────
def page_facilitator():
    if not ss.get("facilitator_key","").strip():
        topbar()
        st.warning("⚠️ Clé manquante — ressaisis-la.")
        with st.form("rekey"):
            rk = st.text_input("Clé facilitateur", type="password")
            if st.form_submit_button("Confirmer", type="primary"):
                if rk.strip(): ss["facilitator_key"]=rk.strip(); st.rerun()
        return

    masked = ss["facilitator_key"][:2]+"••••"
    topbar(right=f'<span style="font-size:11px;color:#94A3B8;font-weight:500">🔑 {masked} · {ss["session_code"]}</span>', show_home=True)

    data = api_get({"action":"getFacDashboard","sessionCode":ss["session_code"]})
    if "error" in data: st.error(f"❌ {data['error']}"); return

    week=data.get("currentWeek",1); status=data.get("status","waiting")
    np=data.get("totalPlayers",0); npl=data.get("playedThisRound",0)
    bwi=data.get("bullwhipIndex",{})

    sh("Tableau de bord", "📊")
    c1,c2,c3,c4 = st.columns(4)
    with c1: mcard("Semaine",   f"{week}/20",       "#1E293B", "en cours")
    with c2: mcard("Joueurs",   str(np),             "#8B5CF6", "connectés")
    with c3:
        d = "#10B981" if npl==np else "#F59E0B"
        mcard("Ont joué", f"{npl}/{np}", d, "ce tour")
    with c4:
        si = {"waiting":"🟡","playing":"🟢","finished":"🔵"}
        mcard("Statut", status.capitalize(), "#3B82F6")

    pct_s = int(npl/max(np,1)*100)
    pb(pct_s, "#10B981" if pct_s==100 else "#F59E0B",
       "Soumissions ce tour", f"{pct_s}%")

    players = data.get("players",[])
    if players:
        sh("Joueurs connectés", "👥")
        records = []
        for p in players:
            if isinstance(p,dict):
                records.append({"Chaîne":p.get("chain","—"),"Rôle":p.get("role","—"),
                                 "Joueur":p.get("name","—"),"Stock":p.get("stock",0),
                                 "Backlog":p.get("backlog",0),
                                 "Coût €":p.get("cost",p.get("totalCost",0.0))})
        if records:
            df=pd.DataFrame(records).sort_values(["Chaîne","Rôle"])
            def add_bwi(row):
                v=bwi.get(f"{row['Chaîne']}-{row['Rôle']}")
                return f"{v:.2f}x" if v else "—"
            df["BWI"]=df.apply(add_bwi,axis=1)
            st.dataframe(df,use_container_width=True,hide_index=True,
                         column_config={"Coût €":st.column_config.NumberColumn(format="%.2f €")})

    st.write("")
    ca,cr,cs,crf = st.columns(4)
    with ca:
        if status!="finished":
            if st.button("▶ Semaine suivante",use_container_width=True,type="primary"):
                resp=api_post({"action":"advanceWeek","sessionCode":ss["session_code"],
                               "facilitatorKey":ss["facilitator_key"]})
                if "error" in resp:
                    err=resp["error"]
                    if any(w in err.lower() for w in ["clé","key","invalid"]):
                        st.error(f"❌ {err}")
                        if st.button("🔑 Réinitialiser la clé"): ss["facilitator_key"]=""; st.rerun()
                    else: st.error(err)
                else: st.success(f"✅ Semaine {resp.get('newWeek','?')} démarrée !"); st.rerun()
    with cr:
        if st.button("📊 Résultats",use_container_width=True): ss["page"]="results"; st.rerun()
    with cs:
        if st.button("🔄 Réinitialiser",use_container_width=True):
            resp=api_post({"action":"resetSession","sessionCode":ss["session_code"],
                           "facilitatorKey":ss["facilitator_key"]})
            if "error" in resp: st.error(resp["error"])
            else: st.success("Réinitialisé."); st.rerun()
    with crf:
        if st.button("↺ Rafraîchir",use_container_width=True): st.rerun()

# ── PAGE : RESULTS ────────────────────────────────────────────────────────────
def page_results():
    topbar()
    st.markdown(f"""
    <div style="font-size:22px;font-weight:800;color:#0F172A;letter-spacing:-.02em;margin-bottom:4px">🏆 Résultats finaux</div>
    <div style="font-size:13px;color:#64748B;margin-bottom:24px">Session {ss['session_code']} · Analyse de l'effet Bullwhip</div>
    """, unsafe_allow_html=True)

    data = api_get({"action":"getResults","sessionCode":ss["session_code"]})
    if "error" in data: st.error(f"❌ {data['error']}"); return

    bwi=data.get("bullwhipIndex",{}); chain_costs=data.get("chainCosts",{}); players=data.get("players",[])

    sh("Indice Bullwhip par échelon", "🌊")
    bwr: dict = {}
    for key,val in bwi.items():
        if "-" not in key or val is None: continue
        _,role=key.split("-",1)
        if role not in bwr: bwr[role]=[]
        try: bwr[role].append(float(val))
        except: pass

    roles_ok=[r for r in ROLES if r in bwr and bwr[r]]
    avg=[sum(bwr[r])/len(bwr[r]) for r in roles_ok if bwr[r]]

    if roles_ok and avg:
        col_ch,col_lg = st.columns([1.8,1],gap="large")
        with col_ch:
            colors=[ROLE_META.get(r,{}).get("dot","#888") for r in roles_ok]
            fig=go.Figure(go.Bar(x=roles_ok,y=avg,marker_color=colors,marker_line_width=0,
                                 text=[f"<b>{v:.2f}</b>" for v in avg],textposition="outside",
                                 textfont=dict(size=12,color="#1E293B")))
            fig.add_hline(y=1,line_dash="dot",line_color="#CBD5E1",line_width=1.5,
                          annotation_text="BWI = 1 (idéal)",
                          annotation_font=dict(size=9,color="#94A3B8"))
            fig.update_layout(yaxis_title="Indice Bullwhip",bargap=.45)
            plotly_clean(fig,280)
        with col_lg:
            for r,v in zip(roles_ok,avg):
                m=ROLE_META.get(r,{})
                sev="🟢" if v<1.5 else "🟡" if v<3 else "🔴"
                st.markdown(f"""
                <div style="background:{m['bg']};border:1.5px solid {m['border']};
                     border-radius:11px;padding:12px 15px;margin-bottom:9px">
                  <div style="font-size:11px;font-weight:700;color:{m['dk']};margin-bottom:4px">{m['emoji']} {r}</div>
                  <div style="font-family:'JetBrains Mono',monospace;font-size:20px;font-weight:700;color:{m['dot']}">{sev} {v:.2f}x</div>
                </div>""", unsafe_allow_html=True)
    else:
        st.info("Indices Bullwhip disponibles après 3+ semaines jouées.")

    if chain_costs:
        sh("Classement des chaînes", "🏅")
        sorted_c=sorted(chain_costs.items(),key=lambda x:x[1])
        medals=["🥇","🥈","🥉"]
        col_p,_ = st.columns([1.4,1])
        with col_p:
            for i,(chain,cost) in enumerate(sorted_c):
                border = "#FCD34D" if i==0 else "#E2E8F0"
                st.markdown(f"""
                <div class="pod" style="border-color:{border};{'background:#FFFBEB;' if i==0 else ''}">
                  <span class="pod-rank">{medals[i] if i<3 else f'#{i+1}'}</span>
                  <div><div class="pod-name">Chaîne {chain}</div></div>
                  <span class="pod-cost">{cost:.2f} €</span>
                </div>""", unsafe_allow_html=True)

    if players:
        sh("Détail par joueur", "👥")
        records=[]
        for p in players:
            if isinstance(p,dict):
                records.append({"Chaîne":p.get("chain","—"),"Rôle":p.get("role","—"),
                                 "Joueur":p.get("name","—"),"Coût total (€)":p.get("totalCost",0.0)})
            elif isinstance(p,(list,tuple)) and len(p)>=4:
                records.append({"Chaîne":p[0],"Rôle":p[1],"Joueur":p[2],"Coût total (€)":p[3]})
        if records:
            df=pd.DataFrame(records).sort_values("Coût total (€)")
            st.dataframe(df,use_container_width=True,hide_index=True,
                         column_config={"Coût total (€)":st.column_config.NumberColumn(format="%.2f €")})

    sh("Enseignements pédagogiques", "🎓")
    insights=[
        ("#EFF6FF","#3B82F6","#1E40AF","🔍 Manque de visibilité",
         "Chaque maillon ne voit que la demande de son voisin direct. L'information se déforme à chaque transmission."),
        ("#FFFBEB","#F59E0B","#92400E","📦 Surcommande par précaution",
         "Face à l'incertitude, chaque acteur commande plus que nécessaire — ce qui amplifie le signal en amont."),
        ("#F5F3FF","#8B5CF6","#4C1D95","⏱️ Délais de livraison",
         "Plus le lead time est long, plus l'incertitude est grande et plus on surcommande."),
        ("#F0FDF4","#10B981","#065F46","✅ Solutions réelles",
         "VMI, partage d'info EDI en temps réel, CPFR, flux tirés Kanban/JIT réduisent l'effet Bullwhip."),
    ]
    ci1,ci2=st.columns(2,gap="large")
    for i,(bg,bc,tc,title,body) in enumerate(insights):
        with (ci1 if i%2==0 else ci2):
            st.markdown(f"""
            <div class="ins" style="background:{bg};border-color:{bc}">
              <div class="ins-title" style="color:{tc}">{title}</div>
              <div class="ins-body">{body}</div>
            </div>""", unsafe_allow_html=True)

    st.write("")
    col_b1, col_b2, _ = st.columns([1.2, 1, 1.8])
    with col_b1:
        if ss.get("is_facilitator"):
            if st.button("← Dashboard facilitateur", use_container_width=True, type="primary"):
                ss["page"] = "facilitator"; st.rerun()
        else:
            if st.button("← Retour à l'accueil", use_container_width=True):
                for k in ["player_id","page","order_history","order_sent","current_state"]:
                    st.session_state.pop(k, None)
                ss["page"] = "home"; st.rerun()
    with col_b2:
        if ss.get("is_facilitator"):
            if st.button("🏠 Quitter", use_container_width=True):
                for k in ["player_id","page","order_history","order_sent","current_state",
                          "is_facilitator","facilitator_key","session_code"]:
                    st.session_state.pop(k, None)
                ss["page"] = "home"; st.rerun()

# ── Router ────────────────────────────────────────────────────────────────────
page=ss.get("page","home")
if   page=="home":              page_home()
elif page=="join":              page_join()
elif page=="play":              page_play()
elif page=="facilitator_login": page_facilitator_login()
elif page=="facilitator":       page_facilitator()
elif page=="results":           page_results()
else: ss["page"]="home"; st.rerun()
