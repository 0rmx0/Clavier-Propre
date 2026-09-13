"""Définition du service Windows natif (pywin32 ``win32serviceutil``).

Le service ne fait que lancer le mode ``--service`` du module principal dans
un thread, puis signaler ``SERVICE_STOPPED`` à l'arrêt.

Installation (administrateur requis) :

    python -m clavier_propre.service_runner install
    python -m clavier_propre.service_runner start

Désinstallation :

    python -m clavier_propre.service_runner stop
    python -m clavier_propre.service_runner remove
"""
from __future__ import annotations

import logging
import threading

log = logging.getLogger(__name__)

try:
    import win32service  # type: ignore[import-not-found]
    import win32serviceutil  # type: ignore[import-not-found]
    import servicemanager  # type: ignore[import-not-found]
    import win32evtlogutil  # type: ignore[import-not-found]
    _HAS_PYWIN32 = True
except ImportError:  # pragma: no cover - environnements non-Windows / tests
    _HAS_PYWIN32 = False


if _HAS_PYWIN32:

    class ClavierPropreService(win32serviceutil.ServiceFramework):
        _svc_name_ = "ClavierPropre"
        _svc_display_name_ = "Clavier-Propre — Protection clavier"
        _svc_description_ = (
            "Désactive les suggestions de mots du clavier physique et la "
            "correction automatique de Microsoft Office / LibreOffice pendant "
            "les phases d'évaluation."
        )

        def __init__(self, args):
            super().__init__(args)
            self._stop_event = threading.Event()
            self._thread: threading.Thread | None = None

        def SvcStop(self):
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            self._stop_event.set()
            if self._thread is not None:
                self._thread.join(timeout=10)

        def SvcDoRun(self):
            servicemanager.LogInfoMsg("Clavier-Propre : démarrage du service.")
            from clavier_propre.controller import ProtectionController

            controller = ProtectionController()
            controller.apply(active=True)

            from clavier_propre import keyboard

            while not self._stop_event.wait(30):
                st = keyboard.get_state()
                if controller.config.protection_active and st.enabled:
                    servicemanager.LogInfoMsg(
                        "Clavier-Propre : réactivation détectée, re-protection."
                    )
                    controller.apply(active=True)

            servicemanager.LogInfoMsg("Clavier-Propre : arrêt du service.")


else:  # pragma: no cover

    class ClavierPropreService:  # type: ignore[no-redef]
        pass
