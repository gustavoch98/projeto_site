import { Suspense } from "react";

import SecaoPainel, { EsqueletoPainel } from "@/components/painel/SecaoPainel";
import SecaoPartidas, { EsqueletoPartidas } from "@/components/partidas/SecaoPartidas";
import { lerPerfilDaUrl, type ParametrosPerfil } from "@/lib/perfil-url";

// Aba "Visão geral" (aba padrão): painel completo + as últimas partidas.
// O cabeçalho e os cards de elo vêm do layout.tsx desta pasta.
// (Mesmo padrão da aba Campeões: params é lido dentro do <Suspense>.)
export default function VisaoGeral({ params }: PageProps<"/perfil/[regiao]/[riotId]">) {
  return (
    <div className="flex flex-col gap-8">
      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-semibold">Painel</h2>
        <Suspense fallback={<EsqueletoPainel />}>
          <Painel params={params} />
        </Suspense>
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-semibold">Últimas partidas</h2>
        <Suspense fallback={<EsqueletoPartidas linhas={5} resumo={false} />}>
          <UltimasPartidas params={params} />
        </Suspense>
      </section>
    </div>
  );
}

async function Painel({ params }: { params: Promise<ParametrosPerfil> }) {
  const { regiao, id } = await lerPerfilDaUrl(params);
  return <SecaoPainel regiao={regiao} nome={id.nome} tag={id.tag} />;
}

async function UltimasPartidas({ params }: { params: Promise<ParametrosPerfil> }) {
  const { regiao, id, base } = await lerPerfilDaUrl(params);
  return <SecaoPartidas regiao={regiao} nome={id.nome} tag={id.tag} limite={5} verTodas={`${base}/partidas`} />;
}
