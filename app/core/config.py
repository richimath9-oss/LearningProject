from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    app_name: str = "BRD Generator"
    environment: str = Field(default="development")
    data_dir: Path = Field(default=Path("data"), env="DATA_DIR")
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    model_name: str = Field(default="gpt-5")
    allow_mock_ai: bool = Field(default=True)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    (settings.data_dir / "uploads").mkdir(parents=True, exist_ok=True)
    (settings.data_dir / "storage").mkdir(parents=True, exist_ok=True)
    return settings
