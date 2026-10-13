"use client";
// "use client" = este componente roda (também) no NAVEGADOR, porque reage ao que o usuário
// digita (estado), busca sugestões enquanto ele digita e navega ao escolher um jogador.

import Image from "next/image";
import { useRouter } from "next/navigation";
import { useEffect, useId, useState } from "react";

import type { Sugestao } from "@/app/api/sugestoes/route";
import { corElo } from "@/lib/ranked";
import { lerRiotId, riotIdParaUrl, separarTexto, type RiotId } from "@/lib/riot-id";

const ESPERA_DIGITACAO_MS = 250; // debounce: só busca quando a pessoa para de digitar
const MINIMO_LETRAS = 2;

export default function BuscaRiotId() {
  // Estado: valores que, quando mudam, fazem o React redesenhar o componente
  const [texto, setTexto] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [sugestoes, setSugestoes] = useState<Sugestao[]>([]);
  const [aberta, setAberta] = useState(false); // lista visível?
  const [ativa, setAtiva] = useState(-1); // sugestão destacada pelo teclado (-1 = nenhuma)
  const router = useRouter();
  const idLista = useId();

  // Efeito: roda depois de cada mudança em "texto". Agenda a busca para daqui a 250 ms;
  // se a pessoa digitar de novo antes disso, a função de limpeza cancela o agendamento
  // (e a requisição anterior, se já tiver saído).
  useEffect(() => {
    if (separarTexto(texto).nome.length < MINIMO_LETRAS) return;

    const controle = new AbortController();
    const agendamento = setTimeout(async () => {
      try {
        const resposta = await fetch(`/api/sugestoes?q=${encodeURIComponent(texto)}`, {
          signal: controle.signal,
        });
        setSugestoes(await resposta.json());
        setAtiva(-1);
      } catch {
        // requisição cancelada ou falhou: mantém a lista como está
      }
    }, ESPERA_DIGITACAO_MS);

    return () => {
      clearTimeout(agendamento);
      controle.abort();
    };
  }, [texto]);

  function digitar(valor: string) {
    setTexto(valor);
    setErro(null);
    setAberta(true);
    if (separarTexto(valor).nome.length < MINIMO_LETRAS) setSugestoes([]);
  }

  function irParaPerfil(riotId: RiotId) {
    setAberta(false);
    router.push(`/perfil/br/${riotIdParaUrl(riotId)}`);
  }

  function enviar(evento: React.FormEvent<HTMLFormElement>) {
    evento.preventDefault(); // impede o navegador de recarregar a página
    if (aberta && ativa >= 0) {
      const escolhida = sugestoes[ativa];
      irParaPerfil({ nome: escolhida.nome, tag: escolhida.tag });
      return;
    }
    const resultado = lerRiotId(texto);
    if ("erro" in resultado) {
      setErro(resultado.erro);
      return;
    }
    irParaPerfil(resultado);
  }

  function teclar(evento: React.KeyboardEvent<HTMLInputElement>) {
    if (evento.key === "ArrowDown" && sugestoes.length > 0) {
      evento.preventDefault();
      setAberta(true);
      setAtiva((i) => (i + 1) % sugestoes.length);
    } else if (evento.key === "ArrowUp" && sugestoes.length > 0) {
      evento.preventDefault();
      setAtiva((i) => (i <= 0 ? sugestoes.length - 1 : i - 1));
    } else if (evento.key === "Escape") {
      setAberta(false);
    }
  }

  const mostrarLista = aberta && sugestoes.length > 0;

  return (
    <form onSubmit={enviar} className="relative w-full text-left">
      <div className="flex overflow-hidden rounded-lg border border-borda bg-painel focus-within:border-destaque">
        <span className="flex items-center bg-painel-claro px-3 text-sm font-semibold text-texto-fraco">
          BR
        </span>
        <input
          value={texto}
          onChange={(e) => digitar(e.target.value)}
          onKeyDown={teclar}
          onFocus={() => setAberta(true)}
          onBlur={() => setAberta(false)}
          placeholder="Nome ou Nome#TAG"
          autoComplete="off"
          spellCheck={false}
          // Atributos ARIA: dizem a leitores de tela que este campo tem uma lista de opções
          role="combobox"
          aria-label="Riot ID"
          aria-expanded={mostrarLista}
          aria-controls={idLista}
          aria-autocomplete="list"
          aria-activedescendant={mostrarLista && ativa >= 0 ? `${idLista}-${ativa}` : undefined}
          aria-invalid={erro !== null}
          className="min-w-0 flex-1 bg-transparent px-3 py-3 outline-none placeholder:text-texto-fraco"
        />
        <button
          type="submit"
          className="bg-destaque px-4 font-semibold text-fundo transition hover:bg-destaque-claro sm:px-6"
        >
          Buscar
        </button>
      </div>

      {mostrarLista && (
        <ul
          id={idLista}
          role="listbox"
          className="absolute z-10 mt-1 w-full overflow-hidden rounded-lg border border-borda bg-painel shadow-xl shadow-black/40"
        >
          {sugestoes.map((s, i) => (
            <li
              key={`${s.nome}#${s.tag}`}
              id={`${idLista}-${i}`}
              role="option"
              aria-selected={i === ativa}
              // onMouseDown (e não onClick): dispara antes do onBlur do campo fechar a lista
              onMouseDown={(e) => {
                e.preventDefault();
                irParaPerfil({ nome: s.nome, tag: s.tag });
              }}
              onMouseEnter={() => setAtiva(i)}
              className={`flex cursor-pointer items-center gap-3 px-3 py-2 ${
                i === ativa ? "bg-painel-claro" : ""
              }`}
            >
              <Image
                src={s.icone}
                alt=""
                width={32}
                height={32}
                className="rounded-md border border-borda"
              />
              <span className="min-w-0 flex-1 truncate">
                {s.nome}
                <span className="text-texto-fraco"> #{s.tag}</span>
              </span>
              <span className="shrink-0 text-right text-xs">
                <span className={s.tier ? corElo(s.tier) : "text-texto-fraco"}>
                  {s.elo ?? "Unranked"}
                </span>
                <span className="block text-texto-fraco">Nível {s.nivel}</span>
              </span>
            </li>
          ))}
        </ul>
      )}

      {erro && (
        <p role="alert" className="mt-2 text-sm text-erro">
          {erro}
        </p>
      )}
    </form>
  );
}
