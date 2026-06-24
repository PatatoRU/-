# Куда Сегодня

Telegram-first MVP бота для поиска мест и событий в пяти городах России: Москва, Санкт-Петербург, Новосибирск, Екатеринбург, Казань.

## Возможности

- `/start`, `/help`, `/profile`, `/settings`
- Поиск: `/find_food`, `/find_fun`, `/find_relax`, nearby по геолокации
- События: `/events`, свидание, семья, дети, бесплатно, сегодня вечером
- Карточки мест: описание, контакты, рейтинг, отзывы, карта OSM, маршрут OSM
- Избранное и история
- Feedback и заявки `/add_place`
- Реклама через Telegram Stars
- LLM-рекомендации: OpenAI → OpenRouter → Ollama → fallback
- Web admin и Telegram `/admin` для `ADMIN_IDS`

## Установка зависимостей

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

## Настройка окружения

```bash
cp .env.example .env
```

Минимально заполнить:

```env
BOT_TOKEN=...
ADMIN_IDS=123456789
ADMIN_PASSWORD=strong-password
DATABASE_URL=postgresql+asyncpg://kuda:strong-password@postgres:5432/kuda
REDIS_URL=redis://redis:6379/0
```

## Локальный запуск

```bash
alembic upgrade head
python -m app.main
```

## Docker/VPS запуск

```bash
docker compose up --build -d
docker compose logs -f bot
docker compose logs -f web
```

## Проверка

```bash
pytest -q
python scripts/security_check.py --include-local
curl http://127.0.0.1:8000/health
```

## Логи

```bash
docker compose logs -f bot
docker compose logs -f web
docker compose logs -f postgres
docker compose logs -f redis
```

## Документы

- `docs/AUDIT_REPORT.md`
- `docs/SECURITY_CHECKLIST.md`
- `docs/MVP_READY_REPORT.md`
- `PROJECT_STATUS.md`
