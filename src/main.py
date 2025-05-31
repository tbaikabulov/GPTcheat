import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                              QPushButton, QLabel, QHBoxLayout, QTextEdit, QSplitter)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal as Signal
from PyQt6.QtGui import QShortcut, QKeySequence, QTextOption, QGuiApplication, QIcon
import time
from datetime import datetime
import markdown2
from PyQt6.Qsci import QsciScintilla, QsciLexerPython

from audio_recorder import AudioRecorder
from wave_visualizer import WaveVisualizer
from file_manager import FileManager
from functions import *

# Конфигурация приложения
CHUNK_INTERVAL = 10000  # Интервал сохранения чанков (10000=10 секунд)
PROCESS_INTERVAL = 10000  # Интервал обработки чата (10 секунд)
MAX_CHUNKS = 7 # Максимальное количество чанков для обработки
MARKDOWN_FONT_SIZE = 13  # Размер шрифта для markdown-текста

def resource_path(relative_path):
    """Возвращает абсолютный путь к ресурсу внутри .app или рядом с .py"""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).parent
    return str(base_path / relative_path)

class ChatProcessor(QThread):
    finished = Signal(dict)  # Сигнал для передачи результата обработки
    text_ready = Signal(str)  # Новый сигнал для передачи распознанного текста
    
    def __init__(self, chat_id):
        super().__init__()
        self.chat_id = chat_id
        self.start_time = time.time()
        self.file_manager = FileManager()
        self.MIN_WORDS = 10  # Минимальное количество слов для обработки
        
    def log_event(self, event_type, details):
        """Логирует событие в файл"""
        self.file_manager.current_chat = f"chat_{self.chat_id}"
        self.file_manager.log_event(event_type, details)
        
    def run(self):
        try:
            # 1. Объединяем чанки
            N = count_chunks(self.chat_id)
            self.log_event("Начало обработки", f"чанков: {N}")
            
            if not unite_chunks(self.chat_id, max(N-MAX_CHUNKS, 0), N, "temp/combined.wav"):
                self.text_ready.emit("Ожидание накопления чанков...")
                return
                
            # 2. Получаем расшифровку
            raw_text = audio_to_text("temp/combined.wav", api_key)
            if not raw_text:
                self.text_ready.emit("Не удалось распознать аудио")
                return
                
            self.log_event("Текст получен", f"Исходный текст: {raw_text}")
            
            # Проверяем количество слов
            word_count = len(raw_text.split())
            if word_count < self.MIN_WORDS:
                self.text_ready.emit("Слушаем аудио...")
                self.log_event("Текст слишком короткий", f"Слов: {word_count}, минимум: {self.MIN_WORDS}")
                return
                
            # 3. Улучшаем текст
            text = text_to_good_text(raw_text, improve_text_prompt)
            if not text:
                self.text_ready.emit("Не удалось обработать текст")
                return
                
            self.log_event("Текст улучшен", f"Улучшенный текст: {text}")
                
            # Отправляем текст сразу после его обработки
            self.text_ready.emit(text)
            
            # 4. Генерируем ответ
            answer = gt_to_answer(text, answer_prompt)
            
            self.log_event("Ответ сгенерирован", f"Ответ: {answer}")
            
            # Отправляем результат с текстом и ответом
            result = {
                'text': text,
                'answer': answer if answer else "Не удалось сгенерировать ответ"
            }
            self.finished.emit(result)
                
        except Exception as e:
            error_msg = f"Ошибка обработки: {str(e)}"
            print(error_msg)
            self.log_event("Ошибка", error_msg)
            self.text_ready.emit(error_msg)
            self.finished.emit({
                'text': error_msg,
                'answer': "Не удалось сгенерировать ответ"
            })

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Interview Assistant")
        self.setMinimumSize(800, 600)
        
        # Загружаем иконку
        icon_path = Path(resource_path("resources/icons/app_icon.svg"))
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        # Загружаем стили
        style_path = Path(resource_path("resources/styles/main.qss"))
        if style_path.exists():
            with open(style_path, "r") as f:
                self.setStyleSheet(f.read())
        
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
        self.chunk_timer.start(CHUNK_INTERVAL)  # Сохраняем чанки каждые CHUNK_INTERVAL мс
        
        self.process_timer = QTimer(self)
        self.process_timer.timeout.connect(self.process_chat)
        self.process_timer.start(PROCESS_INTERVAL)  # Обрабатываем чат каждые PROCESS_INTERVAL мс
        
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
        self.status_label.setObjectName("status_label")
        self.status_label.setProperty("status", "ready")
        self.status_label.setStyleSheet("QLabel { color: gray; }")
        status_layout.addWidget(self.status_label)
        
        self.record_btn = QPushButton("Начать запись (Space)")
        self.record_btn.clicked.connect(self.toggle_recording)
        status_layout.addWidget(self.record_btn)
        top_layout.addLayout(status_layout)
        
        # Визуализация волн
        self.wave_visualizer = WaveVisualizer()
        self.wave_visualizer.setFixedHeight(80)  # Уменьшаем высоту визуализации
        self.wave_visualizer.setObjectName("wave_visualizer")
        top_layout.addWidget(self.wave_visualizer)
        
        main_layout.addWidget(top_widget)
        
        # Разделитель для текста и подсказок (80% высоты)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
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
        
        for edit in [self.text_edit, self.hints_edit]:
            edit.setWordWrapMode(QTextOption.WrapMode.WrapAnywhere)
            edit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        copy_text_on_click(self.hints_edit)
        
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
            self.status_label.setProperty("status", "recording")
            self.status_label.style().unpolish(self.status_label)
            self.status_label.style().polish(self.status_label)
            self.wave_visualizer.clear()
            
        except Exception as e:
            self.status_label.setText(f"Ошибка: {str(e)}")
            self.status_label.setProperty("status", "error")
            self.status_label.style().unpolish(self.status_label)
            self.status_label.style().polish(self.status_label)
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
            self.status_label.setProperty("status", "ready")
            self.status_label.style().unpolish(self.status_label)
            self.status_label.style().polish(self.status_label)
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
            self.chat_processor.text_ready.connect(self.on_text_ready)  # Подключаем новый сигнал
            self.chat_processor.finished.connect(self.on_chat_processed)
            self.chat_processor.start()
            
    def on_text_ready(self, text):
        """Обработчик получения распознанного текста"""
        try:
            set_markdown_with_code_wrap(self.text_edit, text, font_size=MARKDOWN_FONT_SIZE)
            self.text_edit.verticalScrollBar().setValue(0)
        except Exception as e:
            print(f"Ошибка при обновлении текста: {str(e)}")
            
    def on_chat_processed(self, result):
        """Обработчик завершения обработки чата"""
        try:
            if result.get('answer'):
                set_markdown_with_code_wrap(self.hints_edit, result['answer'], font_size=MARKDOWN_FONT_SIZE)
                self.hints_edit.verticalScrollBar().setValue(0)
        except Exception as e:
            print(f"Ошибка при обновлении ответа: {str(e)}")
    
    def closeEvent(self, event):
        self.stop_recording()
        event.accept()

def copy_text_on_click(edit):
    def handler(event):
        QGuiApplication.clipboard().setText(edit.toPlainText())
    edit.mousePressEvent = handler

def set_markdown_with_code_wrap(edit, text, font_size=MARKDOWN_FONT_SIZE):
    # Преобразуем markdown в html
    html = markdown2.markdown(text, extras=["fenced-code-blocks"])
    # Добавим стили для кода и текста с параметром font_size
    style = f"""
    <style>
    body, p, ul, ol, li, h1, h2, h3, h4, h5, h6 {{
        font-size: {font_size}px;
    }}
    pre, code {{
        background: #e6ecf1;
        color: #222;
        border-radius: 6px;
        font-family: 'JetBrains Mono', 'Fira Mono', 'Consolas', 'Menlo', monospace;
        font-size: {font_size}px;
        padding: 8px;
        word-break: break-all;
        white-space: pre-wrap;
        display: block;
    }}
    </style>
    """
    edit.setHtml(style + html)

class CodeWidget(QWidget):
    def __init__(self, code_text, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.editor = QsciScintilla()
        self.editor.setText(code_text)
        self.editor.setReadOnly(True)
        self.editor.setWrapMode(QsciScintilla.WrapWord)
        # Подсветка Python
        lexer = QsciLexerPython()
        self.editor.setLexer(lexer)
        # Копирование по клику
        self.editor.mousePressEvent = lambda event: self.copy_code()
        layout.addWidget(self.editor)

    def copy_code(self):
        from PyQt6.QtGui import QGuiApplication
        QGuiApplication.clipboard().setText(self.editor.text())

# Основной код приложения
if __name__ == '__main__':
    # 1. Создаем экземпляр QApplication - это обязательный первый шаг для любого Qt приложения
    # sys.argv содержит аргументы командной строки, которые передаются в приложение
    app = QApplication(sys.argv)

    # 2. Создаем главное окно приложения
    # MainWindow содержит всю логику интерфейса и обработки аудио
    window = MainWindow()
    
    # 3. Показываем окно на экране
    window.show()
    
    # 4. Запускаем главный цикл обработки событий приложения
    # app.exec() будет работать, пока приложение не будет закрыто
    # sys.exit() обеспечивает корректное завершение программы
    sys.exit(app.exec()) 

# Основные компоненты приложения:
# 1. MainWindow - главное окно приложения
#    - Содержит все элементы интерфейса
#    - Управляет записью аудио
#    - Обрабатывает чаты
#
# 2. AudioRecorder - класс для записи аудио
#    - Записывает аудио с микрофона
#    - Сохраняет чанки аудио
#
# 3. ChatProcessor - класс для обработки чатов
#    - Работает в отдельном потоке
#    - Обрабатывает аудио и генерирует ответы
#
# 4. FileManager - класс для управления файлами
#    - Создает директории для чатов
#    - Сохраняет аудио чанки
#
# 5. WaveVisualizer - класс для визуализации аудио
#    - Показывает уровень звука в реальном времени

# command to run: python src/main.py