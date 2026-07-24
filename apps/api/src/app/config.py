from pathlib import Path

from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)


def _env_files() -> tuple[str, ...]:
    # config.py lives at apps/api/src/app/config.py
    #   parents[2] -> apps/api
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

    # Qdrant
    qdrant_url: str = Field(default="http://localhost:6333")
    qdrant_api_key: str | None = Field(default=None)

    # Neon Postgres
    database_url: str = Field(default="postgresql+asyncpg://localhost/cv_analyzer")

    # LLM / Embeddings
    llm_api_key: str = Field(default="")
    llm_model: str = Field(default="gpt-4o-mini")
    embedding_model: str = Field(default="text-embedding-3-small")

    # Auth
    authjwt_secret: str = Field(default="change-me-in-production")

    # CORS
    cors_allow: str = Field(default="http://localhost:8501")

    # Roadmap data
    base_roadmap_path: Path = Field(default=Path("docs/archives"))

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # Project .env wins over ambient OS env so a polluted shell cannot
        # silently override AUTHJWT_SECRET / DATABASE_URL for local runs.
        return (
            init_settings,
            dotenv_settings,
            env_settings,
            file_secret_settings,
        )

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_allow.split(",") if o.strip()]


settings = Settings()
