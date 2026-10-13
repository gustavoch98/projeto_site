import type { Metadata } from "next";
import { Bricolage_Grotesque, Space_Mono } from "next/font/google";
import Link from "next/link";

import Logo from "@/components/Logo";
import { MARCA } from "@/lib/marca";
import "./globals.css";

// next/font baixa as fontes no build e serve do próprio site (sem pedir ao Google no navegador)
const bricolage = Bricolage_Grotesque({ variable: "--font-bricolage", subsets: ["latin"] });
// Space Mono não é "variável": é preciso dizer quais pesos baixar
const spaceMono = Space_Mono({ variable: "--font-space-mono", subsets: ["latin"], weight: ["400", "700"] });

export const metadata: Metadata = {
  title: { default: MARCA.nome, template: `%s · ${MARCA.nome}` },
  description: MARCA.descricao,
};

// O layout raiz envolve TODAS as páginas. O conteúdo de cada página entra em {children}.
export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="pt-BR" className={`${bricolage.variable} ${spaceMono.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col">
        <header className="border-b-2 border-destaque">
          <div className="mx-auto flex h-14 max-w-4xl items-center px-4">
            <Link href="/" aria-label={`${MARCA.nome}: página inicial`}>
              <Logo />
            </Link>
          </div>
        </header>

        <main className="mx-auto w-full max-w-4xl flex-1 px-4 py-8">{children}</main>

        <footer className="border-t border-borda py-6 text-center text-xs text-texto-fraco">
          <p className="mx-auto max-w-2xl px-4">
            {MARCA.nome} não é endossado pela Riot Games e não reflete as opiniões da Riot Games ou de qualquer
            pessoa oficialmente envolvida na produção ou gestão de League of Legends. League of Legends e Riot
            Games são marcas registradas da Riot Games, Inc.
          </p>
        </footer>
      </body>
    </html>
  );
}
