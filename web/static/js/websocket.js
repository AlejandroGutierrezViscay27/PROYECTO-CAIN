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
