// Mostrado automaticamente enquanto o page.tsx busca os dados.
// É um "esqueleto": caixas cinzas no formato da página, pulsando.
export default function Carregando() {
  return (
    <div className="flex animate-pulse flex-col gap-6" aria-label="Carregando perfil">
      <div className="flex items-center gap-4 rounded-xl border border-borda bg-painel p-5">
        <div className="size-[88px] rounded-2xl bg-painel-claro" />
        <div className="flex flex-1 flex-col gap-2">
          <div className="h-7 w-48 rounded bg-painel-claro" />
          <div className="h-4 w-32 rounded bg-painel-claro" />
        </div>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <div className="h-36 rounded-xl border border-borda bg-painel" />
        <div className="h-36 rounded-xl border border-borda bg-painel" />
      </div>
    </div>
  );
}
