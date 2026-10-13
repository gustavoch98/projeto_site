import Image from "next/image";

import { buscarCampeoes } from "@/lib/api";
import { decimal, maisForte, maisPertoDoMinimo } from "@/lib/campeoes";
import { tabelaCampeoes, versaoAtual } from "@/lib/ddragon";
import { porcentagem } from "@/lib/insights";

import CardCampeao from "./CardCampeao";
import TabelaCampeoes from "./TabelaCampeoes";

type Props = { regiao: string; nome: string; tag: string };

const QUANTIDADE_EM_DESTAQUE = 5;

export default async function SecaoCampeoes({ regiao, nome, tag }: Props) {
  const versao = await versaoAtual();
  const [dados, tabela] = await Promise.all([buscarCampeoes(regiao, nome, tag), tabelaCampeoes(versao)]);

  if (dados === null) return <Aviso texto="Não foi possível carregar os campeões agora." />;
  if (dados.geral === null || dados.campeoes.length === 0) {
    return (
      <Aviso
        texto={
          dados.coletando_historico
            ? "Buscando o histórico de partidas. Atualize a página em alguns minutos."
            : "Nenhuma partida ranqueada recente."
        }
      />
    );
  }

  const { campeoes, geral, minimo_partidas: minimo } = dados;
  const forte = maisForte(campeoes, minimo);
  const proximo = maisPertoDoMinimo(campeoes, minimo);
  const nomeDe = (id: number | null, reserva: string | null) => (id !== null ? tabela[id]?.nome : undefined) ?? reserva ?? "?";
  const imagemDe = (id: number | null) => (id !== null ? tabela[id]?.imagem ?? null : null);

  return (
    <div className="flex flex-col gap-6">
      {/* Destaque: campeão mais forte, ou convite para chegar ao mínimo de partidas */}
      <section className="flex items-center gap-4 rounded-xl border border-borda bg-painel p-5">
        {forte ? (
          <>
            {imagemDe(forte.champion_id) && (
              <Image src={imagemDe(forte.champion_id)!} alt="" width={64} height={64} className="rounded-xl" />
            )}
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-texto-fraco">Seu campeão mais forte</p>
              <p className="text-xl font-bold sm:text-2xl">{nomeDe(forte.champion_id, forte.champion_name)}</p>
              <p className="mt-1 text-sm text-texto-fraco">
                <span className="text-texto">{porcentagem(forte.winrate)}</span> de vitórias em {forte.jogos} partidas · KDA{" "}
                <span className="text-texto">{decimal(forte.kda, 2)}</span> (sua média: {decimal(geral.kda, 2)})
              </p>
            </div>
          </>
        ) : (
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-texto-fraco">Seu campeão mais forte</p>
            <p className="mt-1 text-sm text-texto-fraco">
              Nenhum campeão tem {minimo} partidas ainda.
              {proximo && (
                <>
                  {" "}O mais perto é <span className="text-texto">{nomeDe(proximo.champion_id, proximo.champion_name)}</span>: faltam{" "}
                  {minimo - proximo.jogos} partidas para desbloquear a análise.
                </>
              )}
            </p>
          </div>
        )}
      </section>

      <section className="flex flex-col gap-3">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h2 className="text-lg font-semibold">Mais jogados</h2>
          <p className="text-xs text-texto-fraco">
            <span className="text-destaque">▲</span> / <span className="text-texto-fraco">▼</span> = acima / abaixo da sua média
            geral ({decimal(geral.kda, 2)} KDA · {decimal(geral.cs_por_minuto)} CS/min)
          </p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {campeoes.slice(0, QUANTIDADE_EM_DESTAQUE).map((c) => (
            <CardCampeao
              key={c.champion_id}
              campeao={c}
              geral={geral}
              minimo={minimo}
              nome={nomeDe(c.champion_id, c.champion_name)}
              imagem={imagemDe(c.champion_id)}
            />
          ))}
        </div>
      </section>

      {/* <details>: elemento nativo do HTML que abre/fecha ao clicar no <summary>, sem JavaScript */}
      {campeoes.length > QUANTIDADE_EM_DESTAQUE && (
        <details className="group">
          <summary className="cursor-pointer list-none self-start rounded-lg border border-borda px-4 py-2 text-sm font-semibold text-texto-fraco transition hover:border-destaque hover:text-texto">
            <span className="group-open:hidden">Ver todos os campeões ({campeoes.length})</span>
            <span className="hidden group-open:inline">Esconder lista</span>
          </summary>
          <div className="mt-3">
            <TabelaCampeoes campeoes={campeoes} tabela={tabela} minimo={minimo} />
          </div>
        </details>
      )}

      <p className="text-xs text-texto-fraco">
        Baseado em {dados.partidas_analisadas} partidas ranqueadas recentes (Solo/Duo e Flex, sem remakes). Campeões com
        menos de {minimo} partidas aparecem esmaecidos: poucos jogos ainda não dizem muito sobre o seu desempenho.
        {dados.coletando_historico && " Buscando mais partidas: os números ficam mais precisos em alguns minutos."}
      </p>
    </div>
  );
}

function Aviso({ texto }: { texto: string }) {
  return <p className="rounded-xl border border-borda bg-painel p-5 text-center text-sm text-texto-fraco">{texto}</p>;
}

export function EsqueletoCampeoes() {
  return (
    <div className="flex animate-pulse flex-col gap-6" aria-label="Carregando campeões">
      <div className="h-28 rounded-xl border border-borda bg-painel" />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 3 }, (_, i) => (
          <div key={i} className="h-56 rounded-xl border border-borda bg-painel" />
        ))}
      </div>
    </div>
  );
}
