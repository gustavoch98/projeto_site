import Image from "next/image";

import type { FilaRanked } from "@/lib/api";
import { urlEmblemaElo } from "@/lib/ddragon";
import { corElo, corWinrate, nomeElo } from "@/lib/ranked";

type Props = { titulo: string; fila: FilaRanked | null };

// Server Component: só exibe dados recebidos por "props" (parâmetros do componente).
export default function CardRanked({ titulo, fila }: Props) {
  return (
    <section className="rounded-xl border border-borda bg-painel p-5">
      <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-texto-fraco">
        {titulo}
      </h2>

      {fila === null ? (
        <div className="flex items-center gap-4">
          <div className="flex size-20 items-center justify-center rounded-full border-2 border-dashed border-borda text-2xl text-texto-fraco">
            ?
          </div>
          <p className="text-lg font-semibold text-texto-fraco">Unranked</p>
        </div>
      ) : (
        <div className="flex items-center gap-4">
          {/* O PNG original (2560x1440) tem muita borda transparente em volta do emblema:
              recortamos um quadrado (overflow-hidden) e ampliamos a imagem dentro dele. */}
          <div className="relative size-20 shrink-0 overflow-hidden">
            <Image
              src={urlEmblemaElo(fila.tier)}
              alt={`Emblema ${nomeElo(fila.tier, fila.rank)}`}
              fill
              sizes="240px"
              className="scale-[2.4] object-cover"
            />
          </div>
          <div className="flex-1">
            <p className={`text-xl font-bold ${corElo(fila.tier)}`}>
              {nomeElo(fila.tier, fila.rank)}
            </p>
            <p className="text-sm text-texto">{fila.league_points} PDL</p>
          </div>
          <div className="text-right text-sm">
            <p className="text-texto-fraco">
              {fila.wins}V {fila.losses}D
            </p>
            <p className={`font-semibold ${corWinrate(fila.winrate)}`}>
              {fila.winrate.toLocaleString("pt-BR")}% WR
            </p>
          </div>
        </div>
      )}
    </section>
  );
}
