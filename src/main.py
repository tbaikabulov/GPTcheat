import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QPushButton, QTextEdit, QLabel, QFileDialog, QProgressBar, QHBoxLayout, QSlider)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QShortcut, QKeySequence, QPainter, QColor, QPainterPath, QPen
from audio_capture import AudioCapture
from speech_recognition import SpeechRecognition
from question_analyzer import QuestionAnalyzer
import numpy as np
from collections import deque
import sounddevice as sd

class AudioWaveWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.levels = deque([0] * 200, maxlen=200)  # Буфер для уровней звука
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_level)
        self.timer.start(16)  # 60 FPS для плавной анимации
        self.audio_capture = None
        self.is_recording = False
        
    def set_audio_capture(self, capture):
        self.audio_capture = capture
        self.clear()
        
    def clear(self):
        """Очистить буфер уровней звука"""
        self.levels.clear()
        self.levels.extend([0] * 200)
        self.update()
        
    def update_level(self):
        """Обновить уровень звука"""
        if self.audio_capture and self.is_recording:
            try:
                level = self.audio_capture.get_audio_level()
                # Добавляем новое значение в буфер
                self.levels.append(level)
                self.update()
            except Exception as e:
                print(f"Ошибка обновления уровня: {str(e)}")
    
    def start_recording(self):
        """Начать запись"""
        self.is_recording = True
        
    def stop_recording(self):
        """Остановить запись"""
        self.is_recording = False
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        
        width = self.width()
        height = self.height()
        center_y = height / 2
        
        # Настраиваем цвет и толщину линии
        pen = painter.pen()
        pen.setColor(QColor(0, 150, 255))
        pen.setWidth(1)
        painter.setPen(pen)
        
        # Рисуем волну
        step = width / len(self.levels)
        
        # Рисуем верхнюю часть волны
        for i, level in enumerate(self.levels):
            x = i * step
            y = center_y - level * height * 0.675  # Увеличена высота в 1.5 раза
            painter.drawLine(int(x), int(center_y), int(x), int(y))
            
        # Рисуем нижнюю часть волны
        for i, level in enumerate(self.levels):
            x = i * step
            y = center_y + level * height * 0.675  # Увеличена высота в 1.5 раза
            painter.drawLine(int(x), int(center_y), int(x), int(y))
            
        # Добавляем центральную линию
        painter.setPen(QPen(QColor(100, 100, 100), 1, Qt.PenStyle.DotLine))
        painter.drawLine(0, int(center_y), width, int(center_y))

class ProcessingIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_angle)
        self.timer.start(50)
        
    def update_angle(self):
        self.angle = (self.angle + 10) % 360
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Рисуем крутящийся индикатор
        center = self.rect().center()
        painter.translate(center)
        painter.rotate(self.angle)
        
        for i in range(8):
            painter.rotate(45)
            alpha = 255 - (i * 30)
            painter.setPen(QColor(0, 150, 255, alpha))
            painter.drawLine(0, 0, 20, 0)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GPTcheat - Interview Assistant")
        self.setGeometry(100, 100, 800, 600)
        
        # Инициализация базовых компонентов
        self.speech_recognition = SpeechRecognition()
        self.question_analyzer = QuestionAnalyzer()
        self.audio_capture = None
        self.accumulated_text = ""
        self.is_recording = False
        
        # Таймер для периодического анализа контекста
        self.context_timer = QTimer(self)
        self.context_timer.timeout.connect(self.analyze_context)
        self.context_interval = self.question_analyzer.config['settings']['analysis_interval'] * 1000  # в миллисекундах
        
        # Создание GUI
        self.init_ui()
        
        # Инициализация аудио после создания GUI
        try:
            # Пробуем разные устройства ввода
            devices = sd.query_devices()
            input_devices = [d for d in devices if d['max_input_channels'] > 0]
            
            if not input_devices:
                raise RuntimeError("Не найдены устройства ввода")
            
            # Пробуем найти встроенный микрофон
            builtin_mic = next((d for d in input_devices if 'built-in' in d['name'].lower()), None)
            if builtin_mic:
                print(f"Используем встроенный микрофон: {builtin_mic['name']}")
                self.audio_capture = AudioCapture(device_id=builtin_mic['index'])
            else:
                print(f"Используем первое доступное устройство: {input_devices[0]['name']}")
                self.audio_capture = AudioCapture(device_id=input_devices[0]['index'])
                
            # Устанавливаем audio_capture в виджет волны
            self.audio_wave.set_audio_capture(self.audio_capture)
                
        except Exception as e:
            print(f"Ошибка инициализации аудио: {str(e)}")
            self.status_label.setText(f"Ошибка инициализации аудио: {str(e)}")
            self.status_label.setStyleSheet("QLabel { color: red; }")
        
        # Настройка горячих клавиш
        self.setup_hotkeys()
        
        # Таймер для обновления визуализации
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.audio_wave.update_level)
    
    def init_ui(self):
        # Основной виджет и layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Статус записи
        self.status_label = QLabel("Статус: Ожидание")
        self.status_label.setStyleSheet("QLabel { color: gray; }")
        layout.addWidget(self.status_label)
        
        # Аудио волна
        self.audio_wave = AudioWaveWidget()
        self.audio_wave.setFixedHeight(50)
        layout.addWidget(self.audio_wave)
        
        # Кнопка записи
        self.record_btn = QPushButton("Начать запись (Space)")
        self.record_btn.clicked.connect(self.toggle_recording)
        layout.addWidget(self.record_btn)
        
        # Поле для отображения распознанного текста
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        layout.addWidget(QLabel("Распознанный текст:"))
        layout.addWidget(self.text_display)
        
        # Индикатор обработки GPT
        self.processing_indicator = ProcessingIndicator()
        self.processing_indicator.setFixedSize(50, 50)
        self.processing_indicator.hide()
        layout.addWidget(self.processing_indicator)
        
        # Поле для отображения подсказки
        self.hint_display = QTextEdit()
        self.hint_display.setReadOnly(True)
        layout.addWidget(QLabel("Подсказка:"))
        layout.addWidget(self.hint_display)
        
    def setup_hotkeys(self):
        # Горячая клавиша для записи (Space)
        self.record_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Space), self)
        self.record_shortcut.activated.connect(self.toggle_recording)
        
    def toggle_recording(self):
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
            
    def analyze_context(self):
        """Анализ контекста и генерация подсказок"""
        if not self.is_recording:
            return
            
        try:
            # Получаем последние N секунд аудио
            audio_data = self.audio_capture.get_context_audio()
            if not audio_data:
                return
                
            # Показываем индикатор обработки
            self.processing_indicator.show()
            
            # Распознаем речь
            text = self.speech_recognition.recognize(audio_data)
            if text:
                # Добавляем текст к накопленному контексту
                self.accumulated_text += " " + text
                # Ограничиваем размер накопленного текста
                max_length = self.question_analyzer.config['settings']['max_context_length']
                if len(self.accumulated_text) > max_length:
                    self.accumulated_text = self.accumulated_text[-max_length:]
                
                # Обновляем текст
                self.text_display.setText(self.accumulated_text)
                
                # Генерируем подсказку на основе всего контекста
                hint = self.question_analyzer.analyze_question(self.accumulated_text)
                if hint:
                    self.hint_display.setText(hint)
            
            # Скрываем индикатор обработки
            self.processing_indicator.hide()
            
        except Exception as e:
            print(f"Ошибка при анализе контекста: {str(e)}")
            self.processing_indicator.hide()
    
    def start_recording(self):
        """Начать запись"""
        if not self.is_recording and self.audio_capture:
            try:
                self.is_recording = True
                self.record_btn.setText("⏹ Остановить запись (Space)")
                self.status_label.setText("Запись...")
                self.status_label.setStyleSheet("QLabel { color: red; }")
                
                # Очищаем накопленный текст
                self.accumulated_text = ""
                self.text_display.clear()
                self.hint_display.clear()
                
                # Запускаем запись
                self.audio_capture.start_recording()
                self.audio_wave.start_recording()
                
                # Запускаем таймеры
                self.update_timer.start(16)  # 60 FPS для визуализации
                self.context_timer.start(self.context_interval)  # Анализ контекста каждые 10 секунд
                
            except Exception as e:
                self.is_recording = False
                self.record_btn.setText("🎤 Начать запись (Space)")
                self.status_label.setText(f"Ошибка: {str(e)}")
                self.status_label.setStyleSheet("QLabel { color: red; }")
                print(f"Ошибка при запуске записи: {str(e)}")
    
    def stop_recording(self):
        """Остановить запись"""
        if self.is_recording:
            self.is_recording = False
            self.record_btn.setText("🎤 Начать запись (Space)")
            self.status_label.setText("Готов к записи")
            self.status_label.setStyleSheet("QLabel { color: gray; }")
            
            # Останавливаем запись
            self.audio_capture.stop_recording()
            self.audio_wave.stop_recording()
            
            # Останавливаем таймеры
            self.update_timer.stop()
            self.context_timer.stop()
        
    def closeEvent(self, event):
        # Корректно завершаем все потоки при закрытии окна
        self.stop_recording()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec()) 