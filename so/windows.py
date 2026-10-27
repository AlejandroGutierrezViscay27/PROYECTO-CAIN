"""
ControlSO sobre Windows, con ctypes (sin dependencias).

Fase 10.1: solo lectura. Las únicas llamadas a la API de Windows son de
consulta (EnumWindows, GetWindowText, GetSystemPowerStatus...). Los
procesos se abren con PROCESS_QUERY_LIMITED_INFORMATION, que solo permite
preguntar su nombre: ni leer su memoria ni terminarlos.
"""
import ctypes
import os
import platform
import shutil
from ctypes import wintypes

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
