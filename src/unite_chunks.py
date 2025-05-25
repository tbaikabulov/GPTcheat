import os
import wave

def unite_chunks(chat_id, start_chunk_id, end_chunk_id, output_file_name):
    # Создаем папку temp
    os.makedirs("temp", exist_ok=True)

    # Открываем выходной файл
    with wave.open(output_file_name, 'wb') as out:
        # Берем параметры из первого файла
        with wave.open(f"logs/chat_{chat_id}/chunk{start_chunk_id}.wav", 'rb') as first:
            out.setparams(first.getparams())
        
        # Копируем данные из каждого чанка
        for i in range(start_chunk_id, end_chunk_id + 1):
            with wave.open(f"logs/chat_{chat_id}/chunk{i}.wav", 'rb') as chunk:
                out.writeframes(chunk.readframes(chunk.getnframes()))

    print("Готово! Файл сохранен в temp/combined.wav")

chat_id = 1

# считаем общее кол-во чанков:
def count_chunks(chat_id):
    return len(os.listdir(f"logs/chat_{chat_id}"))

N = count_chunks(chat_id)

unite_chunks(1, N-5, N, "temp/combined.wav")

# command to run: python src/unite_chunks.py