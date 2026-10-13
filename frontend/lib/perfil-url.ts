// Leitura dos parâmetros da URL do perfil (/perfil/[regiao]/[riotId]), usada pelo layout e
// pelas abas. URL inválida ou região não suportada -> página de "não encontrado".

import { notFound } from "next/navigation";

import { riotIdDaUrl, type RiotId } from "@/lib/riot-id";

const REGIOES_ATIVAS = ["br"];

export type ParametrosPerfil = { regiao: string; riotId: string };

export async function lerPerfilDaUrl(
  params: Promise<ParametrosPerfil>,
): Promise<{ regiao: string; riotId: string; id: RiotId; base: string }> {
  // No Next.js 16, params é uma Promise
  const { regiao, riotId } = await params;
  const id = riotIdDaUrl(riotId);
  if (!REGIOES_ATIVAS.includes(regiao) || id === null) notFound();
  // "base" = endereço da aba padrão; as outras abas ficam abaixo dele (base + "/partidas")
  return { regiao, riotId, id, base: `/perfil/${regiao}/${riotId}` };
}
