"""
YouTube en el navegador de CAIN (Fase 10.3). Ver FASE10_PLAN.md §6.3.

Usa una sola pestaña de YouTube (la visible, si hay varias): buscar y poner
un vídeo pasan en ella. Los guiones son JavaScript fijo y solo corren en
youtube.com (Navegador.en_sitio lo comprueba en la propia página). Lo que se
lee de la página (títulos, canales) es texto ajeno: va al usuario, nunca al
LLM, y los enlaces se reducen al id del vídeo (core.arnes.youtube).
"""
import re

from core.arnes import reglas
from core.arnes import youtube as arnes_youtube
from core.arnes.rutas import Denegado
from core.arnes.sistema import host_en

# Vídeos de una página de resultados, de la portada, de un canal o los
# relacionados de un vídeo: enlace, título, canal y cuándo se publicó.
GUION_VIDEOS = r"""(maximo) => {
  const videos = [];
  const fecha = /^(hace|transmitido|streamed)\b|\bago$/i;
  for (const r of document.querySelectorAll('ytd-video-renderer, ytd-rich-item-renderer, yt-lockup-view-model')) {
    if (r.querySelector('ytd-ad-slot-renderer, ytd-in-feed-ad-layout-renderer')) continue;
    if (r.tagName === 'YT-LOCKUP-VIEW-MODEL' && r.closest('ytd-rich-item-renderer')) continue;
    const titulo = r.querySelector('a#video-title, a#video-title-link, h3 a, h3');
    const enlace = (titulo && titulo.closest('a')) || r.querySelector('a[href*="/watch?v="]');
    if (!titulo || !enlace) continue;
    const textoTitulo = (titulo.getAttribute('title') || titulo.textContent || '').trim();
    const textos = [...r.querySelectorAll('span')].map(s => s.textContent.trim()).filter(t => t && t !== textoTitulo);
    const canal = r.querySelector('ytd-channel-name a, #channel-name a, a[href^="/@"]');
    videos.push({
      enlace: enlace.getAttribute('href') || '',
      titulo: textoTitulo,
      // Los relacionados no enlazan al canal: es el primer texto sin cifras.
      canal: canal ? canal.textContent : (textos.find(t => !/\d/.test(t)) || ''),
      publicado: textos.find(t => fecha.test(t)) || '',
    });
    if (videos.length >= maximo) break;
  }
  return videos;
}"""

# El primer canal de una búsqueda filtrada por canales: enlace y nombre.
GUION_PRIMER_CANAL = r"""() => {
  const r = document.querySelector('ytd-channel-renderer');
  if (!r) return null;
  const enlace = r.querySelector('a[href^="/@"], a[href^="/channel/"]');
  const nombre = r.querySelector('#channel-title #text') || r.querySelector('#channel-title');
  return enlace ? {enlace: enlace.getAttribute('href') || '', nombre: nombre ? nombre.textContent : ''} : null;
}"""

# El vídeo abierto en la pestaña y su canal (que YouTube pinta un poco después
# que el vídeo: se espera hasta 5 s).
GUION_VIDEO_ABIERTO = r"""async () => {
  if (!location.pathname.startsWith('/watch')) return null;
  const selector = 'ytd-watch-metadata ytd-channel-name a, #owner ytd-channel-name a';
  for (let i = 0; i < 25 && !document.querySelector(selector); i++) await new Promise(r => setTimeout(r, 200));
  const canal = document.querySelector(selector);
  return {
    enlace: location.pathname + location.search,
    canal: canal ? canal.getAttribute('href') || '' : '',
    nombre_canal: canal ? canal.textContent : '',
  };
}"""

# Hay un vídeo en la pestaña y si está en pausa. Sin títulos: no hacen falta.
GUION_ESTADO = r"""() => {
  const v = document.querySelector('video.html5-main-video, video');
  if (!v || !location.pathname.startsWith('/watch')) return null;
  return {pausado: v.paused || v.ended};
}"""

# play() devuelve una promesa que puede no resolverse nunca (pestaña en segundo
# plano): se espera como mucho 3 s y luego se mira si de verdad suena.
GUION_CONTROL = r"""async (accion) => {
  const v = document.querySelector('video.html5-main-video, video');
  if (!v || !location.pathname.startsWith('/watch')) return 'sin_video';
  if (accion === 'pausar') { v.pause(); return 'ok'; }
  if (accion === 'reanudar') {
    try { await Promise.race([v.play(), new Promise(r => setTimeout(r, 3000))]); } catch (e) { return 'bloqueado'; }
    return v.paused ? 'bloqueado' : 'ok';
  }
  if (accion === 'siguiente') {
    const boton = document.querySelector('.ytp-next-button');
    if (!boton || boton.offsetParent === null || boton.getAttribute('aria-disabled') === 'true') return 'sin_siguiente';
    boton.click();
    return 'ok';
  }
  return 'desconocida';
}"""

# Tras abrir un vídeo: si el navegador no lo arrancó solo, se le da play.
GUION_ARRANCAR = r"""async () => {
  const v = document.querySelector('video.html5-main-video, video');
  if (v && v.paused) { try { await Promise.race([v.play(), new Promise(r => setTimeout(r, 3000))]); } catch (e) {} }
  return true;
}"""

SELECTOR_RESULTADOS    = "ytd-video-renderer a#video-title"
SELECTOR_PORTADA       = "ytd-rich-item-renderer, yt-lockup-view-model"
SELECTOR_CANALES       = "ytd-channel-renderer"
SELECTOR_VIDEOS_CANAL  = "ytd-rich-item-renderer"
SELECTOR_RELACIONADOS  = "yt-lockup-view-model a[href*='/watch?v=']"
SELECTOR_VIDEO         = "video"

# YouTube abrevia las fechas en los resultados ("hace 5 m" son meses, no minutos).
_FECHA_CORTA = re.compile(r"^hace (\d+) (a|m|sem)\.?$")
_FECHA_LARGA = {"a": ("año", "años"), "m": ("mes", "meses"), "sem": ("semana", "semanas")}


def _fecha(texto):
    texto = arnes_youtube.limpiar_texto(texto, arnes_youtube.LARGO_MAX_FECHA)
    corta = _FECHA_CORTA.match(texto)
    if not corta:
        return texto
    numero, unidad = corta.groups()
    singular, plural = _FECHA_LARGA[unidad]
    return f"hace {numero} {singular if numero == '1' else plural}"


class YouTube:

    def __init__(self, navegador):
        self.navegador = navegador

    def _en_youtube(self, guion, arg=None, ir_a=None, esperar=None):
        return self.navegador.en_sitio(reglas.YOUTUBE_DOMINIOS, guion, arg, ir_a=ir_a, esperar=esperar)

    @staticmethod
    def _videos(crudos, maximo):
        """Lo leído de la página → [{url, titulo, canal}] válidos, sin repetir."""
        videos, vistas = [], set()
        for crudo in crudos if isinstance(crudos, list) else []:
            if not isinstance(crudo, dict):
                continue
            try:
                url = arnes_youtube.url_video(crudo.get("enlace"))
            except Denegado:
                continue
            titulo = arnes_youtube.limpiar_texto(crudo.get("titulo"), arnes_youtube.LARGO_MAX_TITULO)
            if not titulo or url in vistas:
                continue
            vistas.add(url)
            videos.append({"url": url, "titulo": titulo,
                           "canal": arnes_youtube.limpiar_texto(crudo.get("canal"), arnes_youtube.LARGO_MAX_CANAL),
                           "publicado": _fecha(crudo.get("publicado"))})
            if len(videos) >= maximo:
                break
        return videos

    def buscar(self, consulta):
        """Abre la búsqueda en la pestaña de YouTube y devuelve los primeros vídeos."""
        crudos = self._en_youtube(GUION_VIDEOS, arnes_youtube.MAX_RESULTADOS * 3,
                                  ir_a=arnes_youtube.url_busqueda(consulta), esperar=SELECTOR_RESULTADOS)
        return self._videos(crudos, arnes_youtube.MAX_RESULTADOS)

    def _videos_de_canal(self, enlace, nombre, maximo):
        """{"nombre", "videos"} de la pestaña Vídeos de un canal: del más nuevo al más viejo."""
        crudos = self._en_youtube(GUION_VIDEOS, maximo * 3, ir_a=arnes_youtube.url_videos_de_canal(enlace),
                                  esperar=SELECTOR_VIDEOS_CANAL)
        videos = self._videos(crudos, maximo)
        nombre = arnes_youtube.limpiar_texto(nombre, arnes_youtube.LARGO_MAX_CANAL)
        for video in videos:   # en su propia página, el canal no siempre aparece en cada vídeo
            video["canal"] = nombre or video["canal"]
        return {"nombre": nombre, "videos": videos}

    def canal(self, nombre, maximo=arnes_youtube.MAX_RESULTADOS):
        """
        Los últimos vídeos del canal que mejor coincide con `nombre` (el primero
        de una búsqueda de canales), o None si no hay ninguno.
        """
        canal = self._en_youtube(GUION_PRIMER_CANAL, ir_a=arnes_youtube.url_busqueda_canales(nombre),
                                 esperar=SELECTOR_CANALES)
        if not isinstance(canal, dict):
            return None
        try:
            return self._videos_de_canal(canal.get("enlace"), canal.get("nombre"), maximo)
        except Denegado:
            return None

    def video_abierto(self):
        """{"url", "canal", "nombre_canal"} del vídeo de la pestaña de YouTube, o None."""
        abierto = self._en_youtube(GUION_VIDEO_ABIERTO)
        if not isinstance(abierto, dict):
            return None
        try:
            url = arnes_youtube.url_video(abierto.get("enlace"))
        except Denegado:
            return None
        return {"url": url, "canal": abierto.get("canal") or "", "nombre_canal": abierto.get("nombre_canal")}

    def relacionados(self, maximo=15):
        """Los que YouTube muestra junto al vídeo abierto (sin navegar: ya están en la página)."""
        crudos = self._en_youtube(GUION_VIDEOS, maximo * 2, esperar=SELECTOR_RELACIONADOS)
        return self._videos(crudos, maximo)

    def del_mismo_canal(self, canal, nombre, maximo=15):
        """Los últimos vídeos del canal del vídeo abierto (canal = su enlace, "/@nombre")."""
        return self._videos_de_canal(canal, nombre, maximo)["videos"]

    def recomendado(self):
        """El primer vídeo de la portada, o None si no tiene (sin sesión ni historial)."""
        crudos = self._en_youtube(GUION_VIDEOS, 10, ir_a=reglas.YOUTUBE_URL, esperar=SELECTOR_PORTADA)
        videos = self._videos(crudos, 1)
        return videos[0] if videos else None

    def reproducir(self, url):
        self._en_youtube(GUION_ARRANCAR, ir_a=arnes_youtube.url_video(url), esperar=SELECTOR_VIDEO)

    def estado(self):
        """{"pausado": bool} si hay un vídeo abierto; None si no (sin abrir el navegador)."""
        if not any(host_en(p.url, reglas.YOUTUBE_DOMINIOS) for p in self.navegador.pestanas()):
            return None
        estado = self._en_youtube(GUION_ESTADO)
        return {"pausado": bool(estado.get("pausado"))} if isinstance(estado, dict) else None

    def control(self, accion):
        """"ok", "sin_video", "sin_siguiente" o "bloqueado"."""
        resultado = self._en_youtube(GUION_CONTROL, arnes_youtube.validar_control(accion))
        return resultado if resultado in ("ok", "sin_video", "sin_siguiente", "bloqueado") else "sin_video"

