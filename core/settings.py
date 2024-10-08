from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", env_file_encoding="utf-8"
    )

    DATABASE_URI: str
    ENVIRONMENT: str
    JWT_SECRET: str


settings = Settings()  # type: ignore # pyright: ignore
