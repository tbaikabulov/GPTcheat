import os
import wave

# Создаем папку temp
os.makedirs("temp", exist_ok=True)

# Открываем выходной файл
with wave.open("temp/combined.wav", 'wb') as out:
    # Берем параметры из первого файла
    with wave.open("logs/chat_20250525_193549/chunk6.wav", 'rb') as first:
        out.setparams(first.getparams())
    
    # Копируем данные из каждого чанка
    for i in range(6, 10):
        with wave.open(f"logs/chat_20250525_193549/chunk{i}.wav", 'rb') as chunk:
            out.writeframes(chunk.readframes(chunk.getnframes()))

print("Готово! Файл сохранен в temp/combined.wav")

# command to run: python audio_to_text.py