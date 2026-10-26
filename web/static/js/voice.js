// ─── Voz — micrófono (push-to-talk y manos libres) ───────────────────────
// Se captura PCM crudo con Web Audio y se envía como WAV 16 kHz mono: es
// justo lo que usa Whisper, así el servidor no tiene que decodificar webm.

const VAD = {
  factorInicio:  3.0,    // hay voz si el RMS supera el ruido de fondo × factor
  minimoInicio:  0.012,  // umbral absoluto mínimo (micrófonos muy silenciosos)
  factorFin:     1.6,
  factorEco:     2.5,    // mientras CAIN habla su voz se cuela por el micro: umbral más alto
  silencioFinMs: 900,    // silencio necesario para dar la frase por terminada
  minHablaMs:    350,    // menos que esto es un golpe o un clic, no una frase
  maxHablaMs:    15000,
  preRollMs:     300,    // audio previo al disparo, para no comerse la primera sílaba
  minPttMs:      250,
};

const mic = {
  ctx: null, stream: null, proc: null,
  manosLibres: false,   // VAD activo
  pttPedido:   false,   // botón presionado (aunque el micro aún se esté abriendo)
  ptt:         false,   // grabando por push-to-talk
  hablando:    false,   // el VAD detectó voz y está grabando la frase
  interrumpio: false,   // ya se cortó a CAIN en esta frase
  ruido:       0.01,    // ruido de fondo estimado (RMS)
  trozos: [], previo: [],
  hablaMs: 0, silencioMs: 0,
};

async function abrirMicrofono() {
  if (mic.ctx) return;
  mic.stream = await navigator.mediaDevices.getUserMedia({
    audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
  });
  mic.ctx = new (window.AudioContext || window.webkitAudioContext)();
  const fuente = mic.ctx.createMediaStreamSource(mic.stream);
  // ScriptProcessor está obsoleto, pero funciona en todos los navegadores y
  // no necesita un archivo de AudioWorklet aparte; para esto sobra.
  mic.proc = mic.ctx.createScriptProcessor(2048, 1, 1);
  fuente.connect(mic.proc);
  mic.proc.connect(mic.ctx.destination);  // sin esto Chrome no llama a onaudioprocess
  mic.proc.onaudioprocess = (e) => procesarFrame(new Float32Array(e.inputBuffer.getChannelData(0)));
}

function cerrarMicrofono() {
  if (!mic.ctx) return;
  mic.proc.disconnect();
  mic.stream.getTracks().forEach((track) => track.stop());
  mic.ctx.close();
  mic.ctx = mic.stream = mic.proc = null;
  mic.hablando = false;
  mic.trozos   = [];
  mic.previo   = [];
}

function procesarFrame(frame) {
  let suma = 0;
  for (let i = 0; i < frame.length; i++) suma += frame[i] * frame[i];
  const rms = Math.sqrt(suma / frame.length);
  const ms  = (frame.length / mic.ctx.sampleRate) * 1000;

  if (mic.ptt) {
    mic.trozos.push(frame);
    mic.hablaMs += ms;
    return;
  }
  if (!mic.manosLibres || mic.pttPedido) return;

  // Mientras CAIN piensa no se escucha: el servidor atiende un turno a la vez.
  if (state.pensando) {
    mic.hablando = false;
    mic.previo   = [];
    return;
  }

  const hablaCain = cainHablando();
  if (!mic.hablando && !hablaCain) mic.ruido = mic.ruido * 0.97 + rms * 0.03;
  const eco          = hablaCain ? VAD.factorEco : 1;
  const umbralInicio = Math.max(VAD.minimoInicio, mic.ruido * VAD.factorInicio) * eco;
  const umbralFin    = Math.max(VAD.minimoInicio * 0.6, mic.ruido * VAD.factorFin) * eco;

  if (!mic.hablando) {
    mic.previo.push(frame);
    while (mic.previo.length > Math.ceil(VAD.preRollMs / ms)) mic.previo.shift();
    if (rms > umbralInicio) {
      mic.hablando    = true;
      mic.interrumpio = false;
      mic.hablaMs     = 0;
      mic.silencioMs  = 0;
      mic.trozos      = mic.previo;
      mic.previo      = [];
    }
    return;
  }

  mic.trozos.push(frame);
  mic.hablaMs   += ms;
  mic.silencioMs = rms < umbralFin ? mic.silencioMs + ms : 0;

  // Se corta a CAIN solo cuando ya es claramente una frase: una tos no lo calla.
  if (!mic.interrumpio && mic.hablaMs - mic.silencioMs >= VAD.minHablaMs) {
    mic.interrumpio = true;
    interrumpirCain();
    setStatus("Escuchando...", false);
    setFaceState("escuchando");
  }

  if (mic.silencioMs >= VAD.silencioFinMs || mic.hablaMs >= VAD.maxHablaMs) {
    mic.hablando = false;
    const trozos = mic.trozos;
    mic.trozos   = [];
    if (mic.interrumpio) enviarAudio(trozos);
  }
}

function enviarAudio(trozos) {
  if (!state.connected) return;
  state.ws.send(codificarWav16k(trozos, mic.ctx.sampleRate));
  setStatus("Enviando audio...", true);
}

// ─── Push-to-talk (mantener presionado el micrófono) ─────────────────────
async function iniciarGrabacion() {
  if (mic.pttPedido || state.pensando || !state.connected) return;
  mic.pttPedido = true;
  micBtn.classList.add("recording");

  try {
    await abrirMicrofono();
  } catch (e) {
    mic.pttPedido = false;
    micBtn.classList.remove("recording");
    setStatus("Sin acceso al micrófono", false);
    return;
  }
  // Se soltó el botón mientras el navegador abría el micrófono.
  if (!mic.pttPedido) {
    if (!mic.manosLibres) cerrarMicrofono();
    return;
  }

  mic.hablando = false;
  mic.trozos   = [];
  mic.hablaMs  = 0;
  mic.ptt      = true;
  interrumpirCain();
  setStatus("Escuchando...", false);
  setFaceState("escuchando");
}

function detenerGrabacion() {
  if (!mic.pttPedido) return;
  mic.pttPedido = false;
  micBtn.classList.remove("recording");
  if (!mic.ptt) return;  // el micrófono no llegó a abrirse

  mic.ptt = false;
  const trozos = mic.trozos;
  mic.trozos   = [];
  if (mic.hablaMs >= VAD.minPttMs) {
    enviarAudio(trozos);
  } else {
    setStatus("En línea", false);
    setFaceState("listo");
  }
  if (!mic.manosLibres) cerrarMicrofono();
}

// ─── Manos libres (VAD) ──────────────────────────────────────────────────
async function alternarManosLibres() {
  if (mic.manosLibres) {
    mic.manosLibres = false;
    mic.hablando    = false;
    vadBtn.classList.remove("active");
    if (!mic.pttPedido) cerrarMicrofono();
    if (!state.pensando) setStatus("En línea", false);
    return;
  }

  try {
    await abrirMicrofono();
  } catch (e) {
    setStatus("Sin acceso al micrófono", false);
    return;
  }
  mic.manosLibres = true;
  mic.ruido       = 0.01;
  vadBtn.classList.add("active");
  if (!state.pensando) setStatus("Manos libres — habla cuando quieras", false);
}

// ─── WAV 16 kHz mono ─────────────────────────────────────────────────────
function codificarWav16k(trozos, frecuenciaOrigen) {
  const total = trozos.reduce((n, t) => n + t.length, 0);
  const datos = new Float32Array(total);
  let offset = 0;
  for (const t of trozos) { datos.set(t, offset); offset += t.length; }

  // Remuestreo lineal a 16 kHz (sobra para voz).
  const razon = frecuenciaOrigen / 16000;
  const n     = Math.floor(datos.length / razon);
  const pcm   = new Int16Array(n);
  for (let i = 0; i < n; i++) {
    const pos = i * razon;
    const i0  = Math.floor(pos);
    const i1  = Math.min(datos.length - 1, i0 + 1);
    const f   = pos - i0;
    const v   = datos[i0] * (1 - f) + datos[i1] * f;
    pcm[i] = Math.max(-32768, Math.min(32767, Math.round(v * 32767)));
  }

  const buffer = new ArrayBuffer(44 + pcm.length * 2);
  const dv     = new DataView(buffer);
  const texto  = (off, s) => { for (let i = 0; i < s.length; i++) dv.setUint8(off + i, s.charCodeAt(i)); };
  texto(0, "RIFF");  dv.setUint32(4, 36 + pcm.length * 2, true);
  texto(8, "WAVE");  texto(12, "fmt ");
  dv.setUint32(16, 16, true);     // tamaño del bloque fmt
  dv.setUint16(20, 1, true);      // PCM
  dv.setUint16(22, 1, true);      // mono
  dv.setUint32(24, 16000, true);  // frecuencia
  dv.setUint32(28, 32000, true);  // bytes por segundo
  dv.setUint16(32, 2, true);      // bytes por muestra
  dv.setUint16(34, 16, true);     // bits por muestra
  texto(36, "data"); dv.setUint32(40, pcm.length * 2, true);
  new Int16Array(buffer, 44).set(pcm);
  return buffer;
}

// ─── Voz — reproducción de la respuesta ──────────────────────────────────
let audioContext  = null;
let nivelAudioTTS = 0;
let audioActual   = null;
let terminarAudio = null;

function getAudioLevel() {
  return nivelAudioTTS;
}

function cainHablando() {
  return audioActual !== null || state.audioPendiente;
}

// Barge-in: si el usuario empieza a hablar, CAIN se calla. Si el audio aún
// no llegó del servidor, se descarta cuando llegue.
function interrumpirCain() {
  if (state.audioPendiente) {
    state.audioPendiente = false;
    state.descartarAudio = true;
  }
  if (audioActual) {
    audioActual.pause();
    terminarAudio();
  }
}

function reproducirAudio(blob) {
  state.audioPendiente = false;
  if (state.descartarAudio) {
    state.descartarAudio = false;
    return;
  }
  if (audioActual) {
    audioActual.pause();
    terminarAudio();
  }

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

  const finalizar = () => {
    if (!activo) return;
    activo        = false;
    nivelAudioTTS = 0;
    audioActual   = null;
    terminarAudio = null;
    URL.revokeObjectURL(url);
    setFaceState("listo");
  };

  audioActual   = audio;
  terminarAudio = finalizar;
  audio.onended = finalizar;
}
