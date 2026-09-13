"""Interface graphique PySide6 : un panneau compact toujours au premier plan,
qui indique à l'instituteur l'état de la protection et permet de la basculer.
"""
from __future__ import annotations

import logging
import sys

from clavier_propre.controller import ProtectionController

log = logging.getLogger(__name__)


def run_gui() -> int:
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtGui import QFont
    from PySide6.QtWidgets import (
        QApplication,
        QCheckBox,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Clavier-Propre")
    try:
        app.setQuitOnLastWindowClosed(False)
    except Exception:
        pass

    controller = ProtectionController()

    window = QWidget()
    window.setWindowTitle("Clavier-Propre")
    window.setWindowFlags(
        Qt.WindowType.FramelessWindowHint
        | Qt.WindowType.WindowStaysOnTopHint
        | Qt.WindowType.Tool
    )
    window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
    window.setFixedSize(240, 150)

    layout = QVBoxLayout(window)
    layout.setContentsMargins(12, 12, 12, 12)
    layout.setSpacing(6)

    status_label = QLabel("Protection ACTIVE")
    status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    font = QFont()
    font.setBold(True)
    font.setPointSize(11)
    status_label.setFont(font)
    layout.addWidget(status_label)

    detail_label = QLabel("Suggestions clavier désactivées")
    detail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    detail_label.setWordWrap(True)
    layout.addWidget(detail_label)

    toggle_btn = QPushButton("Désactiver la protection")
    toggle_btn.setCheckable(True)
    layout.addWidget(toggle_btn)

    options_row = QHBoxLayout()
    word_check = QCheckBox("Word")
    lo_check = QCheckBox("LibreOffice")
    word_check.setChecked(controller.config.manage_word)
    lo_check.setChecked(controller.config.manage_libreoffice)
    options_row.addWidget(word_check)
    options_row.addWidget(lo_check)
    layout.addLayout(options_row)

    def refresh(state):
        if state.active:
            status_label.setText("Protection ACTIVE")
            status_label.setStyleSheet("color: #ffffff;")
            detail_label.setText("Suggestions clavier désactivées")
            window.setStyleSheet("background-color: #c0392b;")
            toggle_btn.setText("Désactiver la protection")
            toggle_btn.setChecked(False)
        else:
            status_label.setText("Protection inactive")
            status_label.setStyleSheet("color: #ffffff;")
            detail_label.setText("Suggestions clavier autorisées")
            window.setStyleSheet("background-color: #27ae60;")
            toggle_btn.setText("Activer la protection")
            toggle_btn.setChecked(True)

    def on_toggle(checked: bool):
        # ``checked`` vient du bouton « Désactiver » : True => on désactive la
        # protection, donc ``active = not checked``.
        new_state = controller.apply(active=not checked)
        refresh(new_state)

    def on_word(state):
        controller.set_word_managed(bool(state))

    def on_lo(state):
        controller.set_libreoffice_managed(bool(state))

    toggle_btn.toggled.connect(on_toggle)
    word_check.stateChanged.connect(on_word)
    lo_check.stateChanged.connect(on_lo)

    # Application de l'état initial au démarrage.
    initial = controller.apply(active=controller.config.protection_active)
    refresh(initial)

    # Surveillance périodique : si les suggestions ont été réactivées par un
    # autre moyen (l'élève via les Paramètres), on ré-applique la protection.
    timer = QTimer(window)
    timer.setInterval(15000)

    def watchdog():
        st = controller.current_state()
        if controller.config.protection_active and st.keyboard_enabled:
            log.info("Réactivation détectée : re-protection.")
            controller.apply(active=True)

    timer.timeout.connect(watchdog)
    timer.start()

    # Rendre la fenêtre déplaçable à la souris (pas de barre de titre).
    _drag_offset = {"x": 0, "y": 0}

    def mouse_press(event):
        if event.button() == Qt.MouseButton.LeftButton:
            _drag_offset["x"] = event.globalPosition().toPoint().x() - window.x()
            _drag_offset["y"] = event.globalPosition().toPoint().y() - window.y()

    def mouse_move(event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            window.move(
                event.globalPosition().toPoint().x() - _drag_offset["x"],
                event.globalPosition().toPoint().y() - _drag_offset["y"],
            )

    window.mousePressEvent = mouse_press  # type: ignore[assignment]
    window.mouseMoveEvent = mouse_move  # type: ignore[assignment]

    window.show()
    return app.exec()
