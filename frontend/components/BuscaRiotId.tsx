"use client";
// "use client" = este componente roda (também) no NAVEGADOR, porque reage ao que o usuário
// digita (estado) e navega para outra página ao enviar.

import { useRouter } from "next/navigation";
import { useState } from "react";

import { lerRiotId, riotIdParaUrl } from "@/lib/riot-id";

export default function BuscaRiotId({ valorInicial = "" }: { valorInicial?: string }) {
  // Estado: valores que, quando mudam, fazem o React redesenhar o componente
  const [texto, setTexto] = useState(valorInicial);
  const [erro, setErro] = useState<string | null>(null);
  const router = useRouter();

  function enviar(evento: React.FormEvent<HTMLFormElement>) {
    evento.preventDefault(); // impede o navegador de recarregar a página
    const resultado = lerRiotId(texto);
    if ("erro" in resultado) {
      setErro(resultado.erro);
      return;
    }
    setErro(null);
    router.push(`/perfil/br/${riotIdParaUrl(resultado)}`);
  }

  return (
    <form onSubmit={enviar} className="w-full">
      <div className="flex overflow-hidden rounded-lg border border-borda bg-painel focus-within:border-destaque">
        <span className="flex items-center bg-painel-claro px-3 text-sm font-semibold text-texto-fraco">
          BR
        </span>
        <input
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
          placeholder="Nome#TAG"
          aria-label="Riot ID"
          aria-invalid={erro !== null}
          className="min-w-0 flex-1 bg-transparent px-3 py-3 outline-none placeholder:text-texto-fraco"
        />
        <button
          type="submit"
          className="bg-destaque px-4 font-semibold text-white transition hover:bg-blue-500 sm:px-6"
        >
          Buscar
        </button>
      </div>
      {erro && (
        <p role="alert" className="mt-2 text-sm text-red-400">
          {erro}
        </p>
      )}
    </form>
  );
}
