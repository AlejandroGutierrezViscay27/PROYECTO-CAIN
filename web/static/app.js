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

// ─── WebSocket ────────────────────────────────────────────────────────────
function conectar() {

    if (state.ws) {
    state.ws.onclose = null; // evitar reconexión automática
    state.ws.close();
  }
  
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl    = `${protocol}//${window.location.host}/ws`;
  state.ws       = new WebSocket(wsUrl);

  state.ws.onopen = () => {
    state.connected = true;
    setStatus("En línea", false);
    cargarMemoria();
    cargarProyectos();
  };

  state.ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    manejarMensaje(data);
  };

  state.ws.onclose = () => {
    state.connected = false;
    setStatus("Desconectado", false);
    setTimeout(conectar, 3000); // reconectar automáticamente
  };

  state.ws.onerror = () => {
    setStatus("Error de conexión", false);
  };
}

function manejarMensaje(data) {
  if (data.tipo === "estado" && data.estado === "pensando") {
    mostrarTyping();
    setStatus("Pensando...", true);
    bloquearInput(true);
  }

  if (data.tipo === "confirmacion") {
    quitarTyping();
    setStatus("Esperando confirmación...", false);
    mostrarModalConfirmacion(data);
  }

  if (data.tipo === "respuesta") {
    quitarTyping();
    cerrarModal();
    agregarMensaje("cain", data.contenido);
    setStatus("En línea", false);
    bloquearInput(false);
    messageInput.focus();
  }

  if (data.tipo === "memoria") {
    actualizarMemoriaPanel(data);
    cargarProyectos();
  }

  if (data.tipo === "error") {
    quitarTyping();
    cerrarModal();
    agregarMensaje("cain", `⚠️ ${data.contenido}`);
    setStatus("En línea", false);
    bloquearInput(false);
  }
}

// ─── Enviar mensaje ───────────────────────────────────────────────────────
function sendMessage() {
  const texto = messageInput.value.trim();
  if (!texto || state.pensando || !state.connected) return;

  agregarMensaje("user", texto);
  messageInput.value = "";
  autoResize();

  state.ws.send(JSON.stringify({ mensaje: texto }));
}

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

// ─── Panel lateral — Memoria ──────────────────────────────────────────────
async function cargarMemoria() {
  try {
    const res  = await fetch("/api/memory");
    const data = await res.json();
    actualizarMemoriaPanel(data);
  } catch (_) {}
}

function actualizarMemoriaPanel(data) {
  const nombre   = document.getElementById("memNombre");
  const rol      = document.getElementById("memRol");
  const intereses = document.getElementById("memIntereses");
  const notas    = document.getElementById("memNotas");
  const mensajes = document.getElementById("memMensajes");

  if (data.nombre) {
    nombre.textContent = data.nombre;
    nombre.classList.add("active");
  }

  if (data.rol) {
    rol.textContent = data.rol;
    rol.classList.add("active");
  }

  if (data.intereses && data.intereses.length > 0) {
    intereses.innerHTML = data.intereses
      .map(i => `<span class="memory-tag">${i}</span>`)
      .join("");
  }

  if (data.notas && data.notas.length > 0) {
    notas.innerHTML = data.notas
      .map(n => `<div class="memory-note">${n}</div>`)
      .join("");
  }

  if (data.mensajes !== undefined) {
    mensajes.textContent = data.mensajes;
  }
}

// ─── Panel lateral — Proyectos ────────────────────────────────────────────
async function cargarProyectos() {
  try {
    const res  = await fetch("/api/proyectos");
    const data = await res.json();
    const lista = document.getElementById("proyectosList");

    if (data.proyectos.length === 0) {
      lista.innerHTML = `<div class="memory-item">Sin proyectos aún</div>`;
      return;
    }

    lista.innerHTML = data.proyectos.map(p => `
      <div class="proyecto-item" onclick="abrirProyecto('${p.nombre}', '${p.tipo}')">
        <div class="proyecto-nombre">${p.nombre}</div>
        <div class="proyecto-tipo">${p.tipo === "web" ? "🌐 web" : "🐍 python"}</div>
      </div>
    `).join("");

  } catch (_) {}
}

// ─── Interacción con proyectos ────────────────────────────────────────────
async function abrirProyecto(nombre, tipo) {
  // Mostrar estado de carga en el proyecto
  mostrarModalCargando(nombre);

  try {
    const res  = await fetch(`/api/proyectos/${nombre}/abrir`, { method: "POST" });
    const data = await res.json();

    if (data.error) {
      cerrarModal();
      agregarMensaje("cain", `⚠️ No pude abrir el proyecto: ${data.error}`);
      return;
    }

    if (data.tipo === "web") {
      cerrarModal();
      // Abrir en pestaña nueva
      window.open(data.url, "_blank");
      agregarMensaje("cain", `🌐 Proyecto <strong>${nombre}</strong> abierto en: ${data.url}`);
    }

    if (data.tipo === "python") {
      mostrarModalCodigo(nombre, data.archivo, data.codigo);
    }

  } catch (e) {
    cerrarModal();
    agregarMensaje("cain", `⚠️ Error al abrir el proyecto.`);
  }
}

// ─── Modal ────────────────────────────────────────────────────────────────
function mostrarModalCargando(nombre) {
  const overlay = document.createElement("div");
  overlay.className = "modal-overlay";
  overlay.id = "modalOverlay";
  overlay.innerHTML = `
    <div class="modal">
      <div class="modal-header">
        <div>
          <div class="modal-title">${nombre}</div>
          <div class="modal-subtitle">Cargando proyecto...</div>
        </div>
        <button class="modal-close" onclick="cerrarModal()">✕</button>
      </div>
      <div class="modal-body" style="display:flex;align-items:center;justify-content:center;min-height:120px;">
        <div class="typing-dots">
          <span></span><span></span><span></span>
        </div>
      </div>
    </div>
  `;
  document.body.appendChild(overlay);
  overlay.addEventListener("click", (e) => { if (e.target === overlay) cerrarModal(); });
}

function mostrarModalCodigo(nombre, archivo, codigo) {
  cerrarModal();

  const overlay = document.createElement("div");
  overlay.className = "modal-overlay";
  overlay.id = "modalOverlay";
  overlay.innerHTML = `
    <div class="modal">
      <div class="modal-header">
        <div>
          <div class="modal-title">${nombre}</div>
          <div class="modal-subtitle">🐍 ${archivo}</div>
        </div>
        <button class="modal-close" onclick="cerrarModal()">✕</button>
      </div>
      <div class="modal-body">
        <pre class="code-block">${escapeHtml(codigo)}</pre>
      </div>
      <div class="modal-footer">
        <button class="btn btn-secondary" onclick="pedirModificacion('${nombre}', '${archivo}')">
          Pedir modificación a CAIN
        </button>
        <button class="btn btn-primary" onclick="reejecutarProyecto('${nombre}', '${archivo}')">
          Re-ejecutar
        </button>
        <button class="btn btn-secondary" onclick="cerrarModal()">Cerrar</button>
      </div>
    </div>
  `;
  document.body.appendChild(overlay);
  overlay.addEventListener("click", (e) => { if (e.target === overlay) cerrarModal(); });
}

function cerrarModal() {
  const overlay = document.getElementById("modalOverlay");
  if (overlay) overlay.remove();
}

function pedirModificacion(nombre, archivo) {
  cerrarModal();
  messageInput.value = `Modifica el proyecto ${nombre}: `;
  messageInput.focus();
  // Colocar cursor al final
  const len = messageInput.value.length;
  messageInput.setSelectionRange(len, len);
}

function reejecutarProyecto(nombre, archivo) {
  cerrarModal();
  const mensaje = `Re-ejecuta el proyecto ${nombre}`;
  agregarMensaje("user", mensaje);
  if (state.ws && state.connected) {
    state.ws.send(JSON.stringify({ mensaje }));
  }
}

function escapeHtml(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

// ─── Input — auto-resize y Enter ─────────────────────────────────────────
messageInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

messageInput.addEventListener("input", autoResize);

function autoResize() {
  messageInput.style.height = "auto";
  messageInput.style.height = Math.min(messageInput.scrollHeight, 150) + "px";
}

// ─── Modal de confirmación de proyecto ───────────────────────────────────
function mostrarModalConfirmacion(plan) {
  cerrarModal();

  const archivosHtml = plan.archivos
    .map(a => `<div style="padding:0.2rem 0; color:var(--text-dim)">📄 ${a}</div>`)
    .join("");

  const overlay = document.createElement("div");
  overlay.className = "modal-overlay";
  overlay.id = "modalOverlay";
  overlay.innerHTML = `
    <div class="modal">
      <div class="modal-header">
        <div>
          <div class="modal-title">Plan de ejecución</div>
          <div class="modal-subtitle">🎭 ${plan.nombre}</div>
        </div>
      </div>
      <div class="modal-body">
        <div class="memory-label" style="margin-bottom:0.6rem">Archivos a crear</div>
        ${archivosHtml}
        <div class="memory-label" style="margin-top:1rem; margin-bottom:0.4rem">Comando</div>
        <div class="code-block" style="padding:0.6rem 0.8rem; font-size:12px">
          📟 ${escapeHtml(plan.comando)}
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn btn-secondary" onclick="responderConfirmacion(false)">
          Cancelar
        </button>
        <button class="btn btn-primary" onclick="responderConfirmacion(true)">
          ✦ Proceder
        </button>
      </div>
    </div>
  `;
  document.body.appendChild(overlay);
}

function responderConfirmacion(confirmado) {
  cerrarModal();
  if (!confirmado) {
    bloquearInput(false);
    setStatus("En línea", false);
  } else {
    mostrarTyping();
    setStatus("Ejecutando...", true);
  }
  state.ws.send(JSON.stringify({
    tipo:       "confirmacion_respuesta",
    confirmado: confirmado
  }));
}

// ─── Init ─────────────────────────────────────────────────────────────────
conectar();
messageInput.focus();