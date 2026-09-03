// ─── Mensajes en el chat ──────────────────────────────────────────────────
function agregarMensaje(tipo, contenido) {
  const div = document.createElement("div");
  div.className = `message ${tipo === "cain" ? "cain-message" : "user-message"}`;

  const avatar  = tipo === "cain" ? "✦" : "tú";
  const content = formatearContenido(contenido);

  div.innerHTML = `
    <div class="message-avatar">${avatar}</div>
    <div class="message-content">${content}</div>
  `;

  chatContainer.appendChild(div);
  scrollAbajo();
}

function formatearContenido(texto) {
  // Convertir saltos de línea
  let html = texto
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\n/g, "<br>");

  // Bloques de código
  html = html.replace(/`([^`]+)`/g, "<code>$1</code>");

  // Emojis y símbolos se renderizan tal cual
  return html;
}

function mostrarTyping() {
  const div = document.createElement("div");
  div.className = "message cain-message typing-indicator";
  div.id = "typingIndicator";
  div.innerHTML = `
    <div class="message-avatar">✦</div>
    <div class="message-content">
      <div class="typing-dots">
        <span></span><span></span><span></span>
      </div>
    </div>
  `;
  chatContainer.appendChild(div);
  scrollAbajo();
}

function quitarTyping() {
  const typing = document.getElementById("typingIndicator");
  if (typing) typing.remove();
}

function scrollAbajo() {
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

// ─── Estado visual ────────────────────────────────────────────────────────
function setStatus(texto, pensando) {
  statusText.textContent = texto;
  state.pensando         = pensando;

  if (pensando) {
    statusDot.classList.add("thinking");
  } else {
    statusDot.classList.remove("thinking");
  }
}

function bloquearInput(bloqueado) {
  sendBtn.disabled       = bloqueado;
  messageInput.disabled  = bloqueado;
}

// ─── Input — auto-resize ──────────────────────────────────────────────────
function autoResize() {
  messageInput.style.height = "auto";
  messageInput.style.height = Math.min(messageInput.scrollHeight, 150) + "px";
}
