"""Contrôleur central : orchestre la bascule entre les trois cibles
(clavier physique, Microsoft Office, LibreOffice) et conserve l'état.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from clavier_propre import keyboard, office_lo, office_ms
from clavier_propre.config import AppConfig

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProtectionState:
    # ``True`` = protection active (suggestions et corrections DÉSACTIVÉS).
    active: bool
    keyboard_enabled: bool  # True = suggestions clavier actuellement actives
    word_managed: bool
    libreoffice_managed: bool


class ProtectionController:
    """Fait le pont entre la GUI/service et les modules de pilotage."""

    def __init__(self, config: AppConfig | None = None) -> None:
        self.config = config or AppConfig.load()

    def current_state(self) -> ProtectionState:
        kb = keyboard.get_state()
        return ProtectionState(
            active=self.config.protection_active,
            keyboard_enabled=kb.enabled,
            word_managed=self.config.manage_word,
            libreoffice_managed=self.config.manage_libreoffice,
        )

    def apply(self, active: bool) -> ProtectionState:
        """Active (``active=True``) ou désactive la protection globale."""
        self.config.protection_active = active
        self.config.save()

        # 1) Clavier physique : on désactive les suggestions quand la
        #    protection est active.
        keyboard.set_suggestions(enabled=not active)

        # 2) Microsoft Office (Word/Excel/PowerPoint).
        if self.config.manage_word:
            try:
                office_ms.apply_office_protection(active=active)
            except Exception as exc:  # pragma: no cover
                log.warning("Pilotage Microsoft Office échoué: %s", exc)

        # 3) LibreOffice.
        if self.config.manage_libreoffice:
            try:
                office_lo.apply_libreoffice_protection(active=active)
            except Exception as exc:  # pragma: no cover
                log.warning("Pilotage LibreOffice échoué: %s", exc)

        return self.current_state()

    def set_word_managed(self, managed: bool) -> None:
        self.config.manage_word = managed
        self.config.save()
        if self.config.protection_active:
            try:
                office_ms.apply_office_protection(active=managed)
            except Exception as exc:  # pragma: no cover
                log.warning("Pilotage Word échoué: %s", exc)

    def set_libreoffice_managed(self, managed: bool) -> None:
        self.config.manage_libreoffice = managed
        self.config.save()
        if self.config.protection_active:
            try:
                office_lo.apply_libreoffice_protection(active=managed)
            except Exception as exc:  # pragma: no cover
                log.warning("Pilotage LibreOffice échoué: %s", exc)
