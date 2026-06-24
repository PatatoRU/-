# MVP Ready Report — «Куда Сегодня»

Дата: 2026-06-24.

## Что исправлено

- Добавлен `ADMIN_IDS` и Telegram `/admin` для владельцев.
- Добавлена заявка `/add_place` для пользователей/бизнеса с сохранением на модерацию.
- Усилены Telegram Stars payments: `pending` → `paid`, payment payload с id, pre-checkout validation, idempotency.
- Админка платежей показывает статус.
- Добавлены audit/security/ready документы и README.
- Добавлены тесты payload payments и production admin config.

## Готовые функции MVP

- Регистрация пользователя через `/start`.
- Выбор города из пяти стартовых городов.
- Поиск еды, развлечений, отдыха и nearby через геолокацию.
- Карточки мест с картой, маршрутом, контактами, рейтингом, отзывами и избранным.
- События и сценарии: свидание, семья, дети, бесплатно, сегодня вечером.
- LLM-рекомендации с fallback.
- Feedback и заявки на добавление места.
- Реклама через Telegram Stars.
- Web admin для просмотра данных.
- Telegram admin статистика по `ADMIN_IDS`.

## Как запустить локально

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
alembic upgrade head
python -m app.main
```

## Как запустить на сервере через Docker

```bash
cp .env.example .env
# заполнить BOT_TOKEN, ADMIN_IDS, ADMIN_PASSWORD, POSTGRES_PASSWORD, DATABASE_URL, REDIS_URL
docker compose up --build -d
```

## Как проверить

```bash
pytest -q
python scripts/security_check.py --include-local
curl http://127.0.0.1:8000/health
docker compose logs -f bot
docker compose logs -f web
```

## Обязательные переменные окружения

- `BOT_TOKEN`
- `ADMIN_IDS`
- `DATABASE_URL`
- `REDIS_URL`
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `POSTGRES_PASSWORD`
- `OPENAI_API_KEY` или `OPENROUTER_API_KEY` — опционально, потому что есть fallback

## Оставшиеся риски

- Нужна ручная Telegram e2e проверка платежей Stars.
- Нужна ротация ранее раскрытых ключей.
- Нужен production backup PostgreSQL.
- Внешние источники событий/мест остаются future scope.

## Можно ли запускать MVP сейчас?

YES — при условии, что на VPS заполнен `.env`, применены миграции, доступны Telegram API/PostgreSQL/Redis и вручную проверены Telegram Stars payments.
