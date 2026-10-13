import type { FaixaDesempenho } from "@/lib/api";
import { confiavel, porcentagem, separarRotulo } from "@/lib/insights";

type Props = { titulo: string; faixas: FaixaDesempenho[]; media: number };

// Gráfico de barras feito só com HTML + Tailwind: cada barra é uma <div> cuja altura
// é o winrate (em %). Para poucos gráficos simples, dispensa uma biblioteca de gráficos.
export default function GraficoFaixas({ titulo, faixas, media }: Props) {
  // min-w-0: itens de grid/flex não encolhem abaixo do próprio conteúdo por padrão
  // (min-width: auto); sem isso, rótulos como "Madrugada" empurram o gráfico para fora da tela.
  return (
    <section className="min-w-0 rounded-xl border border-borda bg-painel p-4 sm:p-5">
      <div className="mb-4 flex items-baseline justify-between gap-2">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-texto-fraco">{titulo}</h3>
        <span className="flex shrink-0 items-center gap-1 text-[11px] text-texto-fraco">
          <span className="w-4 border-t border-dashed border-texto-fraco" /> média {porcentagem(media)}
        </span>
      </div>

      <div className="relative flex h-40 items-end gap-1 sm:gap-2">
        {/* Linha tracejada na altura do winrate médio do jogador */}
        <div
          className="pointer-events-none absolute inset-x-0 border-t border-dashed border-texto-fraco/60"
          style={{ bottom: `${media * 100}%` }}
        />

        {faixas.map((f) => {
          const ok = confiavel(f);
          const cor = !ok ? "bg-neutro" : f.winrate! >= media ? "bg-destaque" : "border-2 border-texto";
          const descricao = f.winrate === null
            ? `${f.rotulo}: sem partidas`
            : `${f.rotulo}: ${porcentagem(f.winrate)} de vitórias em ${f.jogos} partidas` +
              (f.ic_baixo !== null ? ` (intervalo provável: ${porcentagem(f.ic_baixo)} a ${porcentagem(f.ic_alto!)})` : "");
          return (
            <div key={f.chave} className="flex h-full min-w-0 flex-1 flex-col items-center justify-end" title={descricao}>
              <span className={`mb-1 text-[11px] font-semibold sm:text-xs ${ok ? "text-texto" : "text-texto-fraco"}`}>
                {f.winrate === null ? "–" : porcentagem(f.winrate)}
              </span>
              <div className={`w-full max-w-12 rounded-t ${cor}`} style={{ height: `${(f.winrate ?? 0) * 100}%` }} />
            </div>
          );
        })}
      </div>

      {/* Rótulos embaixo de cada barra */}
      <div className="mt-2 flex gap-1 sm:gap-2">
        {faixas.map((f) => {
          const { nome, detalhe } = separarRotulo(f.rotulo);
          return (
            <div key={f.chave} className="min-w-0 flex-1 text-center text-[11px] leading-tight">
              <p className="truncate font-medium text-texto" title={nome}>{nome}</p>
              {detalhe && <p className="hidden text-texto-fraco sm:block">{detalhe}</p>}
              <p className="text-texto-fraco">
                {f.jogos}
                <span className="hidden sm:inline"> jogos</span>
              </p>
            </div>
          );
        })}
      </div>
    </section>
  );
}
