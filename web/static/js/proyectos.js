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
