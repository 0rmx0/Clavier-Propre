"""Mode « service » (sans interface graphique).

Utilisé lorsque l'application est lancée avec l'argument ``--service``. Elle
applique la protection au démarrage puis s'exécute en boucle, en réappliquant
périodiquement la protection si elle a été désactivée par un tiers.

C'est cette fonction qui sert de point d'entrée à l'exécutable Windows
installé comme service (via NSSM ou pywin32 ``win32serviceutil``).
"""
from __future__ import annotations

import logging
import signal
import threading

from clavier_propre.controller import ProtectionController

log = logging.getLogger(__name__)

_STOP = threading.Event()


def _loop(controller: ProtectionController) -> None:
    controller.apply(active=True)
    while not _STOP.wait(30):
        st = controller.current_state()
        if controller.config.protection_active and st.keyboard_enabled:
            log.info("Réactivation détectée : re-protection (mode service).")
            controller.apply(active=True)


def run_headless() -> int:
    controller = ProtectionController()

    def stop_handler(signum, _frame):
        log.info("Arrêt du service demandé (signal %s).", signum)
        _STOP.set()

    signal.signal(signal.SIGINT, stop_handler)
    signal.signal(signal.SIGTERM, stop_handler)

    log.info("Démarrage du service Clavier-Propre (mode headless).")
    _loop(controller)
    log.info("Service arrêté.")
    return 0
