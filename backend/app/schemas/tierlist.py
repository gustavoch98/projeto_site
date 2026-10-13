from pydantic import BaseModel


class CampeaoTierList(BaseModel):
    champion_id: int
    champion_name: str
    rota: str  # TOP, JUNGLE, MIDDLE, BOTTOM, UTILITY
    tier: str | None  # S, A, B, C, D; None quando os dados ainda não sustentam tiers
    jogos: int
    vitorias: int
    winrate: float  # bruto, 0 a 1
    winrate_ajustado: float | None  # com encolhimento para 50% (ver services/tierlist.py)
    pickrate: float  # fração das partidas em que foi escolhido nessa rota
    banrate: float  # fração das partidas em que foi banido (qualquer rota)


class TierList(BaseModel):
    patch: str | None  # ex.: "16.20"; None se não houver partidas
    partidas: int  # partidas analisadas no patch
    minimo_jogos: int
    # Força do prior estimada dos dados (em partidas). None = dados ainda insuficientes
    # para distinguir os campeões: a lista vem sem tiers.
    prior_jogos: int | None
    campeoes: list[CampeaoTierList]  # com tiers: do melhor ao pior; sem: do mais ao menos jogado
