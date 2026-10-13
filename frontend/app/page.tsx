import BuscaRiotId from "@/components/BuscaRiotId";

// Página inicial (rota "/"). É um Server Component: o HTML sai pronto do servidor.
// Só o campo de busca (Client Component) precisa de JavaScript no navegador.
export default function Home() {
  return (
    <section className="flex flex-col items-center gap-6 pt-16 text-center sm:pt-24">
      <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
        LoL <span className="text-destaque">Stats</span>
      </h1>
      <p className="max-w-md text-texto-fraco">
        Digite o Riot ID de um jogador para ver elo, PDL e winrate nas filas ranqueadas.
      </p>
      <div className="w-full max-w-xl">
        <BuscaRiotId />
      </div>
    </section>
  );
}
