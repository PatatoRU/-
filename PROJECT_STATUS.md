# PROJECT STATUS — «Куда Сегодня»

Дата аудита: 2026-06-24.

## Current State

Telegram-first MVP доведён до состояния запуска на VPS с минимальной инфраструктурой: bot polling/webhook, PostgreSQL, Redis, Alembic, Docker Compose, FastAPI health/admin endpoints, OpenStreetMap provider, curated fallback база пяти городов, OpenAI/OpenRouter/Ollama LLM fallback, отзывы, рейтинги, избранное, история, реклама Telegram Stars и базовая аналитика.

Стартовые города:

- Москва
- Санкт-Петербург
- Новосибирск
- Екатеринбург
- Казань

## Full Audit

### Что работает

- Telegram handlers для `/start`, `/help`, `/profile`, `/find_food`, `/find_fun`, `/find_relax`, `/favorites`, `/history`, `/settings`, `/recommend`, `/events`, `/interests`, `/feedback`, `/ads`.
- Reply/inline keyboards для категорий, города, интересов, карточек мест, событий, отзывов, рейтингов, рекламы, геолокации.
- Карточки мест: описание, адрес, телефон, сайт, часы работы, рейтинг, карта OSM, маршрут OSM, отзывы, избранное, реклама.
- Геолокация с подтверждением перед nearby-поиском.
- PostgreSQL модели и Alembic initial migration.
- Redis cache/sessions/popular searches/rate limit/analytics counters.
- OSM/Nominatim provider и curated fallback provider.
- FastAPI `/health`, webhook endpoint и админ-панель с Basic Auth и CSRF для действий.
- Docker Compose для bot/web/postgres/redis.
- Security scanner для секретов в tracked и local files.

### Что было реализовано частично и исправлено

- LLM раньше работал только через OpenAI и простой fallback. Теперь цепочка: OpenAI → OpenRouter → Ollama → deterministic fallback.
- События раньше были смешаны с категорией развлечений. Теперь есть отдельный `EventService` для концертов, фестивалей, выставок, кино, городских сценариев, детей, семьи, свиданий, бесплатного и вечернего досуга.
- Интересы пользователя раньше отсутствовали. Теперь есть выбор интересов через Telegram inline-кнопки с хранением в Redis session.
- Обратная связь раньше отсутствовала. Теперь есть `/feedback` и кнопка `💬 Обратная связь`, сообщения сохраняются в Redis list.
- Аналитика раньше была только косвенно через историю и popular searches. Теперь есть `AnalyticsService` для счётчиков запросов, событий, CTR мест/событий и feedback.

### Что отсутствует или требует внешней настройки

- Живые VK/Telegram/Yandex/2GIS парсеры не включены в текущий Telegram-first MVP, потому что нужны официальные API-ключи, согласие с ToS, rate limits и отдельная очередь задач. Архитектура provider/service позволяет добавить их следующим этапом.
- Production запуск требует реальные `BOT_TOKEN`, `OPENAI_API_KEY` или `OPENROUTER_API_KEY`, сильные `POSTGRES_PASSWORD`, `ADMIN_PASSWORD`, `TELEGRAM_WEBHOOK_SECRET`.
- Полный e2e Telegram test возможен только с доступом к Telegram API.
- Docker build/load test должны выполняться на хосте с Docker и поднятым сервисом.

### Риски

- Nominatim/OSM имеет публичные rate limits; для production нужен кеш Redis, свой User-Agent и fallback — всё это есть, но при росте нагрузки потребуется свой provider/платный геосервис.
- Telegram Stars payments требуют проверки в реальном bot account и корректной поддержки XTR в production Telegram окружении.
- Basic Auth админка достаточна для MVP, но до коммерческого запуска лучше добавить полноценные роли, audit log и reverse proxy TLS.
- Секреты уже передавались в чат; их нужно перевыпустить перед production.

## Roadmap

### Critical

- Заполнить production `.env`: Telegram token, PostgreSQL/Redis URLs, admin password, webhook secret, LLM key.
- Запустить `alembic upgrade head` на PostgreSQL.
- Прогнать `pytest`, `scripts/security_check.py --include-local`, Docker build и smoke launch на VPS.
- Проверить все Telegram callbacks руками: города, интересы, карточки, отзывы, рейтинг, избранное, реклама, payments, геолокация, events.

### High

- Настроить webhook behind Nginx + HTTPS или оставить polling для минимального VPS.
- Добавить systemd/docker restart policy, log rotation и резервное копирование Postgres.
- Подключить OpenRouter как резервный LLM ключ или локальный Ollama для дешёвого fallback.
- Проверить Telegram Stars на тестовой покупке.

### Medium

- Добавить интеграционные тесты с testcontainers PostgreSQL/Redis.
- Добавить Prometheus-compatible metrics endpoint.
- Расширить админку: детальная модерация feedback, аналитики, отзывов, событий и рекламных кампаний.
- Добавить фоновые jobs для обновления событий.

### Future

- Официальные интеграции VK, Telegram каналов, Yandex, 2GIS, Timepad, KudaGo, городских афиш.
- Moderation/anti-spam для отзывов и feedback.
- Персонализация рекомендаций на основе истории и интересов.
- Web/mobile interface после стабилизации Telegram MVP.

## Security Audit

- Секреты должны храниться только в `.env` или secret manager. `scripts/security_check.py --include-local` используется перед деплоем.
- SQL Injection риск снижен: запросы через SQLAlchemy ORM/select, пользовательские значения не интерполируются в SQL вручную.
- Callback input валидируется по префиксам и lookup в БД/словарях городов.
- Admin actions защищены Basic Auth и CSRF token.
- Webhook проверяет `X-Telegram-Bot-Api-Secret-Token`, если secret задан.
- Rate limit есть для поисковых запросов через Redis.
- LLM защищён таймаутом, max tokens и fallback chain; падение provider не валит Telegram flow.

## Monitoring

- `/health` проверяет состояние web process.
- Docker healthcheck настроен на web health endpoint.
- Структурированные логи доступны через application/error/telegram loggers.
- `scripts/load_check.py` выполняет быстрый HTTP load smoke для `/health`.

## Что исправлено в этом recovery pass

- Добавлен отдельный events module.
- Добавлены интересы пользователя.
- Добавлена обратная связь.
- Добавлена Redis-аналитика.
- Расширена клавиатура Telegram для всех продуктовых сценариев текущего этапа.
- Расширен LLM fallback до OpenAI/OpenRouter/Ollama/simple logic.
- Добавлена документация статуса, рисков и roadmap.
- Добавлены админ-разделы для событий, аналитики и feedback.

## Что осталось доделать

- Реальный deploy на VPS и e2e проверка Telegram API.
- Перевыпустить ранее раскрытые Telegram/OpenAI ключи перед production.
- Подключить официальные источники событий и мест через легальные API.
- Настроить резервные копии PostgreSQL и мониторинг процесса на сервере.
