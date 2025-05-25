# Руководство по модулям

## 1. AudioRecorder (audio_recorder.py)

### Что это такое?
Это модуль, который отвечает за запись аудио с микрофона. Представьте его как диктофон.

### Как работает?
1. **Инициализация**:
```python
recorder = AudioRecorder()
```
- Создается пустой буфер для хранения аудио
- Устанавливаются параметры записи:
  - sample_rate = 16000 (частота дискретизации)
  - channels = 1 (моно запись)
  - dtype = float32 (формат данных)

2. **Начало записи**:
```python
recorder.start_recording()
```
- Запускается поток записи с микрофона
- Начинает работать callback функция

3. **Процесс записи**:
```python
def callback(indata, frames, time, status):
    if self.is_recording:
        self.audio_buffer.extend(indata.copy())
```
- Каждые 16мс получаем новые данные
- `indata` - это массив чисел (сэмплов)
- Каждое число - это амплитуда звука в момент времени
- Данные добавляются в буфер

4. **Получение уровня звука**:
```python
def get_audio_level(self):
    recent_samples = self.audio_buffer[-1000:]
    return float(np.abs(recent_samples).mean())
```
- Берем последние 1000 сэмплов
- Находим среднее значение
- Используется для визуализации

5. **Сохранение чанка**:
```python
def save_chunk(self):
    audio_data = np.array(self.audio_buffer, dtype=np.float32)
    audio_data = (audio_data * 32767).astype(np.int16)
    self.audio_buffer.clear()
    return audio_data
```
- Конвертируем буфер в WAV формат
- Очищаем буфер
- Возвращаем данные для сохранения

### Что хранится в буфере?
- Последовательность чисел от -1.0 до 1.0
- Каждое число - это амплитуда звука
- 16000 чисел = 1 секунда записи

## 2. WaveVisualizer (wave_visualizer.py)

### Что это такое?
Визуализатор, который показывает волну звука в реальном времени.

### Как работает?
1. **Инициализация**:
```python
visualizer = WaveVisualizer()
```
- Создается буфер для хранения уровней звука
- Размер буфера = 200 точек

2. **Обновление**:
```python
def update_level(self, level):
    self.levels.append(level)
    self.update()
```
- Получаем новый уровень звука
- Добавляем в буфер
- Перерисовываем виджет

3. **Отрисовка**:
```python
def paintEvent(self, event):
    # Рисуем волну
    for i, level in enumerate(self.levels):
        x = i * step
        y = center_y - level * height * 6.75
        painter.drawLine(int(x), int(center_y), int(x), int(y))
```
- Рисуем вертикальные линии
- Высота линии зависит от уровня звука

## 3. FileManager (file_manager.py)

### Что это такое?
Менеджер файлов, который создает папки и сохраняет аудио.

### Как работает?
1. **Создание директории**:
```python
def create_chat_directory(self):
    chat_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    chat_dir = os.path.join("logs", chat_name)
    os.makedirs(chat_dir, exist_ok=True)
    return chat_dir
```
- Создает папку с текущей датой и временем
- Возвращает путь к папке

2. **Сохранение чанка**:
```python
def save_audio_chunk(self, audio_data):
    filename = f"chunk_{self.chunk_counter:03d}.wav"
    filepath = os.path.join(self.current_chat_dir, filename)
    
    with wave.open(filepath, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(audio_data.tobytes())
    
    self.chunk_counter += 1
    return filepath
```
- Создает WAV файл
- Записывает аудио данные
- Увеличивает счетчик чанков

## 4. MainWindow (main.py)

### Что это такое?
Главное окно приложения, которое объединяет все модули.

### Как работает?
1. **Инициализация**:
```python
def __init__(self):
    self.audio_recorder = AudioRecorder()
    self.file_manager = FileManager()
    self.wave_visualizer = WaveVisualizer()
```
- Создаются все необходимые объекты
- Настраивается интерфейс

2. **Таймеры**:
```python
self.update_timer.start(16)  # 60 FPS
self.chunk_timer.start(10000)  # 10 секунд
```
- Обновление визуализации каждые 16мс
- Сохранение чанка каждые 10 секунд

3. **Управление записью**:
```python
def toggle_recording(self):
    if not self.audio_recorder.is_recording:
        self.start_recording()
    else:
        self.stop_recording()
```
- Запуск/остановка записи
- Обновление интерфейса

## Поток данных

1. **Запись**:
```
Микрофон → AudioRecorder.callback → audio_buffer
```

2. **Визуализация**:
```
audio_buffer → get_audio_level → WaveVisualizer → экран
```

3. **Сохранение**:
```
audio_buffer → save_chunk → FileManager → WAV файл
```

## Отладка

1. **Проверка записи**:
```python
print(f"Длина буфера: {len(recorder.audio_buffer)}")
print(f"Уровень звука: {recorder.get_audio_level()}")
```

2. **Проверка сохранения**:
```python
print(f"Сохранен файл: {filepath}")
```

3. **Проверка визуализации**:
```python
print(f"Количество точек: {len(visualizer.levels)}")
```

## Типичные проблемы

1. **Нет звука**:
- Проверьте доступ к микрофону
- Проверьте уровень звука в системе
- Проверьте `audio_buffer` на наличие данных

2. **Нет визуализации**:
- Проверьте `get_audio_level`
- Проверьте обновление `WaveVisualizer`

3. **Нет сохранения**:
- Проверьте права на запись в папку
- Проверьте формат данных в `save_chunk` 