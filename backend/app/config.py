import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./dev.db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key")
    AUTO_APPEND: bool = True
    GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY", "AIzaSyBZ6dBEABvlaHSfPGdUZJqLoRIisGI5l7A")
    # Basic auth for tunnel protection (username/password)
    BASIC_AUTH_USERNAME: str = os.getenv("BASIC_AUTH_USERNAME", "tunnel")
    BASIC_AUTH_PASSWORD: str = os.getenv("BASIC_AUTH_PASSWORD", "tunnel")


settings = Settings()
