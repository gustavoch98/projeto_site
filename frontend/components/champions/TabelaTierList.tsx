import Image from "next/image";

import type { CampeaoTierList } from "@/lib/api";
import { porcentagem } from "@/lib/insights";
import { ROTAS } from "@/lib/partidas";

type Tabela = Record<number, { nome: string; imagem: string }>;

// Estilo de cada tier: S em destaque cheio, A com contorno, o resto vai esmaecendo
const ESTILO_TIER: Record<string, string> = {
  S: "bg-destaque text-fundo",
  A: "border-2 border-destaque text-destaque",
  B: "border-2 border-texto text-texto",
  C: "border border-borda text-texto-fraco",
  D: "border border-borda text-texto-fraco opacity-70",
};

const umaCasa = (v: number) => `${(v * 100).toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`;

export default function TabelaTierList({ campeoes, tabela }: { campeoes: CampeaoTierList[]; tabela: Tabela }) {
  return (
    // overflow-x-auto: no celular a tabela rola de lado em vez de espremer as colunas
    <div className="overflow-x-auto border border-borda bg-painel">
      <table className="w-full min-w-[620px] text-sm">
        <thead className="text-left font-mono text-[11px] uppercase text-texto-fraco">
          <tr className="border-b border-borda">
            <th className="w-16 px-4 py-3 font-bold">Tier</th>
            <th className="px-3 py-3 font-bold">Campeão</th>
            <th className="px-3 py-3 font-bold">Rota</th>
            <th className="px-3 py-3 text-right font-bold">Vitórias</th>
            <th className="px-3 py-3 text-right font-bold">Escolha</th>
            <th className="px-3 py-3 text-right font-bold">Ban</th>
            <th className="px-4 py-3 text-right font-bold">Partidas</th>
          </tr>
        </thead>
        <tbody>
          {campeoes.map((c) => {
            const info = tabela[c.champion_id];
            return (
              <tr key={`${c.champion_id}-${c.rota}`} className="border-b border-borda/60 last:border-0">
                <td className="px-4 py-2">
                  {c.tier ? (
                    <span className={`inline-flex size-8 items-center justify-center font-extrabold ${ESTILO_TIER[c.tier]}`}>
                      {c.tier}
                    </span>
                  ) : (
                    <span className="inline-flex size-8 items-center justify-center text-texto-fraco">–</span>
                  )}
                </td>
                <td className="px-3 py-2">
                  <div className="flex items-center gap-2">
                    {info && <Image src={info.imagem} alt="" width={32} height={32} />}
                    <span className="font-semibold">{info?.nome ?? c.champion_name}</span>
                  </div>
                </td>
                <td className="px-3 py-2 text-texto-fraco">{ROTAS[c.rota] ?? c.rota}</td>
                <td className="px-3 py-2 text-right font-mono">{porcentagem(c.winrate)}</td>
                <td className="px-3 py-2 text-right font-mono text-texto-fraco">{umaCasa(c.pickrate)}</td>
                <td className="px-3 py-2 text-right font-mono text-texto-fraco">{umaCasa(c.banrate)}</td>
                <td className="px-4 py-2 text-right font-mono text-texto-fraco">{c.jogos}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
