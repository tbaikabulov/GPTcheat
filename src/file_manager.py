import os
from datetime import datetime

class FileManager:
    def __init__(self):
        self.base_dir = "logs"
        self.current_chat = None
        self.chunk_counter = 0
        
    def create_chat_directory(self):
        """Создает директорию для нового чата"""
        chat_name = f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        chat_dir = os.path.join(self.base_dir, chat_name)
        os.makedirs(chat_dir, exist_ok=True)
        self.current_chat = chat_name
        self.chunk_counter = 0
        return chat_dir
        
    def save_audio_chunk(self, audio_data):
        """Сохраняет чанк аудио в текущую директорию чата"""
        if not self.current_chat:
            self.create_chat_directory()
            
        self.chunk_counter += 1
        filename = f"chunk{self.chunk_counter}.wav"
        filepath = os.path.join(self.base_dir, self.current_chat, filename)
        
        with open(filepath, 'wb') as f:
            f.write(audio_data)
            
        return filepath
        
    def get_next_chunk_number(self):
        """Возвращает номер следующего чанка"""
        return self.chunk_counter + 1 