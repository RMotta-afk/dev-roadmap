from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_ROOT_CANDIDATES = [
    Path.cwd() / ".env",
    Path(__file__).resolve().parents[3] / ".env",  # apps/ui/.env
    Path(__file__).resolve().parents[4] / ".env",  # repo root .env
]


def _env_files() -> tuple[str, ...]:
    found = [str(p) for p in _ROOT_CANDIDATES if p.is_file()]
    return tuple(found) if found else (".env",)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_env_files(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_base_url: str = Field(default="http://localhost:8000")
    database_url: str = Field(
        default="postgresql://cv_analyzer:localdev@localhost:5432/cv_analyzer"
    )
    authjwt_secret: str = Field(default="change-me-in-production")
    jwt_expiry_minutes: int = Field(default=15)

    def sync_database_url(self) -> str:
        url = self.database_url
        return url.replace("postgresql+asyncpg://", "postgresql://", 1)


settings = Settings()
