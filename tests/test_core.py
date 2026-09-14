"""Tests de non-régression (exécutables hors Windows via simulation)."""
from __future__ import annotations

from pathlib import Path

import pytest


def test_config_roundtrip(tmp_path: Path, monkeypatch):
    from clavier_propre import config as cfg

    monkeypatch.setattr(cfg, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(cfg, "CONFIG_FILE", tmp_path / "config.json")

    c = cfg.AppConfig(protection_active=False, manage_word=False)
    c.save()
    assert (tmp_path / "config.json").exists()
    loaded = cfg.AppConfig.load()
    assert loaded.protection_active is False
    assert loaded.manage_word is False
    assert loaded.manage_libreoffice is True


def test_config_load_corrupt(tmp_path: Path, monkeypatch):
    from clavier_propre import config as cfg

    monkeypatch.setattr(cfg, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(cfg, "CONFIG_FILE", tmp_path / "config.json")
    (tmp_path / "config.json").write_text("{not json", encoding="utf-8")

    c = cfg.AppConfig.load()
    assert c.protection_active is False


def test_keyboard_state_non_windows():
    from clavier_propre import keyboard

    state = keyboard.get_state()
    # Hors Windows, on simule « suggestions actives ».
    assert state.enabled is True


def test_controller_current_state_non_windows():
    from clavier_propre.controller import ProtectionController

    ctrl = ProtectionController()
    state = ctrl.current_state()
    assert state.active is False
    assert state.word_managed is True
    assert state.libreoffice_managed is True


def test_teacher_password():
    from clavier_propre.config import AppConfig

    c = AppConfig()
    assert c.has_teacher_password() is False
    # Aucun mot de passe défini : tout est autorisé.
    assert c.check_teacher_password("n_importe_quoi") is True

    c.set_teacher_password("secret123")
    assert c.has_teacher_password() is True
    assert c.check_teacher_password("secret123") is True
    assert c.check_teacher_password("wrong") is False

    # Deux définitions identiques produisent des sels/haches différents.
    h1 = c.teacher_password_hash
    c.set_teacher_password("secret123")
    assert c.teacher_password_hash != h1

    # Suppression du mot de passe.
    c.set_teacher_password("")
    assert c.has_teacher_password() is False
    assert c.check_teacher_password("n_importe_quoi") is True
