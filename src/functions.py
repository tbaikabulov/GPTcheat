from openai import OpenAI
from dotenv import load_dotenv
import os
import wave

load_dotenv()

organization = os.getenv("OPENAI_ORGANIZATION")

api_key = os.getenv("OPENAI_API_KEY")

def unite_chunks(chat_id, start_chunk_id, end_chunk_id, output_file_name):
    # Создаем папку temp
    os.makedirs("temp", exist_ok=True)
    
    # Формируем путь к директории чата
    chat_dir = f"logs/chat_{chat_id}"
    
    # Создаем директорию чата, если она не существует
    os.makedirs(chat_dir, exist_ok=True)
    
    # Находим все существующие чанки
    existing_chunks = []
    for i in range(start_chunk_id, end_chunk_id + 1):
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

    print(f"Готово! Файл сохранен в {output_file_name}")
    return True


# считаем общее кол-во чанков:
def count_chunks(chat_id):
    return len(os.listdir(f"logs/chat_{chat_id}"))

def chat_question_gpt(question, temperature = 0, prep="", conversation_id=None):
    client = OpenAI(organization=organization)
    messages = [{"role": "system", "content": prep}]
    messages.append({"role": "user", "content": question})

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=temperature
    )

    answer = completion.choices[0].message.content

    return answer

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
    
def text_to_good_text(text, prompt):
    question = prompt.replace("[[TEXT]]", text)
    answer = chat_question_gpt(question)
    
    return answer


def gt_to_answer(text, prompt):
    question = prompt.replace("[[TEXT]]", text)
    answer = chat_question_gpt(question)
    
    return answer

improve_text_prompt = f"""
Перед тобой текст расшифровки аудио модели whisper.
Твоя задача - переписать текст так, чтобы он был понятен и читабелен.
Учти, что слова могли неверно распознаться, поэтому по контексту пойми, что имелось ввиду.
Общая тема: собеседование на аналитика данных, возможные термины:
pandas, python, sql, статистика, проверка гипотез, ad hoc задачи

Текст расшифровки:
[[TEXT]]

Заново напиши текст, сформулировав что имелось ввиду.
"""

answer_prompt =f"""
    Ты умный помощник на собеседовании на аналитика данных. Прямо сейчас идет собеседование, текст расшифровки аудио:
    [[TEXT]]

    По контексту диалога пойми о чем идет речь, в чем сейчас основной вопрос, и отобрази напиши текст, который
    отобразится на экране

    В нем вкратце должны быть основные тезисы ответа, возможно шпаргалка, которая будет полезна для ответа.

    """

def process_chat(chat_id, wav_file = "temp/combined.wav", improve_text_prompt = improve_text_prompt, answer_prompt = answer_prompt, to_print = True):
    N = count_chunks(chat_id)

    unite_chunks(chat_id, max(N-5, 0), N, wav_file)
    if to_print:
        print(f"Файл объединен перед отправкой на распознавание")
        
    # Получаем расшифровку
    raw_text = audio_to_text(wav_file, api_key)
    if to_print:
        print(f"Расшифровка получена")

    text = text_to_good_text(raw_text, improve_text_prompt)
    if to_print:
        print(f"text: {text}")

    answer = gt_to_answer(text, answer_prompt)
    if to_print:
        print(f"answer: {answer}")

    return raw_text, text, answer