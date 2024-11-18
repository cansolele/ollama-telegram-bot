from typing import List


class Config:
    # Telegram Configuration
    API_TOKEN: str = "token"
    ALLOWED_IDS: List[int] = [
        000,
        000,
    ]  # List of allowed user IDs

    # Ollama API Configuration
    OLLAMA_API_URL: str = "http://localhost:11434/api/generate"
    OLLAMA_CHAT_URL: str = "http://localhost:11434/api/chat"
    IMAGE_MODEL: str = "llava:34b"  # Модель для распознавания изображений

    # Models Configuration
    MODELS = {
        "1": {
            "name": "qwen2.5-coder:32b",
            "display_name": "Qwen 2.5 Coder - 32B",
            "description": "Specialized for code generation and technical tasks",
        },
        "2": {
            "name": "qwen2.5",
            "display_name": "Qwen 2.5",
            "description": "Balanced model for general purpose use",
        },
        "3": {
            "name": "qwen2.5:32b",
            "display_name": "Qwen 2.5 - 32B",
            "description": "Larger model with enhanced capabilities",
        },
    }

    # Database Configuration
    DATABASE_NAME: str = "user_data.db"

    # Message Templates
    MESSAGES = {
        "unauthorized": "Доступ запрещен. У вас нет разрешения на использование этого бота.",
        "help": """
🤖 Помощь по использованию бота

📝 Основные команды:
/start - Начать общение
/help - Показать это сообщение
/reset - Сбросить контекст беседы

⚙️ Модели:
• Qwen 2.5 Coder (32B) - для работы с кодом
• Qwen 2.5 - универсальная модель
• Qwen 2.5 (32B) - расширенная версия

💡 Особенности:
• Бот поддерживает контекстные беседы
• Можно отправлять изображения для анализа
• Контекст сохраняется между сообщениями
• Можно менять модель в процессе общения

🔄 Контекст автоматически очищается через 30 минут неактивности или по команде /reset
        """,
        "model_changed": "Модель успешно изменена на: {}",
        "error": "Произошла ошибка. Пожалуйста, попробуйте позже.",
        "context_reset": "Контекст беседы сброшен.",
        "welcome": "Добро пожаловать! Я готов помочь вам. Используйте /help для получения справки.",
    }
