// Tradução e formatação dos dados de ranked.

const ELOS: Record<string, { nome: string; cor: string }> = {
  IRON: { nome: "Ferro", cor: "text-stone-400" },
  BRONZE: { nome: "Bronze", cor: "text-amber-700" },
  SILVER: { nome: "Prata", cor: "text-slate-300" },
  GOLD: { nome: "Ouro", cor: "text-yellow-400" },
  PLATINUM: { nome: "Platina", cor: "text-teal-300" },
  EMERALD: { nome: "Esmeralda", cor: "text-emerald-400" },
  DIAMOND: { nome: "Diamante", cor: "text-sky-400" },
  MASTER: { nome: "Mestre", cor: "text-fuchsia-400" },
  GRANDMASTER: { nome: "Grão-Mestre", cor: "text-red-400" },
  CHALLENGER: { nome: "Desafiante", cor: "text-amber-300" },
};

// Mestre para cima não tem divisão (I, II, III, IV)
const SEM_DIVISAO = new Set(["MASTER", "GRANDMASTER", "CHALLENGER"]);

export function nomeElo(tier: string, divisao: string): string {
  const nome = ELOS[tier]?.nome ?? tier;
  return SEM_DIVISAO.has(tier) ? nome : `${nome} ${divisao}`;
}

export function corElo(tier: string): string {
  return ELOS[tier]?.cor ?? "text-zinc-300";
}

export function corWinrate(winrate: number): string {
  if (winrate >= 60) return "text-amber-300";
  if (winrate >= 50) return "text-sky-400";
  return "text-zinc-400";
}
