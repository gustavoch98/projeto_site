// Gráfico de linha em SVG puro (sem biblioteca), desenhado no servidor.
//
// O SVG usa um sistema de coordenadas próprio de 100 x 100 (viewBox). Cada valor vira um ponto
// (x = posição na série, y = valor convertido para 0..100, invertido porque no SVG o y cresce
// para baixo). preserveAspectRatio="none" estica o desenho para a largura que houver;
// vector-effect="non-scaling-stroke" mantém a espessura da linha mesmo esticada.

type Props = {
  valores: (number | null)[]; // null = ponto sem valor (não desenhado)
  minimo: number;
  maximo: number;
  referencia?: { valor: number; rotulo: string }; // linha tracejada (ex.: saldo 0, winrate 50%)
  rotuloMinimo: string;
  rotuloMaximo: string;
  rotuloInicio: string; // eixo x: primeira e última data
  rotuloFim: string;
  descricao: string; // texto para leitores de tela
};

export default function GraficoLinha({
  valores,
  minimo,
  maximo,
  referencia,
  rotuloMinimo,
  rotuloMaximo,
  rotuloInicio,
  rotuloFim,
  descricao,
}: Props) {
  const amplitude = maximo - minimo || 1;
  const y = (v: number) => 100 - ((v - minimo) / amplitude) * 100;
  const x = (i: number) => (valores.length > 1 ? (i / (valores.length - 1)) * 100 : 50);

  const pontos = valores.flatMap((v, i) => (v === null ? [] : [`${x(i).toFixed(2)},${y(v).toFixed(2)}`]));
  // Área sob a linha: a mesma linha, fechada até a base do gráfico
  const primeiroX = valores.findIndex((v) => v !== null);
  const area =
    pontos.length > 1 ? `${x(primeiroX).toFixed(2)},100 ${pontos.join(" ")} ${x(valores.length - 1).toFixed(2)},100` : "";

  return (
    <figure className="m-0">
      <div className="flex gap-2">
        {/* Eixo y: só os extremos (e a referência), para não poluir */}
        <div className="relative w-14 shrink-0 font-mono text-[10px] text-texto-fraco">
          <span className="absolute right-0 top-0 -translate-y-1/2">{rotuloMaximo}</span>
          <span className="absolute bottom-0 right-0 translate-y-1/2">{rotuloMinimo}</span>
        </div>

        <div className="relative h-44 min-w-0 flex-1 border-b border-l border-borda">
          {referencia && (
            <div
              className="pointer-events-none absolute inset-x-0 border-t border-dashed border-texto-fraco/60"
              style={{ top: `${y(referencia.valor)}%` }}
            >
              <span className="absolute -top-4 right-0 font-mono text-[10px] text-texto-fraco">{referencia.rotulo}</span>
            </div>
          )}
          <svg
            viewBox="0 0 100 100"
            preserveAspectRatio="none"
            className="absolute inset-0 h-full w-full overflow-visible"
            role="img"
            aria-label={descricao}
          >
            {area && <polygon points={area} fill="var(--color-destaque)" opacity="0.12" />}
            <polyline
              points={pontos.join(" ")}
              fill="none"
              stroke="var(--color-destaque)"
              strokeWidth="2"
              vectorEffect="non-scaling-stroke"
              strokeLinejoin="round"
            />
          </svg>
        </div>
      </div>
      <figcaption className="mt-1 flex justify-between pl-16 font-mono text-[10px] text-texto-fraco">
        <span>{rotuloInicio}</span>
        <span>{rotuloFim}</span>
      </figcaption>
    </figure>
  );
}
