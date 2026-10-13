"""Testa a chave da Riot buscando um Riot ID e imprimindo o PUUID.

Uso (a partir da pasta backend, com o .venv ativado):
    python scripts/testar_chave.py "Nome#TAG"
"""

import os
import sys
from pathlib import Path
from urllib.parse import quote

import httpx
from dotenv import load_dotenv

# O .env fica na raiz do repositório (um nível acima de backend/)
RAIZ = Path(__file__).resolve().parents[2]
load_dotenv(RAIZ / ".env")

# Account-V1 usa host REGIONAL. O BR (plataforma br1) fica na região "americas".
REGIAO = "americas"


def separar_riot_id(riot_id: str) -> tuple[str, str]:
    """Converte 'Nome#TAG' em ('Nome', 'TAG'), removendo espaços nas pontas."""
    if "#" not in riot_id:
        raise ValueError("Formato inválido. Use Nome#TAG (ex.: Faker#KR1).")
    nome, tag = riot_id.rsplit("#", 1)
    nome, tag = nome.strip(), tag.strip()
    if not nome or not tag:
        raise ValueError("Nome e TAG não podem ser vazios.")
    return nome, tag


def main() -> int:
    if len(sys.argv) != 2:
        print('Uso: python scripts/testar_chave.py "Nome#TAG"')
        return 1

    chave = os.getenv("RIOT_API_KEY")
    if not chave or chave.startswith("RGAPI-coloque"):
        print("RIOT_API_KEY não configurada. Copie .env.example para .env e preencha a chave.")
        return 1

    try:
        nome, tag = separar_riot_id(sys.argv[1])
    except ValueError as erro:
        print(erro)
        return 1

    url = (
        f"https://{REGIAO}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/"
        f"{quote(nome)}/{quote(tag)}"
    )
    resposta = httpx.get(url, headers={"X-Riot-Token": chave}, timeout=10)

    if resposta.status_code == 200:
        dados = resposta.json()
        print(f"Jogador: {dados['gameName']}#{dados['tagLine']}")
        print(f"PUUID:   {dados['puuid']}")
        return 0

    mensagens = {
        401: "Chave ausente ou mal formatada (401).",
        403: "Chave inválida ou expirada (403). Gere uma nova no Riot Developer Portal.",
        404: "Jogador não encontrado (404). Confira o nome e a TAG.",
        429: f"Limite de requisições excedido (429). Tente de novo em {resposta.headers.get('Retry-After', '?')}s.",
    }
    print(mensagens.get(resposta.status_code, f"Erro inesperado: HTTP {resposta.status_code}"))
    return 1


if __name__ == "__main__":
    sys.exit(main())
