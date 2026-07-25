from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)


def _repo_root() -> Path:
    """apps/api/src/app/config.py → parents[4] is monorepo root when layout holds."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "docs" / "archives").is_dir() and (parent / "apps").is_dir():
            return parent
    # Fallback: config.py → app → src → api → apps → root
    return here.parents[4]


def _env_files() -> tuple[str, ...]:
    """Discover .env files by walking up from this file and cwd."""
    this_file = Path(__file__).resolve()
    candidates: list[Path] = []
    # Walk parents so install layout / depth cannot miss repo-root .env
    for parent in this_file.parents:
        candidates.append(parent / ".env")
        if parent.parent == parent:
            break
    candidates.append((Path.cwd() / ".env").resolve())

    found: list[str] = []
    seen: set[str] = set()
    for p in candidates:
        try:
            key = str(p.resolve())
        except OSError:
            key = str(p)
        if p.is_file() and key not in seen:
            seen.add(key)
            found.append(key)
    return tuple(found) if found else (".env",)


def _preload_dotenv() -> None:
    """Push .env into os.environ before Settings binds (override ambient OS)."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    for path in _env_files():
        load_dotenv(path, override=True)


_preload_dotenv()


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

    # Auth (shared HMAC secret with UI — env AUTHJWT_SECRET)
    authjwt_secret: str = Field(default="local-dev-secret-change-in-production")

    # CORS
    cors_allow: str = Field(default="http://localhost:8501")

    # Roadmap data (relative paths resolve against monorepo root, not cwd)
    base_roadmap_path: Path = Field(default=Path("docs/archives"))

    @field_validator("base_roadmap_path", mode="after")
    @classmethod
    def _resolve_roadmap_path(cls, value: Path) -> Path:
        path = Path(value)
        if path.is_absolute():
            return path.resolve()
        root_candidate = (_repo_root() / path).resolve()
        if root_candidate.is_dir():
            return root_candidate
        cwd_candidate = (Path.cwd() / path).resolve()
        if cwd_candidate.is_dir():
            return cwd_candidate
        return root_candidate

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # env (preloaded .env + OS) then dotenv file source; init overrides all
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_allow.split(",") if o.strip()]


settings = Settings()
