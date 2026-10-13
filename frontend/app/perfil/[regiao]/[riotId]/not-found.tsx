import BuscaRiotId from "@/components/BuscaRiotId";

// Mostrado quando o page.tsx chama notFound() (jogador inexistente ou URL inválida).
export default function JogadorNaoEncontrado() {
  return (
    <div className="mx-auto flex max-w-xl flex-col items-center gap-4 pt-12 text-center">
      <h1 className="text-2xl font-bold">Jogador não encontrado</h1>
      <p className="text-texto-fraco">
        Confira o nome e a TAG. O Riot ID tem o formato <strong>Nome#TAG</strong>; se você
        digitou só o nome, tentamos a TAG <strong>#BR1</strong>.
      </p>
      <div className="w-full">
        <BuscaRiotId />
      </div>
    </div>
  );
}
