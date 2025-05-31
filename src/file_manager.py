import os
from datetime import datetime

class FileManager:
    def __init__(self):
        self.current_chat = None
        # Создаем директории если их нет
        self.audio_dir = os.path.join("logs", "audio")
        self.text_dir = os.path.join("logs", "text")
        if not os.path.exists(self.audio_dir):
            os.makedirs(self.audio_dir)
        if not os.path.exists(self.text_dir):
            os.makedirs(self.text_dir)
        
    def log_event(self, event_type, details):
        """Логирует событие в файл"""
        if not self.current_chat:
            return
            
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_file = os.path.join(self.text_dir, f"{self.current_chat}_log.txt")
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"{timestamp} - {event_type}: {details}\n")
        
    def create_chat_directory(self):
        """Создает новую директорию для чата"""
        # Находим следующий доступный номер чата
        existing_chats = [d for d in os.listdir(self.audio_dir) 
                         if os.path.isdir(os.path.join(self.audio_dir, d)) and d.startswith('chat_')]
        if existing_chats:
            last_chat = max(int(chat.split('_')[1]) for chat in existing_chats)
            chat_num = last_chat + 1
        else:
            chat_num = 1
            
        # Создаем директорию для нового чата
        chat_dir = os.path.join(self.audio_dir, f'chat_{chat_num}')
        os.makedirs(chat_dir, exist_ok=True)
        self.current_chat = f'chat_{chat_num}'
        
        # Логируем создание нового чата
        self.log_event("Создан новый чат", f"chat_{chat_num}")
        
        return chat_dir
        
    def save_audio_chunk(self, chunk_data):
        """Сохраняет чанк аудио в текущую директорию чата"""
        if not self.current_chat:
            return None
            
        # Находим следующий доступный номер чанка
        chat_dir = os.path.join(self.audio_dir, self.current_chat)
        existing_chunks = [f for f in os.listdir(chat_dir) 
                          if f.startswith('chunk_') and f.endswith('.wav')]
        if existing_chunks:
            last_chunk = max(int(chunk.split('_')[1].split('.')[0]) for chunk in existing_chunks)
            chunk_num = last_chunk + 1
        else:
            chunk_num = 1
            
        # Сохраняем чанк
        filepath = os.path.join(chat_dir, f'chunk_{chunk_num}.wav')
        with open(filepath, 'wb') as f:
            f.write(chunk_data)
            
        # Логируем сохранение чанка
        self.log_event("Сохранен чанк", f"chunk_{chunk_num}")
        
        return filepath
        
    def get_next_chunk_number(self):
        """Возвращает номер следующего чанка"""
        if not self.current_chat:
            return None
            
        chat_dir = os.path.join(self.audio_dir, self.current_chat)
        existing_chunks = [f for f in os.listdir(chat_dir) 
                          if f.startswith('chunk_') and f.endswith('.wav')]
        if existing_chunks:
            last_chunk = max(int(chunk.split('_')[1].split('.')[0]) for chunk in existing_chunks)
            return last_chunk + 1
        else:
            return 1 