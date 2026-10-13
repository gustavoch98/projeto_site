"use client";

import { useState, useTransition } from "react";

import { atualizar } from "@/app/perfil/[regiao]/[riotId]/actions";

type Props = { regiao: string; nome: string; tag: string };

export default function BotaoAtualizar({ regiao, nome, tag }: Props) {
  // useTransition indica se a ação ainda está em andamento (pendente = true)
  const [pendente, iniciar] = useTransition();
  const [mensagem, setMensagem] = useState<string | null>(null);

  function clicar() {
    iniciar(async () => {
      const resultado = await atualizar(regiao, nome, tag);
      setMensagem(resultado.mensagem);
    });
  }

  return (
    <div className="flex flex-col items-start gap-1 sm:items-end">
      <button
        onClick={clicar}
        disabled={pendente}
        className="rounded-lg bg-destaque px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-500 disabled:cursor-wait disabled:opacity-60"
      >
        {pendente ? "Atualizando..." : "Atualizar"}
      </button>
      {mensagem && (
        <p role="status" className="text-xs text-texto-fraco">
          {mensagem}
        </p>
      )}
    </div>
  );
}
