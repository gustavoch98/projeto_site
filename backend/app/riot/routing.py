"""Mapeamento entre a região usada nas URLs do site e os hosts da API da Riot.

A Riot tem dois tipos de host:
- plataforma (servidor do jogo), ex. br1.api.riotgames.com -> Summoner-V4, League-V4
- regional, ex. americas.api.riotgames.com                -> Account-V1, Match-V5
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Roteamento:
    plataforma: str
    regional: str


# Chave: região como aparece na URL do site (/perfil/br/...).
REGIOES: dict[str, Roteamento] = {
    "br": Roteamento("br1", "americas"),
    "na": Roteamento("na1", "americas"),
    "lan": Roteamento("la1", "americas"),
    "las": Roteamento("la2", "americas"),
    "euw": Roteamento("euw1", "europe"),
    "eune": Roteamento("eun1", "europe"),
    "tr": Roteamento("tr1", "europe"),
    "ru": Roteamento("ru", "europe"),
    "kr": Roteamento("kr", "asia"),
    "jp": Roteamento("jp1", "asia"),
    "oce": Roteamento("oc1", "sea"),
}

# No MVP o site só oferece BR, mas o mapeamento já existe para as outras.
REGIOES_ATIVAS = {"br"}


class RegiaoInvalida(ValueError):
    pass


def obter_roteamento(regiao: str) -> Roteamento:
    regiao = regiao.lower()
    if regiao not in REGIOES_ATIVAS:
        raise RegiaoInvalida(f"Região não suportada: {regiao}")
    return REGIOES[regiao]


def host(nome: str) -> str:
    return f"https://{nome}.api.riotgames.com"
