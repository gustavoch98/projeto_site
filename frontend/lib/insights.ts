// Regras para transformar os números do painel em frases (funções puras, sem tela).

import type { FaixaDesempenho } from "@/lib/api";

// Faixas com menos partidas que isso não entram na comparação (aparecem como "poucos dados")
export const MINIMO_POR_FAIXA = 10;
// Abaixo disso, não tiramos conclusão nenhuma
export const MINIMO_TOTAL = 20;

export type Comparacao = {
  melhor: FaixaDesempenho;
  pior: FaixaDesempenho;
  diferencaPontos: number; // em pontos percentuais
  consistente: boolean; // true = dificilmente é só acaso
};

export function confiavel(f: FaixaDesempenho): boolean {
  return f.jogos >= MINIMO_POR_FAIXA && f.winrate !== null;
}

/**
 * Teste z para a diferença entre duas proporções (bicaudal, 5%).
 * Responde: "se o jogador rendesse igual nas duas faixas, seria raro ver uma diferença dessas?"
 */
function diferencaConsistente(a: FaixaDesempenho, b: FaixaDesempenho): boolean {
  const p = (a.vitorias + b.vitorias) / (a.jogos + b.jogos);
  const erro = Math.sqrt(p * (1 - p) * (1 / a.jogos + 1 / b.jogos));
  if (erro === 0) return false;
  const z = (a.vitorias / a.jogos - b.vitorias / b.jogos) / erro;
  return Math.abs(z) > 1.96;
}

/**
 * Melhor e pior faixa entre as que têm partidas suficientes.
 *
 * Não usamos o winrate "cru": com poucas partidas os extremos aparecem por acaso
 * (64% em 14 jogos "venceria" 60% em 111). Por isso:
 * - melhor = maior LIMITE INFERIOR do intervalo de confiança (boa mesmo no cenário pessimista);
 * - pior = menor LIMITE SUPERIOR (ruim mesmo no cenário otimista).
 */
export function comparar(faixas: FaixaDesempenho[]): Comparacao | null {
  const validas = faixas.filter(confiavel);
  if (validas.length < 2) return null;
  const melhor = validas.reduce((a, b) => (b.ic_baixo! > a.ic_baixo! ? b : a));
  const pior = validas.reduce((a, b) => (b.ic_alto! < a.ic_alto! ? b : a));
  if (melhor === pior) return null;
  return {
    melhor,
    pior,
    diferencaPontos: Math.round((melhor.winrate! - pior.winrate!) * 100),
    consistente: diferencaConsistente(melhor, pior),
  };
}

/** "Tarde (12h–17h)" -> { nome: "Tarde", detalhe: "12h–17h" } */
export function separarRotulo(rotulo: string): { nome: string; detalhe: string | null } {
  const [nome, resto] = rotulo.split(" (");
  return { nome, detalhe: resto ? resto.replace(")", "") : null };
}

// Como cada período aparece numa frase: "você rende mais à tarde", "de manhã"...
const EXPRESSAO_PERIODO: Record<string, string> = {
  madrugada: "de madrugada",
  manha: "de manhã",
  tarde: "à tarde",
  noite: "à noite",
};

export function expressaoPeriodo(f: FaixaDesempenho): string {
  return EXPRESSAO_PERIODO[f.chave] ?? separarRotulo(f.rotulo).nome.toLowerCase();
}

export const porcentagem = (v: number) => `${Math.round(v * 100)}%`;
