import json
import os
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

class QuestionAnalyzer:
    def __init__(self):
        # Загружаем переменные окружения из .env
        load_dotenv()
        
        self.config = self.load_config()
        self.log_file = self.config['settings']['log_file']
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))  # Инициализация клиента OpenAI с ключом
        self.setup_logging()
        
    def load_config(self):
        """Загрузка конфигурации из файлов"""
        try:
            # Загружаем контекст
            with open('context/context.txt', 'r', encoding='utf-8') as f:
                context = f.read()
                
            # Загружаем промпт
            with open('context/prompt.txt', 'r', encoding='utf-8') as f:
                prompt_template = f.read()
                
            # Загружаем описание вакансии
            with open('context/vacancy.txt', 'r', encoding='utf-8') as f:
                vacancy_info = f.read()
                
            return {
                "context": {
                    "background": context,
                    "current_role": "",
                    "key_achievements": [],
                    "vacancy_info": vacancy_info
                },
                "settings": {
                    "context_duration": 120,
                    "analysis_interval": 10,
                    "max_context_length": 2000,
                    "log_file": "interview_log.txt"
                },
                "prompt_template": prompt_template
            }
        except Exception as e:
            print(f"Ошибка загрузки конфигурации: {str(e)}")
            return {
                "context": {
                    "background": "",
                    "current_role": "",
                    "key_achievements": [],
                    "vacancy_info": ""
                },
                "settings": {
                    "context_duration": 120,
                    "analysis_interval": 10,
                    "max_context_length": 2000,
                    "log_file": "interview_log.txt"
                },
                "prompt_template": "Ты - ассистент на собеседовании. На основе последних {duration} секунд разговора ({context}) сгенерируй релевантную подсказку или совет."
            }
    
    def setup_logging(self):
        """Настройка логирования"""
        try:
            # Создаем директорию для логов, если её нет
            os.makedirs('logs', exist_ok=True)
            self.log_path = os.path.join('logs', self.log_file)
            
            # Создаем файл с заголовком, если он не существует
            if not os.path.exists(self.log_path):
                with open(self.log_path, 'w', encoding='utf-8') as f:
                    f.write("=== Начало сессии ===\n")
                    f.write(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Контекст: {self.config['context']['background']}\n")
                    f.write("===================\n\n")
        except Exception as e:
            print(f"Ошибка настройки логирования: {str(e)}")
    
    def log_text(self, text):
        """Логирование распознанного текста"""
        try:
            with open(self.log_path, 'a', encoding='utf-8') as f:
                timestamp = datetime.now().strftime('%H:%M:%S')
                f.write(f"[{timestamp}] {text}\n")
        except Exception as e:
            print(f"Ошибка логирования: {str(e)}")
    
    def log_gpt_interaction(self, prompt, response):
        """Логирование взаимодействия с GPT"""
        try:
            # Создаем файл для текущей сессии
            session_file = os.path.join('logs', f'gpt_session_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')
            
            with open(session_file, 'a', encoding='utf-8') as f:
                f.write("=== Запрос к GPT ===\n")
                f.write(f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Промпт:\n{prompt}\n")
                f.write(f"\nОтвет GPT:\n{response}\n")
                f.write("===================\n\n")
        except Exception as e:
            print(f"Ошибка логирования GPT: {str(e)}")
    
    def analyze_question(self, context):
        """Анализ контекста и генерация подсказки"""
        try:
            # Логируем контекст
            self.log_text(context)
            
            # Формируем промпт
            prompt = self.config['prompt_template'].format(
                background=self.config['context']['background'],
                current_role=self.config['context']['current_role'],
                achievements=", ".join(self.config['context']['key_achievements']),
                duration=self.config['settings']['context_duration'],
                context=context,
                vacancy_info=self.config['context']['vacancy_info']
            )
            
            # Отправляем запрос к GPT
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Ты - ассистент на собеседовании. Твоя задача - помогать кандидату, анализируя контекст разговора и предоставляя релевантные подсказки."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=150
            )
            
            hint = response.choices[0].message.content.strip()
            
            # Логируем подсказку
            self.log_text(f"Подсказка: {hint}")
            
            # Логируем полное взаимодействие с GPT
            self.log_gpt_interaction(prompt, hint)
            
            return hint
            
        except Exception as e:
            print(f"Ошибка при анализе вопроса: {str(e)}")
            return None

    def analyze(self, text):
        # Простой анализатор, который определяет, является ли текст вопросом
        return text.strip().endswith('?') 