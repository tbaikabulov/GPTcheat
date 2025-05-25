import os
import wave

from functions import unite_chunks


chat_id = 1

# считаем общее кол-во чанков:
def count_chunks(chat_id):
    return len(os.listdir(f"logs/chat_{chat_id}"))


def unite_chunks(chat_id, start_chunk_id, end_chunk_id, output_file_name, to_print = False):
    # Создаем папку temp
    os.makedirs("temp", exist_ok=True)
    
    # Формируем путь к директории чата
    chat_dir = f"logs/chat_{chat_id}"
    
    # Создаем директорию чата, если она не существует
    os.makedirs(chat_dir, exist_ok=True)
    
    # Находим все существующие чанки
    existing_chunks = []
    for i in range(start_chunk_id, end_chunk_id + 1):
        print(f"chunk{i}.wav")
        chunk_path = os.path.join(chat_dir, f"chunk{i}.wav")
        if os.path.exists(chunk_path):
            existing_chunks.append(i)
    
    if not existing_chunks:
        print(f"Ошибка: Не найдено ни одного чанка в диапазоне {start_chunk_id}-{end_chunk_id}")
        return False

    # Открываем выходной файл
    with wave.open(output_file_name, 'wb') as out:
        # Берем параметры из первого существующего файла
        first_chunk_path = os.path.join(chat_dir, f"chunk{existing_chunks[0]}.wav")
        with wave.open(first_chunk_path, 'rb') as first:
            out.setparams(first.getparams())
        
        # Копируем данные из каждого существующего чанка
        for chunk_id in existing_chunks:
            chunk_path = os.path.join(chat_dir, f"chunk{chunk_id}.wav")
            with wave.open(chunk_path, 'rb') as chunk:
                out.writeframes(chunk.readframes(chunk.getnframes()))
    if to_print:
        print(f"Готово! Файл сохранен в {output_file_name}")
    return True

N = count_chunks(chat_id)

# unite_chunks(1, N-5, N, "temp/combined.wav")

unite_chunks(1, 1, 1, "temp/combined.wav", to_print=True)

# command to run: python src/unite_chunks.py
