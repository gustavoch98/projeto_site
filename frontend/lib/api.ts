// Chamadas à NOSSA API (FastAPI). O front-end nunca fala direto com a Riot.
//
// Estas funções rodam no SERVIDOR do Next.js (Server Components e Server Actions).
// Por isso API_URL não tem o prefixo NEXT_PUBLIC_: ela não é enviada ao navegador.

const API_URL = process.env.API_URL ?? "http://localhost:8000";

// Os tipos espelham o schema PlayerProfile do back-end (backend/app/schemas/player.py).
export type FilaRanked = {
  tier: string;
  rank: string;
  league_points: number;
  wins: number;
  losses: number;
  winrate: number;
};

export type Perfil = {
  puuid: string;
  game_name: string;
  tag_line: string;
  region: string;
  profile_icon_id: number;
  summoner_level: number;
  solo: FilaRanked | null;
  flex: FilaRanked | null;
  updated_at: string;
  refresh_available_at: string;
  cached: boolean;
};

// Em vez de lançar exceções para erros esperados, devolvemos um resultado com "tipo".
// Assim a página decide o que mostrar em cada caso.
export type ResultadoPerfil =
  | { tipo: "ok"; perfil: Perfil }
  | { tipo: "nao-encontrado" }
  | { tipo: "erro"; mensagem: string };

function urlPerfil(regiao: string, nome: string, tag: string): string {
  return `${API_URL}/api/players/${regiao}/${encodeURIComponent(nome)}/${encodeURIComponent(tag)}`;
}

async function chamarApi(url: string, metodo: "GET" | "POST"): Promise<ResultadoPerfil> {
  let resposta: Response;
  try {
    resposta = await fetch(url, { method: metodo });
  } catch {
    return { tipo: "erro", mensagem: "Não foi possível conectar ao servidor. Tente novamente." };
  }

  if (resposta.ok) {
    return { tipo: "ok", perfil: await resposta.json() };
  }
  if (resposta.status === 404) {
    return { tipo: "nao-encontrado" };
  }
  // A API devolve {"detail": "mensagem em português"} nos erros
  const corpo = await resposta.json().catch(() => null);
  return { tipo: "erro", mensagem: corpo?.detail ?? "Erro inesperado. Tente novamente." };
}

export function buscarPerfil(regiao: string, nome: string, tag: string) {
  return chamarApi(urlPerfil(regiao, nome, tag), "GET");
}

export function atualizarPerfil(regiao: string, nome: string, tag: string) {
  return chamarApi(urlPerfil(regiao, nome, tag) + "/refresh", "POST");
}

// --- Autocomplete ------------------------------------------------------------

// Espelha o schema PlayerSuggestion do back-end
export type SugestaoApi = {
  game_name: string;
  tag_line: string;
  region: string;
  profile_icon_id: number;
  summoner_level: number;
  solo: FilaRanked | null;
};

export async function sugerirJogadores(texto: string, regiao = "br"): Promise<SugestaoApi[]> {
  const params = new URLSearchParams({ q: texto, region: regiao });
  try {
    const resposta = await fetch(`${API_URL}/api/players/search?${params}`);
    return resposta.ok ? await resposta.json() : [];
  } catch {
    return []; // autocomplete é um extra: se falhar, simplesmente não mostra sugestões
  }
}

// --- Partidas ----------------------------------------------------------------

// Espelha o schema MatchSummary do back-end (backend/app/schemas/match.py)
export type Partida = {
  match_id: string;
  queue_id: number;
  game_start: string;
  game_duration: number;
  remake: boolean;
  champion_id: number;
  champion_name: string;
  team_position: string;
  win: boolean;
  kills: number;
  deaths: number;
  assists: number;
  cs: number;
  gold: number;
  damage_to_champions: number;
  vision_score: number;
  kill_participation: number | null;
  items: number[];
  summoner_spells: number[];
  kda: number;
  cs_per_minute: number;
};

export async function buscarPartidas(
  regiao: string,
  nome: string,
  tag: string,
): Promise<Partida[] | null> {
  try {
    const resposta = await fetch(`${urlPerfil(regiao, nome, tag)}/matches`);
    return resposta.ok ? await resposta.json() : null;
  } catch {
    return null; // null = não foi possível carregar (a página mostra um aviso)
  }
}

// --- Painel de insights ------------------------------------------------------

// Espelha os schemas de backend/app/schemas/insights.py
export type FaixaDesempenho = {
  chave: string;
  rotulo: string;
  jogos: number;
  vitorias: number;
  winrate: number | null;
  ic_baixo: number | null;
  ic_alto: number | null;
};

export type InsightsHorario = {
  partidas_analisadas: number;
  winrate_geral: number | null;
  primeira_partida: string | null;
  ultima_partida: string | null;
  por_periodo: FaixaDesempenho[];
  por_dia_semana: FaixaDesempenho[];
  coletando_historico: boolean;
};

export async function buscarInsights(
  regiao: string,
  nome: string,
  tag: string,
): Promise<InsightsHorario | null> {
  try {
    const resposta = await fetch(`${urlPerfil(regiao, nome, tag)}/insights`);
    return resposta.ok ? await resposta.json() : null;
  } catch {
    return null;
  }
}
