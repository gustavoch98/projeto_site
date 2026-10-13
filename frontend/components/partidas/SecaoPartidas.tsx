import Link from "next/link";

import { buscarPartidas } from "@/lib/api";
import { tabelaCampeoes, tabelaFeiticos, versaoAtual } from "@/lib/ddragon";
import { resumir } from "@/lib/partidas";

import LinhaPartida from "./LinhaPartida";
import ResumoPartidas from "./ResumoPartidas";

type Props = {
  regiao: string;
  nome: string;
  tag: string;
  limite?: number; // mostra só as N mais recentes, sem o resumo (usado na Visão geral)
  verTodas?: string; // link para a aba com o histórico completo
};

// Server Component assíncrono. A página o envolve em <Suspense>: enquanto ele espera
// a API (que pode levar alguns segundos buscando partidas na Riot), o resto da página
// já aparece, e aqui fica o esqueleto. Quando os dados chegam, o servidor "envia" este
// pedaço do HTML pela mesma conexão (streaming).
export default async function SecaoPartidas({ regiao, nome, tag, limite, verTodas }: Props) {
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

  const resumo = limite === undefined ? resumir(partidas) : null;
  const visiveis = limite === undefined ? partidas : partidas.slice(0, limite);

  return (
    <div className="flex flex-col gap-4">
      {resumo && <ResumoPartidas resumo={resumo} campeoes={campeoes} />}
      <ul className="flex flex-col gap-2">
        {visiveis.map((p) => (
          <LinhaPartida key={p.match_id} partida={p} versao={versao} campeoes={campeoes} feiticos={feiticos} />
        ))}
      </ul>
      {verTodas && (
        <Link
          href={verTodas}
          className="self-center rounded-lg border border-borda px-4 py-2 text-sm font-semibold text-texto-fraco transition hover:border-destaque hover:text-texto"
        >
          Ver todas as partidas
        </Link>
      )}
    </div>
  );
}

function Aviso({ texto }: { texto: string }) {
  return (
    <p className="rounded-xl border border-borda bg-painel p-5 text-center text-sm text-texto-fraco">{texto}</p>
  );
}

export function EsqueletoPartidas({ linhas = 5, resumo = true }: { linhas?: number; resumo?: boolean }) {
  return (
    <div className="flex animate-pulse flex-col gap-2" aria-label="Carregando partidas">
      {resumo && <div className="h-28 rounded-xl border border-borda bg-painel" />}
      {Array.from({ length: linhas }, (_, i) => (
        <div key={i} className="h-16 rounded-lg border border-borda bg-painel" />
      ))}
    </div>
  );
}
