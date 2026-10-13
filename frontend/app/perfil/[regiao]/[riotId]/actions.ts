"use server";
// Server Action: função que roda no SERVIDOR, mas pode ser chamada por um botão no navegador.
// O Next.js cria a ponte (uma requisição HTTP) automaticamente.

import { refresh } from "next/cache";

import { atualizarPerfil } from "@/lib/api";

export type ResultadoAtualizacao = { mensagem: string | null };

export async function atualizar(
  regiao: string,
  nome: string,
  tag: string,
): Promise<ResultadoAtualizacao> {
  const resultado = await atualizarPerfil(regiao, nome, tag);

  if (resultado.tipo === "erro") return { mensagem: resultado.mensagem };
  if (resultado.tipo === "nao-encontrado") return { mensagem: "Jogador não encontrado." };

  // Pede ao navegador para redesenhar a página com os dados novos
  refresh();

  if (resultado.perfil.cached) {
    const liberado = new Date(resultado.perfil.refresh_available_at);
    const segundos = Math.max(1, Math.ceil((liberado.getTime() - Date.now()) / 1000));
    return { mensagem: `Perfil atualizado há pouco. Tente de novo em ${segundos}s.` };
  }
  return { mensagem: null };
}
