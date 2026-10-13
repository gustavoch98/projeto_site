import { buscarEvolucao, type FotoPdl } from "@/lib/api";
import { nomeElo } from "@/lib/ranked";

import GraficoLinha from "./GraficoLinha";

type Props = { regiao: string; nome: string; tag: string };

const data = (iso: string) =>
  new Date(iso).toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit", year: "2-digit", timeZone: "America/Sao_Paulo" });

const comSinal = (n: number) => (n > 0 ? `+${n}` : String(n));

const descreverElo = (f: FotoPdl) => `${nomeElo(f.tier, f.rank)} · ${f.pdl} PDL`;

function textoSequencia(n: number): string {
  if (n === 0) return "–";
  const quantidade = Math.abs(n);
  if (n > 0) return `${quantidade} ${quantidade === 1 ? "vitória" : "vitórias"}`;
  return `${quantidade} ${quantidade === 1 ? "derrota" : "derrotas"}`;
}

export default async function SecaoEvolucao({ regiao, nome, tag }: Props) {
  const dados = await buscarEvolucao(regiao, nome, tag);

  if (dados === null) return <Aviso texto="Não foi possível carregar a evolução agora." />;
  if (dados.partidas.length < 2) {
    return (
      <Aviso
        texto={
          dados.coletando_historico
            ? "Buscando o histórico de partidas. Atualize a página em alguns minutos."
            : "Ainda não há partidas de Solo/Duo suficientes para mostrar a evolução."
        }
      />
    );
  }

  const { partidas, fotos } = dados;
  const saldos = partidas.map((p) => p.saldo);
  const saldoFinal = saldos[saldos.length - 1];
  const menorSaldo = Math.min(0, ...saldos);
  const maiorSaldo = Math.max(0, ...saldos);
  const inicio = data(partidas[0].data);
  const fim = data(partidas[partidas.length - 1].data);

  const cartoes = [
    { rotulo: "Saldo", valor: comSinal(saldoFinal), detalhe: `${dados.vitorias}V ${dados.derrotas}D`, destaque: saldoFinal > 0 },
    {
      rotulo: "Agora",
      valor: textoSequencia(dados.sequencia_atual),
      detalhe: dados.sequencia_atual === 0 ? "" : "seguidas",
      destaque: dados.sequencia_atual > 0,
    },
    { rotulo: "Melhor sequência", valor: textoSequencia(dados.maior_sequencia_vitorias), detalhe: "seguidas", destaque: false },
    { rotulo: "Pior sequência", valor: textoSequencia(-dados.maior_sequencia_derrotas), detalhe: "seguidas", destaque: false },
  ];

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        {cartoes.map((c) => (
          <div key={c.rotulo} className="min-w-0 border border-borda bg-painel p-4">
            <p className="font-mono text-[11px] uppercase text-texto-fraco">{c.rotulo}</p>
            <p className={`mt-1 truncate text-2xl font-extrabold ${c.destaque ? "text-destaque" : ""}`}>{c.valor}</p>
            <p className="text-xs text-texto-fraco">{c.detalhe}</p>
          </div>
        ))}
      </div>

      <Bloco
        titulo="Saldo de vitórias"
        explicacao={`Sobe 1 a cada vitória e desce 1 a cada derrota nas suas ${partidas.length} partidas de Solo/Duo. A Riot não informa o PDL do passado, mas cada vitória rende PDL e cada derrota tira: a tendência desta linha acompanha a do seu PDL.`}
      >
        <GraficoLinha
          valores={saldos}
          minimo={menorSaldo - 1}
          maximo={maiorSaldo + 1}
          referencia={{ valor: 0, rotulo: "0" }}
          rotuloMinimo={comSinal(menorSaldo)}
          rotuloMaximo={comSinal(maiorSaldo)}
          rotuloInicio={inicio}
          rotuloFim={fim}
          descricao={`Saldo de vitórias de ${inicio} a ${fim}: termina em ${comSinal(saldoFinal)}`}
        />
      </Bloco>

      <Bloco
        titulo="Winrate das últimas 20 partidas"
        explicacao="Cada ponto é o seu winrate nas 20 partidas até ali: mostra as fases boas e ruins melhor que o winrate total."
      >
        <GraficoLinha
          valores={partidas.map((p) => (p.winrate_movel === null ? null : p.winrate_movel * 100))}
          minimo={0}
          maximo={100}
          referencia={{ valor: 50, rotulo: "50%" }}
          rotuloMinimo="0%"
          rotuloMaximo="100%"
          rotuloInicio={inicio}
          rotuloFim={fim}
          descricao={`Winrate móvel de 20 partidas, de ${inicio} a ${fim}`}
        />
      </Bloco>

      <Bloco
        titulo="PDL registrado"
        explicacao="Gravamos o seu elo a cada atualização do perfil. Este gráfico fica mais completo quanto mais vezes o perfil for atualizado."
      >
        {fotos.length >= 2 ? (
          <GraficoLinha
            valores={fotos.map((f) => f.pontos)}
            minimo={Math.min(...fotos.map((f) => f.pontos)) - 20}
            maximo={Math.max(...fotos.map((f) => f.pontos)) + 20}
            rotuloMinimo={descreverElo(fotos.reduce((a, b) => (b.pontos < a.pontos ? b : a)))}
            rotuloMaximo={descreverElo(fotos.reduce((a, b) => (b.pontos > a.pontos ? b : a)))}
            rotuloInicio={data(fotos[0].data)}
            rotuloFim={data(fotos[fotos.length - 1].data)}
            descricao={`PDL registrado de ${data(fotos[0].data)} a ${data(fotos[fotos.length - 1].data)}`}
          />
        ) : (
          <p className="text-sm text-texto-fraco">
            {fotos.length === 1 ? (
              <>
                Começamos a registrar em <span className="text-texto">{data(fotos[0].data)}</span>:{" "}
                <span className="text-texto">{descreverElo(fotos[0])}</span>. O gráfico aparece a partir da próxima
                mudança de PDL.
              </>
            ) : (
              "Ainda não registramos o elo deste jogador na Solo/Duo."
            )}
          </p>
        )}
      </Bloco>
    </div>
  );
}

function Bloco({ titulo, explicacao, children }: { titulo: string; explicacao: string; children: React.ReactNode }) {
  return (
    <section className="flex min-w-0 flex-col gap-3 border border-borda bg-painel p-5">
      <div>
        <h2 className="text-lg font-bold">{titulo}</h2>
        <p className="text-xs text-texto-fraco">{explicacao}</p>
      </div>
      {children}
    </section>
  );
}

function Aviso({ texto }: { texto: string }) {
  return <p className="border border-borda bg-painel p-5 text-center text-sm text-texto-fraco">{texto}</p>;
}

export function EsqueletoEvolucao() {
  return (
    <div className="flex animate-pulse flex-col gap-6" aria-label="Carregando evolução">
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        {Array.from({ length: 4 }, (_, i) => (
          <div key={i} className="h-24 border border-borda bg-painel" />
        ))}
      </div>
      <div className="h-72 border border-borda bg-painel" />
      <div className="h-72 border border-borda bg-painel" />
    </div>
  );
}
