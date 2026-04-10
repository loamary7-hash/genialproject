// ============================================================
//  BULLWHIP GAME – Apps Script Backend
//  Fichier : Code.gs
//  Déployer en tant que : Web App (accès à tous, anonyme)
// ============================================================

var SS_ID = ""; // ← Coller ici l'ID de ton Google Sheet après setup
var SHEET_SESSIONS  = "Sessions";
var SHEET_PLAYERS   = "Joueurs";
var SHEET_ORDERS    = "Commandes";
var SHEET_CONFIG    = "Config";

// Coûts par unité
var COST_STOCK    = 0.15;  // € par unité en stock par semaine
var COST_BACKLOG  = 0.50;  // € par unité en rupture par semaine
var TOTAL_WEEKS   = 20;
var DELIVERY_LEAD = 2;     // délai de livraison en semaines

// ------------------------------------------------------------
//  POINT D'ENTRÉE HTTP
// ------------------------------------------------------------

function doGet(e) {
  var action = e.parameter.action;
  var result;

  try {
    if      (action === "getState")      result = getPlayerState(e);
    else if (action === "getSession")    result = getSessionInfo(e);
    else if (action === "getFacDashboard") result = getFacilitatorDashboard(e);
    else if (action === "getResults")    result = getResults(e);
    else result = { error: "Action inconnue : " + action };
  } catch(err) {
    result = { error: err.message };
  }

  return ContentService
    .createTextOutput(JSON.stringify(result))
    .setMimeType(ContentService.MimeType.JSON);
}

function doPost(e) {
  var data   = JSON.parse(e.postData.contents);
  var action = data.action;
  var result;

  try {
    if      (action === "joinSession")   result = joinSession(data);
    else if (action === "submitOrder")   result = submitOrder(data);
    else if (action === "advanceWeek")   result = advanceWeek(data);
    else if (action === "resetSession")  result = resetSession(data);
    else if (action === "createSession") result = createSession(data);
    else result = { error: "Action inconnue : " + action };
  } catch(err) {
    result = { error: err.message };
  }

  return ContentService
    .createTextOutput(JSON.stringify(result))
    .setMimeType(ContentService.MimeType.JSON);
}

// ------------------------------------------------------------
//  ACTIONS – JOUEUR
// ------------------------------------------------------------

/**
 * Rejoindre une session
 * POST { action, sessionCode, playerName, chain, role }
 */
function joinSession(data) {
  var ss      = SpreadsheetApp.openById(SS_ID);
  var sheet   = ss.getSheetByName(SHEET_PLAYERS);
  var rows    = sheet.getDataRange().getValues();

  // Vérifier si le joueur existe déjà
  for (var i = 1; i < rows.length; i++) {
    if (rows[i][0] === data.sessionCode &&
        rows[i][2] === data.chain &&
        rows[i][3] === data.role) {
      return { error: "Ce rôle est déjà pris dans cette chaîne." };
    }
  }

  var playerId = Utilities.getUuid();
  var now      = new Date();

  // Colonnes : sessionCode | playerId | chain | role | playerName | stock | backlog | pendingDelivery | totalCost | joinedAt
  sheet.appendRow([
    data.sessionCode,
    playerId,
    data.chain,
    data.role,
    data.playerName,
    12,    // stock initial
    0,     // backlog initial
    4,     // livraison initiale (pipeline)
    0,     // coût total
    now
  ]);

  return {
    success: true,
    playerId: playerId,
    stock: 12,
    backlog: 0,
    pendingDelivery: 4,
    totalCost: 0
  };
}

/**
 * Soumettre une commande
 * POST { action, sessionCode, playerId, orderQty }
 */
function submitOrder(data) {
  var ss      = SpreadsheetApp.openById(SS_ID);
  var pSheet  = ss.getSheetByName(SHEET_PLAYERS);
  var oSheet  = ss.getSheetByName(SHEET_ORDERS);
  var sesSheet = ss.getSheetByName(SHEET_SESSIONS);

  // Lire la session courante
  var session = getSessionRow(sesSheet, data.sessionCode);
  if (!session) return { error: "Session introuvable." };
  var currentWeek = session.currentWeek;

  // Lire l'état du joueur
  var pRow  = findPlayerRow(pSheet, data.playerId);
  if (!pRow) return { error: "Joueur introuvable." };

  var pData = pSheet.getRange(pRow, 1, 1, 10).getValues()[0];
  var chain = pData[2];
  var role  = pData[3];
  var stock = pData[5];
  var backlog = pData[6];
  var delivery = pData[7];
  var totalCost = pData[8];

  // Calculer la demande entrant (commande du maillon aval)
  var incomingDemand = getIncomingDemand(ss, data.sessionCode, chain, role, currentWeek);

  // Appliquer la mécanique de stock
  var newStock   = stock + delivery - incomingDemand;
  var newBacklog = 0;
  if (newStock < 0) {
    newBacklog = Math.abs(newStock);
    newStock   = 0;
  }

  // Calculer les coûts de cette semaine
  var weekCost = newStock * COST_STOCK + newBacklog * COST_BACKLOG;
  var newTotalCost = totalCost + weekCost;

  // Enregistrer la commande
  oSheet.appendRow([
    data.sessionCode,
    currentWeek,
    chain,
    role,
    data.playerId,
    incomingDemand,
    data.orderQty,
    newStock,
    newBacklog,
    weekCost,
    new Date()
  ]);

  // Mettre à jour l'état du joueur
  pSheet.getRange(pRow, 6, 1, 4).setValues([[newStock, newBacklog, data.orderQty, newTotalCost]]);

  return {
    success: true,
    week: currentWeek,
    incomingDemand: incomingDemand,
    orderPlaced: data.orderQty,
    newStock: newStock,
    newBacklog: newBacklog,
    weekCost: weekCost,
    totalCost: newTotalCost
  };
}

/**
 * Lire l'état courant d'un joueur
 * GET ?action=getState&playerId=xxx&sessionCode=xxx
 */
function getPlayerState(e) {
  var ss      = SpreadsheetApp.openById(SS_ID);
  var pSheet  = ss.getSheetByName(SHEET_PLAYERS);
  var sesSheet = ss.getSheetByName(SHEET_SESSIONS);

  var pRow  = findPlayerRow(pSheet, e.parameter.playerId);
  if (!pRow) return { error: "Joueur introuvable." };

  var pData = pSheet.getRange(pRow, 1, 1, 10).getValues()[0];
  var session = getSessionRow(sesSheet, e.parameter.sessionCode);

  return {
    sessionCode:  pData[0],
    chain:        pData[2],
    role:         pData[3],
    playerName:   pData[4],
    stock:        pData[5],
    backlog:      pData[6],
    pendingDelivery: pData[7],
    totalCost:    pData[8],
    currentWeek:  session ? session.currentWeek : 1,
    totalWeeks:   TOTAL_WEEKS,
    gameStatus:   session ? session.status : "waiting"
  };
}

// ------------------------------------------------------------
//  ACTIONS – FACILITATEUR
// ------------------------------------------------------------

/**
 * Avancer d'une semaine (facilitateur seulement)
 * POST { action, sessionCode, facilitatorKey }
 */
function advanceWeek(data) {
  var ss       = SpreadsheetApp.openById(SS_ID);
  var sesSheet = ss.getSheetByName(SHEET_SESSIONS);

  var session = getSessionRow(sesSheet, data.sessionCode);
  if (!session) return { error: "Session introuvable." };
  if (data.facilitatorKey !== session.facilitatorKey) return { error: "Clé facilitateur invalide." };

  var newWeek = session.currentWeek + 1;
  var newStatus = newWeek > TOTAL_WEEKS ? "finished" : "playing";

  // Mettre à jour la semaine courante
  sesSheet.getRange(session.row, 4).setValue(newWeek);
  sesSheet.getRange(session.row, 5).setValue(newStatus);

  return { success: true, newWeek: newWeek, status: newStatus };
}

/**
 * Créer une nouvelle session
 * POST { action, sessionCode, facilitatorKey, nbChains }
 */
function createSession(data) {
  var ss       = SpreadsheetApp.openById(SS_ID);
  var sesSheet = ss.getSheetByName(SHEET_SESSIONS);

  // Vérifier unicité du code
  var rows = sesSheet.getDataRange().getValues();
  for (var i = 1; i < rows.length; i++) {
    if (rows[i][0] === data.sessionCode) return { error: "Ce code session existe déjà." };
  }

  sesSheet.appendRow([
    data.sessionCode,
    data.facilitatorKey,
    data.nbChains || 5,
    1,          // currentWeek
    "waiting",  // status
    new Date()
  ]);

  return { success: true, sessionCode: data.sessionCode };
}

/**
 * Réinitialiser une session (facilitateur)
 */
function resetSession(data) {
  var ss       = SpreadsheetApp.openById(SS_ID);
  var sesSheet = ss.getSheetByName(SHEET_SESSIONS);
  var pSheet   = ss.getSheetByName(SHEET_PLAYERS);
  var oSheet   = ss.getSheetByName(SHEET_ORDERS);

  var session = getSessionRow(sesSheet, data.sessionCode);
  if (!session) return { error: "Session introuvable." };
  if (data.facilitatorKey !== session.facilitatorKey) return { error: "Clé facilitateur invalide." };

  // Remettre la semaine à 1
  sesSheet.getRange(session.row, 4, 1, 2).setValues([[1, "waiting"]]);

  // Supprimer les commandes de la session
  clearRowsBySession(oSheet, data.sessionCode);

  // Réinitialiser les joueurs
  resetPlayersBySession(pSheet, data.sessionCode);

  return { success: true };
}

/**
 * Dashboard facilitateur en temps réel
 * GET ?action=getFacDashboard&sessionCode=xxx
 */
function getFacilitatorDashboard(e) {
  var ss       = SpreadsheetApp.openById(SS_ID);
  var pSheet   = ss.getSheetByName(SHEET_PLAYERS);
  var oSheet   = ss.getSheetByName(SHEET_ORDERS);
  var sesSheet = ss.getSheetByName(SHEET_SESSIONS);

  var code = e.parameter.sessionCode;
  var session = getSessionRow(sesSheet, code);
  if (!session) return { error: "Session introuvable." };

  var pRows = pSheet.getDataRange().getValues();
  var players = [];
  for (var i = 1; i < pRows.length; i++) {
    if (pRows[i][0] !== code) continue;
    players.push({
      chain:   pRows[i][2],
      role:    pRows[i][3],
      name:    pRows[i][4],
      stock:   pRows[i][5],
      backlog: pRows[i][6],
      cost:    pRows[i][8]
    });
  }

  // Calcul BWI par joueur
  var bwiData = computeBullwhipIndex(oSheet, code);

  // Compter joueurs ayant joué ce round
  var ordRows   = oSheet.getDataRange().getValues();
  var playedThisRound = 0;
  for (var j = 1; j < ordRows.length; j++) {
    if (ordRows[j][0] === code && ordRows[j][1] === session.currentWeek) playedThisRound++;
  }

  return {
    currentWeek:    session.currentWeek,
    status:         session.status,
    totalPlayers:   players.length,
    playedThisRound: playedThisRound,
    players:        players,
    bullwhipIndex:  bwiData
  };
}

/**
 * Résultats finaux
 * GET ?action=getResults&sessionCode=xxx
 */
function getResults(e) {
  var ss     = SpreadsheetApp.openById(SS_ID);
  var pSheet = ss.getSheetByName(SHEET_PLAYERS);
  var oSheet = ss.getSheetByName(SHEET_ORDERS);
  var code   = e.parameter.sessionCode;

  var pRows = pSheet.getDataRange().getValues();
  var results = [];
  for (var i = 1; i < pRows.length; i++) {
    if (pRows[i][0] !== code) continue;
    results.push({
      chain:     pRows[i][2],
      role:      pRows[i][3],
      name:      pRows[i][4],
      totalCost: pRows[i][8]
    });
  }

  // Coût par chaîne
  var chainCosts = {};
  results.forEach(function(r) {
    chainCosts[r.chain] = (chainCosts[r.chain] || 0) + r.totalCost;
  });

  var bwiData = computeBullwhipIndex(oSheet, code);

  return {
    players: results,
    chainCosts: chainCosts,
    bullwhipIndex: bwiData
  };
}

// ------------------------------------------------------------
//  LOGIQUE MÉTIER
// ------------------------------------------------------------

/**
 * Demande entrante : commande passée par le maillon aval
 * Le Détaillant reçoit la demande client réelle (simulée)
 */
function getIncomingDemand(ss, sessionCode, chain, role, week) {
  var roleOrder = ["Détaillant", "Grossiste", "Distributeur", "Fabricant"];
  var idx = roleOrder.indexOf(role);

  if (idx === 0) {
    // Détaillant → demande client simulée
    return getClientDemand(week);
  }

  // Autres rôles → commande du rôle aval
  var downstreamRole = roleOrder[idx - 1];
  var oSheet = ss.getSheetByName(SHEET_ORDERS);
  var rows   = oSheet.getDataRange().getValues();

  for (var i = rows.length - 1; i >= 1; i--) {
    if (rows[i][0] === sessionCode &&
        rows[i][2] === chain &&
        rows[i][3] === downstreamRole &&
        rows[i][1] === week) {
      return rows[i][6]; // quantité commandée par le rôle aval
    }
  }

  // Si le joueur aval n'a pas encore joué, utiliser l'IA de remplacement
  return getAIOrder(week, idx);
}

/**
 * Demande client réelle (légère variation autour de 4–6)
 * Choc semaine 5 : demande passe à 8 puis revient à 4
 */
function getClientDemand(week) {
  var base = [4,4,4,4,8,4,4,4,4,5,4,4,4,4,5,4,4,4,4,4];
  return base[week - 1] || 4;
}

/**
 * Commande IA de remplacement (si joueur absent)
 * Amplification croissante par échelon (effet Bullwhip)
 */
function getAIOrder(week, echelon) {
  var demand = getClientDemand(week);
  var amplification = [1.0, 1.35, 1.7, 2.05];
  var amp = amplification[Math.min(echelon, 3)];
  var noise = (Math.random() - 0.5) * 2;
  return Math.max(0, Math.round(demand * amp + noise));
}

/**
 * Calcul de l'indice Bullwhip par rôle et par chaîne
 * BWI = (écart-type commandes / moyenne commandes) / (écart-type demande / moyenne demande)
 */
function computeBullwhipIndex(oSheet, sessionCode) {
  var rows = oSheet.getDataRange().getValues();
  var byRole = {};

  for (var i = 1; i < rows.length; i++) {
    if (rows[i][0] !== sessionCode) continue;
    var key = rows[i][2] + "-" + rows[i][3]; // chain-role
    if (!byRole[key]) byRole[key] = { demands: [], orders: [] };
    byRole[key].demands.push(rows[i][5]); // demande reçue
    byRole[key].orders.push(rows[i][6]);  // commande passée
  }

  var result = {};
  Object.keys(byRole).forEach(function(key) {
    var d = byRole[key];
    if (d.orders.length < 2) { result[key] = null; return; }
    var cvOrders  = coeffVar(d.orders);
    var cvDemands = coeffVar(d.demands);
    result[key] = cvDemands > 0 ? Math.round((cvOrders / cvDemands) * 100) / 100 : null;
  });

  return result;
}

function coeffVar(arr) {
  var n    = arr.length;
  var mean = arr.reduce(function(a,b){return a+b},0) / n;
  if (mean === 0) return 0;
  var variance = arr.reduce(function(s,v){return s+Math.pow(v-mean,2)},0) / n;
  return Math.sqrt(variance) / mean;
}

// ------------------------------------------------------------
//  HELPERS SHEET
// ------------------------------------------------------------

function getSessionRow(sheet, code) {
  var rows = sheet.getDataRange().getValues();
  for (var i = 1; i < rows.length; i++) {
    if (rows[i][0] === code) {
      return {
        row:           i + 1,
        sessionCode:   rows[i][0],
        facilitatorKey: rows[i][1],
        nbChains:      rows[i][2],
        currentWeek:   rows[i][3],
        status:        rows[i][4]
      };
    }
  }
  return null;
}

function findPlayerRow(sheet, playerId) {
  var rows = sheet.getDataRange().getValues();
  for (var i = 1; i < rows.length; i++) {
    if (rows[i][1] === playerId) return i + 1;
  }
  return null;
}

function clearRowsBySession(sheet, sessionCode) {
  var rows = sheet.getDataRange().getValues();
  for (var i = rows.length - 1; i >= 1; i--) {
    if (rows[i][0] === sessionCode) sheet.deleteRow(i + 1);
  }
}

function resetPlayersBySession(sheet, sessionCode) {
  var rows = sheet.getDataRange().getValues();
  for (var i = 1; i < rows.length; i++) {
    if (rows[i][0] === sessionCode) {
      sheet.getRange(i + 1, 6, 1, 4).setValues([[12, 0, 4, 0]]);
    }
  }
}
