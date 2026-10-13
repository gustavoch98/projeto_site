// Cálculos e formatação das partidas (funções puras, sem tela).

import type { Partida } from "@/lib/api";

export const FILAS: Record<number, string> = { 420: "Solo/Duo", 440: "Flex" };

export const ROTAS: Record<string, string> = {
  TOP: "Topo",
  JUNGLE: "Selva",
  MIDDLE: "Meio",
  BOTTOM: "Atirador",
  UTILITY: "Suporte",
};

export function formatarDuracao(segundos: number): string {
  const min = Math.floor(segundos / 60);
  const seg = segundos % 60;
  return `${min}:${String(seg).padStart(2, "0")}`;
}

export function formatarKda(kda: number): string {
  return kda.toLocaleString("pt-BR", { maximumFractionDigits: 2 });
}

export type ResumoCampeao = { championId: number; jogos: number; vitorias: number; kda: number };

export type Resumo = {
  jogos: number;
  vitorias: number;
  derrotas: number;
  winrate: number;
  kda: number;
  abates: number;
  mortes: number;
  assistencias: number;
  csPorMinuto: number;
  campeoes: ResumoCampeao[];
  rotas: { rota: string; jogos: number }[];
};

/** Estatísticas agregadas. Remakes ficam de fora, como no cliente do jogo. */
export function resumir(partidas: Partida[]): Resumo | null {
  const validas = partidas.filter((p) => !p.remake);
  if (validas.length === 0) return null;

  const soma = (f: (p: Partida) => number) => validas.reduce((total, p) => total + f(p), 0);
  const jogos = validas.length;
  const vitorias = validas.filter((p) => p.win).length;
  const [k, d, a] = [soma((p) => p.kills), soma((p) => p.deaths), soma((p) => p.assists)];

  // Agrupa por campeão (como um GROUP BY)
  const porCampeao = new Map<number, Partida[]>();
  for (const p of validas) {
    porCampeao.set(p.champion_id, [...(porCampeao.get(p.champion_id) ?? []), p]);
  }
  const campeoes = [...porCampeao.entries()]
    .map(([championId, ps]) => {
      const kc = ps.reduce((t, p) => t + p.kills + p.assists, 0);
      const dc = ps.reduce((t, p) => t + p.deaths, 0);
      return {
        championId,
        jogos: ps.length,
        vitorias: ps.filter((p) => p.win).length,
        kda: kc / Math.max(dc, 1),
      };
    })
    .sort((x, y) => y.jogos - x.jogos)
    .slice(0, 3);

  const contagemRotas = new Map<string, number>();
  for (const p of validas) {
    if (p.team_position) contagemRotas.set(p.team_position, (contagemRotas.get(p.team_position) ?? 0) + 1);
  }
  const rotas = [...contagemRotas.entries()]
    .map(([rota, n]) => ({ rota, jogos: n }))
    .sort((x, y) => y.jogos - x.jogos);

  return {
    jogos,
    vitorias,
    derrotas: jogos - vitorias,
    winrate: Math.round((100 * vitorias) / jogos),
    kda: (k + a) / Math.max(d, 1),
    abates: k / jogos,
    mortes: d / jogos,
    assistencias: a / jogos,
    csPorMinuto: soma((p) => p.cs) / (soma((p) => p.game_duration) / 60),
    campeoes,
    rotas,
  };
}
