// Conversões entre o Riot ID digitado ("Nome#TAG") e o formato usado na URL ("Nome-TAG").

export type RiotId = { nome: string; tag: string };

// Quando a pessoa digita só o nome, tentamos a TAG mais comum do servidor brasileiro
export const TAG_PADRAO = "BR1";

/** Separa o que foi digitado em nome e TAG (a TAG pode estar vazia), sem validar. */
export function separarTexto(texto: string): { nome: string; tag: string } {
  const [nome, tag = ""] = texto.split("#");
  return { nome: nome.replace(/\s+/g, " ").trim(), tag: tag.replace(/\s+/g, "") };
}

/** Valida e normaliza o texto digitado na busca. Devolve o Riot ID ou uma mensagem de erro. */
export function lerRiotId(texto: string): RiotId | { erro: string } {
  if (texto.split("#").length > 2) {
    return { erro: "Use o formato Nome#TAG (ex.: Hazze Gu#hazze)." };
  }
  const { nome, tag } = separarTexto(texto);
  if (nome.length < 1 || nome.length > 16) {
    return { erro: "O nome deve ter entre 1 e 16 caracteres." };
  }
  if (tag === "") {
    return { nome, tag: TAG_PADRAO };
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
