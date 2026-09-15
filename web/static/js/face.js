// ─── La Cara — rostro reactivo en Three.js (Fase 8) ──────────────────────
// Un icosaedro deformado por ruido simplex, con normales recalculadas tras
// la deformación (para que la luz responda a las abolladuras reales, no a
// la esfera lisa original) y un halo exterior para dar profundidad.
// setFaceState() es la única API pública que usan websocket.js y voice.js.

const FACE_PRESETS = {
  listo:      { color: 0x7b241c, amplitude: 0.07, frequency: 1.1, speed: 0.18 },
  pensando:   { color: 0xc9a84c, amplitude: 0.16, frequency: 2.0, speed: 0.65 },
  escuchando: { color: 0xc9a84c, amplitude: 0.10, frequency: 2.6, speed: 1.0  },
  ejecutando: { color: 0xe74c3c, amplitude: 0.30, frequency: 3.2, speed: 1.5  },
  hablando:   { color: 0xc0392b, amplitude: 0.14, frequency: 1.8, speed: 0.55 },
};

const FACE_NOISE_GLSL = `
  vec3 mod289(vec3 x){return x-floor(x*(1.0/289.0))*289.0;}
  vec4 mod289(vec4 x){return x-floor(x*(1.0/289.0))*289.0;}
  vec4 permute(vec4 x){return mod289(((x*34.0)+1.0)*x);}
  vec4 taylorInvSqrt(vec4 r){return 1.79284291400159 - 0.85373472095314 * r;}

  float snoise(vec3 v){
    const vec2 C = vec2(1.0/6.0, 1.0/3.0);
    const vec4 D = vec4(0.0, 0.5, 1.0, 2.0);
    vec3 i  = floor(v + dot(v, C.yyy));
    vec3 x0 = v - i + dot(i, C.xxx);
    vec3 g = step(x0.yzx, x0.xyz);
    vec3 l = 1.0 - g;
    vec3 i1 = min(g.xyz, l.zxy);
    vec3 i2 = max(g.xyz, l.zxy);
    vec3 x1 = x0 - i1 + C.xxx;
    vec3 x2 = x0 - i2 + C.yyy;
    vec3 x3 = x0 - D.yyy;
    i = mod289(i);
    vec4 p = permute(permute(permute(
              i.z + vec4(0.0, i1.z, i2.z, 1.0))
            + i.y + vec4(0.0, i1.y, i2.y, 1.0))
            + i.x + vec4(0.0, i1.x, i2.x, 1.0));
    float n_ = 0.142857142857;
    vec3 ns = n_ * D.wyz - D.xzx;
    vec4 j = p - 49.0 * floor(p * ns.z * ns.z);
    vec4 x_ = floor(j * ns.z);
    vec4 y_ = floor(j - 7.0 * x_);
    vec4 x = x_ * ns.x + ns.yyyy;
    vec4 y = y_ * ns.x + ns.yyyy;
    vec4 h = 1.0 - abs(x) - abs(y);
    vec4 b0 = vec4(x.xy, y.xy);
    vec4 b1 = vec4(x.zw, y.zw);
    vec4 s0 = floor(b0) * 2.0 + 1.0;
    vec4 s1 = floor(b1) * 2.0 + 1.0;
    vec4 sh = -step(h, vec4(0.0));
    vec4 a0 = b0.xzyw + s0.xzyw * sh.xxyy;
    vec4 a1 = b1.xzyw + s1.xzyw * sh.zzww;
    vec3 p0 = vec3(a0.xy, h.x);
    vec3 p1 = vec3(a0.zw, h.y);
    vec3 p2 = vec3(a1.xy, h.z);
    vec3 p3 = vec3(a1.zw, h.w);
    vec4 norm = taylorInvSqrt(vec4(dot(p0,p0), dot(p1,p1), dot(p2,p2), dot(p3,p3)));
    p0 *= norm.x; p1 *= norm.y; p2 *= norm.z; p3 *= norm.w;
    vec4 m = max(0.6 - vec4(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)), 0.0);
    m = m * m;
    return 42.0 * dot(m * m, vec4(dot(p0,x0), dot(p1,x1), dot(p2,x2), dot(p3,x3)));
  }
`;

// Malla principal: deformación por ruido + normal recalculada por diferencia
// finita, para que las abolladuras reciban luz y sombra reales.
const FACE_VERTEX_SHADER = `
  uniform float uTime;
  uniform float uAmplitude;
  uniform float uFrequency;
  varying vec3 vNormal;
  varying vec3 vViewPosition;
  varying float vDisplace;

  ${FACE_NOISE_GLSL}

  vec3 orthogonal(vec3 v) {
    return normalize(abs(v.x) > abs(v.z) ? vec3(-v.y, v.x, 0.0) : vec3(0.0, -v.z, v.y));
  }

  vec3 desplazar(vec3 p, out float ruido) {
    ruido = snoise(p * uFrequency + uTime);
    return p + normal * ruido * uAmplitude;
  }

  void main() {
    float ruidoCentro;
    vec3 centro = desplazar(position, ruidoCentro);
    vDisplace = ruidoCentro;

    float e = 0.015;
    vec3 tangente   = orthogonal(normal);
    vec3 bitangente = normalize(cross(normal, tangente));

    float ruidoAux;
    vec3 vecino1 = desplazar(position + tangente * e, ruidoAux);
    vec3 vecino2 = desplazar(position + bitangente * e, ruidoAux);

    vec3 normalDesplazada = normalize(cross(vecino1 - centro, vecino2 - centro));
    if (dot(normalDesplazada, normal) < 0.0) normalDesplazada = -normalDesplazada;

    vNormal = normalize(normalMatrix * normalDesplazada);
    vec4 posicionVista = modelViewMatrix * vec4(centro, 1.0);
    vViewPosition = -posicionVista.xyz;
    gl_Position = projectionMatrix * posicionVista;
  }
`;

// Iluminación tipo Blinn-Phong sencilla + reflejo de borde (fresnel),
// en vez de un color plano, para que se vea como una superficie real.
const FACE_FRAGMENT_SHADER = `
  uniform vec3 uColor;
  uniform float uAudioLevel;
  varying vec3 vNormal;
  varying vec3 vViewPosition;
  varying float vDisplace;

  void main() {
    vec3 normal   = normalize(vNormal);
    vec3 vistaDir = normalize(vViewPosition);
    vec3 luzDir   = normalize(vec3(0.5, 0.8, 1.0));

    float difusa    = max(dot(normal, luzDir), 0.0);
    vec3 mitad      = normalize(luzDir + vistaDir);
    float especular = pow(max(dot(normal, mitad), 0.0), 30.0);
    float fresnel   = pow(1.0 - max(dot(normal, vistaDir), 0.0), 2.5);

    vec3 ambiente        = uColor * 0.30;
    vec3 difusaColor     = uColor * difusa * 0.85;
    vec3 especularColor  = mix(uColor, vec3(1.0), 0.85) * especular * (1.0 + uAudioLevel);
    vec3 rim             = mix(uColor, vec3(1.0), 0.5) * fresnel * (0.9 + uAudioLevel * 0.7);

    vec3 colorFinal = ambiente + difusaColor + especularColor + rim + uColor * vDisplace * 0.12;
    gl_FragColor = vec4(colorFinal, 0.96);
  }
`;

// Halo exterior: un sprite (siempre de cara a cámara) con una textura de
// degradado radial. Una malla 3D vista "por dentro" da un anillo de brillo
// casi uniforme — no se lee como luz. Un degradado real sí se difumina.
function crearTexturaGlow() {
  const tam    = 128;
  const canvas = document.createElement("canvas");
  canvas.width = canvas.height = tam;
  const ctx    = canvas.getContext("2d");

  const gradiente = ctx.createRadialGradient(tam / 2, tam / 2, 0, tam / 2, tam / 2, tam / 2);
  gradiente.addColorStop(0.0,  "rgba(255,255,255,0.9)");
  gradiente.addColorStop(0.35, "rgba(255,255,255,0.25)");
  gradiente.addColorStop(1.0,  "rgba(255,255,255,0)");

  ctx.fillStyle = gradiente;
  ctx.fillRect(0, 0, tam, tam);

  return new THREE.CanvasTexture(canvas);
}

let faceRenderer, faceScene, faceCamera, faceMesh, faceMaterial, auraMesh, auraMaterial;
let faceEstadoActual = "listo";
let faceCurrent = Object.assign({}, FACE_PRESETS.listo);
let faceTarget  = FACE_PRESETS.listo;
let faceColorActual;
let faceReloj  = 0;
let camaraReloj = 0;

function initFace() {
  const canvas = document.getElementById("faceCanvas");
  if (!canvas || typeof THREE === "undefined") return;

  const contenedor = canvas.parentElement;

  faceScene  = new THREE.Scene();
  faceCamera = new THREE.PerspectiveCamera(45, 1, 0.1, 10);
  faceCamera.position.z = 3.1;

  faceRenderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
  faceRenderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));

  faceColorActual = new THREE.Color(FACE_PRESETS.listo.color);

  faceMaterial = new THREE.ShaderMaterial({
    uniforms: {
      uTime:       { value: 0 },
      uAmplitude:  { value: faceCurrent.amplitude },
      uFrequency:  { value: faceCurrent.frequency },
      uColor:      { value: faceColorActual.clone() },
      uAudioLevel: { value: 0 },
    },
    vertexShader:   FACE_VERTEX_SHADER,
    fragmentShader: FACE_FRAGMENT_SHADER,
  });
  faceMesh = new THREE.Mesh(new THREE.IcosahedronGeometry(1, 5), faceMaterial);
  faceScene.add(faceMesh);

  auraMaterial = new THREE.SpriteMaterial({
    map:        crearTexturaGlow(),
    color:      faceColorActual.clone(),
    blending:   THREE.AdditiveBlending,
    transparent: true,
    depthWrite: false,
    opacity:    0.9,
  });
  auraMesh = new THREE.Sprite(auraMaterial);
  auraMesh.scale.set(3.4, 3.4, 1);
  faceScene.add(auraMesh);

  ajustarTamanoFace(contenedor);
  window.addEventListener("resize", () => ajustarTamanoFace(contenedor));

  requestAnimationFrame(animarFace);
}

function ajustarTamanoFace(contenedor) {
  const ancho = contenedor.clientWidth  || 1;
  const alto  = contenedor.clientHeight || 1;
  faceRenderer.setSize(ancho, alto, false);
  faceCamera.aspect = ancho / alto;
  faceCamera.updateProjectionMatrix();
}

function setFaceState(estado) {
  if (!FACE_PRESETS[estado] || estado === faceEstadoActual) return;
  faceEstadoActual = estado;
  faceTarget       = FACE_PRESETS[estado];
}

function animarFace() {
  requestAnimationFrame(animarFace);
  if (!faceMaterial) return;

  faceReloj   += 0.016 * faceCurrent.speed;
  camaraReloj += 0.016;

  // Interpolación suave hacia el estado objetivo (transiciones sin saltos)
  faceCurrent.amplitude += (faceTarget.amplitude - faceCurrent.amplitude) * 0.04;
  faceCurrent.frequency += (faceTarget.frequency - faceCurrent.frequency) * 0.04;
  faceCurrent.speed     += (faceTarget.speed     - faceCurrent.speed)     * 0.04;
  faceColorActual.lerp(new THREE.Color(faceTarget.color), 0.04);

  const nivelAudio = faceEstadoActual === "hablando" && typeof getAudioLevel === "function"
    ? getAudioLevel()
    : 0;

  faceMaterial.uniforms.uTime.value       = faceReloj;
  faceMaterial.uniforms.uAmplitude.value  = faceCurrent.amplitude + nivelAudio * 0.25;
  faceMaterial.uniforms.uFrequency.value  = faceCurrent.frequency;
  faceMaterial.uniforms.uColor.value.copy(faceColorActual);
  faceMaterial.uniforms.uAudioLevel.value = nivelAudio;

  auraMaterial.color.copy(faceColorActual);
  const escalaHalo = 3.2 + faceCurrent.amplitude * 2.5 + nivelAudio * 1.2;
  auraMesh.scale.set(escalaHalo, escalaHalo, 1);

  faceMesh.rotation.y += 0.0025 * (1 + faceCurrent.speed);
  faceMesh.rotation.x += 0.0012 * (1 + faceCurrent.speed);

  // Leve deriva de cámara, a ritmo constante (no ligada a uTime) para que
  // se sienta viva incluso sin cambiar de estado.
  faceCamera.position.x = Math.sin(camaraReloj * 0.3) * 0.15;
  faceCamera.position.y = Math.cos(camaraReloj * 0.25) * 0.1;
  faceCamera.lookAt(0, 0, 0);

  faceRenderer.render(faceScene, faceCamera);
}

document.addEventListener("DOMContentLoaded", initFace);
