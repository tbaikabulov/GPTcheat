

# unite_chunks -> audio_to_text -> text_to_good_text -> gt_to_answer

# temp/combined.wav

from functions import *



wav_file = "temp/combined.wav"

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
chat_id = 1

def process_chat(chat_id):
    N = count_chunks(chat_id)

    unite_chunks(1, N-5, N, wav_file)
        
    # Получаем расшифровку
    raw_text = audio_to_text(wav_file, api_key)

    text = text_to_good_text(raw_text, improve_text_prompt)
        
    print(f"text: {text}")

    answer_prompt =f"""
    Ты умный помощник на собеседовании на аналитика данных. Прямо сейчас идет собеседование, текст расшифровки аудио:
    [[TEXT]]

    По контексту диалога пойми о чем идет речь, в чем сейчас основной вопрос, и отобрази напиши текст, который
    отобразится на экране

    В нем вкратце должны быть основные тезисы ответа, возможно шпаргалка, которая будет полезна для ответа.

    """


    answer = gt_to_answer(text, answer_prompt)

    print(f"answer: {answer}")

    return raw_text, text, answer


# command to run: python src/script.py









