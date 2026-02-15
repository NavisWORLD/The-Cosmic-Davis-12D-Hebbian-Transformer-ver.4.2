/**
 * Purchase Log — Persistent mapping of facilitated marketplace purchases
 */

const fs = require('fs');
const path = require('path');
const config = require('../config');

const PURCHASE_LOG_FILE = path.join(config.dataDir, 'purchase-log.json');

let purchaseLog = {};

function loadLog() {
  try {
    if (fs.existsSync(PURCHASE_LOG_FILE)) {
      purchaseLog = JSON.parse(fs.readFileSync(PURCHASE_LOG_FILE, 'utf-8'));
    }
  } catch (e) {
    console.warn('[PurchaseLog] Failed to load:', e.message);
    purchaseLog = {};
  }
}

function saveLog() {
  try {
    fs.mkdirSync(path.dirname(PURCHASE_LOG_FILE), { recursive: true });
    fs.writeFileSync(PURCHASE_LOG_FILE, JSON.stringify(purchaseLog, null, 2));
  } catch (e) {
    console.warn('[PurchaseLog] Failed to save:', e.message);
  }
}

function recordPurchase(listingId, record) {
  purchaseLog[listingId] = record;
  saveLog();
}

function getPurchase(listingId) {
  return purchaseLog[listingId] || null;
}

function getPurchasesByBuyer(buyerAddress) {
  if (!buyerAddress) return [];
  const addr = buyerAddress.toLowerCase();
  return Object.entries(purchaseLog)
    .filter(([, r]) => r.realBuyer?.toLowerCase() === addr)
    .map(([id, r]) => ({ listingId: parseInt(id), ...r }));
}

// Load on require
loadLog();

module.exports = { loadLog, recordPurchase, getPurchase, getPurchasesByBuyer };
