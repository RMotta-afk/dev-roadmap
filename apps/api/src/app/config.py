from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
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

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_allow.split(",")]


settings = Settings()
