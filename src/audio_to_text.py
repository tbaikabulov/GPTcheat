import os
from openai import OpenAI
from dotenv import load_dotenv

def audio_to_text(wav_file_path, api_key):
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
result = audio_to_text(wav_file)
    
# command to run: python src/audio_to_text.py

