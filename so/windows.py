"""
ControlSO sobre Windows, con ctypes (sin dependencias).

Fase 10.1: lectura. Las llamadas de consulta (EnumWindows, GetWindowText,
GetSystemPowerStatus...) y los procesos se abren con
PROCESS_QUERY_LIMITED_INFORMATION, que solo permite preguntar su nombre: ni
leer su memoria ni terminarlos.

Fase 10.2: abrir apps de la lista blanca (sin consola, con un entorno sin
secretos), teclas multimedia y el volumen general (Core Audio).
"""
import ctypes
import os
import platform
import shutil
import subprocess
from ctypes import wintypes

from core import memory
from core.arnes import reglas, sistema
from core.arnes.rutas import Denegado
from so.base import ControlSO, Ventana

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
GWL_EXSTYLE        = -20
WS_EX_TOOLWINDOW   = 0x00000080
WS_EX_APPWINDOW    = 0x00040000
GW_OWNER           = 4
DWMWA_CLOAKED      = 14
SIN_BATERIA        = 128

_user32   = ctypes.WinDLL("user32", use_last_error=True)
_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
_dwmapi   = ctypes.WinDLL("dwmapi")

_WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

_user32.EnumWindows.argtypes              = [_WNDENUMPROC, wintypes.LPARAM]
_user32.IsWindowVisible.argtypes          = [wintypes.HWND]
_user32.GetWindowTextLengthW.argtypes     = [wintypes.HWND]
_user32.GetWindowTextW.argtypes           = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
_user32.GetWindowLongW.argtypes           = [wintypes.HWND, ctypes.c_int]
_user32.GetWindowLongW.restype            = ctypes.c_long
_user32.GetWindow.argtypes                = [wintypes.HWND, wintypes.UINT]
_user32.GetWindow.restype                 = wintypes.HWND
_user32.GetForegroundWindow.restype       = wintypes.HWND
_user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
_dwmapi.DwmGetWindowAttribute.argtypes    = [wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD]
_kernel32.OpenProcess.argtypes            = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
_kernel32.OpenProcess.restype             = wintypes.HANDLE
_kernel32.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR,
                                                 ctypes.POINTER(wintypes.DWORD)]
_kernel32.CloseHandle.argtypes            = [wintypes.HANDLE]
_kernel32.GetTickCount64.restype          = ctypes.c_ulonglong


class _EstadoEnergia(ctypes.Structure):
    _fields_ = [("ACLineStatus", wintypes.BYTE), ("BatteryFlag", wintypes.BYTE),
                ("BatteryLifePercent", wintypes.BYTE), ("SystemStatusFlag", wintypes.BYTE),
                ("BatteryLifeTime", wintypes.DWORD), ("BatteryFullLifeTime", wintypes.DWORD)]


class _EstadoMemoria(ctypes.Structure):
    _fields_ = [("dwLength", wintypes.DWORD), ("dwMemoryLoad", wintypes.DWORD),
                ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]


def _titulo(hwnd):
    largo = _user32.GetWindowTextLengthW(hwnd)
    if largo <= 0:
        return ""
    buffer = ctypes.create_unicode_buffer(largo + 1)
    _user32.GetWindowTextW(hwnd, buffer, largo + 1)
    return buffer.value


def _oculta(hwnd):
    """Ventanas "cloaked": UWP suspendidas, otros escritorios virtuales..."""
    cloaked = ctypes.c_int(0)
    _dwmapi.DwmGetWindowAttribute(hwnd, DWMWA_CLOAKED, ctypes.byref(cloaked), ctypes.sizeof(cloaked))
    return cloaked.value != 0


def _es_de_alt_tab(hwnd):
    if not _user32.IsWindowVisible(hwnd) or _oculta(hwnd):
        return False
    estilo = _user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    if estilo & WS_EX_TOOLWINDOW:
        return False
    return not _user32.GetWindow(hwnd, GW_OWNER) or bool(estilo & WS_EX_APPWINDOW)


def _proceso(hwnd):
    pid = wintypes.DWORD()
    _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    proceso = _kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
    if not proceso:
        return ""   # p. ej. un proceso elevado visto desde uno normal
    try:
        tamano = wintypes.DWORD(1024)
        buffer = ctypes.create_unicode_buffer(tamano.value)
        if _kernel32.QueryFullProcessImageNameW(proceso, 0, buffer, ctypes.byref(tamano)):
            return os.path.basename(buffer.value)
        return ""
    finally:
        _kernel32.CloseHandle(proceso)


class WindowsSO(ControlSO):

    def ventanas(self):
        activa = _user32.GetForegroundWindow()
        encontradas = []

        def visitar(hwnd, _):
            if _es_de_alt_tab(hwnd):
                titulo = _titulo(hwnd)
                if titulo:
                    encontradas.append(Ventana(titulo, _proceso(hwnd), hwnd == activa))
            return True

        _user32.EnumWindows(_WNDENUMPROC(visitar), 0)
        return encontradas

    def info_sistema(self):
        energia = _EstadoEnergia()
        hay_energia = _kernel32.GetSystemPowerStatus(ctypes.byref(energia))
        sin_bateria = not hay_energia or energia.BatteryFlag & SIN_BATERIA or energia.BatteryLifePercent == 255

        memoria = _EstadoMemoria()
        memoria.dwLength = ctypes.sizeof(_EstadoMemoria)
        _kernel32.GlobalMemoryStatusEx(ctypes.byref(memoria))

        disco = shutil.disk_usage(os.environ.get("SystemDrive", "C:") + "\\")

        return {
            "sistema":       f"Windows {platform.release()} ({platform.version()})",
            "encendido_seg": _kernel32.GetTickCount64() // 1000,
            "bateria_pct":   None if sin_bateria else int(energia.BatteryLifePercent),
            "cargando":      None if sin_bateria else energia.ACLineStatus == 1,
            "ram_total":     memoria.ullTotalPhys,
            "ram_libre":     memoria.ullAvailPhys,
            "disco_total":   disco.total,
            "disco_libre":   disco.free,
        }

    # ─── Fase 10.2 ───────────────────────────────────────────────────────────

    def abrir_app(self, ruta, argumentos):
        permitidos = [reglas.argumentos_app(nombre) for nombre in reglas.apps_permitidas()]
        if list(argumentos) not in permitidos:
            raise Denegado("esos argumentos no son los fijos de la app")
        if list(argumentos) == reglas.argumentos_app("navegador"):
            _preparar_perfil_navegador()
        _lanzar(ruta, list(argumentos))

    def abrir_url(self, url):
        url = sistema.validar_url(url)
        ruta, argumentos = sistema.resolver_app("navegador")
        _preparar_perfil_navegador()
        _lanzar(ruta, [*argumentos, url])

    def multimedia(self, accion):
        tecla = _TECLAS_MULTIMEDIA[sistema.validar_multimedia(accion)]
        _user32.keybd_event(tecla, 0, KEYEVENTF_EXTENDEDKEY, 0)
        _user32.keybd_event(tecla, 0, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0)

    def volumen(self):
        return _con_volumen(_leer_volumen)

    def fijar_volumen(self, porcentaje):
        _, porcentaje = sistema.validar_volumen("fijar", porcentaje)
        _con_volumen(lambda endpoint: _escribir_volumen(endpoint, porcentaje))

    def silenciar(self, silenciado):
        _con_volumen(lambda endpoint: _escribir_mute(endpoint, silenciado))


# ─── Fase 10.2: abrir apps ───────────────────────────────────────────────────

_SIN_CONSOLA = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP

# Preferencias iniciales del perfil del navegador de CAIN: pregunta antes de
# descargar y no concede cámara, micrófono, ubicación ni notificaciones.
_PREFERENCIAS_NAVEGADOR = {
    "download": {"prompt_for_download": True},
    "profile": {"default_content_setting_values": {
        "notifications": 2, "geolocation": 2,
        "media_stream_camera": 2, "media_stream_mic": 2,
    }},
}


def _entorno_app():
    return {k: v for k, v in os.environ.items() if k.upper() in reglas.ENTORNO_APPS}


def _lanzar(ruta, argumentos):
    """Abre el programa sin consola y sin esperarlo. Nunca con shell."""
    if not sistema.es_ejecutable_permitido(ruta):
        raise Denegado("ese programa no está en la lista de apps permitidas")
    subprocess.Popen(
        [ruta, *argumentos],
        cwd=os.path.dirname(ruta),
        env=_entorno_app(),
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        close_fds=True, creationflags=_SIN_CONSOLA,
    )


def _preparar_perfil_navegador():
    """La primera vez, crea el perfil de CAIN con preferencias prudentes."""
    preferencias = os.path.join(reglas.CARPETA_NAVEGADOR, "Default", "Preferences")
    if not os.path.exists(preferencias):
        os.makedirs(os.path.dirname(preferencias), exist_ok=True)
        memory._guardar_json(preferencias, _PREFERENCIAS_NAVEGADOR)


# ─── Fase 10.2: teclas multimedia ────────────────────────────────────────────

KEYEVENTF_EXTENDEDKEY = 0x1
KEYEVENTF_KEYUP       = 0x2
_TECLAS_MULTIMEDIA = {
    "siguiente":         0xB0,   # VK_MEDIA_NEXT_TRACK
    "anterior":          0xB1,   # VK_MEDIA_PREV_TRACK
    "reproducir_pausar": 0xB3,   # VK_MEDIA_PLAY_PAUSE
}

_user32.keybd_event.argtypes = [wintypes.BYTE, wintypes.BYTE, wintypes.DWORD, ctypes.c_size_t]


# ─── Fase 10.2: volumen (Core Audio, IAudioEndpointVolume) ───────────────────

class _GUID(ctypes.Structure):
    _fields_ = [("Data1", wintypes.DWORD), ("Data2", wintypes.WORD),
                ("Data3", wintypes.WORD), ("Data4", ctypes.c_ubyte * 8)]


_ole32 = ctypes.OleDLL("ole32")
_ole32.CLSIDFromString.argtypes  = [wintypes.LPCWSTR, ctypes.POINTER(_GUID)]
_ole32.CoInitializeEx.argtypes   = [ctypes.c_void_p, wintypes.DWORD]
_ole32.CoInitializeEx.restype    = ctypes.c_long   # S_FALSE no es error: se mira a mano
_ole32.CoUninitialize.restype    = None
_ole32.CoCreateInstance.argtypes = [ctypes.POINTER(_GUID), ctypes.c_void_p, wintypes.DWORD,
                                    ctypes.POINTER(_GUID), ctypes.POINTER(ctypes.c_void_p)]

CLSID_MMDeviceEnumerator = "BCDE0395-E52F-467C-8E3D-C4579291692E"
IID_IMMDeviceEnumerator  = "A95664D2-9614-4F35-A746-DE8DB63617E6"
IID_IAudioEndpointVolume = "5CDF2C82-841E-4546-9722-0CF74078229A"
CLSCTX_ALL               = 0x17
COINIT_APARTMENTTHREADED = 0x2
E_RENDER, E_MULTIMEDIA   = 0, 1

# Índices en la vtable de IAudioEndpointVolume
_SET_NIVEL, _GET_NIVEL, _SET_MUTE, _GET_MUTE = 7, 9, 14, 15


def _guid(texto):
    guid = _GUID()
    _ole32.CLSIDFromString("{" + texto + "}", ctypes.byref(guid))
    return guid


def _metodo(objeto, indice, *argtypes):
    """Método `indice` de la vtable de un objeto COM (puntero en un c_void_p)."""
    vtable = ctypes.cast(objeto, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
    funcion = ctypes.WINFUNCTYPE(ctypes.HRESULT, ctypes.c_void_p, *argtypes)(vtable[indice])
    return lambda *args: funcion(objeto, *args)


def _liberar(objeto):
    if objeto:
        vtable = ctypes.cast(objeto, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
        ctypes.WINFUNCTYPE(wintypes.ULONG, ctypes.c_void_p)(vtable[2])(objeto)


def _con_volumen(operacion):
    """
    Llama a operacion(endpoint) con el IAudioEndpointVolume del altavoz por
    defecto. Inicializa COM en este hilo si hace falta (cada turno de CAIN
    puede correr en un hilo distinto).
    """
    hr = _ole32.CoInitializeEx(None, COINIT_APARTMENTTHREADED)
    inicializado = hr in (0, 1)   # S_OK, S_FALSE; si no, ya estaba en otro modo
    enumerador, dispositivo, endpoint = ctypes.c_void_p(), ctypes.c_void_p(), ctypes.c_void_p()
    try:
        _ole32.CoCreateInstance(ctypes.byref(_guid(CLSID_MMDeviceEnumerator)), None, CLSCTX_ALL,
                                ctypes.byref(_guid(IID_IMMDeviceEnumerator)), ctypes.byref(enumerador))
        # IMMDeviceEnumerator::GetDefaultAudioEndpoint
        _metodo(enumerador, 4, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_void_p))(
            E_RENDER, E_MULTIMEDIA, ctypes.byref(dispositivo))
        # IMMDevice::Activate
        _metodo(dispositivo, 3, ctypes.POINTER(_GUID), wintypes.DWORD, ctypes.c_void_p,
                ctypes.POINTER(ctypes.c_void_p))(
            ctypes.byref(_guid(IID_IAudioEndpointVolume)), CLSCTX_ALL, None, ctypes.byref(endpoint))
        return operacion(endpoint)
    finally:
        for objeto in (endpoint, dispositivo, enumerador):
            _liberar(objeto)
        if inicializado:
            _ole32.CoUninitialize()


def _leer_volumen(endpoint):
    nivel, mute = ctypes.c_float(), wintypes.BOOL()
    _metodo(endpoint, _GET_NIVEL, ctypes.POINTER(ctypes.c_float))(ctypes.byref(nivel))
    _metodo(endpoint, _GET_MUTE, ctypes.POINTER(wintypes.BOOL))(ctypes.byref(mute))
    return round(nivel.value * 100), bool(mute.value)


def _escribir_mute(endpoint, silenciado):
    _metodo(endpoint, _SET_MUTE, wintypes.BOOL, ctypes.c_void_p)(bool(silenciado), None)


def _escribir_volumen(endpoint, porcentaje):
    _metodo(endpoint, _SET_NIVEL, ctypes.c_float, ctypes.c_void_p)(porcentaje / 100, None)
    _escribir_mute(endpoint, False)
