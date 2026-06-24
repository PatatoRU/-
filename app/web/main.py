from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from redis.asyncio import Redis
from sqlalchemy import text
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.web.admin import router as admin_router
from app.web.telegram import router as telegram_router
app = FastAPI(title="Куда Сегодня")
app.include_router(admin_router)
app.include_router(telegram_router)


@app.middleware("http")
async def security_headers(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "geolocation=()"
    return response
@app.get("/health")
async def health():
    db_ok=False; redis_ok=False
    async with SessionLocal() as s:
        await s.execute(text("SELECT 1")); db_ok=True
    r=Redis.from_url(get_settings().redis_url, decode_responses=True); redis_ok=bool(await r.ping()); await r.aclose()
    return {"status":"ok", "db":db_ok, "redis":redis_ok}
