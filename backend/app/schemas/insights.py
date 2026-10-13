from datetime import datetime

from pydantic import BaseModel


class FaixaDesempenho(BaseModel):
    """Desempenho numa faixa (um período do dia, um dia da semana...)."""

    chave: str  # identificador estável, ex.: "tarde", "sab"
    rotulo: str  # texto para exibir, ex.: "Tarde (12h–17h)"
    jogos: int
    vitorias: int
    winrate: float | None  # 0 a 1; None quando não há partidas
    ic_baixo: float | None  # intervalo de confiança de 95% (Wilson)
    ic_alto: float | None


class InsightsHorario(BaseModel):
    partidas_analisadas: int
    winrate_geral: float | None
    primeira_partida: datetime | None
    ultima_partida: datetime | None
    por_periodo: list[FaixaDesempenho]
    por_dia_semana: list[FaixaDesempenho]
    # True enquanto o histórico longo ainda está sendo buscado na Riot
    coletando_historico: bool
