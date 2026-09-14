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
        QDialog,
        QDialogButtonBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMessageBox,
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
    window.setFixedSize(260, 200)

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

    # Palette des boutons : fond nettement plus sombre que le fond de la fenêtre
    # pour qu'ils restent bien lisibles, quel que soit l'état (rouge / vert).
    BTN_BG = "#1f1419"
    BTN_HOVER = "#2d1f28"
    toggle_btn = QPushButton("Désactiver la protection")
    toggle_btn.setCheckable(True)
    toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
    toggle_btn.setStyleSheet(
        f"""
        QPushButton {{
            background-color: {BTN_BG};
            color: #ffffff;
            border: 1px solid #000000;
            border-radius: 6px;
            padding: 8px 12px;
            font-weight: 600;
        }}
        QPushButton:hover {{ background-color: {BTN_HOVER}; }}
        QPushButton:pressed {{ background-color: #120a10; }}
        """
    )
    layout.addWidget(toggle_btn)

    options_row = QHBoxLayout()
    word_check = QCheckBox("Word")
    lo_check = QCheckBox("LibreOffice")
    word_check.setChecked(controller.config.manage_word)
    lo_check.setChecked(controller.config.manage_libreoffice)
    checkbox_qss = (
        f"""
        QCheckBox {{
            color: #ffffff;
            background-color: {BTN_BG};
            border-radius: 4px;
            padding: 4px 6px;
        }}
        QCheckBox::indicator {{
            width: 14px; height: 14px;
            border: 1px solid #ffffff;
            border-radius: 3px;
            background-color: #0d0709;
        }}
        QCheckBox::indicator:checked {{ background-color: #ffffff; }}
        """
    )
    word_check.setStyleSheet(checkbox_qss)
    lo_check.setStyleSheet(checkbox_qss)
    options_row.addWidget(word_check)
    options_row.addWidget(lo_check)
    layout.addLayout(options_row)

    # Bouton de réglage du mot de passe professeur.
    password_btn = QPushButton("Mot de passe professeur")
    password_btn.setCursor(Qt.CursorShape.PointingHandCursor)
    password_btn.setStyleSheet(
        f"""
        QPushButton {{
            background-color: {BTN_BG};
            color: #ffffff;
            border: 1px solid #000000;
            border-radius: 6px;
            padding: 6px 10px;
            font-size: 10px;
        }}
        QPushButton:hover {{ background-color: {BTN_HOVER}; }}
        """
    )
    layout.addWidget(password_btn)

    def refresh(state):
        # ``refresh`` est un rafraîchissement programmatique : on bloque les
        # signaux du bouton pour ne pas déclencher ``on_toggle`` (qui exigerait
        # le mot de passe). Le mot de passe ne doit être demandé que sur une
        # action utilisateur.
        toggle_btn.blockSignals(True)
        try:
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
        finally:
            toggle_btn.blockSignals(False)

    def _warn(message: str) -> None:
        QMessageBox.warning(window, "Clavier-Propre", message)

    def _info(message: str) -> None:
        QMessageBox.information(window, "Clavier-Propre", message)

    def ask_teacher_password(prompt: str = "Mot de passe professeur requis") -> bool:
        """Affiche un dialogue de saisie et vérifie le mot de passe.
        Retourne True si aucun mot de passe n'est défini ou si la saisie est
        correcte."""
        if not controller.config.has_teacher_password():
            return True
        dlg = QDialog(window)
        dlg.setWindowTitle("Clavier-Propre")
        dlg.setModal(True)
        dlg.setStyleSheet(
            f"background-color: #2b1d24; color: #ffffff;"
        )
        v = QVBoxLayout(dlg)
        lbl = QLabel(prompt)
        v.addWidget(lbl)
        le = QLineEdit()
        le.setEchoMode(QLineEdit.EchoMode.Password)
        le.setStyleSheet("background-color: #1f1419; color: #ffffff; padding: 6px;")
        v.addWidget(le)
        bb = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        v.addWidget(bb)
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        le.returnPressed.connect(dlg.accept)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return False
        return controller.config.check_teacher_password(le.text())

    def on_toggle(checked: bool):
        # ``checked`` vient du bouton « Désactiver » : True => on désactive la
        # protection, donc ``active = not checked``.
        if checked and not ask_teacher_password(
            "Saisissez le mot de passe professeur pour désactiver la protection"
        ):
            # Annulation : on remet le bouton à l'état antérieur SANS déclencher
            # le signal (sinon récursion / nouvelle demande de mot de passe).
            toggle_btn.blockSignals(True)
            toggle_btn.setChecked(False)
            toggle_btn.blockSignals(False)
            return
        new_state = controller.apply(active=not checked)
        refresh(new_state)

    def on_word(state):
        # Décocher Word nécessite le mot de passe professeur.
        if not bool(state) and not ask_teacher_password(
            "Saisissez le mot de passe professeur pour désactiver Word"
        ):
            word_check.setChecked(True)
            return
        controller.set_word_managed(bool(state))

    def on_lo(state):
        # Décocher LibreOffice nécessite le mot de passe professeur.
        if not bool(state) and not ask_teacher_password(
            "Saisissez le mot de passe professeur pour désactiver LibreOffice"
        ):
            lo_check.setChecked(True)
            return
        controller.set_libreoffice_managed(bool(state))

    def on_password_btn():
        dlg = QDialog(window)
        dlg.setWindowTitle("Mot de passe professeur")
        dlg.setModal(True)
        dlg.setStyleSheet(f"background-color: #2b1d24; color: #ffffff;")
        v = QVBoxLayout(dlg)

        info = QLabel(
            "Définir un mot de passe professeur.\n"
            "S'il est défini, il sera requis pour désactiver\n"
            "la protection ou décocher Word/LibreOffice.\n"
            "Laisser vide pour supprimer le mot de passe."
        )
        info.setWordWrap(True)
        v.addWidget(info)

        if controller.config.has_teacher_password():
            cur_lbl = QLabel("Mot de passe actuel :")
            v.addWidget(cur_lbl)
            cur_le = QLineEdit()
            cur_le.setEchoMode(QLineEdit.EchoMode.Password)
            cur_le.setStyleSheet("background-color: #1f1419; color: #ffffff; padding: 6px;")
            v.addWidget(cur_le)
        else:
            cur_le = None

        new_lbl = QLabel("Nouveau mot de passe :")
        v.addWidget(new_lbl)
        new_le = QLineEdit()
        new_le.setEchoMode(QLineEdit.EchoMode.Password)
        new_le.setStyleSheet("background-color: #1f1419; color: #ffffff; padding: 6px;")
        v.addWidget(new_le)

        confirm_lbl = QLabel("Confirmer :")
        v.addWidget(confirm_lbl)
        confirm_le = QLineEdit()
        confirm_le.setEchoMode(QLineEdit.EchoMode.Password)
        confirm_le.setStyleSheet("background-color: #1f1419; color: #ffffff; padding: 6px;")
        v.addWidget(confirm_le)

        bb = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        v.addWidget(bb)
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        if cur_le is not None and not controller.config.check_teacher_password(
            cur_le.text()
        ):
            _warn("Mot de passe actuel incorrect.")
            return

        new_pw = new_le.text()
        if new_pw != confirm_le.text():
            _warn("Les mots de passe ne correspondent pas.")
            return

        controller.config.set_teacher_password(new_pw)
        controller.config.save()
        _info("Mot de passe professeur mis à jour." if new_pw else "Mot de passe professeur supprimé.")

    toggle_btn.toggled.connect(on_toggle)
    word_check.stateChanged.connect(on_word)
    lo_check.stateChanged.connect(on_lo)
    password_btn.clicked.connect(on_password_btn)

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
