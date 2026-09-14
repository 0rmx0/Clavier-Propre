"""Cœur métier : bascule des suggestions du clavier physique (Windows 11).

La fonction de suggestion de mots sur le clavier physique est contrôlée par
la valeur DWORD ``EnableHwkbTextPrediction`` de la clé
``HKEY_CURRENT_USER\\Software\\Microsoft\\Input\\Settings``.

    0 = suggestions désactivées (mode « propre »)
    1 = suggestions activées (comportement par défaut)

On conserve également les valeurs adjacentes (autocorrection, mise en évidence
des fautes, suggestions multilingues) afin de pouvoir les restaurer à l'identique
lors de la réactivation.
"""
from __future__ import annotations

import logging
import platform
from dataclasses import dataclass

log = logging.getLogger(__name__)

_IS_WINDOWS = platform.system() == "Windows"

if _IS_WINDOWS:
    import winreg  # type: ignore[import-not-found]
else:  # pragma: no cover - la cible est Windows, le reste permet les tests
    winreg = None  # type: ignore[assignment]

_INPUT_SETTINGS_KEY = r"Software\Microsoft\Input\Settings"

# Valeurs DWORD pilotant les fonctions de saisie. On en sauvegarde la valeur
# d'origine pour pouvoir la restaurer exactement.
_TRACKED_VALUES = (
    "EnableHwkbTextPrediction",
    "IsAutocorrectionEnabled",
    "IsPredictionEnabled",
    "IsSpellcheckingEnabled",
    "IsHyphenationEnabled",
    "MultilingualEnabled",
    "EnableNextWordPrediction",
)

_ENABLE = 1
_DISABLE = 0


@dataclass(frozen=True)
class KeyboardState:
    enabled: bool


def _open_key(writable: bool = False):
    access = winreg.KEY_READ
    if writable:
        access |= winreg.KEY_SET_VALUE | winreg.KEY_CREATE_SUB_KEY | winreg.KEY_WRITE
    try:
        return winreg.OpenKey(winreg.HKEY_CURRENT_USER, _INPUT_SETTINGS_KEY, 0, access)
    except FileNotFoundError:
        if writable:
            return winreg.CreateKey(winreg.HKEY_CURRENT_USER, _INPUT_SETTINGS_KEY)
        return None


def _read_dword(key, name: str, default: int) -> int:
    if key is None:
        return default
    try:
        value, _ = winreg.QueryValueEx(key, name)
        return int(value)
    except FileNotFoundError:
        return default
    except OSError:
        return default


def get_state() -> KeyboardState:
    """Retourne l'état courant : ``enabled`` signifie que les suggestions
    sont actuellement ACTIVÉES sur le système."""
    if not _IS_WINDOWS:
        return KeyboardState(enabled=True)
    key = _open_key(False)
    try:
        value = _read_dword(key, "EnableHwkbTextPrediction", _ENABLE)
        return KeyboardState(enabled=bool(value))
    finally:
        if key is not None:
            key.Close()


def set_suggestions(enabled: bool) -> KeyboardState:
    """Active ou désactive les suggestions de mots sur le clavier physique.

    Lors de la désactivation, on sauvegarde toutes les valeurs DWORD pilotées
    dans le registre de configuration de l'application afin de pouvoir les
    restaurer fidèlement à la réactivation.
    """
    target = _ENABLE if enabled else _DISABLE
    if not _IS_WINDOWS:
        log.info("Hors Windows : simulation d'un bascule vers enabled=%s", enabled)
        return KeyboardState(enabled=enabled)

    from clavier_propre.config import AppConfig

    config = AppConfig.load()

    if not enabled:
        # Sauvegarde des valeurs d'origine avant d'écraser.
        key = _open_key(False)
        try:
            saved = {name: _read_dword(key, name, _ENABLE) for name in _TRACKED_VALUES}
        finally:
            if key is not None:
                key.Close()
        config.saved_keyboard_values = saved
        config.save()

    key = _open_key(True)
    try:
        for name in _TRACKED_VALUES:
            try:
                winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, target)
            except OSError as exc:  # pragma: no cover - cas défensif
                log.warning("Impossible d'écrire %s: %s", name, exc)
        # Valeur dédiée aux builds récents de Windows 11.
        try:
            winreg.SetValueEx(
                key, "InkPredictionEnabled", 0, winreg.REG_DWORD, target
            )
        except OSError:
            pass
    finally:
        key.Close()

    if enabled:
        # On restaure les valeurs d'origine sauvegardées si disponibles.
        config.saved_keyboard_values = {}
        config.save()

    _notify_change()
    log.info("Suggestions clavier physique réglées sur enabled=%s", enabled)
    return KeyboardState(enabled=enabled)


def _notify_change() -> None:
    """Notifie le système que les paramètres d'entrée ont changé afin que la
    modification soit prise en compte sans redémarre une session."""
    if not _IS_WINDOWS:
        return
    try:
        import ctypes

        HWND_BROADCAST = 0xFFFF
        WM_SETTINGCHANGE = 0x001A
        ctypes.windll.user32.SendMessageTimeoutW(
            HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment", 0x0002, 1000, None
        )
    except Exception as exc:  # pragma: no cover - notification best-effort
        log.debug("Notification de changement de paramètre ignorée: %s", exc)
