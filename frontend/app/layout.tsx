import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";

// next/font baixa a fonte no build e serve do próprio site (sem pedir ao Google no navegador)
const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: { default: "LoL Stats", template: "%s · LoL Stats" },
  description: "Estatísticas de jogadores de League of Legends: elo, PDL e winrate.",
};

// O layout raiz envolve TODAS as páginas. O conteúdo de cada página entra em {children}.
export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="pt-BR" className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col">
        <header className="border-b border-borda bg-painel/60">
          <div className="mx-auto flex h-14 max-w-4xl items-center px-4">
            <Link href="/" className="text-lg font-bold tracking-tight">
              LoL <span className="text-destaque">Stats</span>
            </Link>
          </div>
        </header>

        <main className="mx-auto w-full max-w-4xl flex-1 px-4 py-8">{children}</main>

        <footer className="border-t border-borda py-6 text-center text-xs text-texto-fraco">
          <p className="mx-auto max-w-2xl px-4">
            LoL Stats não é endossado pela Riot Games e não reflete as opiniões da Riot Games ou de
            qualquer pessoa oficialmente envolvida na produção ou gestão de League of Legends.
            League of Legends e Riot Games são marcas registradas da Riot Games, Inc.
          </p>
        </footer>
      </body>
    </html>
  );
}
