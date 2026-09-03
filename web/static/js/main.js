// ─── Input — Enter para enviar ────────────────────────────────────────────
messageInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

messageInput.addEventListener("input", autoResize);

// ─── Init ─────────────────────────────────────────────────────────────────
conectar();
messageInput.focus();
