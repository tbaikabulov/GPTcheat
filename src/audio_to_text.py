import os
from openai import OpenAI
from dotenv import load_dotenv

from functions import *

wav_file = "temp/combined.wav"
    
# Получаем расшифровку
result = audio_to_text(wav_file, api_key)

print(result)
    
# command to run: python src/audio_to_text.py

