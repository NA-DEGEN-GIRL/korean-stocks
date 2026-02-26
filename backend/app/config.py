from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    DART_API_KEY: str = ""
    DATABASE_URL: str = "sqlite:///./data/stocks.db"
    CORS_ORIGINS: str = "http://localhost:5173"
    LOG_LEVEL: str = "INFO"
    SCRAPE_DELAY_SECONDS: float = 1.5
    PYKRX_DELAY_SECONDS: float = 1.0

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS_ORIGINS string into a list, splitting by comma."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


settings = Settings()
