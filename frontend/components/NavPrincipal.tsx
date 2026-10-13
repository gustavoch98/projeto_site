"use client";
// Client Component porque destaca o item da página atual (lê a URL no navegador).

import Link from "next/link";
import { usePathname } from "next/navigation";

const ITENS = [
  { rotulo: "Home", href: "/" },
  { rotulo: "Champions", href: "/champions" },
];

export default function NavPrincipal() {
  const caminho = usePathname();

  return (
    <nav aria-label="Navegação principal">
      <ul className="flex items-center gap-1">
        {ITENS.map((item) => {
          // Home só fica ativa na própria "/"; as outras também nas subpáginas (/champions/...)
          const ativo = item.href === "/" ? caminho === "/" : caminho.startsWith(item.href);
          return (
            <li key={item.href}>
              <Link
                href={item.href}
                aria-current={ativo ? "page" : undefined}
                className={`block px-3 py-1.5 font-mono text-xs font-bold uppercase transition ${
                  ativo ? "bg-destaque text-fundo" : "text-texto-fraco hover:text-texto"
                }`}
              >
                {item.rotulo}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
