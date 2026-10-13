import { Suspense } from "react";

import SecaoPainel, { EsqueletoPainel } from "@/components/painel/SecaoPainel";
import SecaoPartidas, { EsqueletoPartidas } from "@/components/partidas/SecaoPartidas";
import { lerPerfilDaUrl } from "@/lib/perfil-url";

// Aba "Visão geral" (aba padrão): painel completo + as últimas partidas.
// O cabeçalho e os cards de elo vêm do layout.tsx desta pasta.
export default async function VisaoGeral({ params }: PageProps<"/perfil/[regiao]/[riotId]">) {
  const { regiao, id, base } = await lerPerfilDaUrl(params);

  return (
    <div className="flex flex-col gap-8">
      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-semibold">Painel</h2>
        <Suspense fallback={<EsqueletoPainel />}>
          <SecaoPainel regiao={regiao} nome={id.nome} tag={id.tag} />
        </Suspense>
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-semibold">Últimas partidas</h2>
        <Suspense fallback={<EsqueletoPartidas linhas={5} resumo={false} />}>
          <SecaoPartidas regiao={regiao} nome={id.nome} tag={id.tag} limite={5} verTodas={`${base}/partidas`} />
        </Suspense>
      </section>
    </div>
  );
}
