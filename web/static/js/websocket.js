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
    cargarHistorial();
    cargarMemoria();
    cargarProyectos();
  };

  state.ws.onmessage = (event) => {
    if (event.data instanceof Blob) {
      reproducirAudio(event.data);
      return;
    }
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

// ─── Historial — la conversación sigue al cambiar de dispositivo ─────────
async function cargarHistorial() {
  // Solo la primera vez: al reconectar, el chat ya tiene lo que se vio.
  if (state.historialCargado) return;
  try {
    const res  = await fetch("/api/historial");
    const data = await res.json();
    data.mensajes.forEach(m => agregarMensaje(m.rol, m.contenido));
    state.historialCargado = true;
  } catch (_) {}
}

function manejarMensaje(data) {
  if (data.tipo === "mensaje_usuario") {
    // Lo escribió (o dijo) el usuario desde otro dispositivo.
    agregarMensaje("user", data.contenido);
  }

  if (data.tipo === "estado" && data.estado === "pensando") {
    mostrarTyping();
    setStatus("Pensando...", true);
    bloquearInput(true);
    setFaceState("pensando");
  }

  if (data.tipo === "estado" && data.estado === "escuchando") {
    setStatus("Transcribiendo...", true);
    setFaceState("escuchando");
  }

  if (data.tipo === "estado" && data.estado === "ejecutando") {
    setStatus("Ejecutando...", true);
    setFaceState("ejecutando");
  }

  if (data.tipo === "transcripcion") {
    agregarMensaje("user", data.contenido);
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
    if (data.voz) state.audioPendiente = true;
    if (data.emocion) setFaceEmocion(data.emocion);
    setStatus("En línea", false);
    bloquearInput(false);
    messageInput.focus();
    setFaceState("listo");
  }

  if (data.tipo === "sin_audio") {
    // La síntesis falló: no va a llegar el audio que anunció la respuesta.
    state.audioPendiente = false;
    state.descartarAudio = false;
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
    setFaceState("listo");
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
