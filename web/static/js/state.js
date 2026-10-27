// ─── Estado ───────────────────────────────────────────────────────────────
const state = {
  ws:          null,
  pensando:    false,
  connected:   false,
  // Voz: la respuesta avisa si viene audio detrás; si el usuario interrumpe
  // antes de que llegue, ese audio se descarta (ver voice.js).
  audioPendiente: false,
  descartarAudio: false,
  historialCargado: false,
};

// ─── Elementos DOM ────────────────────────────────────────────────────────
const chatContainer = document.getElementById("chatContainer");
const messageInput  = document.getElementById("messageInput");
const sendBtn       = document.getElementById("sendBtn");
const micBtn        = document.getElementById("micBtn");
const vadBtn        = document.getElementById("vadBtn");
const statusDot     = document.getElementById("statusDot");
const statusText    = document.getElementById("statusText");
