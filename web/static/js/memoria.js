// ─── Panel lateral — cajón en el móvil ────────────────────────────────────
// En pantallas anchas el panel siempre está visible y esto no hace nada
// visible: las clases solo tienen efecto dentro del @media del móvil.
function abrirPanel() {
  document.getElementById("sidebar").classList.add("abierta");
  document.getElementById("sidebarBackdrop").classList.add("visible");
  document.getElementById("menuBtn").setAttribute("aria-expanded", "true");
}

function cerrarPanel() {
  document.getElementById("sidebar").classList.remove("abierta");
  document.getElementById("sidebarBackdrop").classList.remove("visible");
  document.getElementById("menuBtn").setAttribute("aria-expanded", "false");
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
