"""
Bullwhip Game – Interface Streamlit
Connectée à Apps Script + Google Sheets

Lancement :
    pip install -r requirements.txt
    streamlit run bullwhip_game.py
"""

import streamlit as st
import requests
import json
import time
import pandas as pd
import plotly.graph_objects as go

# ── Configuration ────────────────────────────────────────────
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbz_VmabDh4BVYLVIeHDKBmwcCykXsrM-LIr_hGxWd9Jp36-GGSXggiE59aQe1eIg7XqnQ/exec"
ROLES = ["Détaillant", "Grossiste", "Distributeur", "Fabricant"]
CHAINS = ["A", "B", "C", "D", "E", "F"]

# ── Helpers API ──────────────────────────────────────────────

def api_get(params: dict) -> dict:
    try:
        r = requests.get(APPS_SCRIPT_URL, params=params, timeout=15)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def api_post(payload: dict) -> dict:
    try:
        r = requests.post(
            APPS_SCRIPT_URL,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        return r.json()
    except Exception as e:
        return {"error": str(e)}

# ── Mise en page globale ─────────────────────────────────────

st.set_page_config(
    page_title="Bullwhip Game – ESLI",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
  .main { max-width: 800px; margin: 0 auto; }
  .big-number { font-size: 2.4rem; font-weight: 600; }
  .role-tag { background: #E1F5EE; color: #085041; padding: 3px 10px;
              border-radius: 6px; font-size: 0.85rem; font-weight: 500; }
  .warn-tag  { background: #FAEEDA; color: #633806; padding: 3px 10px;
               border-radius: 6px; font-size: 0.85rem; font-weight: 500; }
  .danger-tag{ background: #FCEBEB; color: #791F1F; padding: 3px 10px;
               border-radius: 6px; font-size: 0.85rem; font-weight: 500; }
  .hint { font-size: 0.85rem; color: #888; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)

# ── État de session Streamlit ────────────────────────────────

def init_state():
    defaults = {
        "page": "home",          # home | join | play | facilitator | results
        "player_id": None,
        "session_code": "",
        "player_name": "",
        "chain": "A",
        "role": "Détaillant",
        "is_facilitator": False,
        "facilitator_key": "",
        "order_history": [],     # [{week, incoming, order, stock, backlog, cost}]
        "current_state": {},
        "order_sent": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()
ss = st.session_state

# ── PAGE : Accueil ───────────────────────────────────────────

def page_home():
    st.title("📦 Bullwhip Game")
    st.caption("Simulation pédagogique de la chaîne logistique – ESLI")
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Je suis étudiant")
        st.write("Rejoindre une session et jouer en temps réel avec ta chaîne.")
        if st.button("Rejoindre une session →", use_container_width=True, type="primary"):
            ss["page"] = "join"
            st.rerun()
    with col2:
        st.subheader("Je suis facilitateur")
        st.write("Créer et piloter une session, voir le dashboard temps réel.")
        if st.button("Espace facilitateur →", use_container_width=True):
            ss["page"] = "facilitator_login"
            st.rerun()
    st.divider()
    with st.expander("Comment fonctionne ce jeu ?"):
        st.markdown("""
**L'effet Bullwhip** est un phénomène bien documenté en supply chain :
de petites variations de la demande finale créent des oscillations
de plus en plus grandes en remontant la chaîne.

**Ton rôle** : chaque semaine, tu reçois une commande de ton client
et tu dois décider combien commander à ton fournisseur.

**Objectif** : minimiser tes coûts sur 20 semaines —
0,15 €/unité en stock + 0,50 €/unité en rupture par semaine.

**Après la partie**, le groupe compare les indices Bullwhip
de chaque échelon et discute des causes et des solutions.
        """)

# ── PAGE : Rejoindre ─────────────────────────────────────────

def page_join():
    st.title("Rejoindre une session")
    if st.button("← Retour"):
        ss["page"] = "home"; st.rerun()

    with st.form("join_form"):
        code  = st.text_input("Code session (donné par le facilitateur)", value="BW-2025")
        name  = st.text_input("Ton prénom")
        chain = st.selectbox("Chaîne", CHAINS[:6])
        role  = st.selectbox("Rôle", ROLES, help=(
            "Détaillant : voit la demande réelle du client. "
            "Fabricant : tout en haut de la chaîne, n'a aucune visibilité sur la demande finale."
        ))
        submitted = st.form_submit_button("Rejoindre →", use_container_width=True, type="primary")

    if submitted:
        if not name.strip():
            st.error("Entre ton prénom."); return
        with st.spinner("Connexion..."):
            resp = api_post({
                "action":      "joinSession",
                "sessionCode": code.strip().upper(),
                "playerName":  name.strip(),
                "chain":       chain,
                "role":        role,
            })
        if "error" in resp:
            st.error(resp["error"])
        else:
            ss["player_id"]    = resp["playerId"]
            ss["session_code"] = code.strip().upper()
            ss["player_name"]  = name.strip()
            ss["chain"]        = chain
            ss["role"]         = role
            ss["page"]         = "play"
            ss["order_sent"]   = False
            st.rerun()

# ── PAGE : Jeu ───────────────────────────────────────────────

def page_play():
    # Rafraîchir l'état depuis le serveur
    state = api_get({
        "action":      "getState",
        "playerId":    ss["player_id"],
        "sessionCode": ss["session_code"],
    })
    if "error" in state:
        st.error(state["error"]); return

    ss["current_state"] = state
    week  = state.get("currentWeek", 1)
    total = state.get("totalWeeks", 20)
    game_status = state.get("gameStatus", "playing")

    if game_status == "finished":
        ss["page"] = "results"; st.rerun()

    # En-tête
    col_title, col_badge = st.columns([3,1])
    with col_title:
        st.markdown(f"### Semaine {week} / {total}")
    with col_badge:
        st.markdown(
            f'<span class="role-tag">{ss["role"]} · Chaîne {ss["chain"]}</span>',
            unsafe_allow_html=True
        )

    # Barre de progression
    st.progress(week / total)
    st.write("")

    # Métriques
    stock   = state.get("stock", 0)
    backlog = state.get("backlog", 0)
    deliv   = state.get("pendingDelivery", 0)
    cost    = state.get("totalCost", 0)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Stock", stock, delta=None,
              delta_color="normal" if stock >= 8 else "inverse")
    c2.metric("Backlog", backlog,
              delta=None, delta_color="inverse")
    c3.metric("Livraison prévue", deliv)
    c4.metric("Coût total", f"{cost:.2f} €")

    st.divider()

    # Saisie de commande
    if not ss["order_sent"]:
        st.subheader("Ta commande ce tour")

        # Estimation de la demande entrante basée sur l'historique
        hist = ss["order_history"]
        last_incoming = hist[-1]["incoming"] if hist else 4
        st.info(f"Dernière commande reçue de ton client : **{last_incoming} unités**")

        order_qty = st.number_input(
            "Quantité à commander à ton fournisseur",
            min_value=0, max_value=200,
            value=last_incoming,
            step=1,
            key=f"order_w{week}"
        )

        # Estimation coût
        projected_stock   = max(0, stock + deliv - last_incoming)
        projected_backlog = max(0, last_incoming - stock - deliv)
        est_cost = projected_stock * 0.15 + projected_backlog * 0.50
        st.caption(
            f"Coût estimé : stock {projected_stock * 0.15:.2f} € "
            f"+ rupture {projected_backlog * 0.50:.2f} € "
            f"= **{est_cost:.2f} €**"
        )

        if st.button("✅ Valider la commande", use_container_width=True, type="primary"):
            with st.spinner("Envoi de ta commande..."):
                resp = api_post({
                    "action":      "submitOrder",
                    "sessionCode": ss["session_code"],
                    "playerId":    ss["player_id"],
                    "orderQty":    int(order_qty),
                })
            if "error" in resp:
                st.error(resp["error"])
            else:
                ss["order_history"].append({
                    "week":    resp["week"],
                    "incoming": resp["incomingDemand"],
                    "order":    resp["orderPlaced"],
                    "stock":    resp["newStock"],
                    "backlog":  resp["newBacklog"],
                    "cost":     resp["weekCost"],
                })
                ss["order_sent"] = True
                st.rerun()
    else:
        st.success("Commande envoyée · En attente des autres joueurs et du facilitateur...")
        if st.button("Rafraîchir"):
            ss["order_sent"] = False
            st.rerun()
        st.caption("Le facilitateur passe à la semaine suivante depuis son dashboard.")

    # Historique graphique
    if ss["order_history"]:
        st.divider()
        st.subheader("Historique")
        df = pd.DataFrame(ss["order_history"])
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df["week"], y=df["incoming"],
            name="Demande reçue", marker_color="#1D9E75", opacity=0.8
        ))
        fig.add_trace(go.Scatter(
            x=df["week"], y=df["order"],
            name="Tes commandes", mode="lines+markers",
            line=dict(color="#EF9F27", width=2),
            marker=dict(size=6)
        ))
        fig.update_layout(
            height=240, margin=dict(l=0,r=0,t=10,b=0),
            legend=dict(orientation="h", y=-0.3),
            xaxis_title="Semaine",
            yaxis_title="Unités"
        )
        st.plotly_chart(fig, use_container_width=True)

    # Chaîne visuelle
    st.divider()
    st.caption("Ta position dans la chaîne logistique")
    chain_html = '<div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap">'
    all_roles = ["Client fictif"] + ROLES
    for i, r in enumerate(all_roles):
        style = ('background:#E1F5EE;color:#085041;border:2px solid #1D9E75;'
                 if r == ss["role"] else
                 'background:#f5f5f5;color:#666;border:1px solid #ddd;')
        chain_html += (
            f'<div style="padding:6px 12px;border-radius:6px;font-size:13px;{style}">{r}</div>'
        )
        if i < len(all_roles) - 1:
            chain_html += '<span style="color:#aaa">→</span>'
    chain_html += '</div>'
    st.markdown(chain_html, unsafe_allow_html=True)

# ── PAGE : Facilitateur login ─────────────────────────────────

def page_facilitator_login():
    st.title("Espace facilitateur")
    if st.button("← Retour"):
        ss["page"] = "home"; st.rerun()

    with st.form("fac_form"):
        code = st.text_input("Code session", value="BW-2025")
        key  = st.text_input("Clé facilitateur", type="password", placeholder="FAC-SECRET")
        submitted = st.form_submit_button("Accéder →", type="primary", use_container_width=True)

    if submitted:
        ss["session_code"]   = code.strip().upper()
        ss["facilitator_key"] = key.strip()
        ss["is_facilitator"] = True
        ss["page"]           = "facilitator"
        st.rerun()

    st.divider()
    st.subheader("Créer une nouvelle session")
    with st.form("create_form"):
        new_code = st.text_input("Code session (ex. BW-2025)")
        new_key  = st.text_input("Clé facilitateur (garde-la secrète !)")
        nb_chains = st.slider("Nombre de chaînes", 1, 8, 5)
        if st.form_submit_button("Créer la session →", use_container_width=True):
            resp = api_post({
                "action":        "createSession",
                "sessionCode":   new_code.strip().upper(),
                "facilitatorKey": new_key.strip(),
                "nbChains":      nb_chains,
            })
            if "error" in resp:
                st.error(resp["error"])
            else:
                st.success(f"Session {new_code.upper()} créée ! Partage ce code aux étudiants.")

# ── PAGE : Facilitateur dashboard ────────────────────────────

def page_facilitator():
    st.title("Dashboard facilitateur")
    col_h, col_btn = st.columns([3, 1])
    with col_h:
        st.caption(f"Session : {ss['session_code']}")
    with col_btn:
        if st.button("Rafraîchir", use_container_width=True):
            st.rerun()

    data = api_get({
        "action":      "getFacDashboard",
        "sessionCode": ss["session_code"],
    })
    if "error" in data:
        st.error(data["error"]); return

    week   = data.get("currentWeek", 1)
    status = data.get("status", "waiting")
    n_players = data.get("totalPlayers", 0)
    n_played  = data.get("playedThisRound", 0)

    # Métriques globales
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Semaine courante", f"{week} / 20")
    c2.metric("Joueurs actifs", n_players)
    c3.metric("Ont joué ce tour", f"{n_played} / {n_players}")
    c4.metric("Statut", status)

    st.progress(n_played / max(n_players, 1))
    st.divider()

    # Tableau joueurs
    players = data.get("players", [])
    bwi     = data.get("bullwhipIndex", {})

    if players:
        df = pd.DataFrame(players)
        df.columns = ["Chaîne","Rôle","Joueur","Stock","Backlog","Coût total (€)"]
        df = df.sort_values(["Chaîne","Rôle"])

        # Ajouter BWI
        def get_bwi(row):
            key = f"{row['Chaîne']}-{row['Rôle']}"
            v = bwi.get(key)
            return f"{v:.2f}" if v else "—"
        df["BWI"] = df.apply(get_bwi, axis=1)

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Coût total (€)": st.column_config.NumberColumn(format="%.2f €"),
            }
        )

    st.divider()
    col_adv, col_res, col_reset = st.columns(3)

    with col_adv:
        if status != "finished":
            if st.button("▶ Semaine suivante", use_container_width=True, type="primary"):
                resp = api_post({
                    "action":        "advanceWeek",
                    "sessionCode":   ss["session_code"],
                    "facilitatorKey": ss["facilitator_key"],
                })
                if "error" in resp:
                    st.error(resp["error"])
                else:
                    st.success(f"Semaine {resp['newWeek']} démarrée !")
                    st.rerun()

    with col_res:
        if st.button("Voir les résultats →", use_container_width=True):
            ss["page"] = "results"; st.rerun()

    with col_reset:
        if st.button("Réinitialiser la session", use_container_width=True):
            resp = api_post({
                "action":        "resetSession",
                "sessionCode":   ss["session_code"],
                "facilitatorKey": ss["facilitator_key"],
            })
            if "error" in resp:
                st.error(resp["error"])
            else:
                st.success("Session réinitialisée."); st.rerun()

    # Auto-refresh toutes les 10 secondes
    time.sleep(0)
    st.caption("Dashboard · Rafraîchissement manuel ou via le bouton")

# ── PAGE : Résultats ─────────────────────────────────────────

def page_results():
    st.title("Résultats finaux")
    st.caption(f"Session {ss['session_code']}")

    data = api_get({
        "action":      "getResults",
        "sessionCode": ss["session_code"],
    })
    if "error" in data:
        st.error(data["error"]); return

    bwi       = data.get("bullwhipIndex", {})
    chain_costs = data.get("chainCosts", {})
    players   = data.get("players", [])

    # Graphique Bullwhip par rôle
    st.subheader("Indice Bullwhip par échelon")
    bwi_by_role = {}
    for key, val in bwi.items():
        _, role = key.split("-", 1)
        if role not in bwi_by_role:
            bwi_by_role[role] = []
        if val:
            bwi_by_role[role].append(val)

    roles_ordered = [r for r in ROLES if r in bwi_by_role]
    avg_bwi = [
        sum(bwi_by_role[r]) / len(bwi_by_role[r])
        for r in roles_ordered
    ]

    if avg_bwi:
        colors = ["#1D9E75","#EF9F27","#E24B4A","#A32D2D"][:len(avg_bwi)]
        fig = go.Figure(go.Bar(
            x=roles_ordered, y=avg_bwi,
            marker_color=colors, text=[f"{v:.2f}" for v in avg_bwi],
            textposition="outside"
        ))
        fig.add_hline(y=1, line_dash="dash", line_color="#aaa",
                      annotation_text="BWI = 1 (pas d'amplification)")
        fig.update_layout(
            height=300, margin=dict(l=0,r=0,t=20,b=0),
            yaxis_title="Indice Bullwhip (BWI)",
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Classement des chaînes
    st.subheader("Classement des chaînes")
    if chain_costs:
        sorted_chains = sorted(chain_costs.items(), key=lambda x: x[1])
        for i, (chain, cost) in enumerate(sorted_chains):
            medal = ["🥇","🥈","🥉"][i] if i < 3 else f"#{i+1}"
            st.markdown(f"**{medal} Chaîne {chain}** — {cost:.2f} € de coût total")

    st.divider()

    # Tableau complet
    if players:
        st.subheader("Détail par joueur")
        df = pd.DataFrame(players)
        df.columns = ["Chaîne","Rôle","Joueur","Coût total (€)"]
        df = df.sort_values("Coût total (€)")
        st.dataframe(df, use_container_width=True, hide_index=True,
                     column_config={
                         "Coût total (€)": st.column_config.NumberColumn(format="%.2f €")
                     })

    st.divider()
    st.subheader("Enseignements pédagogiques")
    st.markdown("""
**L'effet Bullwhip en action** : la demande client variait légèrement,
mais les commandes du Fabricant ont oscillé bien plus fortement.
Pourquoi ?

- **Manque de visibilité** : chaque maillon ne voit que la demande de son voisin direct.
- **Ajustement des stocks** : face à l'incertitude, on commande plus "pour être sûr".
- **Délais de livraison** : l'information tarde à remonter la chaîne.

**Solutions réelles** : partage d'information en temps réel (EDI, VMI),
réduction des délais, réapprovisionnement sur signal de vente réel (Vendor Managed Inventory).
    """)

    if st.button("← Retour à l'accueil"):
        for k in ["player_id","page","order_history","order_sent","current_state"]:
            if k in ss:
                del st.session_state[k]
        ss["page"] = "home"
        st.rerun()

# ── ROUTEUR PRINCIPAL ────────────────────────────────────────

page = ss.get("page", "home")

if   page == "home":               page_home()
elif page == "join":               page_join()
elif page == "play":               page_play()
elif page == "facilitator_login":  page_facilitator_login()
elif page == "facilitator":        page_facilitator()
elif page == "results":            page_results()
else:
    ss["page"] = "home"; st.rerun()
