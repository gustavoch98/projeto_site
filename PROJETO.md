# PROJETO.md — Site de estatísticas de League of Legends

> Documento de definição do projeto. Leia este arquivo inteiro antes de começar e consulte-o sempre que for tomar uma decisão de arquitetura ou escopo.

---

## 1. Visão geral

Site no estilo OP.GG / DeepLoL, começando por League of Legends. Qualquer pessoa digita um **Riot ID** (`Nome#TAG`) e vê o perfil do jogador com dados puxados da API oficial da Riot.

**Objetivos do projeto (em ordem de importância):**

1. **Aprendizado:** entender na prática como consumir APIs externas, montar um back-end, um front-end e fazer o deploy de um site com domínio próprio.
2. **Portfólio:** projeto público, com código organizado, README bom e site no ar.
3. **Produto:** no futuro, oferecer análises que os outros sites não mostram (definidas depois de explorar os dados).

---

## 2. Sobre o desenvolvedor e forma de trabalho

- O desenvolvedor (Gustavo) tem **muita experiência com Python e banco de dados relacional (SQL)**, e é pós-graduado em ciência de dados.
- Tem **pouca experiência com front-end**.

**Modo de trabalho: aprendizado.** Isso significa:

- Trabalhar em **etapas pequenas**. Cada etapa termina com algo que roda e pode ser testado.
- **Antes** de escrever código de uma etapa, explique em poucas linhas o que será feito e por quê.
- **Depois** de cada etapa, explique o que foi criado, como testar e quais conceitos novos apareceram.
- No **front-end**, explique com mais detalhe (componentes, rotas, estado, renderização no servidor vs. cliente). No **back-end Python e SQL**, pode ser mais direto.
- Ao introduzir uma ferramenta nova (Docker, Vercel, variáveis de ambiente, DNS etc.), explique para que ela serve antes de usar.
- Nunca avance de fase sem confirmar comigo.
- Prefira soluções simples e legíveis a soluções "espertas".

---

## 3. Stack definida

| Camada | Tecnologia | Motivo |
|---|---|---|
| Front-end | **Next.js** (App Router) + **TypeScript** + **Tailwind CSS** | Padrão de mercado, deploy fácil na Vercel, bom para portfólio |
| Back-end / API própria | **Python + FastAPI** | Linguagem que o dev domina; tipagem com Pydantic; docs automáticas (Swagger) |
| Cliente HTTP | **httpx** (assíncrono) | Chamadas à API da Riot |
| Banco de dados | **PostgreSQL** | Ver justificativa abaixo |
| ORM / migrations | **SQLAlchemy 2.x** + **Alembic** | Controle de schema versionado |
| Cache | Tabelas no Postgres com timestamp (MVP). **Redis** só se for necessário depois | Evitar complexidade cedo |
| Ambiente local | **Docker Compose** (Postgres) | Ambiente reproduzível |
| Controle de versão | Git + GitHub (repositório público) | Portfólio |

### Por que PostgreSQL

- Os dados da Riot são bem estruturados (contas, partidas, participantes, ranked): o modelo relacional se encaixa bem e o dev já domina SQL.
- As análises futuras (winrate por campeão, desempenho por horário, tendências) são consultas analíticas com `JOIN`, `GROUP BY` e window functions — terreno forte do SQL.
- O payload bruto das partidas pode ser guardado numa coluna **JSONB**, o que dá flexibilidade de NoSQL sem trocar de banco.
- Escala bem para o tamanho deste projeto com índices adequados; se crescer, dá para usar particionamento por data, réplicas de leitura ou uma camada de cache.
- Tem oferta gerenciada com plano gratuito (Neon, Supabase).

---

## 4. API da Riot — o que precisamos saber

### Chaves e limites

- **Chave de desenvolvimento:** gerada no Riot Developer Portal, **expira a cada 24h**. Serve só para desenvolver.
- Chaves de desenvolvimento e pessoais têm limite baixo: **20 requisições/segundo e 100 requisições/2 minutos**, por região de roteamento.
- **A Riot não permite manter um produto público com chave de desenvolvimento.** Para colocar o site no ar será preciso registrar o projeto no portal ("Register Project") e pedir uma **chave de produção** (limite inicial bem maior). Isso tem prazo de aprovação, então deve ser pedido assim que houver um protótipo funcionando.
- A chave **nunca** vai para o front-end nem para o Git. Fica em variável de ambiente (`RIOT_API_KEY`) só no back-end.

### Roteamento

A API usa dois tipos de host:

- **Plataforma** (servidor do jogo): ex. `br1.api.riotgames.com` — usado por Summoner-V4 e League-V4.
- **Regional**: ex. `americas.api.riotgames.com` — usado por Account-V1 e Match-V5.

O BR usa plataforma `br1` e região `americas`. O código deve ter um mapeamento plataforma → região desde o início, mesmo que o MVP use só BR.

### Endpoints do MVP

1. **Account-V1** — `GET /riot/account/v1/accounts/by-riot-id/{gameName}/{tagLine}` (regional) → retorna o **PUUID**, o identificador principal do jogador.
2. **Summoner-V4** — `GET /lol/summoner/v4/summoners/by-puuid/{puuid}` (plataforma) → ícone e nível.
3. **League-V4** — `GET /lol/league/v4/entries/by-puuid/{puuid}` (plataforma) → elo, divisão, PDL, vitórias e derrotas de Solo/Duo e Flex.

### Endpoints das próximas fases

- **Match-V5** — `GET /lol/match/v5/matches/by-puuid/{puuid}/ids` e `GET /lol/match/v5/matches/{matchId}` (regional) → histórico e detalhes das partidas.
- **Champion-Mastery-V4** — maestrias por PUUID.

### Observações importantes

- Use sempre **PUUID** como chave. Nomes de invocador estão descontinuados e os IDs antigos (summonerId) estão sendo removidos. Confirme na documentação oficial antes de depender de qualquer campo.
- **Data Dragon** (CDN estático da Riot) fornece imagens de ícones, campeões e itens, e a versão atual do jogo. Não consome limite da API.
- Tratar respostas `404` (jogador não existe), `429` (limite excedido; respeitar o header `Retry-After`), `401/403` (chave inválida ou expirada) e `5xx`.
- Riot ID não diferencia maiúsculas de minúsculas na busca, e o usuário pode digitar com espaços. Normalizar a entrada.

---

## 5. Escopo do MVP

**Uma única funcionalidade, bem feita:** buscar um jogador pelo Riot ID e ver o perfil.

### Telas

1. **Página inicial (`/`)**
   - Campo de busca para o Riot ID (`Nome#TAG`), com validação do formato.
   - Região fixa em BR no MVP (o seletor de região fica para depois).

2. **Página de perfil (`/perfil/br/{nome}-{tag}`)**
   - Cabeçalho: ícone de perfil, Riot ID, nível.
   - Cards de ranked: Solo/Duo e Flex — emblema do elo, tier e divisão, PDL, vitórias, derrotas e winrate. Mostrar "Unranked" quando não houver.
   - Botão **"Atualizar"** que força nova consulta à Riot (respeitando o cache mínimo).
   - Indicação de "última atualização há X minutos".
   - Estados de **carregando**, **jogador não encontrado** e **erro**.

### Visual

- Tema **escuro**, interface em **português (PT-BR)**.
- Layout responsivo (funcionar bem no celular).
- Referências: OP.GG e DeepLoL, mas sem copiar logotipo, nome ou identidade visual deles.

### Fora do MVP (não fazer agora)

Login de usuários, histórico de partidas, detalhes de partida, estatísticas por campeão, partida ao vivo, ranking, múltiplos jogos.

---

## 6. Arquitetura

```
[Navegador] → [Next.js (Vercel)] → [FastAPI (back-end)] → [API da Riot]
                                          ↕
                                   [PostgreSQL]
```

- O front **nunca** chama a Riot diretamente. Sempre passa pelo back-end, que guarda a chave e controla o limite.
- **Estratégia de cache:** ao buscar um jogador, o back-end verifica no banco se há dados com menos de **N minutos** (configurável, ex. 10). Se sim, devolve do banco. Se não, consulta a Riot, salva e devolve.
- O back-end deve ter um **controle de rate limit** próprio (ex. token bucket simples) para não estourar os limites da chave.

### Endpoints da API própria (MVP)

- `GET /api/players/{region}/{gameName}/{tagLine}` → perfil completo (conta + summoner + ranked), usando cache.
- `POST /api/players/{region}/{gameName}/{tagLine}/refresh` → força atualização.
- `GET /health` → para o monitoramento do deploy.

### Modelo de dados inicial (sugestão)

- `accounts` — `puuid` (PK), `game_name`, `tag_line`, `region`, `profile_icon_id`, `summoner_level`, `updated_at`.
- `ranked_entries` — `puuid` (FK), `queue_type`, `tier`, `rank`, `league_points`, `wins`, `losses`, `updated_at`.
- Índice único em (`lower(game_name)`, `lower(tag_line)`, `region`) para a busca.

Na fase de partidas entram `matches` (com coluna JSONB para o payload bruto) e `match_participants`.

---

## 7. Estrutura do repositório (monorepo)

```
/
├── PROJETO.md
├── README.md
├── docker-compose.yml        # Postgres local
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py         # variáveis de ambiente
│   │   ├── riot/             # cliente da API da Riot + rate limit
│   │   ├── models/           # SQLAlchemy
│   │   ├── schemas/          # Pydantic
│   │   ├── services/         # regras de negócio e cache
│   │   └── routes/
│   ├── alembic/
│   ├── tests/
│   └── pyproject.toml
└── frontend/
    ├── app/                  # rotas do Next.js
    ├── components/
    ├── lib/                  # chamadas à API própria
    └── package.json
```

- Variáveis de ambiente em `.env` (no `.gitignore`), com um `.env.example` versionado.
- Testes no back-end com **pytest**, mockando a API da Riot.

---

## 8. Deploy

- **Front-end:** Vercel.
- **Back-end:** Railway, Render ou Fly.io (escolher na fase de deploy, explicando prós e contras de cada um).
- **Banco:** Postgres gerenciado (Neon ou Supabase).
- **Domínio próprio:** já será comprado. Configurar DNS apontando o domínio para a Vercel e um subdomínio (ex. `api.meudominio.com`) para o back-end. Explicar cada passo de DNS e HTTPS.
- Variáveis de ambiente configuradas nos painéis de cada serviço, nunca no código.
- Lembrar: o site público precisa da **chave de produção** da Riot (ver seção 4).

---

## 9. Roadmap por fases

Cada fase só começa depois que a anterior estiver funcionando e eu confirmar.

**Fase 0 — Preparação**
- Criar repositório, estrutura de pastas, `.gitignore`, `.env.example`, Docker Compose com Postgres.
- Script Python simples que testa a chave da Riot buscando um Riot ID e imprime o PUUID.

**Fase 1 — Back-end do MVP**
- Cliente da Riot (Account, Summoner, League) com tratamento de erros e rate limit.
- Modelos, migrations, lógica de cache e endpoints da API própria.
- Testes com pytest.

**Fase 2 — Front-end do MVP**
- Setup do Next.js + Tailwind, explicando a estrutura.
- Página inicial com busca e página de perfil consumindo a API própria.
- Imagens via Data Dragon. Estados de carregamento e erro.

**Fase 3 — Deploy**
- Banco gerenciado, back-end e front-end no ar, domínio próprio com HTTPS.
- Registrar o projeto na Riot e pedir chave de produção.
- README de portfólio com prints, arquitetura e instruções para rodar localmente.

**Fase 4 — Partidas e exploração de dados**
- Ingestão das partidas via Match-V5 para o Postgres (payload bruto em JSONB + tabelas normalizadas).
- Ambiente de exploração (notebook/SQL) para descobrir quais análises próprias valem a pena.

**Fase 5 — Funcionalidades além do MVP** (a definir depois da Fase 4)
- Histórico de partidas, detalhe de partida, estatísticas por campeão, seletor de região.
- **Análises exclusivas** (o diferencial do projeto).

---

## 10. Regras gerais para o Claude Code

- Siga a stack e as decisões deste documento. Se achar que alguma decisão deve mudar, **pergunte antes** e explique o motivo.
- Nunca exponha a `RIOT_API_KEY` em código, log, commit ou front-end.
- Commits pequenos e com mensagens descritivas.
- Antes de usar qualquer endpoint da Riot, confira a documentação oficial em developer.riotgames.com, porque a API muda com frequência.
- Mantenha este arquivo atualizado: quando uma decisão nova for tomada, registre aqui.

---

## 11. Registro de decisões

| Data | Decisão | Motivo |
|---|---|---|
| 2026-10-13 | Driver do Postgres: **asyncpg** (URL `postgresql+asyncpg://`) | O modo assíncrono do psycopg não funciona com o event loop padrão do Windows |
| 2026-10-13 | Rate limit por **janela deslizante** (20/1s e 100/120s), um limitador por host da Riot | Reproduz exatamente a regra da Riot, que conta os limites separadamente por host |
| 2026-10-13 | "Atualizar" ignora o TTL do cache, mas respeita `REFRESH_COOLDOWN_SECONDS` (120s) | Evita que o botão seja usado para esgotar o limite da chave |
| 2026-10-13 | Se a Riot falhar (5xx, 429, chave expirada) e houver dados antigos no banco, eles são devolvidos com `cached: true` | Melhor experiência do que uma tela de erro |
| 2026-10-13 | Resposta do perfil traz `solo` e `flex` separados (`null` = Unranked) | Simplifica o front-end |
| 2026-10-13 | Testes usam o banco `lolstats_test` no mesmo container e **respx** para simular a Riot | Não gasta limite da chave nem depende dela |
| 2026-10-13 | Front-end em **Next.js 16** com `cacheComponents` (padrão do gerador): nada é cacheado sem `"use cache"` | Perfil sempre busca dados frescos da API (que tem o próprio cache); só a versão do Data Dragon é cacheada (horas) |
| 2026-10-13 | Emblemas de elo vêm do **CommunityDragon** (`raw.communitydragon.org`) | O Data Dragon não tem emblemas de elo |
| 2026-10-13 | Front chama a API **só pelo servidor do Next.js** (Server Components e Server Action do botão "Atualizar"); `API_URL` sem `NEXT_PUBLIC_` | O navegador não precisa conhecer o endereço do back-end, e não dependemos de CORS |
| 2026-10-13 | URL do perfil usa o **último hífen** como separador (`/perfil/br/Nome-TAG`) | A TAG só tem letras e números, mas o nome pode ter hífen |
| 2026-10-13 | **Autocomplete** na busca (adicionado ao MVP a pedido): `GET /api/players/search` busca por prefixo do nome **no nosso banco**, com índice `lower(game_name) text_pattern_ops` | A API da Riot não tem busca por prefixo; como no OP.GG, as sugestões vêm dos jogadores que o site já conhece. A base cresce com as buscas e, na Fase 4, com as partidas |
| 2026-10-13 | A `#TAG` é opcional na busca: sem ela, tentamos `#BR1` | Simplifica o uso; a página de "não encontrado" explica a tentativa |
| 2026-10-13 | Front acessa o autocomplete por um **Route Handler** do Next (`/api/sugestoes`), que repassa ao FastAPI | Mantém a regra de que o navegador não chama o back-end diretamente |
| 2026-10-13 | Script de "semente" (`scripts/semear_ranking.py`) com os ~10,6 mil jogadores Mestre+ do BR | Popula o autocomplete; retomável e com ritmo configurável para não esgotar a chave |
| 2026-10-13 | **Fase 4 antecipada** antes do deploy: o perfil ganha partidas e análises | Sem histórico de partidas não há insights; o site estava cru para o portfólio |
| 2026-10-13 | Estrutura de páginas: **uma página por jogador** (`/perfil/br/Nome-TAG`) com seções/abas; "Meu perfil" será um atalho salvo no navegador, sem login | Sem recursos pessoais (metas, alertas) duas páginas mostrariam os mesmos dados; login fica para quando houver |
| 2026-10-13 | Partidas: `matches` (JSON bruto em JSONB) + `match_participants` (colunas de análise, com início/duração/fila desnormalizados); endpoint próprio `.../matches` carregado com `<Suspense>` | O elo aparece na hora e as partidas chegam por streaming; cada partida é buscada na Riot uma única vez |
| 2026-10-13 | `ranked_history`: "foto" do elo a cada mudança | Permite gráfico de evolução do PDL; só existe a partir de quando começamos a gravar |
| 2026-10-13 | Prioridade de análises exclusivas: **horário e tilt** | Escolha do Gustavo. Atenção: horários vêm em UTC; converter para America/Sao_Paulo nas análises |
| 2026-10-13 | Espaço: ~50 KB por partida no banco (JSON comprimido) | O plano grátis do Neon tem 0,5 GB; reavaliar guardar o JSON bruto no deploy |
| 2026-10-13 | Coleta para exploração: `scripts/coletar_partidas.py` (um jogador + amostra de 10 por elo, 100 partidas cada, sorteio com semente fixa salvo em `backend/dados/`, fora do Git) | Tilt e horário exigem sequências longas por jogador e jogadores de todos os elos |
| 2026-10-13 | Notebooks com dependências opcionais `.[analise]` (JupyterLab, pandas, matplotlib, psycopg síncrono) | O pandas não lê com driver assíncrono; a API não precisa dessas bibliotecas |
| 2026-10-13 | Definições da exploração 01: sessão = intervalo ≤ 45 min entre partidas; comparação entre jogadores pelo desvio do winrate do próprio jogador; IC 95% de Wilson | Evita misturar *quem* joga em cada horário com *como* joga; deixa a incerteza visível |
| 2026-10-13 | **Painel do jogador**, 1º bloco: desempenho por período do dia e dia da semana (`GET .../insights`, agregado em SQL no horário de Brasília) | Primeira análise que vira produto; começa o "painel" com vários cartões |
| 2026-10-13 | Histórico de 100 partidas buscado **em segundo plano** (BackgroundTasks) na 1ª visita (`HISTORICO_PARTIDAS`) | 20 partidas não sustentam análise por horário; a página não pode esperar ~2 min |
| 2026-10-13 | Destaque do painel escolhe melhor/pior faixa pelos **limites do IC de Wilson** (não pelo winrate cru), exige ≥ 10 partidas por faixa e ≥ 20 no total, e usa teste z de duas proporções para dizer se "pode ser acaso" | Com amostra pequena os extremos aparecem por acaso (ex.: 64% em 14 jogos "vencia" 60% em 111) |
| 2026-10-13 | Perfil em **abas com URL própria**: `/perfil/br/Nome-TAG` (Visão geral: painel + 5 últimas partidas) e `/perfil/br/Nome-TAG/partidas` (resumo + histórico). Cabeçalho, cards de elo e abas ficam num `layout.tsx` | Separa "como estou jogando" de "o que aconteceu"; links compartilháveis, botão Voltar funciona, cada aba busca só os próprios dados; novas abas = nova pasta |
| 2026-10-13 | `loading`/`not-found`/`error` do perfil ficam em `app/perfil/[regiao]/` e um segundo `loading.tsx` em `[riotId]/` | Os arquivos de um segmento não envolvem o layout do mesmo segmento; o `loading` interno deixa a troca de aba instantânea (só o conteúdo mostra esqueleto) |
| 2026-10-13 | Aba **Campeões** (`/campeoes`, `GET .../champions`): todos os campeões, 5 mais jogados em cards comparados à média geral do jogador, tabela completa recolhível (`<details>`) | Mostrar tudo, mas campeões com < 10 partidas aparecem esmaecidos com barra "faltam N partidas" (incentiva jogar mais com o campeão); "mais forte" escolhido pelo limite inferior do IC |
| 2026-10-13 | Gravação de conta/elo com **upsert** (`INSERT ... ON CONFLICT DO UPDATE`); as seções do perfil leem a conta do banco (`conta_para_consulta`) e só a rota do perfil consulta a Riot | A página faz vários pedidos simultâneos; com cache vencido eles disputavam a mesma linha (erro de chave duplicada) e consultavam a Riot várias vezes |
| Pendente | Comparar métricas do campeão com a média **da mesma rota** (hoje é a média geral) | Quem joga atirador e suporte vê "visão baixa" no atirador só porque a média inclui o suporte |
| 2026-10-13 | **Nome: Raio (raio.gg)** e identidade visual **"C"**: preto `#000000` + amarelo-limão `#E6FF2E`, cantos retos, Bricolage Grotesque + Space Mono; logo = raio preto em quadrado limão | Diferenciar do OP.GG e afins; nome curto, serve para outros jogos e não usa marcas da Riot ("LoL Stats" não poderia ser usado na chave de produção). mira.gg e engage.gg estavam registrados; raio.gg sem registro DNS (confirmar no registrador) |
| 2026-10-13 | Cores do front por **significado** (tokens `destaque`, `neutro`, `erro`... em `globals.css`) e nome em `lib/marca.ts` | Trocar paleta ou nome é editar um arquivo. Vitória = limão, derrota = neutro: sem vermelho/verde (daltonismo) e sem o padrão azul/vermelho dos concorrentes |

