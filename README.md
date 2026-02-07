# Deliverybot_pro

Монорепозиторий платформы автоматизации заказов в Telegram.

## Состав
- `apps/` — фронтенд (landing, admin, client, staff)
- `services/` — микросервисы (NestJS)
- `packages/` — общие библиотеки
- `telegram-bot/` — бот-магазин и админ-бот
- `docker-compose.yml` — локальная инфраструктура

## Быстрый старт (локально)
```bash
pnpm install
pnpm -C services/auth-service build
```

## Документы
- `ARCHITECTURE.md` — решения по архитектуре.
- `TECHNICAL_SPEC.md` — полное ТЗ.
