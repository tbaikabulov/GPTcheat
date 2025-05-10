import os
from openai import OpenAI
from dotenv import load_dotenv
import tempfile
import wave
import io

class SpeechRecognition:
    def __init__(self):
        load_dotenv()
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY не найден в .env файле")
        self.client = OpenAI(api_key=api_key)
        
    def recognize(self, audio_data):
        if not audio_data:
            print("Пустые аудио данные")
            return None
            
        try:
            # Создаем временный файл для аудио
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                # Проверяем и конвертируем аудио в правильный формат
                with io.BytesIO(audio_data) as audio_buffer:
                    with wave.open(audio_buffer, 'rb') as wav_file:
                        # Проверяем параметры WAV файла
                        if wav_file.getnchannels() != 1:
                            print("Аудио должно быть моно")
                            return None
                        if wav_file.getsampwidth() != 2:
                            print("Аудио должно быть 16-bit")
                            return None
                        if wav_file.getframerate() != 16000:
                            print("Частота дискретизации должна быть 16kHz")
                            return None
                
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            try:
                # Отправляем на распознавание
                with open(temp_file_path, "rb") as audio_file:
                    transcript = self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language="ru",
                        response_format="text"
                    )
                return transcript
                    
            finally:
                # Гарантируем удаление временного файла
                try:
                    os.remove(temp_file_path)
                except:
                    pass
                    
        except Exception as e:
            print(f"Ошибка при распознавании речи: {str(e)}")
            return None 