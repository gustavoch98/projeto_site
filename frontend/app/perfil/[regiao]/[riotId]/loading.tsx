// Esqueleto do CONTEÚDO das abas. Fica abaixo do layout.tsx desta pasta: ao trocar de aba,
// o cabeçalho e os cards de elo continuam na tela e só a área da aba mostra este esqueleto.
// (O esqueleto da página inteira, para o primeiro carregamento, é o loading.tsx de [regiao].)
export default function CarregandoAba() {
  return (
    <div className="flex animate-pulse flex-col gap-4" aria-label="Carregando">
      <div className="h-6 w-32 rounded bg-painel-claro" />
      <div className="h-32 rounded-xl border border-borda bg-painel" />
      <div className="grid gap-4 md:grid-cols-2">
        <div className="h-64 rounded-xl border border-borda bg-painel" />
        <div className="h-64 rounded-xl border border-borda bg-painel" />
      </div>
    </div>
  );
}
