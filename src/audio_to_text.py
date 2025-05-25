import os
from openai import OpenAI
from dotenv import load_dotenv

def transcribe_audio(wav_file_path):
    # Загружаем API ключ из .env файла
    load_dotenv()
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY не найден в .env файле")
    
    # Создаем клиент OpenAI
    client = OpenAI(api_key=api_key)
    
    try:
        # Открываем и отправляем файл на распознавание
        with open(wav_file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="ru",
                response_format="text"
            )
        return transcript
    except Exception as e:
        print(f"Ошибка при распознавании речи: {str(e)}")
        return None

wav_file = "temp/combined.wav"
    
# Получаем расшифровку
result = transcribe_audio(wav_file)
    
# Выводим результат
if result:
    print("Расшифровка аудио:")
    print(result)
else:
    print("Не удалось распознать аудио")

# command to run: python src/audio_to_text.py

