# LoL Stats

Site de estatísticas de League of Legends (estilo OP.GG / DeepLoL): digite um Riot ID (`Nome#TAG`) e veja o perfil do jogador com dados da API oficial da Riot.

> Projeto em desenvolvimento. Veja o planejamento completo em [PROJETO.md](PROJETO.md).

## Stack

- **Front-end:** Next.js + TypeScript + Tailwind CSS
- **Back-end:** Python + FastAPI + httpx
- **Banco:** PostgreSQL (SQLAlchemy + Alembic)
- **Ambiente local:** Docker Compose

## Rodando localmente

Pré-requisitos: Python 3.12+, Node.js 20+, Docker Desktop, Git.

```bash
# 1. Variáveis de ambiente
cp .env.example .env          # depois edite o .env e coloque sua RIOT_API_KEY

# 2. Banco de dados
docker compose up -d

# 3. Back-end
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows (Linux/macOS: source .venv/bin/activate)
pip install -e ".[dev]"

# 4. Testar a chave da Riot
python scripts/testar_chave.py "Nome#TAG"
```
