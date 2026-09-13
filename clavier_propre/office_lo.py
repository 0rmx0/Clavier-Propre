"""Pilotage de la correction automatique de LibreOffice via l'API UNO.

LibreOffice expose un service UNO accessible depuis Python par le module
``uno`` livré avec la suite. On se connecte à une instance en cours d'exécution
(démarrée en mode écoute socket) ou, à défaut, on pilote les préférences via le
fichier de configuration utilisateur.

    active=True  -> on DÉSACTIVE la correction (mode « propre »)
    active=False -> on RÉACTIVE la correction (comportement normal)

L'activation/désactivation se fait en éditant la valeur
``IsAutoSpellCheck`` du nœud de configuration
``org.openoffice.Office.Writer``. Cette modification est prise en compte par
les documents ouverts et persiste pour les prochains lancements.
"""
from __future__ import annotations

import logging
import os
import platform
import shutil
import subprocess
from pathlib import Path

log = logging.getLogger(__name__)

_IS_WINDOWS = platform.system() == "Windows"

# Nœud de configuration LibreOffice régissant l'auto-spellcheck.
_CONFIG_NODE = "org.openoffice.Office.Writer"
_CONFIG_KEY = "IsAutoSpellCheck"


def _find_soffice() -> str | None:
    candidates = []
    if _IS_WINDOWS:
        env_candidates = os.environ.get("PROGRAMFILES")
        if env_candidates:
            candidates.append(Path(env_candidates) / "LibreOffice" / "program" / "soffice.exe")
        env_x86 = os.environ.get("PROGRAMFILES(X86)")
        if env_x86:
            candidates.append(Path(env_x86) / "LibreOffice" / "program" / "soffice.exe")
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    found = shutil.which("soffice") or shutil.which("soffice.exe")
    return found


def _connect_uno():
    """Tente d'importer le module ``uno`` et de se connecter à une instance
    LibreOffice en cours d'exécution. Retourne ``(None, None)`` si impossible."""
    try:
        import uno  # type: ignore[import-not-found]
        from com.sun.star.beans import PropertyValue  # type: ignore[import-not-found]
    except ImportError:
        log.info("Module uno indisponible : pilotage UNO direct impossible.")
        return None, None

    try:
        local_context = uno.getComponentContext()
        resolver = local_context.ServiceManager.createInstanceWithContext(
            "com.sun.star.bridge.UnoUrlResolver", local_context
        )
        ctx = resolver.resolve(
            "uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext"
        )
        smgr = ctx.ServiceManager
        desktop = smgr.createInstanceWithContext(
            "com.sun.star.frame.Desktop", ctx
        )
        return ctx, desktop
    except Exception as exc:
        log.debug("Connexion UNO échouée: %s", exc)
        return None, None


def _set_config_uno(ctx, active: bool) -> bool:
    """Modifie le nœud de configuration via l'API UNO ConfigurationProvider."""
    try:
        import uno  # type: ignore[import-not-found]
        from com.sun.star.beans import PropertyValue  # type: ignore[import-not-found]
    except ImportError:
        return False
    try:
        smgr = ctx.ServiceManager
        provider = smgr.createInstanceWithContext(
            "com.sun.star.configuration.ConfigurationProvider", ctx
        )
        node_args = PropertyValue()
        node_args.Name = "nodepath"
        node_args.Value = _CONFIG_NODE
        node_args_2 = PropertyValue()
        node_args_2.Name = "EnableAsync"
        node_args_2.Value = False
        access = provider.createInstanceWithArguments(
            "com.sun.star.configuration.ConfigurationUpdateAccess",
            (node_args, node_args_2),
        )
        access.setPropertyValue(_CONFIG_KEY, not active)
        access.commitChanges()
        return True
    except Exception as exc:  # pragma: no cover
        log.warning("Échec mise à jour config UNO: %s", exc)
        return False


def _bootstrap_sozi(path: str):
    """Démarre une instance soffice en mode écoute socket si aucune n'existe.
    Cela permet le pilotage UNO sans intervention manuelle de l'utilisateur."""
    try:
        subprocess.Popen(
            [
                path,
                "--headless",
                "--norestore",
                "--nologo",
                "--accept=socket,host=localhost,port=2002;urp;",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as exc:  # pragma: no cover
        log.warning("Impossible de démarrer LibreOffice en mode écoute: %s", exc)


def apply_libreoffice_protection(active: bool) -> None:
    """``active=True`` : désactive la correction automatique de LibreOffice.
    ``active=False`` : la réactive."""
    if not _IS_WINDOWS:
        log.info("Hors Windows : gestion LibreOffice ignorée.")
        return

    ctx, desktop = _connect_uno()
    if ctx is None:
        soffice = _find_soffice()
        if soffice is None:
            log.info("LibreOffice non installé : aucune correction LO à piloter.")
            return
        _bootstrap_sozi(soffice)
        import time

        time.sleep(3)
        ctx, desktop = _connect_uno()

    if ctx is None:
        log.warning("Connexion à LibreOffice impossible : correction LO non modifiée.")
        return

    if _set_config_uno(ctx, active):
        log.info("Correction LibreOffice réglée via UNO sur active=%s", active)
    else:
        log.warning("Échec de la mise à jour de la correction LibreOffice.")
