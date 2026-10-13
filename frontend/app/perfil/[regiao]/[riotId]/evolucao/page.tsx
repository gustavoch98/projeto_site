import { Suspense } from "react";

import SecaoEvolucao, { EsqueletoEvolucao } from "@/components/evolucao/SecaoEvolucao";
import { lerPerfilDaUrl, type ParametrosPerfil } from "@/lib/perfil-url";

// Aba "Evolução": saldo de vitórias, winrate móvel, sequências e PDL registrado (Solo/Duo).
// (Mesmo padrão das outras abas: params é lido dentro do <Suspense>.)
export default function AbaEvolucao({ params }: PageProps<"/perfil/[regiao]/[riotId]/evolucao">) {
  return (
    <Suspense fallback={<EsqueletoEvolucao />}>
      <Conteudo params={params} />
    </Suspense>
  );
}

async function Conteudo({ params }: { params: Promise<ParametrosPerfil> }) {
  const { regiao, id } = await lerPerfilDaUrl(params);
  return <SecaoEvolucao regiao={regiao} nome={id.nome} tag={id.tag} />;
}
