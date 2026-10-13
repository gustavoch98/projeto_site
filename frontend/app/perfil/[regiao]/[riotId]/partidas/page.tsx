import { Suspense } from "react";

import SecaoPartidas, { EsqueletoPartidas } from "@/components/partidas/SecaoPartidas";
import { lerPerfilDaUrl, type ParametrosPerfil } from "@/lib/perfil-url";

// Aba "Partidas": resumo das últimas 20 e o histórico completo.
// (Mesmo padrão da aba Campeões: params é lido dentro do <Suspense>.)
export default function AbaPartidas({ params }: PageProps<"/perfil/[regiao]/[riotId]/partidas">) {
  return (
    <section className="flex flex-col gap-3">
      <h2 className="sr-only">Partidas recentes</h2>
      <Suspense fallback={<EsqueletoPartidas />}>
        <Conteudo params={params} />
      </Suspense>
    </section>
  );
}

async function Conteudo({ params }: { params: Promise<ParametrosPerfil> }) {
  const { regiao, id } = await lerPerfilDaUrl(params);
  return <SecaoPartidas regiao={regiao} nome={id.nome} tag={id.tag} />;
}
