"""Détails de l'installation en tant que service Windows natif (pywin32)."""
from __future__ import annotations

import logging
import sys

log = logging.getLogger(__name__)

SERVICE_NAME = "ClavierPropre"
SERVICE_DISPLAY = "Clavier-Propre — Protection clavier"


def install_service() -> int:
    """Installe l'exécutable courant en tant que service Windows automatique.
    Nécessite pywin32 et d'être lancé en administrateur."""
    try:
        import servicemanager  # type: ignore[import-not-found]
        import win32serviceutil  # type: ignore[import-not-found]
    except ImportError:
        log.error("pywin32 requis pour installer le service.")
        return 1

    try:
        from clavier_propre.win_service import ClavierPropreService
    except Exception as exc:
        log.error("Module de service indisponible: %s", exc)
        return 1

    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(ClavierPropreService)
        servicemanager.StartServiceCtrlDispatcher()
        return 0

    win32serviceutil.HandleCommandLine(ClavierPropreService)
    return 0
