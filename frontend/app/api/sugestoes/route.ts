// Route Handler: uma rota de API dentro do próprio Next.js (GET /api/sugestoes?q=...).
// O campo de busca, no navegador, chama esta rota; ela repassa para o FastAPI no servidor.
// Assim o navegador continua sem conhecer o endereço do back-end.

import { sugerirJogadores } from "@/lib/api";
import { urlIconePerfil, versaoAtual } from "@/lib/ddragon";
import { nomeElo } from "@/lib/ranked";

// Formato enviado ao navegador: só o que a lista precisa, já pronto para exibir
export type Sugestao = {
  nome: string;
  tag: string;
  nivel: number;
  icone: string;
  elo: string | null;
  tier: string | null;
};

export async function GET(request: Request) {
  const texto = new URL(request.url).searchParams.get("q") ?? "";
  if (texto.trim().length < 2) return Response.json([]);

  const [jogadores, versao] = await Promise.all([sugerirJogadores(texto), versaoAtual()]);

  const sugestoes: Sugestao[] = jogadores.map((j) => ({
    nome: j.game_name,
    tag: j.tag_line,
    nivel: j.summoner_level,
    icone: urlIconePerfil(versao, j.profile_icon_id),
    elo: j.solo ? nomeElo(j.solo.tier, j.solo.rank) : null,
    tier: j.solo?.tier ?? null,
  }));
  return Response.json(sugestoes);
}
