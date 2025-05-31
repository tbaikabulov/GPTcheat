import os
import wave

from functions import unite_chunks, count_chunks

chat_id = 1

N = count_chunks(chat_id)

# unite_chunks(1, N-5, N, "temp/combined.wav")

unite_chunks(1, 1, 1, "temp/combined.wav", to_print=True)

# command to run: python src/unite_chunks.py
