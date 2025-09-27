from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Dict, Literal


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="REGSCRAPER_", env_file=".env", extra="ignore"
    )

    # HTTP
    user_agent: str = Field(
        default="RegScraper/2.0 (+https://your-org.example/contact)"
    )
    default_delay: float = Field(default=2.0)
    default_concurrency: int = Field(default=2)
    global_max_concurrency: int = Field(default=12)

    # Storage
    output_dir: str = Field(default="output")
    raw_dir: str = Field(default="output/raw")
    json_dir: str = Field(default="output/structured")
    db_path: str = Field(default="output/regscraper.db")

    # LLM
    openai_api_key: str | None = None
    llm_model: str = Field(default="gpt-4o")

    # Per-site overrides
    site_overrides: Dict[str, Dict[str, float | int | Literal["static", "dynamic"]]] = {
        "sec.gov": {"delay": 5.0, "concurrency": 1, "type": "static"},
        "ec.europa.eu": {"delay": 3.0, "concurrency": 2, "type": "static"},
        "fda.gov": {"delay": 2.5, "concurrency": 2, "type": "static"},
    }


settings = Settings()
