import { Suspense } from "react";

import SecaoCampeoes, { EsqueletoCampeoes } from "@/components/campeoes/SecaoCampeoes";
import { lerPerfilDaUrl, type ParametrosPerfil } from "@/lib/perfil-url";

// Aba "Campeões": desempenho com cada campeão, comparado à média geral do jogador.
//
// A página não lê a URL (params) diretamente: passa a Promise para dentro do <Suspense>.
// Assim o Next.js mostra o esqueleto na hora ao trocar de aba ("navegação instantânea").
export default function AbaCampeoes({ params }: PageProps<"/perfil/[regiao]/[riotId]/campeoes">) {
  return (
    <Suspense fallback={<EsqueletoCampeoes />}>
      <Conteudo params={params} />
    </Suspense>
  );
}

async function Conteudo({ params }: { params: Promise<ParametrosPerfil> }) {
  const { regiao, id } = await lerPerfilDaUrl(params);
  return <SecaoCampeoes regiao={regiao} nome={id.nome} tag={id.tag} />;
}
