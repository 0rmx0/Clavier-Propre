"""Persistance de l'état de l'application (JSON dans %LOCALAPPDATA%)."""
from __future__ import annotations

import hashlib
import json
import logging
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

log = logging.getLogger(__name__)

CONFIG_DIR = Path.home() / "AppData" / "Local" / "Clavier-Propre"
CONFIG_FILE = CONFIG_DIR / "config.json"


def hash_password(password: str, salt: str) -> str:
    """Hache un mot de passe avec un sel (PBKDF2-HMAC-SHA256, 200 000 itérations)."""
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 200_000
    ).hex()


@dataclass
class AppConfig:
    # ``True`` = fonction active (suggestions désactivées sur le système).
    # Par défaut, l'outil démarre NON protégé : l'instituteur active
    # explicitement la protection quand il le souhaite.
    protection_active: bool = False
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
    # Mot de passe professeur (vide = aucun mot de passe requis).
    # On stocke le sel + le hash, jamais le mot de passe en clair.
    teacher_password_salt: str = ""
    teacher_password_hash: str = ""

    def has_teacher_password(self) -> bool:
        return bool(self.teacher_password_hash) and bool(self.teacher_password_salt)

    def set_teacher_password(self, password: str) -> None:
        if not password:
            self.teacher_password_salt = ""
            self.teacher_password_hash = ""
            return
        self.teacher_password_salt = os.urandom(16).hex()
        self.teacher_password_hash = hash_password(
            password, self.teacher_password_salt
        )

    def check_teacher_password(self, password: str) -> bool:
        if not self.has_teacher_password():
            return True
        return hash_password(password, self.teacher_password_salt) == self.teacher_password_hash

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
