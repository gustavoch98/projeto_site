import BuscaRiotId from "@/components/BuscaRiotId";
import Logo from "@/components/Logo";

// Página inicial (rota "/"). É um Server Component: o HTML sai pronto do servidor.
// Só o campo de busca (Client Component) precisa de JavaScript no navegador.
export default function Home() {
  return (
    <section className="flex flex-col items-center gap-6 pt-16 text-center sm:pt-24">
      <h1>
        <Logo tamanho="lg" />
      </h1>
      <p className="max-w-md text-texto-fraco">
        Digite o Riot ID de um jogador para ver elo, partidas e{" "}
        <span className="box-decoration-clone bg-destaque px-1 font-semibold text-fundo">o que realmente decide os jogos dele</span>.
      </p>
      <div className="w-full max-w-xl">
        <BuscaRiotId />
      </div>
    </section>
  );
}
