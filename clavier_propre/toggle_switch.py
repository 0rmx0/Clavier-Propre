"""Commutateur ON/OFF (toggle switch) personnalisé pour PySide6.

Widget peint à la main : un curseur qui glisse entre OFF (gauche, gris) et
ON (droite, vert). Émet ``toggled(bool)`` quand l'utilisateur change l'état.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget


class ToggleSwitch(QWidget):
    toggled = Signal(bool)

    def __init__(self, label_on: str = "ON", label_off: str = "OFF", parent=None):
        super().__init__(parent)
        self._on = False
        self._label_on = label_on
        self._label_off = label_off
        self.setFixedSize(120, 40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def isChecked(self) -> bool:
        return self._on

    def setChecked(self, checked: bool) -> None:
        if self._on != checked:
            self._on = checked
            self.update()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._flip()

    def _flip(self) -> None:
        self._on = not self._on
        self.update()
        self.toggled.emit(self._on)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        h = self.height()
        margin = 3
        track = self.rect().adjusted(margin, margin, -margin, -margin)

        if self._on:
            track_color = QColor("#27ae60")
            label = self._label_on
            label_color = QColor("#ffffff")
        else:
            track_color = QColor("#7f8c8d")
            label = self._label_off
            label_color = QColor("#ffffff")

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(track_color)
        p.drawRoundedRect(track, h / 2, h / 2)

        # Texte d'état à gauche du curseur.
        p.setPen(label_color)
        font = p.font()
        font.setBold(True)
        font.setPointSize(8)
        p.setFont(font)
        text_rect = track.adjusted(8, 0, -int(h * 1.4), 0)
        p.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, label)

        # Curseur (cercle blanc).
        knob_d = h - 2 * margin - 4
        if self._on:
            knob_x = w - margin - knob_d - 2
        else:
            knob_x = margin + 2
        knob_y = margin + 2
        p.setBrush(QColor("#ffffff"))
        p.drawEllipse(int(knob_x), int(knob_y), int(knob_d), int(knob_d))
        p.end()
