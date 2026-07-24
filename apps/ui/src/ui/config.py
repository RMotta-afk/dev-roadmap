from pathlib import Path

from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)


def _env_files() -> tuple[str, ...]:
    # config.py lives at apps/ui/src/ui/config.py
    #   parents[2] -> apps/ui
    #   parents[4] -> repo root
    this_file = Path(__file__).resolve()
    candidates = [
        this_file.parents[4] / ".env",
        this_file.parents[2] / ".env",
        (Path.cwd() / ".env").resolve(),
    ]
    found: list[str] = []
    seen: set[str] = set()
    for p in candidates:
        key = str(p)
        if p.is_file() and key not in seen:
            seen.add(key)
            found.append(key)
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

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            dotenv_settings,
            env_settings,
            file_secret_settings,
        )

    def sync_database_url(self) -> str:
        url = self.database_url
        return url.replace("postgresql+asyncpg://", "postgresql://", 1)


settings = Settings()
