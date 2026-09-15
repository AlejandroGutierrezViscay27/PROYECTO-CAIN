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

// ─── Init ─────────────────────────────────────────────────────────────────
conectar();
messageInput.focus();
