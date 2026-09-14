"""Clavier-Propre — service Windows qui désactive les suggestions de mots
du clavier physique, ainsi que la correction automatique de LibreOffice et
Microsoft Office, avec un indicateur visuel au premier plan et un bouton de
bascule pour l'instituteur.

Lancé en interactif, l'application démarre la fenêtre PySide6.
Lancé en mode service (via le module ``service``), aucune GUI n'est levée :
l'application s'exécute en arrière-plan et conserve la fonction active.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

LOG_PATH = Path.home() / "AppData" / "Local" / "Clavier-Propre" / "clavier-propre.log"
APP_NAME = "Clavier-Propre"
APP_VERSION = "1.0.0"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def main() -> int:
    if "--service" in sys.argv:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            filename=str(LOG_PATH),
        )
        from clavier_propre.service import run_headless

        return run_headless()

    from clavier_propre.gui import run_gui

    return run_gui()


if __name__ == "__main__":
    sys.exit(main())
