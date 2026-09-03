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

function escapeHtml(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
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
