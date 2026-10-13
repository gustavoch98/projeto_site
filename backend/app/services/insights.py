"""Painel de insights do jogador. Tudo calculado a partir das partidas já salvas no banco."""

import math

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.insights import (
    CampeoesJogador,
    EstatisticasCampeao,
    FaixaDesempenho,
    InsightsHorario,
)

# Os horários do banco estão em UTC; o jogador pensa no horário local.
FUSO_BR = "America/Sao_Paulo"

PERIODOS = [
    ("madrugada", "Madrugada (0h–5h)"),
    ("manha", "Manhã (6h–11h)"),
    ("tarde", "Tarde (12h–17h)"),
    ("noite", "Noite (18h–23h)"),
]
DIAS_SEMANA = [  # isodow do Postgres: 1 = segunda ... 7 = domingo
    ("1", "Seg"), ("2", "Ter"), ("3", "Qua"), ("4", "Qui"), ("5", "Sex"), ("6", "Sáb"), ("7", "Dom"),
]

# Partidas que entram nas análises: ranqueadas (Solo/Duo e Flex), sem remakes
FILTRO_PARTIDAS = "puuid = :puuid AND NOT remake AND queue_id IN (420, 440)"

CONSULTA_RESUMO = f"""
SELECT count(*) AS jogos,
       avg(win::int) AS winrate,
       min(game_start) AS primeira,
       max(game_start) AS ultima
FROM match_participants
WHERE {FILTRO_PARTIDAS}
"""

CONSULTA_POR_PERIODO = f"""
SELECT CASE
           WHEN hora < 6 THEN 'madrugada'
           WHEN hora < 12 THEN 'manha'
           WHEN hora < 18 THEN 'tarde'
           ELSE 'noite'
       END AS chave,
       count(*) AS jogos,
       sum(win::int) AS vitorias
FROM (
    SELECT extract(hour FROM game_start AT TIME ZONE :fuso)::int AS hora, win
    FROM match_participants
    WHERE {FILTRO_PARTIDAS}
) partidas
GROUP BY 1
"""

CONSULTA_POR_DIA = f"""
SELECT extract(isodow FROM game_start AT TIME ZONE :fuso)::int::text AS chave,
       count(*) AS jogos,
       sum(win::int) AS vitorias
FROM match_participants
WHERE {FILTRO_PARTIDAS}
GROUP BY 1
"""


def wilson(vitorias: int, jogos: int, z: float = 1.96) -> tuple[float, float]:
    """Intervalo de confiança de 95% para uma proporção (método de Wilson).

    Melhor que "p ± 1,96·erro padrão" com amostras pequenas: nunca sai de [0, 1].
    """
    p = vitorias / jogos
    denominador = 1 + z**2 / jogos
    centro = (p + z**2 / (2 * jogos)) / denominador
    margem = z * math.sqrt(p * (1 - p) / jogos + z**2 / (4 * jogos**2)) / denominador
    return max(0.0, centro - margem), min(1.0, centro + margem)


def montar_faixas(linhas, categorias: list[tuple[str, str]]) -> list[FaixaDesempenho]:
    """Converte o resultado do GROUP BY em faixas, incluindo as que não tiveram partidas."""
    por_chave = {linha.chave: linha for linha in linhas}
    faixas = []
    for chave, rotulo in categorias:
        linha = por_chave.get(chave)
        if linha is None:
            faixas.append(FaixaDesempenho(
                chave=chave, rotulo=rotulo, jogos=0, vitorias=0,
                winrate=None, ic_baixo=None, ic_alto=None,
            ))
            continue
        baixo, alto = wilson(linha.vitorias, linha.jogos)
        faixas.append(FaixaDesempenho(
            chave=chave, rotulo=rotulo, jogos=linha.jogos, vitorias=linha.vitorias,
            winrate=linha.vitorias / linha.jogos, ic_baixo=baixo, ic_alto=alto,
        ))
    return faixas


async def calcular_insights_horario(
    session: AsyncSession, puuid: str, coletando_historico: bool
) -> InsightsHorario:
    params = {"puuid": puuid, "fuso": FUSO_BR}
    resumo = (await session.execute(text(CONSULTA_RESUMO), params)).one()
    por_periodo = (await session.execute(text(CONSULTA_POR_PERIODO), params)).all()
    por_dia = (await session.execute(text(CONSULTA_POR_DIA), params)).all()

    return InsightsHorario(
        partidas_analisadas=resumo.jogos,
        winrate_geral=float(resumo.winrate) if resumo.winrate is not None else None,
        primeira_partida=resumo.primeira,
        ultima_partida=resumo.ultima,
        por_periodo=montar_faixas(por_periodo, PERIODOS),
        por_dia_semana=montar_faixas(por_dia, DIAS_SEMANA),
        coletando_historico=coletando_historico,
    )


# --- Campeões ---------------------------------------------------------------------

MINIMO_PARTIDAS_CAMPEAO = 10

# Somas de cada grupo; as médias e taxas são calculadas em Python a partir delas.
COLUNAS_ESTATISTICAS = """
       count(*) AS jogos,
       sum(win::int) AS vitorias,
       sum(kills) AS abates,
       sum(deaths) AS mortes,
       sum(assists) AS assistencias,
       sum(cs) AS cs,
       sum(damage_to_champions) AS dano,
       sum(vision_score) AS visao,
       sum(gold) AS ouro,
       sum(game_duration) AS segundos,
       avg(kill_participation) AS participacao_abates,
       -- mode(): o valor mais frequente do grupo (a rota que ele mais joga)
       mode() WITHIN GROUP (ORDER BY nullif(team_position, '')) AS rota_principal,
       max(game_start) AS ultima_partida
"""

CONSULTA_POR_CAMPEAO = f"""
SELECT champion_id, max(champion_name) AS champion_name, {COLUNAS_ESTATISTICAS}
FROM match_participants
WHERE {FILTRO_PARTIDAS}
GROUP BY champion_id
ORDER BY jogos DESC, vitorias DESC
"""

# Todas as partidas juntas (sem GROUP BY). O HAVING evita uma linha de nulos se não houver partidas.
CONSULTA_GERAL = f"""
SELECT NULL::int AS champion_id, NULL::text AS champion_name, {COLUNAS_ESTATISTICAS}
FROM match_participants
WHERE {FILTRO_PARTIDAS}
HAVING count(*) > 0
"""


def montar_estatisticas(linha) -> EstatisticasCampeao:
    minutos = linha.segundos / 60
    baixo, alto = wilson(linha.vitorias, linha.jogos)
    return EstatisticasCampeao(
        champion_id=linha.champion_id,
        champion_name=linha.champion_name,
        jogos=linha.jogos,
        vitorias=linha.vitorias,
        winrate=linha.vitorias / linha.jogos,
        ic_baixo=baixo,
        ic_alto=alto,
        kda=(linha.abates + linha.assistencias) / max(linha.mortes, 1),
        abates=linha.abates / linha.jogos,
        mortes=linha.mortes / linha.jogos,
        assistencias=linha.assistencias / linha.jogos,
        cs_por_minuto=linha.cs / minutos,
        dano_por_minuto=linha.dano / minutos,
        visao_por_minuto=linha.visao / minutos,
        ouro_por_minuto=linha.ouro / minutos,
        participacao_abates=(
            float(linha.participacao_abates) if linha.participacao_abates is not None else None
        ),
        rota_principal=linha.rota_principal,
        ultima_partida=linha.ultima_partida,
    )


async def calcular_campeoes(
    session: AsyncSession, puuid: str, coletando_historico: bool
) -> CampeoesJogador:
    params = {"puuid": puuid}
    por_campeao = await session.execute(text(CONSULTA_POR_CAMPEAO), params)
    geral = await session.execute(text(CONSULTA_GERAL), params)

    campeoes = [montar_estatisticas(linha) for linha in por_campeao]
    linha_geral = geral.first()
    return CampeoesJogador(
        partidas_analisadas=sum(c.jogos for c in campeoes),
        minimo_partidas=MINIMO_PARTIDAS_CAMPEAO,
        geral=montar_estatisticas(linha_geral) if linha_geral else None,
        campeoes=campeoes,
        coletando_historico=coletando_historico,
    )

