"use client";
// Precisa ser Client Component porque o texto muda sozinho com o passar do tempo.

import { useEffect, useState } from "react";

function descrever(data: Date, agora: number): string {
  const minutos = Math.floor((agora - data.getTime()) / 60_000);
  if (minutos < 1) return "agora mesmo";
  if (minutos < 60) return `há ${minutos} ${minutos === 1 ? "minuto" : "minutos"}`;
  const horas = Math.floor(minutos / 60);
  if (horas < 24) return `há ${horas} ${horas === 1 ? "hora" : "horas"}`;
  const dias = Math.floor(horas / 24);
  return `há ${dias} ${dias === 1 ? "dia" : "dias"}`;
}

export default function TempoRelativo({ iso }: { iso: string }) {
  const data = new Date(iso);
  const [agora, setAgora] = useState(() => Date.now());

  // useEffect roda só no navegador, depois que o componente aparece na tela.
  // Aqui ele cria um relógio que atualiza o texto a cada 30 segundos.
  useEffect(() => {
    const relogio = setInterval(() => setAgora(Date.now()), 30_000);
    return () => clearInterval(relogio); // limpeza quando o componente sai da tela
  }, []);

  return (
    // O servidor e o navegador podem calcular horários ligeiramente diferentes;
    // suppressHydrationWarning evita um aviso por causa disso.
    <time dateTime={iso} title={data.toLocaleString("pt-BR")} suppressHydrationWarning>
      {descrever(data, agora)}
    </time>
  );
}
