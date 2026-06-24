# Audit Report — «Куда Сегодня» Telegram MVP

Дата: 2026-06-24.

## Scope

Проверены структура проекта, зависимости, env/config, запуск, Telegram handlers/callbacks, PostgreSQL/SQLite слой, Alembic, Redis/cache/sessions, LLM fallback, админские функции, Telegram Stars payments, webhook/polling безопасность, Docker/deploy и тесты.

## Что работает

- Telegram-first бот на aiogram 3 с polling/webhook entrypoint.
- Команды `/start`, `/help`, `/profile`, `/find_food`, `/find_fun`, `/find_relax`, `/events`, `/interests`, `/feedback`, `/add_place`, `/favorites`, `/history`, `/settings`, `/recommend`, `/ads`, `/admin`.
- Главное меню, выбор города, карточки мест, OSM карта/маршрут, отзывы, рейтинги, избранное, геолокация с подтверждением.
- События и сценарии: свидание, семья, дети, бесплатно, сегодня вечером.
- PostgreSQL/SQLite через SQLAlchemy async, Alembic initial migration.
- Redis cache/session/popular searches/rate-limit/analytics/feedback/submissions.
- OpenAI → OpenRouter → Ollama → deterministic fallback для LLM-рекомендаций.
- Telegram Stars invoice, `pre_checkout_query`, `successful_payment`, запись платежа, paid-only активация рекламы, idempotency по payment id / charge id.
- Web admin: места, отзывы, реклама, платежи, события, аналитика, feedback.
- Security scanner для tracked/local секретов.
- Dockerfile и Docker Compose для VPS запуска.

## Что было сломано или рискованно

- Платёжная запись создавалась только после `successful_payment`, не было `pending` статуса до invoice.
- Payload платежа не содержал payment id, поэтому защита от повторной обработки была слабой.
- Платёжная услуга могла создаваться повторно при повторном событии `successful_payment`.
- Не было `ADMIN_IDS`, поэтому Telegram-админские команды нельзя было безопасно ограничить владельцами.
- Не было пользовательской заявки на добавление места/бизнеса.
- Документы аудита, security checklist, MVP readiness и README отсутствовали.

## Что отсутствует

- Реальный e2e запуск с Telegram API в этом контейнере не выполнен.
- Docker build в этом контейнере невозможен, потому что Docker не установлен.
- Живые внешние парсеры VK/Telegram/Yandex/2GIS не включены в MVP: для них нужны официальные API/ToS/rate limits.
- Нет полноценной модерации заявок в Telegram; заявки пока складываются в Redis для ручной обработки.

## Критические риски

- Ранее переданные пользователем Telegram/OpenAI ключи считаются раскрытыми и должны быть перевыпущены перед production.
- В production обязательно задать `BOT_TOKEN`, `ADMIN_IDS`, `ADMIN_PASSWORD`, `POSTGRES_PASSWORD`, Redis/Postgres URL.
- Telegram Stars нужно проверить на живом боте, потому что тестовое окружение Telegram payments недоступно в контейнере.
- Nominatim/OSM имеет rate limits; для роста нагрузки нужен платный/свой provider.

## Что мешает запуску MVP

P0-блокеров в коде после текущего pass не осталось. Для фактического запуска нужны только внешние условия:

- VPS с Docker или Python 3.11+;
- заполненный `.env`;
- доступ к Telegram API;
- PostgreSQL/Redis;
- `alembic upgrade head`;
- ручная e2e проверка платежей и callbacks.

## Приоритеты

### P0 — до запуска

- Перевыпустить раскрытые токены и заполнить `.env`.
- Прогнать миграции на PostgreSQL.
- Проверить Telegram polling запуск и команды.
- Проверить Stars invoice/pre-checkout/successful payment на реальном боте.
- Убедиться, что `ADMIN_IDS` содержит Telegram ID владельцев.

### P1 — первые пользователи

- Добавить простую Telegram-модерацию заявок мест и feedback.
- Настроить backup PostgreSQL и log rotation.
- Подключить OpenRouter key как резервный LLM provider.
- Настроить VPS firewall и reverse proxy, если используется webhook/admin web.

### P2 — после MVP

- Официальные внешние интеграции событий/мест.
- Расширенная аналитика и Prometheus metrics.
- Антиспам для отзывов/feedback.
- Персонализация рекомендаций по истории и интересам.
