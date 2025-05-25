import sounddevice as sd
import numpy as np
import wave
import io

class AudioRecorder:
    def __init__(self):
        self.sample_rate = 16000
        self.channels = 1
        self.is_recording = False
        self.audio_buffer = []
        
    def start_recording(self):
        """Начинает запись аудио"""
        self.is_recording = True
        self.audio_buffer = []
        
        def callback(indata, frames, time, status):
            if status:
                print(f"Ошибка записи: {status}")
            if self.is_recording:
                self.audio_buffer.extend(indata.copy())
        
        self.stream = sd.InputStream(
            channels=self.channels,
            samplerate=self.sample_rate,
            callback=callback
        )
        self.stream.start()
        
    def stop_recording(self):
        """Останавливает запись аудио"""
        if self.is_recording:
            self.is_recording = False
            if hasattr(self, 'stream'):
                self.stream.stop()
                self.stream.close()
                
    def get_audio_level(self):
        """Возвращает текущий уровень звука для визуализации"""
        if not self.audio_buffer:
            return 0
        recent_samples = self.audio_buffer[-1000:] if len(self.audio_buffer) > 1000 else self.audio_buffer
        return float(np.abs(recent_samples).mean())
        
    def save_chunk(self):
        """Сохраняет текущий чанк аудио и очищает буфер"""
        if not self.audio_buffer:
            return None
            
        audio_data = np.array(self.audio_buffer, dtype=np.float32)
        audio_data = (audio_data * 32767).astype(np.int16)
        self.audio_buffer = []
        
        with io.BytesIO() as wav_buffer:
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(self.channels)
                wav_file.setsampwidth(2)
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(audio_data.tobytes())
            return wav_buffer.getvalue() 