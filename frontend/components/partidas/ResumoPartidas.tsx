import Image from "next/image";

import { corWinrate } from "@/lib/ranked";
import { formatarKda, ROTAS, type Resumo } from "@/lib/partidas";

type Campeoes = Record<number, { nome: string; imagem: string }>;

const umaCasa = (n: number) => n.toLocaleString("pt-BR", { maximumFractionDigits: 1 });

export default function ResumoPartidas({ resumo, campeoes }: { resumo: Resumo; campeoes: Campeoes }) {
  return (
    <section className="grid gap-4 rounded-xl border border-borda bg-painel p-5 sm:grid-cols-3">
      <div>
        <p className="text-xs text-texto-fraco">
          Últimas {resumo.jogos} partidas · {resumo.vitorias}V {resumo.derrotas}D
        </p>
        <p className={`text-3xl font-bold ${corWinrate(resumo.winrate)}`}>{resumo.winrate}%</p>
        <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-neutro">
          <div className="h-full bg-destaque" style={{ width: `${resumo.winrate}%` }} />
        </div>
      </div>

      <div>
        <p className="text-xs text-texto-fraco">Média por partida</p>
        <p className="text-lg font-semibold">
          {umaCasa(resumo.abates)} / <span className="text-texto-fraco">{umaCasa(resumo.mortes)}</span> /{" "}
          {umaCasa(resumo.assistencias)}
        </p>
        <p className="text-sm text-texto-fraco">
          KDA <span className="text-texto">{formatarKda(resumo.kda)}</span> · CS/min{" "}
          <span className="text-texto">{umaCasa(resumo.csPorMinuto)}</span>
        </p>
        <p className="mt-1 text-xs text-texto-fraco">
          {resumo.rotas
            .slice(0, 2)
            .map((r) => `${ROTAS[r.rota] ?? r.rota} ${Math.round((100 * r.jogos) / resumo.jogos)}%`)
            .join(" · ")}
        </p>
      </div>

      <ul className="flex flex-col gap-2">
        {resumo.campeoes.map((c) => {
          const campeao = campeoes[c.championId];
          const wr = Math.round((100 * c.vitorias) / c.jogos);
          return (
            <li key={c.championId} className="flex items-center gap-2 text-sm">
              {campeao && (
                <Image src={campeao.imagem} alt="" width={28} height={28} className="rounded-full" />
              )}
              <span className="flex-1 truncate">{campeao?.nome ?? c.championId}</span>
              <span className={corWinrate(wr)}>{wr}%</span>
              <span className="w-16 text-right text-xs text-texto-fraco">
                {c.vitorias}V {c.jogos - c.vitorias}D
              </span>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
