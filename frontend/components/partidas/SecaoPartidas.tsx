import { buscarPartidas } from "@/lib/api";
import { tabelaCampeoes, tabelaFeiticos, versaoAtual } from "@/lib/ddragon";
import { resumir } from "@/lib/partidas";

import LinhaPartida from "./LinhaPartida";
import ResumoPartidas from "./ResumoPartidas";

type Props = { regiao: string; nome: string; tag: string };

// Server Component assíncrono. A página o envolve em <Suspense>: enquanto ele espera
// a API (que pode levar alguns segundos buscando partidas na Riot), o resto da página
// já aparece, e aqui fica o esqueleto. Quando os dados chegam, o servidor "envia" este
// pedaço do HTML pela mesma conexão (streaming).
export default async function SecaoPartidas({ regiao, nome, tag }: Props) {
  const versao = await versaoAtual();
  const [partidas, campeoes, feiticos] = await Promise.all([
    buscarPartidas(regiao, nome, tag),
    tabelaCampeoes(versao),
    tabelaFeiticos(versao),
  ]);

  if (partidas === null) {
    return <Aviso texto="Não foi possível carregar as partidas agora. Tente atualizar a página." />;
  }
  if (partidas.length === 0) {
    return <Aviso texto="Nenhuma partida ranqueada recente." />;
  }

  const resumo = resumir(partidas);

  return (
    <div className="flex flex-col gap-4">
      {resumo && <ResumoPartidas resumo={resumo} campeoes={campeoes} />}
      <ul className="flex flex-col gap-2">
        {partidas.map((p) => (
          <LinhaPartida key={p.match_id} partida={p} versao={versao} campeoes={campeoes} feiticos={feiticos} />
        ))}
      </ul>
    </div>
  );
}

function Aviso({ texto }: { texto: string }) {
  return (
    <p className="rounded-xl border border-borda bg-painel p-5 text-center text-sm text-texto-fraco">{texto}</p>
  );
}

export function EsqueletoPartidas() {
  return (
    <div className="flex animate-pulse flex-col gap-2" aria-label="Carregando partidas">
      <div className="h-28 rounded-xl border border-borda bg-painel" />
      {Array.from({ length: 5 }, (_, i) => (
        <div key={i} className="h-16 rounded-lg border border-borda bg-painel" />
      ))}
    </div>
  );
}
