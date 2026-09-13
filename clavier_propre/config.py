"""Persistance de l'état de l'application (JSON dans %LOCALAPPDATA%)."""
from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path

log = logging.getLogger(__name__)

CONFIG_DIR = Path.home() / "AppData" / "Local" / "Clavier-Propre"
CONFIG_FILE = CONFIG_DIR / "config.json"


@dataclass
class AppConfig:
    # ``True`` = fonction active (suggestions désactivées sur le système).
    protection_active: bool = True
    # Valeurs DWORD d'origine du clavier sauvegardées à la désactivation.
    saved_keyboard_values: dict[str, int] = field(default_factory=dict)
    # Préférences de correction bureautique.
    manage_word: bool = True
    manage_libreoffice: bool = True
    # Dernier état connu de la correction dans Word/LO, pour restauration.
    saved_word_check_spelling: bool = True
    saved_word_check_grammar: bool = True
    saved_word_auto_correct: bool = True
    saved_lo_auto_spellcheck: bool = True

    @classmethod
    def load(cls) -> "AppConfig":
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return cls()
        except (json.JSONDecodeError, OSError) as exc:
            log.warning("Configuration illisible, réinitialisation: %s", exc)
            return cls()
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def save(self) -> None:
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            CONFIG_FILE.write_text(
                json.dumps(asdict(self), indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError as exc:  # pragma: no cover - erreur d'E/O disque
            log.warning("Impossible d'enregistrer la configuration: %s", exc)
