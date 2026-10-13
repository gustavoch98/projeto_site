import { buscarInsights, type InsightsHorario } from "@/lib/api";
import { comparar, expressaoPeriodo, MINIMO_POR_FAIXA, MINIMO_TOTAL, porcentagem, type Comparacao } from "@/lib/insights";

import GraficoFaixas from "./GraficoFaixas";

type Props = { regiao: string; nome: string; tag: string };

// Painel do jogador: cartões com análises calculadas a partir do histórico de partidas.
// Começa com "desempenho por horário"; novos cartões entram aqui.
export default async function SecaoPainel({ regiao, nome, tag }: Props) {
  const insights = await buscarInsights(regiao, nome, tag);

  if (insights === null) {
    return <Aviso texto="Não foi possível carregar o painel agora." />;
  }
  if (insights.partidas_analisadas < MINIMO_TOTAL || insights.winrate_geral === null) {
    return (
      <Aviso
        texto={
          insights.coletando_historico
            ? "Buscando o histórico de partidas para montar o painel. Atualize a página em alguns minutos."
            : `O painel precisa de pelo menos ${MINIMO_TOTAL} partidas ranqueadas recentes.`
        }
      />
    );
  }

  const media = insights.winrate_geral;

  return (
    <div className="flex flex-col gap-4">
      <Destaque insights={insights} comparacao={comparar(insights.por_periodo)} />
      <div className="grid gap-4 md:grid-cols-2">
        <GraficoFaixas titulo="Vitórias por período do dia" faixas={insights.por_periodo} media={media} />
        <GraficoFaixas titulo="Vitórias por dia da semana" faixas={insights.por_dia_semana} media={media} />
      </div>
      <p className="text-xs text-texto-fraco">
        Baseado em {insights.partidas_analisadas} partidas ranqueadas (Solo/Duo e Flex, sem remakes), no horário de
        Brasília. Barras cinzas têm menos de {MINIMO_POR_FAIXA} partidas e não entram na comparação. No computador, passe o mouse sobre uma barra para ver o intervalo provável.
        {insights.coletando_historico && " Buscando mais partidas: os números ficam mais precisos em alguns minutos."}
      </p>
    </div>
  );
}

function Destaque({ insights, comparacao }: { insights: InsightsHorario; comparacao: Comparacao | null }) {
  if (comparacao === null) {
    return (
      <Aviso texto="Ainda não há partidas suficientes em horários diferentes para comparar." />
    );
  }
  const { melhor, pior, diferencaPontos, consistente } = comparacao;

  return (
    <section className="rounded-xl border border-borda bg-painel p-5">
      <p className="text-xs font-semibold uppercase tracking-wide text-texto-fraco">Seu melhor horário</p>
      <p className="mt-1 text-xl font-bold sm:text-2xl">
        Você rende mais <span className="text-sky-400">{expressaoPeriodo(melhor)}</span>
      </p>
      <p className="mt-2 text-sm text-texto-fraco">
        <span className="text-texto">{porcentagem(melhor.winrate!)}</span> de vitórias em {melhor.jogos} partidas, contra{" "}
        <span className="text-texto">{porcentagem(pior.winrate!)}</span> {expressaoPeriodo(pior)} ({pior.jogos} partidas):{" "}
        <span className="text-texto">{diferencaPontos} pontos</span> de diferença. Sua média geral é{" "}
        {porcentagem(insights.winrate_geral!)}.
      </p>
      <p className={`mt-3 inline-block rounded-full px-3 py-1 text-xs ${consistente ? "bg-sky-500/15 text-sky-300" : "bg-zinc-500/15 text-zinc-300"}`}>
        {consistente
          ? "Com essa quantidade de partidas, dificilmente a diferença é só acaso."
          : "Ainda pode ser acaso: com mais partidas o resultado fica mais confiável."}
      </p>
    </section>
  );
}

function Aviso({ texto }: { texto: string }) {
  return <p className="rounded-xl border border-borda bg-painel p-5 text-center text-sm text-texto-fraco">{texto}</p>;
}

export function EsqueletoPainel() {
  return (
    <div className="flex animate-pulse flex-col gap-4" aria-label="Carregando painel">
      <div className="h-32 rounded-xl border border-borda bg-painel" />
      <div className="grid gap-4 md:grid-cols-2">
        <div className="h-64 rounded-xl border border-borda bg-painel" />
        <div className="h-64 rounded-xl border border-borda bg-painel" />
      </div>
    </div>
  );
}
