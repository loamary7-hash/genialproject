"""
game_engine.py — Moteur de simulation Bullwhip Effect
======================================================
Moteur complet, modulaire, testable sans interface.
Compatible Streamlit + Apps Script backend.

Architecture :
  BullwhipEngine      → orchestrateur principal
  Actor               → état d'un maillon de la chaîne
  Pipeline            → file de livraisons en transit
  DemandGenerator     → scénarios de demande client
  EventManager        → perturbations aléatoires
  Calendar            → calendrier saisonnier
  PedagogyEngine      → feedback pédagogique temps réel
  SimLogger           → logs structurés
"""

from __future__ import annotations

import random
import math
import logging
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Optional

# ──────────────────────────────────────────────────────────────────────────────
# CONSTANTES GLOBALES
# ──────────────────────────────────────────────────────────────────────────────

ROLES = ["Détaillant", "Grossiste", "Distributeur", "Fabricant"]

# Lead times par maillon (semaines)
LEAD_TIMES: dict[str, int] = {
    "Détaillant":   1,   # Grossiste → Détaillant
    "Grossiste":    2,   # Distributeur → Grossiste
    "Distributeur": 2,   # Fabricant → Distributeur
    "Fabricant":    3,   # Production → Fabricant
}

# Coûts unitaires
COST_STOCK   = 0.15   # €/unité/semaine en stock
COST_BACKLOG = 0.50   # €/unité/semaine en rupture

# Stock initial identique pour tous
INIT_STOCK   = 12
INIT_DEMAND  = 4      # demande stable de départ

# Total semaines
TOTAL_WEEKS  = 20

# ──────────────────────────────────────────────────────────────────────────────
# LOGGER
# ──────────────────────────────────────────────────────────────────────────────

logging.basicConfig(level=logging.DEBUG, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("BullwhipEngine")


# ──────────────────────────────────────────────────────────────────────────────
# PIPELINE
# ──────────────────────────────────────────────────────────────────────────────

class Pipeline:
    """
    File FIFO des livraisons en transit.
    Chaque slot = une semaine de délai.
    pipeline[0] = livraison prévue la semaine prochaine.
    """

    def __init__(self, lead_time: int, init_value: int = INIT_DEMAND):
        self.lead_time = max(1, lead_time)
        # Pré-remplir le pipeline avec la demande initiale
        self._slots: list[int] = [init_value] * self.lead_time

    def advance(self) -> int:
        """Avance d'une semaine : retourne la livraison qui arrive."""
        delivery = self._slots.pop(0) if self._slots else 0
        self._slots.append(0)          # nouveau slot vide en queue
        return delivery

    def push(self, qty: int) -> None:
        """Enregistre une commande ; arrive dans lead_time semaines."""
        if self._slots:
            self._slots[-1] += qty
        else:
            self._slots = [qty]

    def peek_next(self) -> int:
        """Livraison prévue la semaine prochaine (sans consommer)."""
        return self._slots[0] if self._slots else 0

    def total_in_transit(self) -> int:
        return sum(self._slots)

    def snapshot(self) -> list[int]:
        return list(self._slots)

    def __repr__(self) -> str:
        return f"Pipeline(lead={self.lead_time}, slots={self._slots})"


# ──────────────────────────────────────────────────────────────────────────────
# ACTEUR
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class Actor:
    """
    Représente un maillon de la chaîne logistique.
    Gère son propre stock, backlog, pipeline et historique.
    """
    role: str
    player_name: str = "IA"
    is_human: bool = False

    stock: int = INIT_STOCK
    backlog: int = 0
    total_cost: float = 0.0

    pipeline: Pipeline = field(init=False)

    # Historiques
    hist_stock:    list[int]   = field(default_factory=list)
    hist_backlog:  list[int]   = field(default_factory=list)
    hist_orders:   list[int]   = field(default_factory=list)
    hist_incoming: list[int]   = field(default_factory=list)
    hist_delivery: list[int]   = field(default_factory=list)
    hist_cost:     list[float] = field(default_factory=list)

    # Multiplicateur d'événement sur le lead time
    lead_time_multiplier: float = 1.0

    def __post_init__(self):
        lt = LEAD_TIMES.get(self.role, 2)
        self.pipeline = Pipeline(lead_time=lt, init_value=INIT_DEMAND)

    def effective_lead_time(self) -> int:
        base = LEAD_TIMES.get(self.role, 2)
        return max(1, round(base * self.lead_time_multiplier))

    # ── Cycle hebdomadaire ───────────────────────────────────────────────────

    def step_receive_delivery(self) -> int:
        """Étape 1 : recevoir les livraisons arrivant ce tour."""
        delivery = self.pipeline.advance()
        self.stock += delivery
        self.hist_delivery.append(delivery)
        logger.debug(f"[{self.role}] +{delivery} livraison → stock={self.stock}")
        return delivery

    def step_fulfill_demand(self, incoming_demand: int) -> int:
        """
        Étapes 2–4 : recevoir la demande, expédier, mettre à jour backlog.
        Retourne la quantité réellement expédiée.
        """
        self.hist_incoming.append(incoming_demand)
        total_needed = incoming_demand + self.backlog
        shipped      = min(self.stock, total_needed)
        self.stock  -= shipped
        self.backlog = total_needed - shipped
        logger.debug(
            f"[{self.role}] demande={incoming_demand}, expédié={shipped}, "
            f"backlog={self.backlog}, stock={self.stock}"
        )
        return shipped

    def step_compute_cost(self) -> float:
        """Étape 5 : calculer et enregistrer les coûts de la semaine."""
        week_cost     = self.stock * COST_STOCK + self.backlog * COST_BACKLOG
        self.total_cost += week_cost
        self.hist_cost.append(round(week_cost, 2))
        self.hist_stock.append(self.stock)
        self.hist_backlog.append(self.backlog)
        return week_cost

    def step_place_order(self, order_qty: int) -> None:
        """Étapes 6–7 : décider et injecter la commande dans le pipeline."""
        order_qty = max(0, int(order_qty))
        self.hist_orders.append(order_qty)
        # Ajustement du pipeline si le lead time a changé (événement)
        new_lt = self.effective_lead_time()
        if new_lt != self.pipeline.lead_time:
            self.pipeline.lead_time = new_lt
            # Étendre ou réduire les slots si besoin
            diff = new_lt - len(self.pipeline._slots)
            if diff > 0:
                self.pipeline._slots.extend([0] * diff)
            elif diff < 0:
                # On absorbe les livraisons perdues dans le stock
                absorbed = sum(self.pipeline._slots[new_lt:])
                self.pipeline._slots = self.pipeline._slots[:new_lt]
                self.stock += absorbed
        self.pipeline.push(order_qty)
        logger.debug(f"[{self.role}] commande={order_qty}, pipeline={self.pipeline}")

    # ── Politique IA ─────────────────────────────────────────────────────────

    def ai_order(self, incoming_demand: int, echelon_index: int) -> int:
        """
        Politique Order-Up-To avec amplification croissante par échelon.
        Simule le comportement humain naturellement biaisé → Bullwhip Effect.
        """
        amplification = [1.0, 1.35, 1.70, 2.10]
        amp   = amplification[min(echelon_index, 3)]
        lt    = self.effective_lead_time()
        # Stock de sécurité = lead_time × demande estimée
        safety_stock  = lt * incoming_demand * amp
        # Order-Up-To policy
        target = safety_stock - self.stock - self.pipeline.total_in_transit() + incoming_demand + self.backlog
        noise  = random.randint(-1, 2) * amp
        order  = max(0, int(target + noise))
        logger.debug(f"[{self.role}][IA] amp={amp:.2f} → commande IA={order}")
        return order

    # ── Helpers ──────────────────────────────────────────────────────────────

    def snapshot(self) -> dict:
        return {
            "role":            self.role,
            "player_name":     self.player_name,
            "is_human":        self.is_human,
            "stock":           self.stock,
            "backlog":         self.backlog,
            "total_cost":      round(self.total_cost, 2),
            "pending_delivery": self.pipeline.peek_next(),
            "pipeline":        self.pipeline.snapshot(),
            "lead_time":       self.effective_lead_time(),
        }


# ──────────────────────────────────────────────────────────────────────────────
# CALENDRIER SAISONNIER
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class CalendarEvent:
    week: int
    name: str
    description: str
    demand_multiplier: float = 1.0
    emoji: str = "📅"


CALENDAR_EVENTS: list[CalendarEvent] = [
    CalendarEvent(3,  "Soldes d'hiver",      "Les soldes boostent les ventes en magasin.",  1.4, "🛍️"),
    CalendarEvent(5,  "Saint-Valentin",       "Légère hausse sur les cadeaux et fleurs.",    1.2, "💝"),
    CalendarEvent(8,  "Jours fériés de mai",  "Ralentissement des livraisons.",              0.8, "🏖️"),
    CalendarEvent(10, "Rentrée scolaire",     "Forte hausse de la demande en fournitures.",  1.5, "✏️"),
    CalendarEvent(12, "Black Friday",         "Pic de demande exceptionnel.",                2.0, "🔥"),
    CalendarEvent(14, "Noël approche",        "Demande soutenue avant les fêtes.",           1.7, "🎄"),
    CalendarEvent(16, "Après Noël",           "Retour à la normale post-fêtes.",             0.7, "📉"),
    CalendarEvent(18, "Soldes d'été",         "Légère reprise des achats.",                  1.3, "☀️"),
    CalendarEvent(20, "Fin d'année fiscale",  "Commandes de clôture de bilan.",              1.2, "📊"),
]


class Calendar:
    def __init__(self):
        self._index: dict[int, CalendarEvent] = {e.week: e for e in CALENDAR_EVENTS}

    def get_event(self, week: int) -> Optional[CalendarEvent]:
        return self._index.get(week)

    def demand_multiplier(self, week: int) -> float:
        ev = self.get_event(week)
        return ev.demand_multiplier if ev else 1.0


# ──────────────────────────────────────────────────────────────────────────────
# GÉNÉRATEUR DE DEMANDE
# ──────────────────────────────────────────────────────────────────────────────

class DemandGenerator:
    """
    Génère la demande client sur TOTAL_WEEKS semaines.
    Plusieurs scénarios disponibles, reproduisibles via seed.
    """

    SCENARIOS = {
        "stable":     "Demande stable autour de 4–5 unités avec léger bruit.",
        "croissance":  "Croissance progressive avec un pic de Noël.",
        "pic":         "Choc unique semaine 5 (+100%), puis retour à la normale.",
        "volatile":    "Demande très erratique, forte incertitude.",
        "declin":      "Décroissance progressive du marché.",
    }

    def __init__(self, scenario: str = "pic", seed: Optional[int] = None):
        self.scenario = scenario if scenario in self.SCENARIOS else "pic"
        self.seed     = seed
        self.calendar = Calendar()
        if seed is not None:
            random.seed(seed)
        self._sequence: list[int] = self._generate()

    def _generate(self) -> list[int]:
        fn = {
            "stable":     self._stable,
            "croissance":  self._growth,
            "pic":         self._shock,
            "volatile":    self._volatile,
            "declin":      self._decline,
        }[self.scenario]
        base = fn()

        # Appliquer les multiplicateurs calendrier
        result = []
        for w, d in enumerate(base, start=1):
            mult = self.calendar.demand_multiplier(w)
            result.append(max(1, round(d * mult)))
        return result

    def _stable(self) -> list[int]:
        return [max(1, 4 + random.randint(-1, 1)) for _ in range(TOTAL_WEEKS)]

    def _shock(self) -> list[int]:
        seq = []
        for w in range(1, TOTAL_WEEKS + 1):
            if w <= 4:
                seq.append(4)
            elif w == 5:
                seq.append(8)      # le choc
            else:
                seq.append(max(1, 8 + random.randint(-1, 2)))
        return seq

    def _growth(self) -> list[int]:
        seq = []
        for w in range(1, TOTAL_WEEKS + 1):
            trend = 3 + w * 0.4
            noise = random.randint(-1, 2)
            seq.append(max(1, round(trend + noise)))
        return seq

    def _volatile(self) -> list[int]:
        seq = []
        for w in range(1, TOTAL_WEEKS + 1):
            base  = 5 + round(3 * math.sin(w * 0.7))
            noise = random.randint(-3, 4)
            seq.append(max(1, base + noise))
        return seq

    def _decline(self) -> list[int]:
        seq = []
        for w in range(1, TOTAL_WEEKS + 1):
            trend = max(1, 10 - w * 0.35)
            noise = random.randint(-1, 1)
            seq.append(max(1, round(trend + noise)))
        return seq

    def get(self, week: int) -> int:
        """Retourne la demande de la semaine (1-indexed)."""
        idx = week - 1
        if 0 <= idx < len(self._sequence):
            return self._sequence[idx]
        return INIT_DEMAND

    def full_sequence(self) -> list[int]:
        return list(self._sequence)


# ──────────────────────────────────────────────────────────────────────────────
# ÉVÉNEMENTS PERTURBATEURS
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class GameEvent:
    week: int
    event_type: str        # "lead_time_increase" | "supply_cut" | "promo" | "crisis"
    role: str              # rôle affecté ("Tous" = tous)
    name: str
    description: str
    emoji: str = "⚡"
    magnitude: float = 1.0  # facteur d'amplification


class EventManager:
    """
    Génère et applique des événements perturbateurs sur la chaîne.
    Les événements sont visibles côté UI mais leur impact est réel.
    """

    EVENT_POOL = [
        {"type": "lead_time_increase", "role": "Fabricant",
         "name": "Grève portuaire",
         "desc": "Retard d'expédition : le lead time du Fabricant augmente de 2 semaines.",
         "emoji": "⛵", "magnitude": 2.0},

        {"type": "supply_cut",         "role": "Distributeur",
         "name": "Rupture fournisseur",
         "desc": "Le Distributeur ne reçoit aucune livraison cette semaine.",
         "emoji": "🚫", "magnitude": 0.0},

        {"type": "promo",              "role": "Tous",
         "name": "Promotion flash",
         "desc": "Une promo double la demande client cette semaine.",
         "emoji": "🔥", "magnitude": 2.0},

        {"type": "crisis",             "role": "Tous",
         "name": "Crise de marché",
         "desc": "La demande client chute de 50% pendant 2 semaines.",
         "emoji": "📉", "magnitude": 0.5},

        {"type": "lead_time_increase", "role": "Grossiste",
         "name": "Embouteillages logistiques",
         "desc": "Délai de livraison du Grossiste augmenté d'1 semaine.",
         "emoji": "🚛", "magnitude": 1.5},
    ]

    def __init__(self, seed: Optional[int] = None, enabled: bool = True):
        self.enabled = enabled
        if seed is not None:
            random.seed(seed + 42)
        self._events: list[GameEvent] = self._schedule()
        self._index: dict[int, list[GameEvent]] = {}
        for ev in self._events:
            self._index.setdefault(ev.week, []).append(ev)

    def _schedule(self) -> list[GameEvent]:
        if not self.enabled:
            return []
        events = []
        # Placer 2–3 événements sur la partie, jamais avant S4 ni après S18
        n_events = random.randint(2, 3)
        weeks_used: set[int] = set()
        pool_copy = list(self.EVENT_POOL)
        random.shuffle(pool_copy)

        for template in pool_copy[:n_events]:
            # Choisir une semaine libre
            candidates = [w for w in range(4, 19) if w not in weeks_used]
            if not candidates:
                break
            week = random.choice(candidates)
            weeks_used.add(week)
            events.append(GameEvent(
                week       = week,
                event_type = template["type"],
                role       = template["role"],
                name       = template["name"],
                description= template["desc"],
                emoji      = template["emoji"],
                magnitude  = template["magnitude"],
            ))
        logger.info(f"[EventManager] {len(events)} événements planifiés : {[e.week for e in events]}")
        return events

    def get_events(self, week: int) -> list[GameEvent]:
        return self._index.get(week, [])

    def apply_events(self, week: int, actors: list[Actor],
                     base_demand: int) -> tuple[int, list[GameEvent]]:
        """
        Applique les événements de la semaine.
        Retourne (demande modifiée, événements déclenchés).
        """
        triggered = self.get_events(week)
        modified_demand = base_demand

        for ev in triggered:
            logger.info(f"[EventManager] S{week} — {ev.emoji} {ev.name}")

            if ev.event_type == "promo" and ev.role == "Tous":
                modified_demand = round(base_demand * ev.magnitude)

            elif ev.event_type == "crisis" and ev.role == "Tous":
                modified_demand = round(base_demand * ev.magnitude)

            elif ev.event_type == "lead_time_increase":
                for actor in actors:
                    if ev.role == "Tous" or actor.role == ev.role:
                        actor.lead_time_multiplier = ev.magnitude
                        logger.info(f"[EventManager] Lead time {actor.role} ×{ev.magnitude}")

            elif ev.event_type == "supply_cut":
                for actor in actors:
                    if ev.role == "Tous" or actor.role == ev.role:
                        # Vider le pipeline entrant ce tour
                        if actor.pipeline._slots:
                            actor.pipeline._slots[0] = 0
                        logger.info(f"[EventManager] Livraison annulée pour {actor.role}")

        return max(1, modified_demand), triggered


# ──────────────────────────────────────────────────────────────────────────────
# MOTEUR PÉDAGOGIQUE
# ──────────────────────────────────────────────────────────────────────────────

class PedagogyEngine:
    """
    Analyse le comportement du joueur et génère des feedbacks pédagogiques
    en temps réel.
    """

    @staticmethod
    def analyze(actor: Actor, order_placed: int,
                incoming_demand: int) -> list[dict]:
        """
        Retourne une liste de messages feedback.
        Chaque message : {"type": "warning|danger|success|info", "text": str}
        """
        feedbacks = []
        if len(actor.hist_orders) < 2:
            return feedbacks

        last_orders = actor.hist_orders[-3:] if len(actor.hist_orders) >= 3 else actor.hist_orders
        avg_orders  = sum(last_orders) / len(last_orders) if last_orders else 0

        # 1. Amplification Bullwhip
        if len(actor.hist_incoming) >= 2:
            prev_in  = actor.hist_incoming[-2]
            curr_in  = incoming_demand
            delta_in = abs(curr_in - prev_in)
            delta_or = abs(order_placed - (actor.hist_orders[-2] if len(actor.hist_orders) >= 2 else order_placed))
            if delta_in > 0 and delta_or > delta_in * 2:
                feedbacks.append({
                    "type": "warning",
                    "text": f"🌊 Tu amplifias la demande : variation réelle +{delta_in}u → ta commande varie de +{delta_or}u. C'est l'effet Bullwhip !"
                })

        # 2. Surstockage
        lt = LEAD_TIMES.get(actor.role, 2)
        if actor.stock > incoming_demand * (lt + 3):
            feedbacks.append({
                "type": "warning",
                "text": f"📦 Surstockage : tu as {actor.stock}u en stock pour une demande de {incoming_demand}u. Tu paies {actor.stock * COST_STOCK:.2f}€ de holding cost inutiles."
            })

        # 3. Ignore le lead time
        in_transit = actor.pipeline.total_in_transit()
        if order_placed > 0 and actor.stock + in_transit > incoming_demand * (lt + 2) * 1.5:
            feedbacks.append({
                "type": "info",
                "text": f"⏱️ Tu ignores le pipeline : {in_transit}u déjà en transit. Avant de commander plus, attends les livraisons prévues."
            })

        # 4. Rupture répétée
        if actor.backlog > 0 and len(actor.hist_backlog) >= 3:
            if all(b > 0 for b in actor.hist_backlog[-3:]):
                feedbacks.append({
                    "type": "danger",
                    "text": f"🔴 Rupture répétée depuis 3 semaines ({actor.backlog}u en backlog). Augmente significativement ta commande pour rattraper le retard."
                })

        # 5. Bonne gestion
        if actor.backlog == 0 and actor.stock <= incoming_demand * 3 and actor.stock >= incoming_demand:
            feedbacks.append({
                "type": "success",
                "text": "✅ Bonne gestion ! Ton stock est équilibré et tu n'as pas de rupture."
            })

        return feedbacks

    @staticmethod
    def bullwhip_index(orders: list[int], demands: list[int]) -> Optional[float]:
        """Calcule le BWI = CV(commandes) / CV(demande)."""
        def cv(lst):
            n = len(lst)
            if n < 2:
                return 0.0
            mean = sum(lst) / n
            if mean == 0:
                return 0.0
            variance = sum((x - mean) ** 2 for x in lst) / n
            return math.sqrt(variance) / mean

        cv_orders  = cv(orders)
        cv_demands = cv(demands)
        if cv_demands == 0:
            return None
        return round(cv_orders / cv_demands, 2)

    @staticmethod
    def end_of_game_report(actors: list[Actor]) -> dict:
        """Rapport final avec analyse pédagogique par acteur."""
        report = {}
        for actor in actors:
            bwi = PedagogyEngine.bullwhip_index(
                actor.hist_orders,
                actor.hist_incoming or [INIT_DEMAND] * len(actor.hist_orders)
            )
            severity = "🟢 Faible" if (bwi or 0) < 1.5 else "🟡 Modéré" if (bwi or 0) < 3 else "🔴 Fort"
            report[actor.role] = {
                "bwi":           bwi,
                "severity":      severity,
                "total_cost":    round(actor.total_cost, 2),
                "avg_stock":     round(sum(actor.hist_stock) / max(len(actor.hist_stock), 1), 1),
                "total_backlog": sum(actor.hist_backlog),
                "player_name":   actor.player_name,
            }
        return report


# ──────────────────────────────────────────────────────────────────────────────
# MOTEUR PRINCIPAL
# ──────────────────────────────────────────────────────────────────────────────

class BullwhipEngine:
    """
    Orchestrateur principal du jeu.

    Usage :
        engine = BullwhipEngine(scenario="pic", seed=42)
        engine.set_human("Fabricant", "Amary")

        # Début de partie — semaine 1
        ctx = engine.get_week_context()
        engine.submit_order("Fabricant", 12)

        # Avancer la semaine quand tout le monde a joué
        engine.advance_week()
    """

    def __init__(
        self,
        scenario: str = "pic",
        seed: Optional[int] = None,
        events_enabled: bool = True,
        total_weeks: int = TOTAL_WEEKS,
    ):
        self.seed          = seed
        self.scenario      = scenario
        self.total_weeks   = total_weeks
        self.current_week  = 1
        self.phase         = "waiting"   # waiting | playing | finished

        # Sous-systèmes
        self.demand_gen    = DemandGenerator(scenario=scenario, seed=seed)
        self.event_manager = EventManager(seed=seed, enabled=events_enabled)
        self.calendar      = Calendar()
        self.pedagogy      = PedagogyEngine()

        # Acteurs (tous IA par défaut)
        self.actors: dict[str, Actor] = {
            role: Actor(role=role, player_name="IA", is_human=False)
            for role in ROLES
        }

        # État du round en cours
        self._orders_this_round: dict[str, Optional[int]] = {r: None for r in ROLES}
        self._feedbacks_this_round: dict[str, list[dict]] = {r: [] for r in ROLES}
        self._events_this_round: list[GameEvent] = []

        # Log global
        self.week_logs: list[dict] = []

        logger.info(f"[Engine] Initialisé — scénario={scenario}, seed={seed}, events={events_enabled}")

    # ── Configuration ─────────────────────────────────────────────────────────

    def set_human(self, role: str, player_name: str) -> None:
        """Désigne un acteur comme humain (le reste reste IA)."""
        if role not in self.actors:
            raise ValueError(f"Rôle inconnu : {role}")
        self.actors[role].player_name = player_name
        self.actors[role].is_human    = True
        self.phase = "playing"
        logger.info(f"[Engine] Joueur humain : {player_name} → {role}")

    # ── Contexte semaine ──────────────────────────────────────────────────────

    def get_week_context(self, role: Optional[str] = None) -> dict:
        """
        Retourne le contexte de la semaine courante pour un rôle donné
        (ou tous les rôles si role=None).
        Inclut : état acteur, événements, demande client (si Détaillant),
        feedback joueur précédent.
        """
        base_demand = self.demand_gen.get(self.current_week)
        cal_event   = self.calendar.get_event(self.current_week)
        game_events = self.event_manager.get_events(self.current_week)

        ctx = {
            "week":         self.current_week,
            "total_weeks":  self.total_weeks,
            "phase":        self.phase,
            "base_demand":  base_demand,
            "calendar_event": {
                "name":  cal_event.name,
                "desc":  cal_event.description,
                "emoji": cal_event.emoji,
                "multiplier": cal_event.demand_multiplier,
            } if cal_event else None,
            "game_events": [
                {
                    "name":   e.name,
                    "desc":   e.description,
                    "emoji":  e.emoji,
                    "role":   e.role,
                    "type":   e.event_type,
                }
                for e in game_events
            ],
            "actors": {},
        }

        target_roles = [role] if role else list(ROLES)
        for r in target_roles:
            actor = self.actors[r]
            ctx["actors"][r] = {
                **actor.snapshot(),
                "order_submitted":  self._orders_this_round.get(r) is not None,
                "feedbacks":        self._feedbacks_this_round.get(r, []),
                "incoming_demand":  self._get_incoming_demand(r),
            }

        return ctx

    def _get_incoming_demand(self, role: str) -> int:
        """
        Retourne la demande entrante estimée pour un rôle.
        Détaillant → demande client (avec multiplicateur).
        Autres → dernière commande de l'acteur aval (si jouée) ou IA.
        """
        idx = ROLES.index(role)
        if idx == 0:
            base = self.demand_gen.get(self.current_week)
            mult = self.calendar.demand_multiplier(self.current_week)
            return max(1, round(base * mult))
        downstream_role  = ROLES[idx - 1]
        downstream_order = self._orders_this_round.get(downstream_role)
        if downstream_order is not None:
            return downstream_order
        # Estimation basée sur l'historique
        hist = self.actors[downstream_role].hist_orders
        return hist[-1] if hist else INIT_DEMAND

    # ── Soumission de commande ────────────────────────────────────────────────

    def submit_order(self, role: str, order_qty: int) -> dict:
        """
        Enregistre la commande d'un joueur pour ce round.
        Retourne un feedback immédiat.
        """
        if role not in self.actors:
            return {"error": f"Rôle inconnu : {role}"}
        if self._orders_this_round.get(role) is not None:
            return {"error": "Commande déjà soumise ce round."}
        if self.current_week > self.total_weeks:
            return {"error": "Partie terminée."}

        order_qty = max(0, int(order_qty))
        self._orders_this_round[role] = order_qty

        incoming = self._get_incoming_demand(role)
        feedbacks = self.pedagogy.analyze(self.actors[role], order_qty, incoming)
        self._feedbacks_this_round[role] = feedbacks

        logger.info(f"[Engine] S{self.current_week} {role} commande {order_qty}u")
        return {
            "success":   True,
            "role":      role,
            "order_qty": order_qty,
            "feedbacks": feedbacks,
            "all_submitted": self._all_submitted(),
        }

    def _all_submitted(self) -> bool:
        return all(v is not None for v in self._orders_this_round.values())

    def pending_roles(self) -> list[str]:
        return [r for r, v in self._orders_this_round.items() if v is None]

    # ── Avancement de la semaine ──────────────────────────────────────────────

    def advance_week(self, auto_ai: bool = True) -> dict:
        """
        Traite la semaine complète :
        1. Compléter les IA pour les rôles non soumis
        2. Appliquer les événements
        3. Traiter chaque acteur dans l'ordre (Détaillant → Fabricant)
        4. Logger le round
        5. Avancer le compteur

        Retourne un résumé du round.
        """
        if self.current_week > self.total_weeks:
            return {"error": "Partie déjà terminée."}

        # Compléter les commandes IA
        if auto_ai:
            for i, role in enumerate(ROLES):
                if self._orders_this_round[role] is None:
                    incoming = self._get_incoming_demand(role)
                    ai_order = self.actors[role].ai_order(incoming, i)
                    self._orders_this_round[role] = ai_order
                    logger.debug(f"[Engine] IA {role} → {ai_order}u")

        # Appliquer les événements de la semaine
        base_demand = self.demand_gen.get(self.current_week)
        effective_demand, triggered = self.event_manager.apply_events(
            self.current_week,
            list(self.actors.values()),
            base_demand,
        )
        self._events_this_round = triggered

        # Traitement dans l'ordre Détaillant → Fabricant
        round_summary: dict[str, dict] = {}

        for i, role in enumerate(ROLES):
            actor    = self.actors[role]
            order_to_place = self._orders_this_round[role]  # type: ignore

            # Étape 1 : recevoir livraison
            delivery = actor.step_receive_delivery()

            # Étape 2–4 : traiter la demande entrante
            if i == 0:
                incoming = effective_demand
            else:
                upstream_order = self._orders_this_round.get(ROLES[i - 1], INIT_DEMAND)
                incoming = upstream_order or INIT_DEMAND  # type: ignore
            shipped = actor.step_fulfill_demand(incoming)

            # Étape 5 : calculer coûts
            week_cost = actor.step_compute_cost()

            # Étapes 6–7 : passer la commande
            actor.step_place_order(order_to_place)  # type: ignore

            round_summary[role] = {
                "delivery":  delivery,
                "incoming":  incoming,
                "shipped":   shipped,
                "order":     order_to_place,
                "stock":     actor.stock,
                "backlog":   actor.backlog,
                "week_cost": round(week_cost, 2),
                "total_cost": round(actor.total_cost, 2),
            }

        # Logger le round
        log_entry = {
            "week":           self.current_week,
            "client_demand":  effective_demand,
            "events":         [e.name for e in triggered],
            "actors":         round_summary,
        }
        self.week_logs.append(log_entry)
        logger.info(f"[Engine] S{self.current_week} terminée — demande client={effective_demand}")

        # Réinitialiser pour le prochain round
        self._orders_this_round   = {r: None for r in ROLES}
        self._feedbacks_this_round = {r: [] for r in ROLES}

        # Avancer
        self.current_week += 1
        if self.current_week > self.total_weeks:
            self.phase = "finished"
            logger.info("[Engine] Partie terminée.")

        return {
            "success":        True,
            "processed_week": self.current_week - 1,
            "new_week":       self.current_week,
            "phase":          self.phase,
            "round_summary":  round_summary,
            "events":         [{"name": e.name, "emoji": e.emoji, "desc": e.description} for e in triggered],
            "client_demand":  effective_demand,
        }

    # ── Résultats finaux ──────────────────────────────────────────────────────

    def get_results(self) -> dict:
        """Résultats complets + analyse pédagogique finale."""
        actors_list = list(self.actors.values())
        report      = self.pedagogy.end_of_game_report(actors_list)

        chain_demand = self.demand_gen.full_sequence()
        chain_orders = {
            role: actor.hist_orders
            for role, actor in self.actors.items()
        }

        chain_costs = {}
        for role, actor in self.actors.items():
            chain_costs[role] = round(actor.total_cost, 2)

        return {
            "week_logs":     self.week_logs,
            "chain_demand":  chain_demand,
            "chain_orders":  chain_orders,
            "chain_costs":   chain_costs,
            "actor_report":  report,
            "scenario":      self.scenario,
            "seed":          self.seed,
            "calendar_events": [
                {"week": e.week, "name": e.name, "emoji": e.emoji}
                for e in CALENDAR_EVENTS
            ],
            "game_events": [
                {"week": e.week, "name": e.name, "emoji": e.emoji, "role": e.role}
                for e in self.event_manager._events
            ],
        }

    # ── Sérialisation ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        """Sérialise l'état complet pour persistance (session Streamlit)."""
        return {
            "seed":          self.seed,
            "scenario":      self.scenario,
            "total_weeks":   self.total_weeks,
            "current_week":  self.current_week,
            "phase":         self.phase,
            "demand_seq":    self.demand_gen.full_sequence(),
            "orders_round":  self._orders_this_round,
            "week_logs":     self.week_logs,
            "actors": {
                role: {
                    "player_name":   a.player_name,
                    "is_human":      a.is_human,
                    "stock":         a.stock,
                    "backlog":       a.backlog,
                    "total_cost":    a.total_cost,
                    "pipeline":      a.pipeline.snapshot(),
                    "lead_mult":     a.lead_time_multiplier,
                    "hist_stock":    a.hist_stock,
                    "hist_backlog":  a.hist_backlog,
                    "hist_orders":   a.hist_orders,
                    "hist_incoming": a.hist_incoming,
                    "hist_delivery": a.hist_delivery,
                    "hist_cost":     a.hist_cost,
                }
                for role, a in self.actors.items()
            },
            "events": [
                {"week": e.week, "type": e.event_type, "role": e.role,
                 "name": e.name, "desc": e.description, "emoji": e.emoji,
                 "magnitude": e.magnitude}
                for e in self.event_manager._events
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BullwhipEngine":
        """Restaure un moteur depuis un état sérialisé."""
        engine = cls.__new__(cls)
        engine.seed         = data["seed"]
        engine.scenario     = data["scenario"]
        engine.total_weeks  = data["total_weeks"]
        engine.current_week = data["current_week"]
        engine.phase        = data["phase"]
        engine.calendar     = Calendar()
        engine.pedagogy     = PedagogyEngine()
        engine.week_logs    = data["week_logs"]
        engine._orders_this_round   = data.get("orders_round", {r: None for r in ROLES})
        engine._feedbacks_this_round = {r: [] for r in ROLES}
        engine._events_this_round   = []

        # Restaurer le générateur de demande
        engine.demand_gen = DemandGenerator.__new__(DemandGenerator)
        engine.demand_gen.scenario  = data["scenario"]
        engine.demand_gen.seed      = data["seed"]
        engine.demand_gen.calendar  = Calendar()
        engine.demand_gen._sequence = data["demand_seq"]

        # Restaurer l'event manager sans régénérer les événements
        engine.event_manager = EventManager.__new__(EventManager)
        engine.event_manager.enabled = True
        engine.event_manager._events = [
            GameEvent(
                week=e["week"], event_type=e["type"], role=e["role"],
                name=e["name"], description=e["desc"], emoji=e["emoji"],
                magnitude=e["magnitude"]
            )
            for e in data.get("events", [])
        ]
        engine.event_manager._index = {}
        for ev in engine.event_manager._events:
            engine.event_manager._index.setdefault(ev.week, []).append(ev)

        # Restaurer les acteurs
        engine.actors = {}
        for role, ad in data["actors"].items():
            lt = LEAD_TIMES.get(role, 2)
            a  = Actor.__new__(Actor)
            a.role               = role
            a.player_name        = ad["player_name"]
            a.is_human           = ad["is_human"]
            a.stock              = ad["stock"]
            a.backlog            = ad["backlog"]
            a.total_cost         = ad["total_cost"]
            a.lead_time_multiplier = ad.get("lead_mult", 1.0)
            a.hist_stock         = ad["hist_stock"]
            a.hist_backlog       = ad["hist_backlog"]
            a.hist_orders        = ad["hist_orders"]
            a.hist_incoming      = ad["hist_incoming"]
            a.hist_delivery      = ad["hist_delivery"]
            a.hist_cost          = ad["hist_cost"]
            a.pipeline           = Pipeline(lead_time=lt)
            a.pipeline._slots    = ad["pipeline"]
            engine.actors[role]  = a

        logger.info(f"[Engine] Restauré — S{engine.current_week}, phase={engine.phase}")
        return engine


# ──────────────────────────────────────────────────────────────────────────────
# TESTS RAPIDES (sans interface)
# ──────────────────────────────────────────────────────────────────────────────

def _run_headless_test():
    """Simule une partie complète sans interface pour valider le moteur."""
    print("\n" + "="*60)
    print("TEST MOTEUR BULLWHIP — partie complète en mode IA")
    print("="*60)

    engine = BullwhipEngine(scenario="pic", seed=2025, events_enabled=True)
    engine.set_human("Fabricant", "Amary")

    for week in range(1, TOTAL_WEEKS + 1):
        ctx = engine.get_week_context()
        assert ctx["week"] == week

        # Simuler la décision du joueur humain
        incoming = ctx["actors"]["Fabricant"]["incoming_demand"]
        order    = max(0, incoming + engine.actors["Fabricant"].backlog + 2)
        engine.submit_order("Fabricant", order)

        result = engine.advance_week(auto_ai=True)
        assert result.get("success"), f"Erreur S{week}: {result}"

        if result["events"]:
            print(f"  S{week} ⚡ Événement : {result['events'][0]['emoji']} {result['events'][0]['name']}")

    results = engine.get_results()
    print("\n📊 RAPPORT FINAL")
    print(f"{'Rôle':<15} {'BWI':>6} {'Coût total':>12} {'Backlog':>8}")
    print("-" * 45)
    for role, r in results["actor_report"].items():
        bwi = f"{r['bwi']:.2f}x" if r["bwi"] else "N/A"
        print(f"{role:<15} {bwi:>6} {r['total_cost']:>10.2f}€ {r['total_backlog']:>8}")

    # Test sérialisation/restauration
    state   = engine.to_dict()
    engine2 = BullwhipEngine.from_dict(state)
    assert engine2.current_week == engine.current_week
    assert engine2.phase        == engine.phase
    print("\n✅ Sérialisation/restauration OK")
    print("✅ Moteur validé — zéro erreur critique\n")


if __name__ == "__main__":
    _run_headless_test()