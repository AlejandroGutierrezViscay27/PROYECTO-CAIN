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
