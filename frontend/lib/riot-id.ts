// Conversões entre o Riot ID digitado ("Nome#TAG") e o formato usado na URL ("Nome-TAG").

export type RiotId = { nome: string; tag: string };

/** Valida e normaliza o texto digitado na busca. Devolve o Riot ID ou uma mensagem de erro. */
export function lerRiotId(texto: string): RiotId | { erro: string } {
  const partes = texto.split("#");
  if (partes.length !== 2) {
    return { erro: "Use o formato Nome#TAG (ex.: Hazze Gu#hazze)." };
  }
  const nome = partes[0].replace(/\s+/g, " ").trim();
  const tag = partes[1].replace(/\s+/g, "");
  if (nome.length < 1 || nome.length > 16) {
    return { erro: "O nome deve ter entre 1 e 16 caracteres." };
  }
  if (!/^[\p{L}\p{N}]{1,5}$/u.test(tag)) {
    return { erro: "A TAG deve ter de 1 a 5 letras ou números." };
  }
  return { nome, tag };
}

/** "Hazze Gu" + "hazze" -> "Hazze%20Gu-hazze" (pronto para usar na URL). */
export function riotIdParaUrl({ nome, tag }: RiotId): string {
  return encodeURIComponent(`${nome}-${tag}`);
}

/**
 * Faz o caminho inverso. Usa o ÚLTIMO hífen como separador, porque a TAG
 * só tem letras e números, mas o nome pode conter hífen.
 */
export function riotIdDaUrl(segmento: string): RiotId | null {
  const texto = decodeURIComponent(segmento);
  const posicao = texto.lastIndexOf("-");
  if (posicao <= 0 || posicao === texto.length - 1) return null;
  return { nome: texto.slice(0, posicao), tag: texto.slice(posicao + 1) };
}
