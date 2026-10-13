"""Configurações lidas das variáveis de ambiente (ou do .env na raiz do repositório)."""

from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

RAIZ_REPOSITORIO = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=RAIZ_REPOSITORIO / ".env",
        env_file_encoding="utf-8",
        extra="ignore",  # o .env também tem variáveis do Postgres/Docker
    )

    # SecretStr esconde o valor em prints e logs: aparece como '**********'
    riot_api_key: SecretStr
    database_url: str
    cache_ttl_minutes: int = 10
    refresh_cooldown_seconds: int = 120
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origem.strip() for origem in self.cors_origins.split(",") if origem.strip()]


@lru_cache
def get_settings() -> Settings:
    """Lê as configurações uma única vez e reaproveita nas próximas chamadas."""
    return Settings()
