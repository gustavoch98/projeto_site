import Image from "next/image";

import type { EstatisticasCampeao } from "@/lib/api";
import { compararComMedia, decimal } from "@/lib/campeoes";
import { porcentagem } from "@/lib/insights";
import { ROTAS } from "@/lib/partidas";
import { corWinrate } from "@/lib/ranked";

type Props = {
  campeao: EstatisticasCampeao;
  geral: EstatisticasCampeao;
  minimo: number;
  nome: string;
  imagem: string | null;
};

// Card de um dos campeões mais jogados. Abaixo do mínimo de partidas, os números aparecem
// esmaecidos e uma barra mostra quanto falta para a análise completa.
export default function CardCampeao({ campeao: c, geral, minimo, nome, imagem }: Props) {
  const completo = c.jogos >= minimo;

  const metricas = [
    { rotulo: "KDA", valor: decimal(c.kda, 2), comparacao: compararComMedia(c.kda, geral.kda, 2) },
    { rotulo: "CS/min", valor: decimal(c.cs_por_minuto), comparacao: compararComMedia(c.cs_por_minuto, geral.cs_por_minuto) },
    { rotulo: "Dano/min", valor: decimal(c.dano_por_minuto, 0), comparacao: compararComMedia(c.dano_por_minuto, geral.dano_por_minuto, 0) },
    { rotulo: "Visão/min", valor: decimal(c.visao_por_minuto, 2), comparacao: compararComMedia(c.visao_por_minuto, geral.visao_por_minuto, 2) },
  ];

  return (
    <article className="flex min-w-0 flex-col gap-3 rounded-xl border border-borda bg-painel p-4">
      <header className="flex items-center gap-3">
        {imagem && <Image src={imagem} alt="" width={48} height={48} className="rounded-lg" />}
        <div className="min-w-0 flex-1">
          <h3 className="truncate font-semibold">{nome}</h3>
          <p className="text-xs text-texto-fraco">
            {c.jogos} partidas{c.rota_principal ? ` · ${ROTAS[c.rota_principal] ?? c.rota_principal}` : ""}
          </p>
        </div>
        <div className="text-right">
          <p className={`text-xl font-bold ${completo ? corWinrate(Math.round(c.winrate * 100)) : "text-texto-fraco"}`}>
            {porcentagem(c.winrate)}
          </p>
          <p className="text-[11px] text-texto-fraco">
            {c.vitorias}V {c.jogos - c.vitorias}D
          </p>
        </div>
      </header>

      <p className="text-sm">
        {decimal(c.abates)} / <span className="text-texto-fraco">{decimal(c.mortes)}</span> / {decimal(c.assistencias)}
        <span className="text-texto-fraco"> por partida</span>
      </p>

      <dl className={`grid grid-cols-2 gap-x-3 gap-y-2 text-sm ${completo ? "" : "opacity-60"}`}>
        {metricas.map((m) => (
          <div key={m.rotulo}>
            <dt className="text-[11px] text-texto-fraco">{m.rotulo}</dt>
            <dd className="font-semibold">
              {m.valor} <span className={`text-[11px] font-normal ${m.comparacao.cor}`}>{m.comparacao.texto}</span>
            </dd>
          </div>
        ))}
      </dl>

      {!completo && (
        <div className="mt-auto">
          <div className="h-1.5 overflow-hidden rounded-full bg-painel-claro">
            <div className="h-full bg-destaque" style={{ width: `${(100 * c.jogos) / minimo}%` }} />
          </div>
          <p className="mt-1 text-[11px] text-texto-fraco">
            Faltam {minimo - c.jogos} {minimo - c.jogos === 1 ? "partida" : "partidas"} para a análise completa
          </p>
        </div>
      )}
    </article>
  );
}
