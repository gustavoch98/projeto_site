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

// --- Tabelas de tradução (número -> nome/imagem), em português -----------------

type Traducao = { nome: string; imagem: string };
type ArquivoDados = { data: Record<string, { key: string; id: string; name: string }> };

async function baixarTabela(versao: string, arquivo: string): Promise<Record<number, Traducao>> {
  "use cache";
  cacheLife("hours");
  const resposta = await fetch(`https://ddragon.leagueoflegends.com/cdn/${versao}/data/pt_BR/${arquivo}`);
  const dados: ArquivoDados = await resposta.json();
  return Object.fromEntries(
    Object.values(dados.data).map((x) => [Number(x.key), { nome: x.name, imagem: x.id }]),
  );
}

/** championId (ex.: 62) -> { nome: "Wukong", imagem: ".../champion/MonkeyKing.png" } */
export async function tabelaCampeoes(versao: string): Promise<Record<number, Traducao>> {
  const tabela = await baixarTabela(versao, "champion.json");
  return Object.fromEntries(
    Object.entries(tabela).map(([k, v]) => [
      k,
      { nome: v.nome, imagem: `https://ddragon.leagueoflegends.com/cdn/${versao}/img/champion/${v.imagem}.png` },
    ]),
  );
}

/** summonerId (ex.: 4) -> { nome: "Flash", imagem: ".../spell/SummonerFlash.png" } */
export async function tabelaFeiticos(versao: string): Promise<Record<number, Traducao>> {
  const tabela = await baixarTabela(versao, "summoner.json");
  return Object.fromEntries(
    Object.entries(tabela).map(([k, v]) => [
      k,
      { nome: v.nome, imagem: `https://ddragon.leagueoflegends.com/cdn/${versao}/img/spell/${v.imagem}.png` },
    ]),
  );
}

export function urlItem(versao: string, itemId: number): string {
  return `https://ddragon.leagueoflegends.com/cdn/${versao}/img/item/${itemId}.png`;
}
