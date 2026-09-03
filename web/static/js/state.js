// ─── Estado ───────────────────────────────────────────────────────────────
const state = {
  ws:        null,
  pensando:  false,
  connected: false,
};

// ─── Elementos DOM ────────────────────────────────────────────────────────
const chatContainer = document.getElementById("chatContainer");
const messageInput  = document.getElementById("messageInput");
const sendBtn       = document.getElementById("sendBtn");
const statusDot     = document.getElementById("statusDot");
const statusText    = document.getElementById("statusText");
