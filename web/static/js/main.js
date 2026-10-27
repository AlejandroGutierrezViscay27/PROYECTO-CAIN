// ─── Input — Enter para enviar ────────────────────────────────────────────
messageInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

messageInput.addEventListener("input", autoResize);

// ─── Micrófono — mantener presionado para hablar ─────────────────────────
micBtn.addEventListener("mousedown", iniciarGrabacion);
micBtn.addEventListener("mouseup", detenerGrabacion);
micBtn.addEventListener("mouseleave", detenerGrabacion);
micBtn.addEventListener("touchstart", (e) => { e.preventDefault(); iniciarGrabacion(); });
micBtn.addEventListener("touchend", (e) => { e.preventDefault(); detenerGrabacion(); });

// ─── Manos libres — clic para activar/desactivar ─────────────────────────
vadBtn.addEventListener("click", alternarManosLibres);

// ─── Panel lateral en el móvil — ☰ abre; fondo, ✕ o Escape cierran ───────
document.getElementById("menuBtn").addEventListener("click", abrirPanel);
document.getElementById("sidebarClose").addEventListener("click", cerrarPanel);
document.getElementById("sidebarBackdrop").addEventListener("click", cerrarPanel);
document.addEventListener("keydown", (e) => { if (e.key === "Escape") cerrarPanel(); });

// ─── Init ─────────────────────────────────────────────────────────────────
conectar();
messageInput.focus();
