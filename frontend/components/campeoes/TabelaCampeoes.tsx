import Image from "next/image";

import type { EstatisticasCampeao } from "@/lib/api";
import { decimal } from "@/lib/campeoes";
import { porcentagem } from "@/lib/insights";
import { corWinrate } from "@/lib/ranked";

type Tabela = Record<number, { nome: string; imagem: string }>;
type Props = { campeoes: EstatisticasCampeao[]; tabela: Tabela; minimo: number };

// Todos os campeões. No celular a tabela rola de lado (overflow-x-auto) em vez de espremer as colunas.
export default function TabelaCampeoes({ campeoes, tabela, minimo }: Props) {
  return (
    <div className="overflow-x-auto rounded-xl border border-borda bg-painel">
      <table className="w-full min-w-[640px] text-sm">
        <thead className="text-left text-[11px] uppercase tracking-wide text-texto-fraco">
          <tr className="border-b border-borda">
            <th className="px-4 py-3 font-semibold">Campeão</th>
            <th className="px-3 py-3 text-right font-semibold">Partidas</th>
            <th className="px-3 py-3 text-right font-semibold">Vitórias</th>
            <th className="px-3 py-3 text-right font-semibold">KDA</th>
            <th className="px-3 py-3 text-right font-semibold">K / D / A</th>
            <th className="px-3 py-3 text-right font-semibold">CS/min</th>
            <th className="px-4 py-3 text-right font-semibold">Dano/min</th>
          </tr>
        </thead>
        <tbody>
          {campeoes.map((c) => {
            const info = c.champion_id !== null ? tabela[c.champion_id] : undefined;
            const completo = c.jogos >= minimo;
            return (
              <tr key={c.champion_id} className="border-b border-borda/60 last:border-0">
                <td className="px-4 py-2">
                  <div className="flex items-center gap-2">
                    {info && <Image src={info.imagem} alt="" width={28} height={28} className="rounded" />}
                    <span className="truncate">{info?.nome ?? c.champion_name}</span>
                  </div>
                </td>
                <td className="px-3 py-2 text-right">{c.jogos}</td>
                <td className={`px-3 py-2 text-right font-semibold ${completo ? corWinrate(Math.round(c.winrate * 100)) : "text-texto-fraco"}`}>
                  {porcentagem(c.winrate)}
                </td>
                <td className="px-3 py-2 text-right">{decimal(c.kda, 2)}</td>
                <td className="px-3 py-2 text-right text-texto-fraco">
                  {decimal(c.abates)} / {decimal(c.mortes)} / {decimal(c.assistencias)}
                </td>
                <td className="px-3 py-2 text-right">{decimal(c.cs_por_minuto)}</td>
                <td className="px-4 py-2 text-right">{decimal(c.dano_por_minuto, 0)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
