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

# 4. Criar as tabelas no banco
alembic upgrade head

# 5. Subir a API (http://localhost:8000/docs para a documentação interativa)
uvicorn app.main:app --reload

# 6. Rodar os testes (a Riot é simulada; usa o banco lolstats_test)
pytest
```

```bash
# 7. Front-end (em outro terminal, na pasta frontend)
cp .env.example .env.local
npm install
npm run dev                   # http://localhost:3000
```

Para testar só a chave da Riot: `python scripts/testar_chave.py "Nome#TAG"`.

## API própria

| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/players/{region}/{gameName}/{tagLine}` | Perfil (conta, nível, ranked Solo/Flex), com cache de 10 min |
| POST | `/api/players/{region}/{gameName}/{tagLine}/refresh` | Força atualização (mínimo de 2 min entre atualizações) |
| GET | `/health` | Status da API e do banco |
