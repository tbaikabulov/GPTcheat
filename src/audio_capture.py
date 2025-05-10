import sounddevice as sd
import numpy as np
import wave
import io
import threading
import queue
from collections import deque

class AudioCapture:
    def __init__(self, device_id=None):
        self.sample_rate = 16000
        self.channels = 1
        self.dtype = np.int16
        self.chunk_size = 1024
        self.device_id = device_id
        
        # Буфер для уровней звука
        self.levels_buffer = deque(maxlen=200)
        self.levels_lock = threading.Lock()
        
        # Буфер для аудио фреймов
        self.frames = []
        self.frames_lock = threading.Lock()
        
        # Буфер для последних N секунд аудио
        self.context_duration = 30  # секунды контекста
        self.context_frames = []
        self.context_lock = threading.Lock()
        
        # Флаги состояния
        self.is_recording = False
        self.stream = None
        
    def _audio_callback(self, indata, frames, time, status):
        """Callback для получения аудио данных"""
        if status:
            print(f"Ошибка аудио потока: {status}")
        if self.is_recording:
            # Вычисляем уровень звука
            level = np.max(np.abs(indata)) / 32768.0
            level = np.power(level, 0.5)  # Усиливаем слабые сигналы
            
            # Сохраняем уровень в буфер
            with self.levels_lock:
                self.levels_buffer.append(level)
            
            # Сохраняем аудио фрейм
            with self.frames_lock:
                self.frames.append(indata.tobytes())
            
            # Сохраняем фрейм в контекстный буфер
            with self.context_lock:
                self.context_frames.append(indata.tobytes())
                # Ограничиваем размер контекстного буфера
                max_frames = int(self.context_duration * self.sample_rate / self.chunk_size)
                if len(self.context_frames) > max_frames:
                    self.context_frames = self.context_frames[-max_frames:]
    
    def start_recording(self):
        """Начать запись"""
        if not self.is_recording:
            try:
                self.is_recording = True
                self.levels_buffer.clear()
                self.frames.clear()  # Очищаем буфер фреймов
                
                # Запускаем аудио поток
                self.stream = sd.InputStream(
                    device=self.device_id,
                    samplerate=self.sample_rate,
                    channels=self.channels,
                    dtype=self.dtype,
                    callback=self._audio_callback,
                    blocksize=self.chunk_size
                )
                self.stream.start()
                print("Аудио поток успешно запущен")
                
            except Exception as e:
                self.is_recording = False
                print(f"Ошибка запуска аудио потока: {str(e)}")
                raise
    
    def stop_recording(self):
        """Остановить запись"""
        if self.is_recording:
            self.is_recording = False
            if self.stream:
                try:
                    self.stream.stop()
                    self.stream.close()
                    self.stream = None
                except Exception as e:
                    print(f"Ошибка остановки аудио потока: {str(e)}")
    
    def get_audio_level(self):
        """Получить текущий уровень звука"""
        with self.levels_lock:
            if self.levels_buffer:
                return self.levels_buffer[-1]
        return 0
    
    def get_audio_data(self):
        """Получить записанные аудио данные"""
        try:
            with self.frames_lock:
                if not self.frames:
                    print("Нет аудио данных для обработки")
                    return None
                
                # Создаем WAV файл в памяти
                with io.BytesIO() as wav_buffer:
                    with wave.open(wav_buffer, 'wb') as wav_file:
                        wav_file.setnchannels(self.channels)
                        wav_file.setsampwidth(2)  # 16-bit audio
                        wav_file.setframerate(self.sample_rate)
                        wav_file.writeframes(b''.join(self.frames))
                    
                    # Получаем аудио данные
                    wav_buffer.seek(0)
                    return wav_buffer.read()
                
        except Exception as e:
            print(f"Ошибка при получении аудио данных: {str(e)}")
            return None
    
    def get_context_audio(self):
        """Получить последние N секунд аудио для контекста"""
        try:
            with self.context_lock:
                if not self.context_frames:
                    return None
                
                # Создаем WAV файл в памяти
                with io.BytesIO() as wav_buffer:
                    with wave.open(wav_buffer, 'wb') as wav_file:
                        wav_file.setnchannels(self.channels)
                        wav_file.setsampwidth(2)  # 16-bit audio
                        wav_file.setframerate(self.sample_rate)
                        wav_file.writeframes(b''.join(self.context_frames))
                    
                    # Получаем аудио данные
                    wav_buffer.seek(0)
                    return wav_buffer.read()
                
        except Exception as e:
            print(f"Ошибка при получении контекстного аудио: {str(e)}")
            return None
    
    def __del__(self):
        self.stop_recording() 