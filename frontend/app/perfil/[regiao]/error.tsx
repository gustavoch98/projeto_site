"use client"; // Componentes de erro precisam ser Client Components

// Rede de segurança para erros INESPERADOS (bugs). Erros previstos, como a Riot fora do ar,
// já são tratados no page.tsx com uma mensagem própria.
export default function ErroPerfil({ retry }: { error: Error & { digest?: string }; retry: () => void }) {
  return (
    <div className="flex flex-col items-center gap-4 pt-12 text-center">
      <h1 className="text-2xl font-bold">Algo deu errado</h1>
      <p className="text-texto-fraco">Não foi possível carregar este perfil.</p>
      <button
        onClick={() => retry()}
        className="rounded-lg bg-destaque px-4 py-2 font-semibold text-white hover:bg-blue-500"
      >
        Tentar novamente
      </button>
    </div>
  );
}
