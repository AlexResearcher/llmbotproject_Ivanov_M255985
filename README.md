# Итоговый проект: двухсервисная система LLM-консультаций
# Проект выполнил студент группы М25-555 Иванов Александр Александрович (М255985)

Проект состоит из двух независимых сервисов:

- `auth_service` — FastAPI-сервис регистрации, логина и выпуска JWT.
- `bot_service` — Telegram-бот на aiogram, который принимает JWT, валидирует его локально и отправляет LLM-задачи в Celery через RabbitMQ.

Redis используется сразу в двух ролях: как result backend для Celery и как хранилище JWT, привязанных к Telegram `user_id`.

## Структура

```text
.
├── auth_service
├── bot_service
├── docker-compose.yml
└── README.md
```

## Архитектура

```mermaid
flowchart LR
    U["Пользователь"] --> S["Auth Service (FastAPI)"]
    S --> DB["SQLite"]
    S --> T["JWT"]
    U --> B["Telegram Bot (aiogram)"]
    B --> R["Redis"]
    B --> Q["RabbitMQ"]
    Q --> W["Celery Worker"]
    W --> O["OpenRouter"]
    W --> TG["Telegram API"]
```

## Что реализовано

### Auth Service

- `POST /auth/register` — регистрация пользователя
- `POST /auth/login` — логин через `OAuth2PasswordRequestForm`, выдача JWT
- `GET /auth/me` — профиль текущего пользователя по Bearer JWT
- безопасное хеширование паролей через `passlib[bcrypt]`
- JWT с полями `sub`, `role`, `iat`, `exp`
- SQLAlchemy 2.0 + `aiosqlite`
- модульные и интеграционные тесты

### Bot Service

- команда `/token <jwt>` сохраняет JWT в Redis по ключу `token:<telegram_user_id>`
- обычные текстовые сообщения доступны только при валидном JWT
- JWT не создается в боте, а только валидируется
- запросы к LLM уходят в Celery-задачу `llm_request`
- RabbitMQ работает как broker Celery
- Redis используется как backend Celery и как хранилище токенов
- интеграционный тест OpenRouter-клиента через `respx`
- мок-тесты хэндлеров с `fakeredis` и `pytest-mock`

## Переменные окружения

### `auth_service/.env`

```env
APP_NAME=auth-service
ENV=local
JWT_SECRET=change_me_super_secret
JWT_ALG=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
SQLITE_PATH=./auth.db
```

### `bot_service/.env`

```env
APP_NAME=bot-service
ENV=local
TELEGRAM_BOT_TOKEN=
AUTH_SERVICE_URL=http://auth_service:8000
JWT_SECRET=change_me_super_secret
JWT_ALG=HS256
REDIS_URL=redis://redis:6379/0
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672//
OPENROUTER_API_KEY=
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=stepfun/step-3.5-flash:free
OPENROUTER_SITE_URL=https://example.com
OPENROUTER_APP_NAME=bot-service
```

## Локальный запуск через uv

Ниже пример запуска без Docker. Для работы Telegram-бота и OpenRouter нужно заполнить:

- `bot_service/.env -> TELEGRAM_BOT_TOKEN`
- `bot_service/.env -> OPENROUTER_API_KEY`

### 1. Auth Service

```powershell
cd auth_service
python -m pip install uv
uv sync
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Swagger будет доступен по адресу [http://0.0.0.0:8000/docs#/](http://0.0.0.0:8000/docs#/).

### 2. Bot API

```powershell
cd bot_service
python -m pip install uv
uv sync
uv run uvicorn app.main:app --host 0.0.0.0 --port 8001
```

### 3. Celery worker

```powershell
cd bot_service
uv run celery -A app.infra.celery_app.celery_app worker --loglevel=info
```

### 4. Telegram bot

```powershell
cd bot_service
uv run python run_bot.py
```

### 5. Redis и RabbitMQ

Их проще поднять через Docker:

```powershell
docker compose up redis rabbitmq -d
```

RabbitMQ UI: [http://localhost:15672](http://localhost:15672)  
Логин/пароль по умолчанию: `guest / guest`

## Запуск целиком через Docker Compose

```powershell
docker compose up --build
```

После запуска будут доступны:

- Auth Swagger: [http://localhost:8000/docs#/](http://localhost:8000/docs#/)
- Bot health: [http://localhost:8001/health](http://localhost:8001/health)
- RabbitMQ UI: [http://localhost:15672](http://localhost:15672)

## Сценарий тестирования

1. Откройте Swagger Auth Service.
2. Зарегистрируйте пользователя, например `petrov@email.com`.
3. Выполните логин и скопируйте `access_token`.
4. Отправьте боту сообщение `/token <ваш_jwt>`.
5. После подтверждения отправьте обычный текстовый вопрос.
6. Проверьте RabbitMQ UI: задача должна попасть в очередь Celery.
7. Получите ответ от бота в Telegram.

## Тесты

### Auth Service

```powershell
cd auth_service
uv run pytest
```

Покрывается:

- хеширование и проверка пароля
- генерация и декодирование JWT
- сценарий `register -> login -> me`
- негативные кейсы `409`, `401`

### Bot Service

```powershell
cd bot_service
uv run pytest
```

Покрывается:

- проверка JWT
- сохранение токена через `/token`
- отказ при отсутствии токена
- публикация задачи в Celery при валидном токене
- OpenRouter клиент через `respx`

## Что еще понадобится

Для полного живого запуска нужны только два секрета:

- Telegram bot token
- OpenRouter API key

Без них проект, структура, тесты и Docker-конфигурация уже готовы, но реальный обмен сообщениями с Telegram и LLM не выполнится.


Тестирование:

1. Аутентификация
![alt text](/Скрины/authentication.png)

2. Выпуск access_token
![alt text](/Скрины/get_access_token.png)

3. Авторизация 
![alt text](/Скрины/authorization.png)

4. auth_me
![alt text](/Скрины/auth_me.png)

5. Локальные тесты auth
![alt text](/Скрины/Локальные%20тесты%20auth.png)

6. Локальные тесты bot
![alt text](/Скрины/Локальные%20тесты%20bot.png)

7. Взаимодействие с ботом
![alt text](/Скрины/Взаимодействие%20с%20ботом.png)

8. RabbitMQ очередь
![alt text](/Скрины/Очередь.png)

9. RabbitMQ Консьюмер
![alt text](/Скрины/Консьюмер.png)

9. Celery в терминале
![alt text](/Скрины/Celery в терминале.png)
