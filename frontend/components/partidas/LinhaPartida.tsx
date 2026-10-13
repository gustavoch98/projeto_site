import Image from "next/image";

import TempoRelativo from "@/components/TempoRelativo";
import type { Partida } from "@/lib/api";
import { urlItem } from "@/lib/ddragon";
import { FILAS, formatarDuracao, formatarKda } from "@/lib/partidas";

type Tabela = Record<number, { nome: string; imagem: string }>;
type Props = { partida: Partida; versao: string; campeoes: Tabela; feiticos: Tabela };

// Cores por resultado: limão = vitória, branco = derrota, cinza = remake (sem vermelho/verde)
function estilo(p: Partida) {
  if (p.remake) return { borda: "border-l-neutro", texto: "text-texto-fraco", rotulo: "Remake" };
  if (p.win) return { borda: "border-l-destaque", texto: "text-destaque", rotulo: "Vitória" };
  return { borda: "border-l-texto-fraco", texto: "text-texto", rotulo: "Derrota" };
}

export default function LinhaPartida({ partida: p, versao, campeoes, feiticos }: Props) {
  const e = estilo(p);
  const campeao = campeoes[p.champion_id];
  const minutos = p.game_duration / 60;

  return (
    <li
      className={`flex flex-wrap items-center gap-x-4 gap-y-2 rounded-lg border border-borda border-l-4 bg-painel px-3 py-2 ${e.borda}`}
    >
      {/* Fila, resultado e quando foi */}
      <div className="w-28 text-xs">
        <p className="font-semibold text-texto">{FILAS[p.queue_id] ?? "Ranqueada"}</p>
        <p className={`font-semibold ${e.texto}`}>{e.rotulo}</p>
        <p className="text-texto-fraco">
          {formatarDuracao(p.game_duration)} · <TempoRelativo iso={p.game_start} />
        </p>
      </div>

      {/* Campeão e feitiços */}
      <div className="flex items-center gap-1">
        {campeao && (
          <Image
            src={campeao.imagem}
            alt={campeao.nome}
            title={campeao.nome}
            width={44}
            height={44}
            className="rounded-lg"
          />
        )}
        <div className="flex flex-col gap-0.5">
          {p.summoner_spells.map((id, i) =>
            feiticos[id] ? (
              <Image
                key={i}
                src={feiticos[id].imagem}
                alt={feiticos[id].nome}
                title={feiticos[id].nome}
                width={20}
                height={20}
                className="rounded"
              />
            ) : (
              <span key={i} className="size-5 rounded bg-painel-claro" />
            ),
          )}
        </div>
      </div>

      {/* K/D/A */}
      <div className="w-24 text-center">
        <p className="font-semibold">
          {p.kills} / <span className="text-texto-fraco">{p.deaths}</span> / {p.assists}
        </p>
        <p className="text-xs text-texto-fraco">{formatarKda(p.kda)} KDA</p>
      </div>

      {/* Farm, visão e participação */}
      <div className="w-28 text-xs text-texto-fraco">
        <p>
          {p.cs} CS ({p.cs_per_minute.toLocaleString("pt-BR")}/min)
        </p>
        <p>Visão {(p.vision_score / minutos).toLocaleString("pt-BR", { maximumFractionDigits: 1 })}/min</p>
        {p.kill_participation !== null && <p>Part. abates {Math.round(p.kill_participation * 100)}%</p>}
      </div>

      {/* Itens (o 7º espaço é o amuleto/sentinela) */}
      <div className="flex gap-0.5">
        {p.items.map((id, i) =>
          id ? (
            <Image key={i} src={urlItem(versao, id)} alt="" width={26} height={26} className="rounded" />
          ) : (
            <span key={i} className="size-[26px] rounded bg-painel-claro" />
          ),
        )}
      </div>
    </li>
  );
}
