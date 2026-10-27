// ─── Modal ────────────────────────────────────────────────────────────────
function mostrarModalCargando(nombre) {
  const overlay = document.createElement("div");
  overlay.className = "modal-overlay";
  overlay.id = "modalOverlay";
  overlay.innerHTML = `
    <div class="modal">
      <div class="modal-header">
        <div>
          <div class="modal-title">${escapeHtml(nombre)}</div>
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
  // Argumentos de los onclick: literales JS (JSON) escapados para el atributo.
  const args = escapeHtml(`${JSON.stringify(nombre)}, ${JSON.stringify(archivo)}`);

  const overlay = document.createElement("div");
  overlay.className = "modal-overlay";
  overlay.id = "modalOverlay";
  overlay.innerHTML = `
    <div class="modal">
      <div class="modal-header">
        <div>
          <div class="modal-title">${escapeHtml(nombre)}</div>
          <div class="modal-subtitle">🐍 ${escapeHtml(archivo)}</div>
        </div>
        <button class="modal-close" onclick="cerrarModal()">✕</button>
      </div>
      <div class="modal-body">
        <pre class="code-block">${escapeHtml(codigo)}</pre>
      </div>
      <div class="modal-footer">
        <button class="btn btn-secondary" onclick="pedirModificacion(${args})">
          Pedir modificación a CAIN
        </button>
        <button class="btn btn-primary" onclick="reejecutarProyecto(${args})">
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
  // También comillas: el texto puede acabar dentro de un atributo.
  return String(text ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

// ─── Modal de confirmación (arnés de seguridad) ──────────────────────────
// Todo lo que viene en el plan lo escribió el LLM: se escapa SIEMPRE. Un
// nombre de archivo con <script> podría, si no, pulsar "Proceder" solo.
function mostrarModalConfirmacion(plan) {
  cerrarModal();

  const nivel = escapeHtml(plan.nivel || "");
  const advertencias = (plan.advertencias || [])
    .map(a => `<div class="confirm-aviso">⚠️ ${escapeHtml(a)}</div>`)
    .join("");
  const avisosHtml = advertencias
    ? `<div class="memory-label" style="margin-top:1rem; margin-bottom:0.4rem">Revisa esto</div>${advertencias}`
    : "";

  let titulo, cuerpo;
  if (plan.clase === "accion") {
    titulo = escapeHtml(plan.titulo);
    cuerpo = `<div style="color:var(--text-dim)">${escapeHtml(plan.detalle)}</div>`;
  } else {
    const archivosHtml = (plan.archivos || [])
      .map(a => `<div style="padding:0.2rem 0; color:var(--text-dim)">📄 ${escapeHtml(a)}</div>`)
      .join("");
    titulo = `🎭 ${escapeHtml(plan.nombre)}`;
    cuerpo = `
        <div class="memory-label" style="margin-bottom:0.6rem">Archivos a crear</div>
        ${archivosHtml}
        <div class="memory-label" style="margin-top:1rem; margin-bottom:0.4rem">Comando</div>
        <div class="code-block" style="padding:0.6rem 0.8rem; font-size:12px">
          📟 ${escapeHtml(plan.comando)}
        </div>`;
  }

  const overlay = document.createElement("div");
  overlay.className = "modal-overlay";
  overlay.id = "modalOverlay";
  overlay.innerHTML = `
    <div class="modal">
      <div class="modal-header">
        <div>
          <div class="modal-title">🛡️ Confirmar <span class="confirm-nivel">${nivel}</span></div>
          <div class="modal-subtitle">${titulo}</div>
        </div>
      </div>
      <div class="modal-body">
        ${cuerpo}
        ${avisosHtml}
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
