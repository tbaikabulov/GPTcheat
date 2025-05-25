from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor, QPen
from collections import deque

class WaveVisualizer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.levels = deque([0] * 200, maxlen=200)
        
    def update_level(self, level):
        """Обновляет уровень звука"""
        self.levels.append(level)
        self.update()
        
    def clear(self):
        """Очищает буфер уровней звука"""
        self.levels.clear()
        self.levels.extend([0] * 200)
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        width = self.width()
        height = self.height()
        center_y = height / 2
        
        # Рисуем волну
        pen = painter.pen()
        pen.setColor(QColor(0, 150, 255))
        pen.setWidth(1)
        painter.setPen(pen)
        
        step = width / len(self.levels)
        for i, level in enumerate(self.levels):
            x = i * step
            y = center_y - level * height * 15
            painter.drawLine(int(x), int(center_y), int(x), int(y))
            y = center_y + level * height * 15
            painter.drawLine(int(x), int(center_y), int(x), int(y))
            
        # Центральная линия
        painter.setPen(QPen(QColor(100, 100, 100), 1, Qt.PenStyle.DotLine))
        painter.drawLine(0, int(center_y), width, int(center_y)) 