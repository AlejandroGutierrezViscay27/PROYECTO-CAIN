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
    setFaceState("escuchando");
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
let audioContext  = null;
let nivelAudioTTS = 0;

function getAudioLevel() {
  return nivelAudioTTS;
}

function reproducirAudio(blob) {
  const url   = URL.createObjectURL(blob);
  const audio = new Audio(url);

  audio.play().catch(() => {});
  setFaceState("hablando");

  let analizador = null;
  let origen     = null;
  let activo     = true;

  try {
    audioContext = audioContext || new (window.AudioContext || window.webkitAudioContext)();
    analizador   = audioContext.createAnalyser();
    analizador.fftSize = 128;
    origen = audioContext.createMediaElementSource(audio);
    origen.connect(analizador);
    analizador.connect(audioContext.destination);

    const datos = new Uint8Array(analizador.frequencyBinCount);
    const medirNivel = () => {
      if (!activo) return;
      analizador.getByteFrequencyData(datos);
      const promedio = datos.reduce((a, b) => a + b, 0) / datos.length;
      nivelAudioTTS  = promedio / 255;
      requestAnimationFrame(medirNivel);
    };
    medirNivel();
  } catch (e) {
    // Sin Web Audio API disponible: la cara igual anima con el preset base.
  }

  audio.onended = () => {
    activo        = false;
    nivelAudioTTS = 0;
    URL.revokeObjectURL(url);
    setFaceState("listo");
  };
}
