# Ollama Telegram Bot

Telegram бот для взаимодействия с локальным Ollama API. Поддерживает контекстные беседы, анализ изображений и различные модели.

## Возможности

- 🤖 Поддержка моделей (С Возможность добавления):
  - Qwen 2.5 Coder (32B)
  - Qwen 2.5
  - Qwen 2.5 (32B)
  - LLaVA (34B) для анализа изображений
- 💬 Контекстные беседы
- 🖼️ Анализ изображений
- 🔄 Автоматическая очистка старых контекстов
- ⚡ Асинхронная обработка запросов
- 🚀 Systemd интеграция

## Требования

- Python 3.9+
- Ollama с установленными моделями
- Telegram Bot Token
- Linux с systemd

## Установка

### Вариант 1: Автоматическая установка (рекомендуется)

```bash
# Клонируем репозиторий
git clone https://github.com/yourusername/ollama-telegram-bot.git
cd ollama-telegram-bot

# Делаем скрипт установки исполняемым
chmod +x install.sh

# Запускаем установку
sudo ./install.sh
```

Скрипт установки:

- Установит все зависимости через pip
- Запустит setup.py для создания systemd сервиса
- Настроит все необходимые права доступа
- Создаст и активирует systemd сервис

### Вариант 2: Ручная установка

```bash
# Клонируем репозиторий
git clone https://github.com/yourusername/ollama-telegram-bot.git
cd ollama-telegram-bot

# Устанавливаем зависимости и создаем сервис
pip install -r requirements.txt
sudo python3 setup.py develop
```

## Настройка

1. Установите Ollama и модели:

```bash
ollama pull qwen2.5-coder:32b
ollama pull qwen2.5
ollama pull qwen2.5:32b
ollama pull llava:34b
```

2. Настройте конфигурацию в config.py:

```python
API_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
ALLOWED_IDS = [your_telegram_id]  # Список разрешенных ID пользователей
OLLAMA_API_URL: str = "http://localhost:11434/api/generate" # Адрес узла с Ollama
OLLAMA_CHAT_URL: str = "http://localhost:11434/api/chat" # Адрес узла с Ollama
```

## Запуск

### Через systemd (после установки):

```bash
# Включаем автозапуск
sudo systemctl enable ollama-bot

# Запускаем сервис
sudo systemctl start ollama-bot
```

### Ручной запуск (для отладки):

```bash
python main.py
```

## Управление сервисом

```bash
# Проверка статуса
sudo systemctl status ollama-bot

# Просмотр логов
sudo journalctl -u ollama-bot -f

# Перезапуск
sudo systemctl restart ollama-bot

# Остановка
sudo systemctl stop ollama-bot
```

## Использование бота

1. Команды:

   - `/start` - Начать работу
   - `/help` - Справка
   - `/reset` - Сбросить контекст

2. Кнопки меню:

   - 🔄 Сбросить контекст
   - ⚙️ Сменить модель
   - ❓ Помощь

3. Возможности:
   - Отправка текстовых сообщений
   - Отправка изображений для анализа
   - Контекстные беседы (сохранение истории)
   - Выбор различных моделей

## Структура проекта

```
ollama-telegram-bot/
├── main.py           # Основной файл бота
├── config.py         # Конфигурация
├── database.py       # База данных
├── setup.py         # Установка и настройка systemd
├── install.sh       # Скрипт автоматической установки
└── requirements.txt  # Зависимости
```

## Устранение неполадок

1. Проблемы с установкой:

```bash
# Просмотр логов установки
sudo ./install.sh

# Проверка сервиса
sudo systemctl status ollama-bot
sudo journalctl -u ollama-bot -f

# Проверка прав доступа
ls -la /etc/systemd/system/ollama-bot.service
sudo systemctl daemon-reload
```

2. Проверка компонентов:
   - Ollama запущен и доступен (`systemctl status ollama`)
   - Модели установлены (`ollama list`)
   - Конфигурация верная (токен, ID и адрес в config.py)
   - База данных создана и доступна для записи
