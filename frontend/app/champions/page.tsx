import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";

import TabelaTierList from "@/components/champions/TabelaTierList";
import { buscarTierList } from "@/lib/api";
import { tabelaCampeoes, versaoAtual } from "@/lib/ddragon";

export const metadata: Metadata = { title: "Champions" };

const FILTROS = [
  { valor: undefined, rotulo: "Todas" },
  { valor: "TOP", rotulo: "Topo" },
  { valor: "JUNGLE", rotulo: "Selva" },
  { valor: "MIDDLE", rotulo: "Meio" },
  { valor: "BOTTOM", rotulo: "Atirador" },
  { valor: "UTILITY", rotulo: "Suporte" },
];

// Página Champions: tier list do patch atual. O filtro de rota é a URL (?rota=TOP): cada filtro
// tem link próprio e funciona sem JavaScript. searchParams é lido dentro do <Suspense>
// (navegação instantânea), como nas abas do perfil.
export default function PaginaChampions({ searchParams }: PageProps<"/champions">) {
  return (
    <div className="flex flex-col gap-6">
      <header>
        <p className="inline-block -rotate-2 bg-destaque px-2 py-0.5 font-mono text-xs font-bold uppercase text-fundo">
          Tier list
        </p>
        <h1 className="mt-2 text-3xl font-extrabold uppercase tracking-tight">Champions</h1>
        <p className="mt-1 max-w-2xl text-sm text-texto-fraco">
          Desempenho de cada campeão na Solo/Duo do patch atual, calculado com as partidas que o Raio já analisou.
        </p>
      </header>

      <Suspense fallback={<Esqueleto />}>
        <Conteudo searchParams={searchParams} />
      </Suspense>
    </div>
  );
}

async function Conteudo({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const parametros = await searchParams;
  const rota = typeof parametros.rota === "string" ? parametros.rota : undefined;
  const versao = await versaoAtual();
  const [dados, tabela] = await Promise.all([buscarTierList(rota), tabelaCampeoes(versao)]);

  return (
    <>
      <nav aria-label="Filtrar por rota" className="-mx-4 overflow-x-auto px-4">
        <ul className="flex gap-2">
          {FILTROS.map((f) => {
            const ativo = f.valor === rota;
            return (
              <li key={f.rotulo}>
                <Link
                  href={f.valor ? `/champions?rota=${f.valor}` : "/champions"}
                  aria-current={ativo ? "page" : undefined}
                  className={`block whitespace-nowrap px-3 py-1.5 text-sm font-semibold transition ${
                    ativo ? "bg-destaque text-fundo" : "border border-borda text-texto-fraco hover:text-texto"
                  }`}
                >
                  {f.rotulo}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {dados === null ? (
        <Aviso texto="Não foi possível carregar a tier list agora." />
      ) : dados.patch === null || dados.campeoes.length === 0 ? (
        <Aviso texto="Ainda não há partidas suficientes do patch atual para montar a lista." />
      ) : (
        <>
          <p className={`p-4 text-sm ${dados.prior_jogos ? "border border-borda text-texto-fraco" : "border-2 border-destaque"}`}>
            {dados.prior_jogos ? (
              <>
                Patch <strong className="text-texto">{dados.patch}</strong> · {dados.partidas.toLocaleString("pt-BR")}{" "}
                partidas. Os tiers usam o winrate ajustado: campeões com poucas partidas são puxados para 50%, na
                medida que os próprios dados indicam.
              </>
            ) : (
              <>
                <strong className="text-destaque">Prévia, ainda sem tiers.</strong> Com{" "}
                {dados.partidas.toLocaleString("pt-BR")} partidas do patch {dados.patch}, as diferenças de winrate entre
                os campeões ainda não se distinguem do acaso. Por enquanto a lista mostra os dados brutos, do mais ao
                menos jogado; os tiers aparecem sozinhos quando houver partidas suficientes.
              </>
            )}{" "}
            Só entram campeões com pelo menos {dados.minimo_jogos} partidas na rota.
          </p>
          <TabelaTierList campeoes={dados.campeoes} tabela={tabela} />
        </>
      )}
    </>
  );
}

function Aviso({ texto }: { texto: string }) {
  return <p className="border border-borda bg-painel p-5 text-center text-sm text-texto-fraco">{texto}</p>;
}

function Esqueleto() {
  return (
    <div className="flex animate-pulse flex-col gap-4" aria-label="Carregando tier list">
      <div className="h-9 w-2/3 bg-painel" />
      <div className="h-16 border border-borda bg-painel" />
      <div className="h-96 border border-borda bg-painel" />
    </div>
  );
}
