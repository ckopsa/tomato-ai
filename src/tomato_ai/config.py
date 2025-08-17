
from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DB_HOST: str = "localhost"
    DB_USER: str = "user"
    DB_PASS: str = "password"
    DB_NAME: str = "tomato-ai"
    TEST_DATABASE_URL: str | None = None

    TELEGRAM_BOT_TOKEN: str | None = None
    TELEGRAM_CHAT_ID: str | None = None

    OLLAMA_API_KEY: str | None = None

    @property
    def database_url(self) -> PostgresDsn:
        if self.TEST_DATABASE_URL:
            return self.TEST_DATABASE_URL
        return f"postgresql://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}/{self.DB_NAME}"


settings = Settings()
