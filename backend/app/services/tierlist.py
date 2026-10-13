"""Tier list de campeões calculada a partir das partidas salvas no nosso banco.

A Riot não fornece tier list nem estatísticas globais de campeões: sites como OP.GG montam a
deles agregando milhões de partidas. Aqui fazemos o mesmo com a base que temos, dizendo sempre
quantas partidas sustentam os números.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.tierlist import CampeaoTierList, TierList

FILA_SOLO_ID = 420
MINIMO_JOGOS = 15  # campeão/rota com menos partidas que isso fica fora da lista

# Encolhimento bayesiano: o winrate de cada campeão é "puxado" para 50% como se tivesse
# k partidas extras com 50% de vitória. Com muitas partidas quase não muda; com poucas, muda muito.
# k NÃO é chutado: é estimado dos próprios dados (empirical Bayes, ver estimar_prior).
PRIOR_WINRATE = 0.5
# Se o prior estimado passar disso, os dados ainda não distinguem os campeões: sem tiers.
PRIOR_MAXIMO = 1000

# Limites do winrate AJUSTADO para cada tier (do melhor para o pior)
LIMITES_TIER = [("S", 0.53), ("A", 0.515), ("B", 0.50), ("C", 0.485)]  # abaixo disso: D

# Patch = os dois primeiros números da versão ("16.20.824.8524" -> "16.20"), da partida mais recente
CONSULTA_PATCH = """
SELECT split_part(game_version, '.', 1) || '.' || split_part(game_version, '.', 2) AS patch
FROM matches
WHERE queue_id = :fila AND NOT remake
ORDER BY game_start DESC
LIMIT 1
"""

CONSULTA_TOTAL = """
SELECT count(*) FROM matches WHERE queue_id = :fila AND NOT remake AND game_version LIKE :prefixo
"""

CONSULTA_TIER_LIST = """
WITH partidas AS (
    SELECT match_id, raw
    FROM matches
    WHERE queue_id = :fila AND NOT remake AND game_version LIKE :prefixo
),
escolhas AS (
    SELECT mp.champion_id,
           max(mp.champion_name) AS champion_name,
           mp.team_position AS rota,
           count(*) AS jogos,
           sum(mp.win::int) AS vitorias
    FROM match_participants mp
    JOIN partidas USING (match_id)
    WHERE mp.team_position <> ''
    GROUP BY mp.champion_id, mp.team_position
),
-- Os banimentos só existem no JSON bruto: info.teams[].bans[].championId (-1 = sem banimento).
-- jsonb_array_elements "abre" cada lista em linhas, como um UNNEST.
banimentos AS (
    SELECT (ban ->> 'championId')::int AS champion_id,
           count(DISTINCT partidas.match_id) AS partidas_banido
    FROM partidas,
         jsonb_array_elements(partidas.raw -> 'info' -> 'teams') AS time,
         jsonb_array_elements(time -> 'bans') AS ban
    WHERE (ban ->> 'championId')::int > 0
    GROUP BY 1
)
SELECT escolhas.*, coalesce(banimentos.partidas_banido, 0) AS partidas_banido
FROM escolhas
LEFT JOIN banimentos USING (champion_id)
WHERE escolhas.jogos >= :minimo
"""


def qui2_critico(graus: int, z: float = 1.645) -> float:
    """Valor crítico da qui-quadrado a 5% (unilateral), pela aproximação de Wilson-Hilferty.

    Evita depender do SciPy só para isso; o erro é desprezível a partir de poucos graus.
    """
    return graus * (1 - 2 / (9 * graus) + z * (2 / (9 * graus)) ** 0.5) ** 3


def estimar_prior(linhas: list[tuple[int, int]]) -> float | None:
    """Força do prior (em partidas) pelo método dos momentos.

    A variância observada dos winrates = diferença REAL entre campeões (tau²) + ruído de
    amostragem (média de p(1-p)/n). Logo tau² = observada - ruído, e o prior ideal é
    k = p(1-p)/tau². Devolve None quando tau² <= 0 (toda a variação é explicável por ruído)
    ou quando k passa de PRIOR_MAXIMO: nos dois casos não dá para montar tiers confiáveis.
    """
    if len(linhas) < 2:
        return None
    winrates = [v / n for v, n in linhas]
    media = sum(winrates) / len(winrates)

    # 1) Os campeões diferem DE VERDADE? Teste qui-quadrado de homogeneidade: sem diferença
    #    real, a soma abaixo segue uma qui-quadrado com K-1 graus de liberdade. Sem esse teste,
    #    o ruído às vezes deixa tau² um pouco positivo por acaso e "inventa" tiers.
    variancia_base = media * (1 - media)
    qui2 = sum((w - media) ** 2 / (variancia_base / n) for w, (_, n) in zip(winrates, linhas))
    if variancia_base == 0 or qui2 <= qui2_critico(len(linhas) - 1):
        return None

    # 2) Quanto diferem: método dos momentos
    variancia_observada = sum((w - media) ** 2 for w in winrates) / len(winrates)
    ruido = sum(w * (1 - w) / n for w, (_, n) in zip(winrates, linhas)) / len(linhas)
    tau2 = variancia_observada - ruido
    if tau2 <= 0:
        return None
    prior = PRIOR_WINRATE * (1 - PRIOR_WINRATE) / tau2
    return prior if prior <= PRIOR_MAXIMO else None


def winrate_ajustado(vitorias: int, jogos: int, prior: float) -> float:
    return (vitorias + prior * PRIOR_WINRATE) / (jogos + prior)


def tier_de(ajustado: float) -> str:
    for tier, limite in LIMITES_TIER:
        if ajustado >= limite:
            return tier
    return "D"


async def calcular_tier_list(session: AsyncSession, rota: str | None = None) -> TierList:
    patch = await session.scalar(text(CONSULTA_PATCH), {"fila": FILA_SOLO_ID})
    if patch is None:
        return TierList(
            patch=None, partidas=0, minimo_jogos=MINIMO_JOGOS, prior_jogos=None, campeoes=[]
        )

    params = {"fila": FILA_SOLO_ID, "prefixo": f"{patch}.%"}
    total_partidas = await session.scalar(text(CONSULTA_TOTAL), params)
    linhas = (
        await session.execute(text(CONSULTA_TIER_LIST), {**params, "minimo": MINIMO_JOGOS})
    ).all()

    # O prior é estimado com TODAS as rotas (mais dados = estimativa mais estável)
    prior = estimar_prior([(linha.vitorias, linha.jogos) for linha in linhas])

    campeoes = []
    for linha in linhas:
        if rota and linha.rota != rota:
            continue
        ajustado = winrate_ajustado(linha.vitorias, linha.jogos, prior) if prior else None
        campeoes.append(
            CampeaoTierList(
                champion_id=linha.champion_id,
                champion_name=linha.champion_name,
                rota=linha.rota,
                tier=tier_de(ajustado) if ajustado is not None else None,
                jogos=linha.jogos,
                vitorias=linha.vitorias,
                winrate=linha.vitorias / linha.jogos,
                winrate_ajustado=ajustado,
                pickrate=linha.jogos / total_partidas,
                banrate=linha.partidas_banido / total_partidas,
            )
        )
    # Com tiers: do melhor para o pior. Sem tiers: dos mais jogados para os menos jogados,
    # para não sugerir um ranking que os dados não sustentam.
    if prior:
        campeoes.sort(key=lambda c: c.winrate_ajustado, reverse=True)
    else:
        campeoes.sort(key=lambda c: c.jogos, reverse=True)
    return TierList(
        patch=patch,
        partidas=total_partidas,
        minimo_jogos=MINIMO_JOGOS,
        prior_jogos=round(prior) if prior else None,
        campeoes=campeoes,
    )
