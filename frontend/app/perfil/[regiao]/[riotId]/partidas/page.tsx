import { Suspense } from "react";

import SecaoPartidas, { EsqueletoPartidas } from "@/components/partidas/SecaoPartidas";
import { lerPerfilDaUrl } from "@/lib/perfil-url";

// Aba "Partidas": resumo das últimas 20 e o histórico completo.
export default async function AbaPartidas({ params }: PageProps<"/perfil/[regiao]/[riotId]/partidas">) {
  const { regiao, id } = await lerPerfilDaUrl(params);

  return (
    <section className="flex flex-col gap-3">
      <h2 className="sr-only">Partidas recentes</h2>
      <Suspense fallback={<EsqueletoPartidas />}>
        <SecaoPartidas regiao={regiao} nome={id.nome} tag={id.tag} />
      </Suspense>
    </section>
  );
}
