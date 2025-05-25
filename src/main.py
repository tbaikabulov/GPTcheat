import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                              QPushButton, QLabel, QHBoxLayout, QTextEdit, QSplitter)
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtGui import QShortcut, QKeySequence
import threading
import time

from audio_recorder import AudioRecorder
from wave_visualizer import WaveVisualizer
from file_manager import FileManager
from functions import process_chat

class ChatProcessor(QThread):
    finished = Signal(dict)  # Сигнал для передачи результата обработки
    
    def __init__(self, chat_id):
        super().__init__()
        self.chat_id = chat_id
        
    def run(self):
        try:
            # Обрабатываем чат
            print(f"Обрабатываем чат {self.chat_id}")
            raw_text, text, answer = process_chat(self.chat_id)
            if text:
                result = {
                    'text': text,
                    'answer': answer
                }
            else:
                result = {
                    'text': "Не удалось распознать текст",
                    'answer': "Нет данных для генерации ответа"
                }
            
            self.finished.emit(result)
        except Exception as e:
            print(f"Ошибка в ChatProcessor: {str(e)}")
            self.finished.emit({
                'text': f"Ошибка обработки: {str(e)}",
                'answer': "Не удалось сгенерировать ответ"
            })

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GPTcheat - Interview Assistant")
        self.setGeometry(100, 100, 1200, 800)
        
        self.audio_recorder = AudioRecorder()
        self.file_manager = FileManager()
        self.chat_processor = None
        
        self.init_ui()
        self.setup_hotkeys()
        
        # Таймеры
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_visualization)
        self.update_timer.start(16)  # 60 FPS
        
        self.chunk_timer = QTimer(self)
        self.chunk_timer.timeout.connect(self.save_chunk)
        self.chunk_timer.start(10000)  # каждые 10 секунд
        
        self.process_timer = QTimer(self)
        self.process_timer.timeout.connect(self.process_chat)
        self.process_timer.start(10000)  # каждые 10 секунд
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)  # Убираем отступы между элементами
        
        # Статус и визуализация (20% высоты)
        top_widget = QWidget()
        top_widget.setFixedHeight(160)  # 20% от 800
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(10, 10, 10, 10)  # Отступы внутри верхнего блока
        
        # Статус и кнопка в одну строку
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Статус: Ожидание")
        self.status_label.setStyleSheet("QLabel { color: gray; }")
        status_layout.addWidget(self.status_label)
        
        self.record_btn = QPushButton("Начать запись (Space)")
        self.record_btn.clicked.connect(self.toggle_recording)
        status_layout.addWidget(self.record_btn)
        top_layout.addLayout(status_layout)
        
        # Визуализация волн
        self.wave_visualizer = WaveVisualizer()
        self.wave_visualizer.setFixedHeight(80)  # Уменьшаем высоту визуализации
        top_layout.addWidget(self.wave_visualizer)
        
        main_layout.addWidget(top_widget)
        
        # Разделитель для текста и подсказок (80% высоты)
        splitter = QSplitter(Qt.Horizontal)
        
        # Блок с распознанным текстом
        text_widget = QWidget()
        text_layout = QVBoxLayout(text_widget)
        text_layout.setContentsMargins(10, 10, 10, 10)
        text_label = QLabel("Распознанный текст:")
        text_layout.addWidget(text_label)
        
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setPlaceholderText("Здесь будет отображаться распознанный текст...")
        text_layout.addWidget(self.text_edit)
        
        # Блок с подсказками
        hints_widget = QWidget()
        hints_layout = QVBoxLayout(hints_widget)
        hints_layout.setContentsMargins(10, 10, 10, 10)
        hints_label = QLabel("Подсказки:")
        hints_layout.addWidget(hints_label)
        
        self.hints_edit = QTextEdit()
        self.hints_edit.setReadOnly(True)
        self.hints_edit.setPlaceholderText("Здесь будут отображаться подсказки...")
        hints_layout.addWidget(self.hints_edit)
        
        # Добавляем виджеты в разделитель
        splitter.addWidget(text_widget)
        splitter.addWidget(hints_widget)
        
        # Устанавливаем начальные размеры
        splitter.setSizes([600, 600])
        
        main_layout.addWidget(splitter)
        
    def setup_hotkeys(self):
        self.record_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Space), self)
        self.record_shortcut.activated.connect(self.toggle_recording)
        
    def toggle_recording(self):
        if not self.audio_recorder.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
            
    def start_recording(self):
        try:
            chat_dir = self.file_manager.create_chat_directory()
            print(f"Создана директория для записи: {chat_dir}")
            
            self.audio_recorder.start_recording()
            
            # Запускаем таймеры при старте записи
            self.chunk_timer.start()
            self.process_timer.start()
            
            self.record_btn.setText("⏹ Остановить запись (Space)")
            self.status_label.setText("Запись...")
            self.status_label.setStyleSheet("QLabel { color: red; }")
            self.wave_visualizer.clear()
            
        except Exception as e:
            self.status_label.setText(f"Ошибка: {str(e)}")
            self.status_label.setStyleSheet("QLabel { color: red; }")
            print(f"Ошибка при запуске записи: {str(e)}")
    
    def stop_recording(self):
        if self.audio_recorder.is_recording:
            # Останавливаем таймеры при остановке записи
            self.chunk_timer.stop()
            self.process_timer.stop()
            
            # Сохраняем последний чанк перед остановкой
            chunk_data = self.audio_recorder.save_chunk()
            if chunk_data:
                filepath = self.file_manager.save_audio_chunk(chunk_data)
                print(f"Сохранен последний чанк: {filepath}")
            
            self.audio_recorder.stop_recording()
            
            self.record_btn.setText("🎤 Начать запись (Space)")
            self.status_label.setText("Готов к записи")
            self.status_label.setStyleSheet("QLabel { color: gray; }")
            self.wave_visualizer.clear()
            
    def update_visualization(self):
        if self.audio_recorder.is_recording:
            level = self.audio_recorder.get_audio_level()
            self.wave_visualizer.update_level(level)
            
    def save_chunk(self):
        if self.audio_recorder.is_recording:
            chunk_data = self.audio_recorder.save_chunk()
            if chunk_data:
                filepath = self.file_manager.save_audio_chunk(chunk_data)
                print(f"Сохранен чанк: {filepath}")
            
    def process_chat(self):
        """Асинхронная обработка чата"""
        if self.audio_recorder.is_recording and self.file_manager.current_chat:
            # Если предыдущий процессор все еще работает, не запускаем новый
            if self.chat_processor and self.chat_processor.isRunning():
                print("Предыдущий процессор все еще работает, пропускаем...")
                return
                
            # Получаем ID текущего чата
            chat_id = int(self.file_manager.current_chat.split('_')[1])
            
            # Создаем и запускаем процессор в отдельном потоке
            self.chat_processor = ChatProcessor(chat_id)
            self.chat_processor.finished.connect(self.on_chat_processed)
            self.chat_processor.start()
            
    def on_chat_processed(self, result):
        """Обработчик завершения обработки чата"""
        try:
            # Обновляем текстовые поля
            if result.get('text'):
                self.text_edit.setText(result['text'])
            if result.get('answer'):
                self.hints_edit.setText(result['answer'])
            
            # Прокручиваем к началу
            self.text_edit.verticalScrollBar().setValue(0)
            self.hints_edit.verticalScrollBar().setValue(0)
        except Exception as e:
            print(f"Ошибка при обновлении текста: {str(e)}")
    
    def closeEvent(self, event):
        self.stop_recording()
        event.accept()

if __name__ == '__main__':
    # подробный комментарий по коду:
    # 1. мы создаем окно приложения
    # 2. мы создаем экземпляр класса AudioRecorder для записи аудио
    # 3. мы создаем экземпляр класса FileManager для управления файлами
    # 4. мы создаем экземпляр класса ChatProcessor для обработки чата
    # 5. мы создаем экземпляр класса MainWindow для отображения окна
    # 6. мы создаем экземпляр класса QApplication для запуска приложения
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()
    sys.exit(app.exec()) 


# command to run: python src/main.py