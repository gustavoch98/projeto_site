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


class EstatisticasCampeao(BaseModel):
    """Desempenho do jogador com um campeão (ou no geral, quando champion_id é None)."""

    champion_id: int | None
    champion_name: str | None
    jogos: int
    vitorias: int
    winrate: float
    ic_baixo: float  # intervalo de confiança de 95% (Wilson) do winrate
    ic_alto: float
    kda: float  # (abates + assistências) / mortes, somando todas as partidas
    abates: float  # médias por partida
    mortes: float
    assistencias: float
    cs_por_minuto: float
    dano_por_minuto: float
    visao_por_minuto: float
    ouro_por_minuto: float
    participacao_abates: float | None  # 0 a 1
    rota_principal: str | None  # rota mais frequente (TOP, JUNGLE, MIDDLE, BOTTOM, UTILITY)
    ultima_partida: datetime


class CampeoesJogador(BaseModel):
    partidas_analisadas: int
    minimo_partidas: int  # abaixo disso, o campeão aparece como "poucos dados"
    geral: EstatisticasCampeao | None  # todas as partidas juntas, para comparação
    campeoes: list[EstatisticasCampeao]  # do mais jogado para o menos jogado
    coletando_historico: bool
