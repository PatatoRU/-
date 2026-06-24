from functools import lru_cache
from pydantic import AnyUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    bot_token: str = Field(default="", alias="BOT_TOKEN")
    database_url: str = Field(default="sqlite+aiosqlite:///./kuda.db", alias="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    app_env: str = Field(default="development", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    web_host: str = Field(default="0.0.0.0", alias="WEB_HOST")
    web_port: int = Field(default=8000, alias="WEB_PORT")
    bot_mode: str = Field(default="polling", alias="BOT_MODE")
    telegram_webhook_url: str | None = Field(default=None, alias="TELEGRAM_WEBHOOK_URL")
    telegram_webhook_secret: str | None = Field(default=None, alias="TELEGRAM_WEBHOOK_SECRET")
    admin_username: str = Field(default="admin", alias="ADMIN_USERNAME")
    admin_password: str = Field(default="change_me", alias="ADMIN_PASSWORD")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-5.5", alias="OPENAI_MODEL")
    osm_nominatim_url: AnyUrl = Field(default="https://nominatim.openstreetmap.org/search", alias="OSM_NOMINATIM_URL")
    osm_user_agent: str = Field(default="KudaSegodnyaBot/1.0", alias="OSM_USER_AGENT")
    osm_timeout_seconds: float = Field(default=7.0, alias="OSM_TIMEOUT_SECONDS")
    osm_result_limit: int = Field(default=8, alias="OSM_RESULT_LIMIT")

    @field_validator("bot_token")
    @classmethod
    def validate_bot_token(cls, value: str) -> str:
        if not value:
            return value
        if ":" not in value or len(value) < 20:
            raise ValueError("BOT_TOKEN has invalid format")
        return value

    def validate_production_safety(self) -> None:
        if self.app_env.lower() == "production" and not self.bot_token:
            raise ValueError("BOT_TOKEN must be configured for production")
        if self.app_env.lower() == "production" and "sqlite" in self.database_url:
            raise ValueError("PostgreSQL DATABASE_URL is required for production")
        if self.app_env.lower() == "production" and self.admin_password == "change_me":
            raise ValueError("ADMIN_PASSWORD must be changed for production")
        if self.app_env.lower() == "production" and self.bot_mode == "webhook" and not self.telegram_webhook_secret:
            raise ValueError("TELEGRAM_WEBHOOK_SECRET must be configured for production webhook mode")

@lru_cache
def get_settings() -> Settings:
    return Settings()
