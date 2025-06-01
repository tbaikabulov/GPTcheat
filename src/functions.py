from openai import OpenAI
from dotenv import load_dotenv
import os
import wave
from anthropic import Anthropic
import requests

load_dotenv()

OPENAI_ORGANIZATION = os.getenv("OPENAI_ORGANIZATION")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL")
GROK_API_KEY = os.getenv("GROK_API_KEY")    

def unite_chunks(chat_id, start_chunk, end_chunk, output_file):
    """Объединяет чанки аудио в один файл"""
    try:
        # Получаем список чанков
        chat_dir = f"logs/audio/chat_{chat_id}"
        chunks = sorted([f for f in os.listdir(chat_dir) if f.startswith('chunk_') and f.endswith('.wav')])
        
        if not chunks:
            return False
            
        # Объединяем чанки
        with wave.open(output_file, 'wb') as output:
            for i, chunk in enumerate(chunks[start_chunk:end_chunk]):
                with wave.open(os.path.join(chat_dir, chunk), 'rb') as w:
                    if i == 0:
                        output.setparams(w.getparams())
                    output.writeframes(w.readframes(w.getnframes()))
        return True
    except Exception as e:
        print(f"Ошибка при объединении чанков: {str(e)}")
        return False

def count_chunks(chat_id):
    """Возвращает количество чанков в чате"""
    try:
        return len(os.listdir(f"logs/audio/chat_{chat_id}"))
    except:
        return 0

def chat_question_claude(question, temperature=0, prep="", conversation_id=None):
    anthropic = Anthropic(api_key=CLAUDE_API_KEY)
    
    try:
        messages = []
        if prep:
            messages.append({
                "role": "system",
                "content": prep
            })
        
        messages.append({
            "role": "user",
            "content": question
        })
        
        response = anthropic.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1000,
            messages=messages,
            temperature=temperature
        )
        
        return response.content[0].text
        
    except Exception as e:
        print(f"Error in Claude request: {str(e)}")
        return "An error occurred while processing your request. Please try again."


def chat_question_grok(question, temperature=0, prep="You are a test assistant."):
    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROK_API_KEY}"
    }
    
    data = {
        "messages": [
            {
                "role": "system",
                "content": prep
            },
            {
                "role": "user",
                "content": question
            }
        ],
        "model": "grok-2-latest",
        "stream": False,
        "temperature": temperature
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        return response.json()['choices'][0]['message']['content']
        
    except requests.exceptions.RequestException as e:
        print(f"Error making request to Grok API: {str(e)}")
        return "An error occurred while processing your request. Please try again."

def chat_question_gpt(question, temperature = 0, prep="", conversation_id=None):
    client = OpenAI(organization=OPENAI_ORGANIZATION)
    messages = [{"role": "system", "content": prep}]
    messages.append({"role": "user", "content": question})

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=temperature
    )

    answer = completion.choices[0].message.content

    return answer

def audio_to_text(wav_file_path):
    client = OpenAI(api_key=OPENAI_API_KEY)
    
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


def gt_to_answer(text, answer_prompt):
    question = answer_prompt.replace("[[TEXT]]", text)
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

Заново напиши текст, сформулировав что имелось ввиду. Только текст ответа, без дополнительных комментариев.
"""

answer_prompt =f"""
   Ты умный помощник на собеседовании на аналитика данных. Прямо сейчас идёт собеседование, ниже расшифровка текста разговора:

[[TEXT]]

На основе этого текста выведи на экран краткую, полезную выжимку для кандидата — как шпаргалку. Никаких вступлений, пояснений, воды.

В ответе:
1. Чётко сформулируй, в чём сейчас основной вопрос интервьюера (1 предложение).
2. Дай 2–3 пункта краткого пошагового решения, с минимально необходимыми пояснениями и примерами кода на Python.
3. В конце — 1 дополнительный совет, как ответить на уточняющие вопросы или углубить тему.

Только факты. Только по делу.



    """
