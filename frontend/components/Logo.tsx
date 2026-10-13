import { MARCA } from "@/lib/marca";

// Logotipo: um raio preto num quadrado limão + "RAIO" e o ".gg" em fonte mono.
export default function Logo({ tamanho = "md" }: { tamanho?: "md" | "lg" }) {
  const grande = tamanho === "lg";
  const icone = grande ? 56 : 28;
  return (
    <span className="inline-flex items-center gap-2">
      <svg width={icone} height={icone} viewBox="0 0 44 44" aria-hidden="true" className="shrink-0">
        <rect width="44" height="44" fill="var(--color-destaque)" />
        <path d="M25 6 L12 25 H21 L18 38 L32 18 H23 Z" fill="var(--color-fundo)" />
      </svg>
      <span className={`font-extrabold uppercase leading-none tracking-tighter ${grande ? "text-6xl" : "text-2xl"}`}>
        {MARCA.nome}
        <span className={`font-mono font-bold lowercase tracking-normal text-destaque ${grande ? "text-3xl" : "text-sm"}`}>
          .gg
        </span>
      </span>
    </span>
  );
}
