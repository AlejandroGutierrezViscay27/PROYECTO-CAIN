// ─── Voz — grabación (push-to-talk) ──────────────────────────────────────
let mediaRecorder = null;
let audioChunks    = [];

async function iniciarGrabacion() {
  if (state.grabando || state.pensando || !state.connected) return;

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    audioChunks   = [];

    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) audioChunks.push(e.data);
    };

    mediaRecorder.onstop = () => {
      stream.getTracks().forEach((track) => track.stop());
      const blob = new Blob(audioChunks, { type: mediaRecorder.mimeType });
      if (blob.size > 0 && state.connected) {
        state.ws.send(blob);
        setStatus("Enviando audio...", true);
      }
      micBtn.classList.remove("recording");
      state.grabando = false;
    };

    mediaRecorder.start();
    state.grabando = true;
    micBtn.classList.add("recording");
    setStatus("Escuchando...", false);
  } catch (e) {
    setStatus("Sin acceso al micrófono", false);
  }
}

function detenerGrabacion() {
  if (mediaRecorder && mediaRecorder.state === "recording") {
    mediaRecorder.stop();
  }
}

// ─── Voz — reproducción de la respuesta ──────────────────────────────────
function reproducirAudio(blob) {
  const url   = URL.createObjectURL(blob);
  const audio = new Audio(url);
  audio.play().catch(() => {});
  audio.onended = () => URL.revokeObjectURL(url);
}
