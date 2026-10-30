"""ClauseTrace backend configuration settings."""

from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment or .env file."""

    META_API_KEY: str = ""
    META_API_BASE_URL: str = "https://api.llama.com/compat/v1/"
    META_PRIMARY_MODEL: str = "Llama-3.3-70B-Instruct"
    META_FAST_MODEL: str = "Llama-3.1-8B-Instruct"
    DATABASE_PATH: str = "./data/clausetrace.db"
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
