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


def _isolate_config(tmp_path: Path, monkeypatch):
    from clavier_propre import config as cfg

    monkeypatch.setattr(cfg, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(cfg, "CONFIG_FILE", tmp_path / "config.json")


def _isolate_wordcraft(tmp_path: Path, monkeypatch, installed: bool = True):
    from clavier_propre import wordcraft as wc

    ui = tmp_path / "WordCraft" / "ui.json"
    monkeypatch.setattr(wc, "prefs_path", lambda: ui)
    monkeypatch.setattr(
        wc, "find_wordcraft", (lambda: "/fake/wordcraft.exe") if installed else (lambda: None)
    )
    return ui


def test_config_wordcraft_defaults():
    from clavier_propre.config import AppConfig

    c = AppConfig()
    assert c.manage_wordcraft is True
    assert c.saved_wordcraft_ui == {}


def test_wordcraft_apply_and_restore(tmp_path: Path, monkeypatch):
    import json

    from clavier_propre import wordcraft as wc

    _isolate_config(tmp_path, monkeypatch)
    ui = _isolate_wordcraft(tmp_path, monkeypatch, installed=True)
    ui.parent.mkdir(parents=True)
    original = {
        "checkSpelling": True,
        "theme": "dark",
        "editing": {
            "checkSpelling": True,
            "markGrammar": False,
            "autocorrect": {"enabled": True, "replaceText": True, "entries": [["teh", "the"]]},
        },
    }
    ui.write_text(json.dumps(original), encoding="utf-8")

    assert wc.apply_wordcraft_protection(active=True) is True
    data = json.loads(ui.read_text(encoding="utf-8"))
    assert data["checkSpelling"] is False
    assert data["theme"] == "dark"
    assert data["editing"]["checkSpelling"] is False
    assert data["editing"]["markGrammar"] is False
    assert data["editing"]["autocorrect"]["enabled"] is False
    assert data["editing"]["autocorrect"]["replaceText"] is False
    # Les données utilisateur (entries) sont préservées.
    assert data["editing"]["autocorrect"]["entries"] == [["teh", "the"]]
    assert wc.get_state().protected is True

    # La sauvegarde des valeurs d'origine a eu lieu.
    from clavier_propre.config import AppConfig

    saved = AppConfig.load().saved_wordcraft_ui
    assert saved["checkSpelling"] is True
    assert saved["editing"]["markGrammar"] is False
    assert saved["editing"]["autocorrect"]["enabled"] is True

    # Un second apply (watchdog) ne doit pas écraser la sauvegarde par « off ».
    wc.apply_wordcraft_protection(active=True)
    assert AppConfig.load().saved_wordcraft_ui["editing"]["markGrammar"] is False

    assert wc.apply_wordcraft_protection(active=False) is True
    data = json.loads(ui.read_text(encoding="utf-8"))
    assert data["checkSpelling"] is True
    assert data["editing"]["checkSpelling"] is True
    assert data["editing"]["markGrammar"] is False
    assert data["editing"]["autocorrect"]["enabled"] is True
    assert data["editing"]["autocorrect"]["entries"] == [["teh", "the"]]
    assert AppConfig.load().saved_wordcraft_ui == {}
    assert wc.get_state().protected is False


def test_wordcraft_get_state_without_file(tmp_path: Path, monkeypatch):
    from clavier_propre import wordcraft as wc

    _isolate_wordcraft(tmp_path, monkeypatch, installed=True)
    assert wc.get_state().protected is False


def test_wordcraft_not_installed_is_noop(tmp_path: Path, monkeypatch):
    from clavier_propre import wordcraft as wc

    _isolate_config(tmp_path, monkeypatch)
    ui = _isolate_wordcraft(tmp_path, monkeypatch, installed=False)
    assert wc.apply_wordcraft_protection(active=True) is False
    assert not ui.exists()


def test_controller_wordcraft_state(tmp_path: Path, monkeypatch):
    from clavier_propre.controller import ProtectionController

    _isolate_config(tmp_path, monkeypatch)
    ctrl = ProtectionController()
    state = ctrl.current_state()
    assert state.wordcraft_managed is True

    ctrl.set_wordcraft_managed(False)
    assert ctrl.current_state().wordcraft_managed is False
