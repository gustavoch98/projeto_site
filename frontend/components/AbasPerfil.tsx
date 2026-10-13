"use client";
// Client Component porque precisa saber qual aba está aberta (lê a URL atual no navegador).

import Link from "next/link";
import { useSelectedLayoutSegment } from "next/navigation";

// segmento = pasta da aba dentro de [riotId]; null = page.tsx da própria pasta (aba padrão)
const ABAS = [
  { segmento: null, rotulo: "Visão geral", caminho: "" },
  { segmento: "partidas", rotulo: "Partidas", caminho: "/partidas" },
];

export default function AbasPerfil({ base }: { base: string }) {
  // Chamado dentro do layout de [riotId]: devolve o segmento logo abaixo dele
  // (null em /perfil/br/Nome-TAG, "partidas" em /perfil/br/Nome-TAG/partidas)
  const ativo = useSelectedLayoutSegment();

  return (
    <nav aria-label="Seções do perfil" className="-mx-4 overflow-x-auto px-4">
      <ul className="flex gap-1 border-b border-borda">
        {ABAS.map((aba) => {
          const selecionada = aba.segmento === ativo;
          return (
            <li key={aba.rotulo}>
              <Link
                href={base + aba.caminho}
                aria-current={selecionada ? "page" : undefined}
                className={`-mb-px block whitespace-nowrap border-b-2 px-4 py-2 text-sm font-semibold transition ${
                  selecionada
                    ? "border-destaque text-texto"
                    : "border-transparent text-texto-fraco hover:text-texto"
                }`}
              >
                {aba.rotulo}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
