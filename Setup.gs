// ============================================================
//  BULLWHIP GAME – Setup du Google Sheet
//  Fichier : Setup.gs
//  Exécuter UNE SEULE FOIS : lancez setupSpreadsheet()
// ============================================================

function setupSpreadsheet() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();

  // Supprimer les feuilles existantes sauf la première
  var sheets = ss.getSheets();
  for (var i = sheets.length - 1; i > 0; i--) {
    ss.deleteSheet(sheets[i]);
  }
  sheets[0].setName("Sessions");

  // ── 1. Feuille Sessions ──────────────────────────────────
  var sesSheet = ss.getSheetByName("Sessions");
  sesSheet.clearContents();
  sesSheet.appendRow(["sessionCode","facilitatorKey","nbChains","currentWeek","status","createdAt"]);
  sesSheet.getRange(1,1,1,6).setFontWeight("bold").setBackground("#E1F5EE");
  sesSheet.setFrozenRows(1);
  sesSheet.setColumnWidth(1, 120);
  sesSheet.setColumnWidth(2, 160);

  // ── 2. Feuille Joueurs ───────────────────────────────────
  var pSheet = ss.insertSheet("Joueurs");
  pSheet.appendRow([
    "sessionCode","playerId","chain","role","playerName",
    "stock","backlog","pendingDelivery","totalCost","joinedAt"
  ]);
  pSheet.getRange(1,1,1,10).setFontWeight("bold").setBackground("#E6F1FB");
  pSheet.setFrozenRows(1);
  [1,2,4,5].forEach(function(c){ pSheet.setColumnWidth(c,120); });
  pSheet.setColumnWidth(3, 80);
  pSheet.setColumnWidth(6, 80);
  pSheet.setColumnWidth(7, 80);
  pSheet.setColumnWidth(8, 120);
  pSheet.setColumnWidth(9, 80);

  // ── 3. Feuille Commandes ─────────────────────────────────
  var oSheet = ss.insertSheet("Commandes");
  oSheet.appendRow([
    "sessionCode","week","chain","role","playerId",
    "incomingDemand","orderQty","stockAfter","backlogAfter","weekCost","timestamp"
  ]);
  oSheet.getRange(1,1,1,11).setFontWeight("bold").setBackground("#FAEEDA");
  oSheet.setFrozenRows(1);
  oSheet.setColumnWidth(1, 120);
  oSheet.setColumnWidth(2, 60);
  oSheet.setColumnWidth(5, 160);

  // ── 4. Feuille Config ────────────────────────────────────
  var cfSheet = ss.insertSheet("Config");
  cfSheet.appendRow(["Paramètre","Valeur","Description"]);
  cfSheet.getRange(1,1,1,3).setFontWeight("bold").setBackground("#F1EFE8");
  cfSheet.appendRow(["COST_STOCK",   0.15, "€ par unité en stock par semaine"]);
  cfSheet.appendRow(["COST_BACKLOG", 0.50, "€ par unité en rupture par semaine"]);
  cfSheet.appendRow(["TOTAL_WEEKS",  20,   "Nombre de semaines par partie"]);
  cfSheet.appendRow(["DELIVERY_LEAD",2,    "Délai de livraison (semaines)"]);
  cfSheet.appendRow(["INITIAL_STOCK",12,   "Stock initial de chaque joueur"]);
  cfSheet.setColumnWidth(1, 160);
  cfSheet.setColumnWidth(2, 80);
  cfSheet.setColumnWidth(3, 300);

  // ── 5. Feuille Dashboard (lecture humaine) ───────────────
  var dSheet = ss.insertSheet("Dashboard");
  setupDashboardFormulas(dSheet);

  // ── 6. Validation & mise en forme ───────────────────────
  var roles = ["Détaillant","Grossiste","Distributeur","Fabricant"];
  var roleRule = SpreadsheetApp.newDataValidation()
    .requireValueInList(roles, true)
    .setAllowInvalid(false)
    .build();
  pSheet.getRange(2, 4, 500, 1).setDataValidation(roleRule);

  var statusRule = SpreadsheetApp.newDataValidation()
    .requireValueInList(["waiting","playing","finished"], true)
    .build();
  sesSheet.getRange(2, 5, 100, 1).setDataValidation(statusRule);

  // Enregistrer l'ID du spreadsheet dans les propriétés
  var props = PropertiesService.getScriptProperties();
  props.setProperty("SS_ID", ss.getId());

  // Afficher l'URL de déploiement
  SpreadsheetApp.getUi().alert(
    "Setup terminé !\n\n" +
    "ID du Spreadsheet : " + ss.getId() + "\n\n" +
    "Prochaine étape :\n" +
    "1. Copier cet ID dans la variable SS_ID de Code.gs\n" +
    "2. Déployer en tant que Web App (Extensions > Apps Script > Déployer)\n" +
    "3. Copier l'URL de déploiement dans bullwhip_game.py"
  );
}

function setupDashboardFormulas(sheet) {
  sheet.clearContents();
  sheet.appendRow(["BULLWHIP GAME – Dashboard en direct"]);
  sheet.getRange(1,1).setFontSize(16).setFontWeight("bold");
  sheet.appendRow([]);
  sheet.appendRow(["Sessions actives :"]);
  sheet.appendRow(["=COUNTIF(Sessions!E:E,\"playing\")"]);
  sheet.appendRow(["Joueurs connectés :"]);
  sheet.appendRow(["=COUNTA(Joueurs!A:A)-1"]);
  sheet.appendRow(["Commandes enregistrées :"]);
  sheet.appendRow(["=COUNTA(Commandes!A:A)-1"]);
  sheet.appendRow([]);
  sheet.appendRow(["Pour voir le tableau complet, utilisez le dashboard Facilitateur dans l'app Streamlit."]);
  sheet.setColumnWidth(1, 400);
}

// ── Utilitaire : créer une session de test ─────────────────
function createTestSession() {
  var ss       = SpreadsheetApp.getActiveSpreadsheet();
  var sesSheet = ss.getSheetByName("Sessions");
  var pSheet   = ss.getSheetByName("Joueurs");

  sesSheet.appendRow(["BW-2025","FAC-SECRET",3,1,"waiting",new Date()]);

  var roles  = ["Détaillant","Grossiste","Distributeur","Fabricant"];
  var chains = ["A","B","C"];

  chains.forEach(function(chain) {
    roles.forEach(function(role, idx) {
      pSheet.appendRow([
        "BW-2025",
        Utilities.getUuid(),
        chain, role,
        "Joueur " + chain + (idx+1),
        12, 0, 4, 0,
        new Date()
      ]);
    });
  });

  SpreadsheetApp.getUi().alert("Session de test BW-2025 créée avec 3 chaînes × 4 joueurs.");
}
