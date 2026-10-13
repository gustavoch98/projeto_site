// Regras da aba de campeões (funções puras, sem tela).

import type { EstatisticasCampeao } from "@/lib/api";

/**
 * Campeão "mais forte": entre os que têm partidas suficientes, o de maior LIMITE INFERIOR
 * do intervalo de confiança do winrate (a mesma régua do painel de horário: 75% em 12 jogos
 * não passa na frente de 71% em 21 só por sorte).
 */
export function maisForte(campeoes: EstatisticasCampeao[], minimo: number): EstatisticasCampeao | null {
  const elegiveis = campeoes.filter((c) => c.jogos >= minimo);
  if (elegiveis.length === 0) return null;
  return elegiveis.reduce((a, b) => (b.ic_baixo > a.ic_baixo ? b : a));
}

/** Campeão mais perto de atingir o mínimo (para o convite "faltam N partidas"). */
export function maisPertoDoMinimo(campeoes: EstatisticasCampeao[], minimo: number): EstatisticasCampeao | null {
  const abaixo = campeoes.filter((c) => c.jogos < minimo);
  return abaixo.length ? abaixo.reduce((a, b) => (b.jogos > a.jogos ? b : a)) : null;
}

export type Comparacao = { texto: string; cor: string };

/**
 * Compara uma métrica do campeão com a média geral do jogador.
 * Diferenças menores que 5% são tratadas como "igual à média" (=).
 */
export function compararComMedia(valor: number, media: number, casas = 1): Comparacao {
  const diferenca = valor - media;
  if (media === 0 || Math.abs(diferenca) / media < 0.05) {
    return { texto: "=", cor: "text-texto-fraco" };
  }
  const formatado = Math.abs(diferenca).toLocaleString("pt-BR", { maximumFractionDigits: casas });
  return diferenca > 0
    ? { texto: `▲ ${formatado}`, cor: "text-sky-400" }
    : { texto: `▼ ${formatado}`, cor: "text-red-400" };
}

export const decimal = (v: number, casas = 1) => v.toLocaleString("pt-BR", { maximumFractionDigits: casas });
