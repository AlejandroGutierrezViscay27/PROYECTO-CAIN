// ─── Estado ───────────────────────────────────────────────────────────────
const state = {
  ws:          null,
  pensando:    false,
  connected:   false,
  grabando:    false,
};

// ─── Elementos DOM ────────────────────────────────────────────────────────
const chatContainer = document.getElementById("chatContainer");
const messageInput  = document.getElementById("messageInput");
const sendBtn       = document.getElementById("sendBtn");
const micBtn        = document.getElementById("micBtn");
const statusDot     = document.getElementById("statusDot");
const statusText    = document.getElementById("statusText");
