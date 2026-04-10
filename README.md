# Bullwhip Game – Guide d'installation
## Stack : Google Sheets + Apps Script + Streamlit

---

## Étape 1 – Créer le Google Sheet

1. Aller sur https://sheets.google.com → Nouveau spreadsheet
2. Nommer-le "Bullwhip Game ESLI"
3. Menu : Extensions > Apps Script

---

## Étape 2 – Coller les fichiers Apps Script

Dans l'éditeur Apps Script :

1. Remplacer le contenu de `Code.gs` par le contenu du fichier `Code.gs`
2. Créer un nouveau fichier : **Fichier > Nouveau > Script** → nommer `Setup`
3. Coller le contenu de `Setup.gs`
4. Sauvegarder (Ctrl+S)

---

## Étape 3 – Initialiser le Sheet

1. Dans l'éditeur Apps Script, sélectionner la fonction `setupSpreadsheet`
2. Cliquer sur **Exécuter**
3. Autoriser les permissions (compte Google)
4. Une popup affiche l'**ID du Spreadsheet** → copier cet ID

---

## Étape 4 – Configurer Code.gs

Ouvrir `Code.gs` et remplacer :
```javascript
var SS_ID = ""; // ← Coller ici l'ID du Spreadsheet
```
par
```javascript
var SS_ID = "1BxiMV...VOTRE_ID...abc";
```

---

## Étape 5 – Déployer la Web App

1. Dans Apps Script : **Déployer > Nouveau déploiement**
2. Type : **Application Web**
3. Paramètres :
   - Exécuter en tant que : **Moi**
   - Qui peut accéder : **Tout le monde** (anonymous)
4. Cliquer **Déployer** → copier l'URL fournie

---

## Étape 6 – Configurer Streamlit

Dans `bullwhip_game.py`, remplacer :
```python
APPS_SCRIPT_URL = "https://script.google.com/macros/s/VOTRE_ID_ICI/exec"
```
par l'URL copiée à l'étape 5.

---

## Étape 7 – Lancer l'app

```bash
pip install -r requirements.txt
streamlit run bullwhip_game.py
```

Ouvre sur : http://localhost:8501

---

## Créer une session de cours

### Option A – Via Apps Script
1. Dans l'éditeur Apps Script, exécuter `createTestSession`
2. Cela crée la session **BW-2025** avec clé **FAC-SECRET**

### Option B – Via l'interface
1. Ouvrir http://localhost:8501
2. Espace facilitateur > Créer une nouvelle session
3. Choisir un code (ex. **ESLI-S1**) et une clé secrète

---

## Partager avec les étudiants

1. Déployer Streamlit sur **Streamlit Cloud** (gratuit) :
   - https://share.streamlit.io
   - Connecter ton repo GitHub
   - Ajouter `APPS_SCRIPT_URL` dans les secrets Streamlit

2. Partager le lien + le code session aux étudiants

---

## Architecture des données (Google Sheet)

| Feuille      | Contenu                              |
|--------------|--------------------------------------|
| Sessions     | Sessions actives, semaine courante   |
| Joueurs      | Un joueur par ligne, état du stock   |
| Commandes    | Toutes les commandes (historique)    |
| Config       | Paramètres modifiables               |
| Dashboard    | Formules de synthèse (lecture seule) |

---

## Personnaliser le jeu

Dans `Code.gs`, modifier les constantes :
```javascript
var COST_STOCK    = 0.15;  // coût stock
var COST_BACKLOG  = 0.50;  // coût rupture
var TOTAL_WEEKS   = 20;    // durée de la partie
var DELIVERY_LEAD = 2;     // délai de livraison
```

Pour modifier la demande client (choc, saisonnalité) :
```javascript
function getClientDemand(week) {
  var base = [4,4,4,4,8,4,4,4,4,5,...];
  return base[week - 1] || 4;
}
```
