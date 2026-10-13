import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";

import AbasPerfil from "@/components/AbasPerfil";
import BotaoAtualizar from "@/components/BotaoAtualizar";
import CardRanked from "@/components/CardRanked";
import TempoRelativo from "@/components/TempoRelativo";
import { buscarPerfil } from "@/lib/api";
import { urlIconePerfil, versaoAtual } from "@/lib/ddragon";
import { lerPerfilDaUrl } from "@/lib/perfil-url";
import { riotIdDaUrl } from "@/lib/riot-id";

type Props = LayoutProps<"/perfil/[regiao]/[riotId]">;

// Título da aba do navegador, ex.: "Hazze Gu#hazze · Raio"
export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { riotId } = await params;
  const id = riotIdDaUrl(riotId);
  return { title: id ? `${id.nome}#${id.tag}` : "Perfil" };
}

// Layout do perfil: a parte FIXA (cabeçalho, cards de elo e abas). Ao trocar de aba,
// o Next.js mantém este layout na tela e só troca o {children}, que é a página da aba.
//
// Os arquivos loading/not-found/error ficam na pasta de cima ([regiao]): os da mesma
// pasta não "enxergam" o layout, só o que está abaixo dele.
export default async function LayoutPerfil({ params, children }: Props) {
  const { regiao, riotId, id, base } = await lerPerfilDaUrl(params);

  const [resultado, versao] = await Promise.all([
    buscarPerfil(regiao, id.nome, id.tag),
    versaoAtual(),
  ]);

  if (resultado.tipo === "nao-encontrado") notFound();

  if (resultado.tipo === "erro") {
    return (
      <div className="rounded-xl border border-erro/50 bg-erro/10 p-6 text-center">
        <p className="font-semibold text-erro">{resultado.mensagem}</p>
        <Link href={`/perfil/${regiao}/${riotId}`} className="mt-4 inline-block text-sm text-destaque hover:underline">
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

      <AbasPerfil base={base} />

      {children}
    </div>
  );
}
