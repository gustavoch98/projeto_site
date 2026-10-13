// Imagens estáticas do jogo. Não consomem o limite da API da Riot.
// - Data Dragon (oficial da Riot): ícones de perfil, campeões, itens.
// - CommunityDragon (mantido pela comunidade): emblemas de elo, que o Data Dragon não tem.

import { cacheLife } from "next/cache";

const VERSAO_RESERVA = "16.20.1";

/** Versão atual do jogo (ex.: "16.20.1"). Guardada em cache por algumas horas. */
export async function versaoAtual(): Promise<string> {
  "use cache";
  cacheLife("hours");
  try {
    const resposta = await fetch("https://ddragon.leagueoflegends.com/api/versions.json");
    const versoes: string[] = await resposta.json();
    return versoes[0] ?? VERSAO_RESERVA;
  } catch {
    return VERSAO_RESERVA;
  }
}

export function urlIconePerfil(versao: string, iconeId: number): string {
  return `https://ddragon.leagueoflegends.com/cdn/${versao}/img/profileicon/${iconeId}.png`;
}

export function urlEmblemaElo(tier: string): string {
  return `https://raw.communitydragon.org/latest/plugins/rcp-fe-lol-static-assets/global/default/images/ranked-emblem/emblem-${tier.toLowerCase()}.png`;
}
