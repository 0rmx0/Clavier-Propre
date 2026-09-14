"""Pastille indicatrice de l'état de la protection.

Petit widget circulaire coloré (rouge = protection active, vert = inactive),
sans bordure, toujours au premier plan. Un clic gauche (court) affiche à
nouveau la GUI complète ; un clic droit bascule directement la protection.
La pastille est déplaçable à la souris (clic gauche maintenu + déplacement).
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget


class PastilleButton(QWidget):
    clicked_show = Signal()
    clicked_toggle = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._active = False
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(28, 28)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._drag = None

    def set_active(self, active: bool) -> None:
        if self._active != active:
            self._active = active
            self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QColor(0, 0, 0, 180))
        color = QColor("#c0392b") if self._active else QColor("#27ae60")
        p.setBrush(color)
        p.drawEllipse(2, 2, self.width() - 4, self.height() - 4)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(255, 255, 255, 60))
        p.drawEllipse(int(self.width() * 0.28), int(self.height() * 0.22),
                      int(self.width() * 0.18), int(self.height() * 0.18))
        p.end()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag = {
                "x": event.position().toPoint().x(),
                "y": event.position().toPoint().y(),
                "origin_global": event.globalPosition().toPoint(),
            }
        elif event.button() == Qt.MouseButton.RightButton:
            self.clicked_toggle.emit()

    def mouseMoveEvent(self, event) -> None:
        if event.buttons() & Qt.MouseButton.LeftButton and self._drag is not None:
            self.move(
                event.globalPosition().toPoint().x() - self._drag["x"],
                event.globalPosition().toPoint().y() - self._drag["y"],
            )

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._drag is not None:
            moved = (event.globalPosition().toPoint() - self._drag["origin_global"]).manhattanLength()
            self._drag = None
            if moved < 5:
                self.clicked_show.emit()
