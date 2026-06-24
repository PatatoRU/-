# Security Checklist — «Куда Сегодня» MVP

## Secrets

- [x] `.env` находится в `.gitignore`.
- [x] `.env.example` содержит только placeholder values.
- [x] `scripts/security_check.py` проверяет tracked files и опционально local secret files.
- [ ] Перед production перевыпустить ранее раскрытые Telegram/OpenAI ключи.

## Admin Access

- [x] Web admin защищён Basic Auth.
- [x] Web admin mutating actions защищены CSRF token.
- [x] Telegram admin command `/admin` доступен только пользователям из `ADMIN_IDS`.
- [x] Production validation требует `ADMIN_IDS`.

## Telegram Payments

- [x] Invoice создаётся с currency `XTR`.
- [x] До invoice создаётся payment со статусом `pending`.
- [x] `pre_checkout_query` проверяет payload, тариф, сумму и pending status.
- [x] Услуга активируется только после `successful_payment`.
- [x] Повторная обработка платежа блокируется через status `paid` и charge id.
- [x] Платежи видны в admin UI со статусом.

## User Input

- [x] Callback prefixes валидируются.
- [x] Город выбирается только из whitelist пяти стартовых городов.
- [x] HTML output экранируется через `_safe`/`_escape`.
- [x] Feedback и заявки ограничены по длине перед записью в Redis.

## Rate Limit / Anti-Spam

- [x] Поисковые запросы ограничены через Redis `RateLimitService`.
- [x] LLM имеет timeout и fallback chain.
- [ ] Добавить отдельный лимит на отзывы, feedback и заявки после первых пользователей.

## SQL / Storage

- [x] SQLAlchemy ORM/select без ручной SQL-интерполяции пользовательских строк.
- [x] Alembic создаёт индексы и уникальные ограничения для платежных payload/charge.

## Webhook / Polling

- [x] Polling допустим для MVP.
- [x] Webhook endpoint проверяет Telegram secret token, если он задан.
- [x] Production validation требует webhook secret при webhook mode.
