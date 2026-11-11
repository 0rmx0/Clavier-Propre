"""Pilotage de la correction automatique de WordCraft (storytold/wordcraft).

WordCraft est un traitement de texte open source (Rust) qui stocke ses
préférences dans ``ui.json``, dans son dossier de paramètres :
``%APPDATA%\\WordCraft`` sous Windows (``WORDCRAFT_PROFILE_DIR`` permet de
déplacer tout le profil). Le fichier est du JSON ``camelCase`` ; les champs
qui nous intéressent :

- ``checkSpelling`` (racine) : « Check spelling as you type » persisté (#1792) ;
- ``editing.checkSpelling`` / ``editing.markGrammar`` : mêmes réglages, copie
  « editing » des préférences de session ;
- ``editing.autocorrect`` : objet ``AutoCorrectPrefs`` ; ``enabled=false``
  désactive toute la correction/formatage automatique pendant la saisie.

    active=True  -> on DÉSACTIVE la correction (mode « propre »)
    active=False -> on RÉACTIVE la correction (comportement normal)

WordCraft lit ``ui.json`` au démarrage et le réécrit à la fermeture : si
l'application tourne pendant qu'on modifie le fichier, elle peut écraser le
changement à sa sortie. Le watchdog de Clavier-Propre réapplique donc
périodiquement la protection. Les valeurs d'origine sont sauvegardées dans la
configuration de Clavier-Propre pour une restauration fidèle.
"""
from __future__ import annotations

import json
import logging
import os
import platform
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

_IS_WINDOWS = platform.system() == "Windows"

# Champs « autocorrect » basculés à False quand la protection est active.
# (Les listes utilisateur — entries, removed, exceptions… — ne sont pas touchées.)
_AUTOCORRECT_FLAGS = (
    "enabled",
    "replaceText",
    "twoInitialCaps",
    "capSentences",
    "capCells",
    "capDays",
    "capsLock",
    "smartQuotes",
    "fractions",
    "ordinals",
    "boldItalic",
    "dashes",
    "links",
    "bullets",
    "numbering",
    "borderLines",
    "tabIndent",
    "headingStyles",
    "doubleSpacePeriod",
)


@dataclass(frozen=True)
class WordcraftState:
    # ``True`` = la correction est actuellement DÉSACTIVÉE dans ui.json.
    protected: bool


def settings_dir() -> Path | None:
    """Dossier de paramètres de WordCraft (préférences, logs, clés)."""
    override = os.environ.get("WORDCRAFT_PROFILE_DIR")
    if override:
        return Path(override)
    if _IS_WINDOWS:
        appdata = os.environ.get("APPDATA")
        return Path(appdata) / "WordCraft" if appdata else None
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / "wordcraft"


def prefs_path() -> Path | None:
    """Chemin du fichier ``ui.json`` de WordCraft."""
    base = settings_dir()
    return base / "ui.json" if base is not None else None


def find_wordcraft() -> str | None:
    """Retourne le chemin de l'exécutable WordCraft s'il est installé."""
    candidates: list[Path] = []
    if _IS_WINDOWS:
        for env_name in ("LOCALAPPDATA", "PROGRAMFILES", "PROGRAMFILES(X86)"):
            base = os.environ.get(env_name)
            if base:
                candidates.append(
                    Path(base) / "Programs" / "ArtCraft" / "WordCraft" / "wordcraft.exe"
                    if env_name == "LOCALAPPDATA"
                    else Path(base) / "ArtCraft" / "WordCraft" / "wordcraft.exe"
                )
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return shutil.which("wordcraft") or shutil.which("wordcraft.exe")


def is_installed() -> bool:
    """Vrai si WordCraft est installé (exécutable trouvé) ou si un ``ui.json``
    existe déjà (l'utilisateur s'en est servi au moins une fois)."""
    if find_wordcraft() is not None:
        return True
    path = prefs_path()
    return path is not None and path.exists()


def _read_ui(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except (json.JSONDecodeError, OSError, UnicodeDecodeError) as exc:
        log.warning("ui.json de WordCraft illisible (%s) : on repart d'un objet vide.", exc)
        return {}
    return data if isinstance(data, dict) else {}


def _write_ui(path: Path, ui: dict[str, Any]) -> None:
    """Écriture atomique (fichier temporaire + renommage), comme WordCraft."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(ui, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)


def _extract_originals(ui: dict[str, Any]) -> dict[str, Any]:
    editing = ui.get("editing") if isinstance(ui.get("editing"), dict) else {}
    autocorrect = editing.get("autocorrect")
    return {
        "checkSpelling": ui.get("checkSpelling", True),
        "editing": {
            "checkSpelling": editing.get("checkSpelling", True),
            "markGrammar": editing.get("markGrammar", True),
            "autocorrect": dict(autocorrect) if isinstance(autocorrect, dict) else {},
        },
    }


def _apply_values(ui: dict[str, Any], active: bool, saved: dict[str, Any] | None) -> None:
    if active:
        ui["checkSpelling"] = False
        editing = ui.setdefault("editing", {})
        if not isinstance(editing, dict):
            editing = {}
            ui["editing"] = editing
        editing["checkSpelling"] = False
        editing["markGrammar"] = False
        autocorrect = editing.setdefault("autocorrect", {})
        if not isinstance(autocorrect, dict):
            autocorrect = {}
            editing["autocorrect"] = autocorrect
        for flag in _AUTOCORRECT_FLAGS:
            autocorrect[flag] = False
        return

    # Réactivation : on restaure les valeurs d'origine sauvegardées, sinon les
    # défauts de WordCraft (correction active).
    saved = saved or {}
    saved_editing = saved.get("editing") if isinstance(saved.get("editing"), dict) else {}
    saved_autocorrect = (
        saved_editing.get("autocorrect")
        if isinstance(saved_editing.get("autocorrect"), dict)
        else {}
    )
    ui["checkSpelling"] = saved.get("checkSpelling", True)
    editing = ui.setdefault("editing", {})
    if not isinstance(editing, dict):
        editing = {}
        ui["editing"] = editing
    editing["checkSpelling"] = saved_editing.get("checkSpelling", True)
    editing["markGrammar"] = saved_editing.get("markGrammar", True)
    autocorrect = editing.setdefault("autocorrect", {})
    if not isinstance(autocorrect, dict):
        autocorrect = {}
        editing["autocorrect"] = autocorrect
    if saved_autocorrect:
        for flag in _AUTOCORRECT_FLAGS:
            if flag in saved_autocorrect:
                autocorrect[flag] = saved_autocorrect[flag]
            else:
                autocorrect.pop(flag, None)
    else:
        for flag in _AUTOCORRECT_FLAGS:
            autocorrect[flag] = True


def get_state() -> WordcraftState:
    """État courant lu dans ``ui.json`` : ``protected=True`` si la correction
    y est désactivée. Fichier absent = non protégé (défaut WordCraft = actif)."""
    path = prefs_path()
    if path is None or not path.exists():
        return WordcraftState(protected=False)
    ui = _read_ui(path)
    editing = ui.get("editing") if isinstance(ui.get("editing"), dict) else {}
    top = ui.get("checkSpelling", True)
    inner = editing.get("checkSpelling", True)
    return WordcraftState(protected=(top is False) or (inner is False))


def apply_wordcraft_protection(active: bool) -> bool:
    """``active=True`` : désactive la correction automatique de WordCraft.
    ``active=False`` : la réactive (restauration des valeurs d'origine).
    Retourne ``True`` si le fichier a été écrit."""
    path = prefs_path()
    if path is None:
        log.info("Dossier de paramètres WordCraft introuvable : rien à piloter.")
        return False
    if not is_installed():
        log.info("WordCraft non détecté : aucune correction WordCraft à piloter.")
        return False

    from clavier_propre.config import AppConfig

    config = AppConfig.load()
    ui = _read_ui(path)

    if active:
        # On ne sauvegarde les valeurs d'origine qu'une fois : un ré-apply
        # (watchdog) ne doit pas écraser la sauvegarde par les valeurs « off ».
        if not config.saved_wordcraft_ui:
            config.saved_wordcraft_ui = _extract_originals(ui)
            config.save()
        _apply_values(ui, active=True, saved=None)
    else:
        _apply_values(ui, active=False, saved=config.saved_wordcraft_ui)
        config.saved_wordcraft_ui = {}
        config.save()

    try:
        _write_ui(path, ui)
    except OSError as exc:
        log.warning("Impossible d'écrire %s: %s", path, exc)
        return False

    log.info("Correction WordCraft réglée via %s sur active=%s", path, active)
    return True
