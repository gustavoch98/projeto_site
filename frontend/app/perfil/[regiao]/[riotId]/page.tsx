import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";

import BotaoAtualizar from "@/components/BotaoAtualizar";
import CardRanked from "@/components/CardRanked";
import SecaoPainel, { EsqueletoPainel } from "@/components/painel/SecaoPainel";
import SecaoPartidas, { EsqueletoPartidas } from "@/components/partidas/SecaoPartidas";
import TempoRelativo from "@/components/TempoRelativo";
import { buscarPerfil } from "@/lib/api";
import { urlIconePerfil, versaoAtual } from "@/lib/ddragon";
import { riotIdDaUrl } from "@/lib/riot-id";

const REGIOES_ATIVAS = ["br"];

type Props = PageProps<"/perfil/[regiao]/[riotId]">;

// Título da aba do navegador, ex.: "Hazze Gu#hazze · LoL Stats"
export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { riotId } = await params;
  const id = riotIdDaUrl(riotId);
  return { title: id ? `${id.nome}#${id.tag}` : "Perfil" };
}

// Server Component assíncrono: busca os dados NO SERVIDOR antes de gerar o HTML.
// Enquanto isso, o Next.js mostra o loading.tsx desta pasta.
export default async function PaginaPerfil({ params }: Props) {
  // No Next.js 16, params é uma Promise
  const { regiao, riotId } = await params;
  const id = riotIdDaUrl(riotId);
  if (!REGIOES_ATIVAS.includes(regiao) || id === null) notFound();

  const [resultado, versao] = await Promise.all([
    buscarPerfil(regiao, id.nome, id.tag),
    versaoAtual(),
  ]);

  if (resultado.tipo === "nao-encontrado") notFound(); // mostra o not-found.tsx

  if (resultado.tipo === "erro") {
    return (
      <div className="rounded-xl border border-red-900/60 bg-red-950/30 p-6 text-center">
        <p className="font-semibold text-red-300">{resultado.mensagem}</p>
        <Link
          href={`/perfil/${regiao}/${riotId}`}
          className="mt-4 inline-block text-sm text-destaque hover:underline"
        >
          Tentar novamente
        </Link>
      </div>
    );
  }

  const perfil = resultado.perfil;

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col gap-4 rounded-xl border border-borda bg-painel p-5 sm:flex-row sm:items-center">
        <div className="relative w-fit">
          <Image
            src={urlIconePerfil(versao, perfil.profile_icon_id)}
            alt="Ícone de perfil"
            width={88}
            height={88}
            priority
            className="rounded-2xl border-2 border-borda"
          />
          <span className="absolute -bottom-2 left-1/2 -translate-x-1/2 rounded-full border border-borda bg-fundo px-2 text-xs font-semibold">
            {perfil.summoner_level}
          </span>
        </div>

        <div className="flex-1">
          <h1 className="text-2xl font-bold">
            {perfil.game_name}
            <span className="text-texto-fraco"> #{perfil.tag_line}</span>
          </h1>
          <p className="mt-1 text-sm text-texto-fraco">
            {perfil.region.toUpperCase()} · Atualizado <TempoRelativo iso={perfil.updated_at} />
          </p>
        </div>

        <BotaoAtualizar regiao={regiao} nome={id.nome} tag={id.tag} />
      </header>

      <div className="grid gap-4 md:grid-cols-2">
        <CardRanked titulo="Ranqueada Solo/Duo" fila={perfil.solo} />
        <CardRanked titulo="Ranqueada Flex" fila={perfil.flex} />
      </div>

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-semibold">Painel</h2>
        <Suspense fallback={<EsqueletoPainel />}>
          <SecaoPainel regiao={regiao} nome={id.nome} tag={id.tag} />
        </Suspense>
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-semibold">Partidas recentes</h2>
        {/* O elo acima aparece na hora; as partidas chegam depois (streaming) */}
        <Suspense fallback={<EsqueletoPartidas />}>
          <SecaoPartidas regiao={regiao} nome={id.nome} tag={id.tag} />
        </Suspense>
      </section>
    </div>
  );
}
