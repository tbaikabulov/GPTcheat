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

    # Открываем выходной файл
    with wave.open(output_file_name, 'wb') as out:
        # Берем параметры из первого файла
        with wave.open(f"logs/chat_{chat_id}/chunk{start_chunk_id}.wav", 'rb') as first:
            out.setparams(first.getparams())
        
        # Копируем данные из каждого чанка
        for i in range(start_chunk_id, end_chunk_id + 1):
            with wave.open(f"logs/chat_{chat_id}/chunk{i}.wav", 'rb') as chunk:
                out.writeframes(chunk.readframes(chunk.getnframes()))

    print(f"Готово! Файл сохранен в {output_file_name}")

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