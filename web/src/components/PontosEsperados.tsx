export function PontosEsperados({ esperado, encontrados }: { esperado: number | null; encontrados: number }) {
  if (esperado == null) return <div className="hachura h-10 w-full rounded" aria-label="Referência proporcional indisponível" />;
  const maior = Math.max(esperado, encontrados, 1);
  const larguraEsperada = (esperado / maior) * 100;
  const larguraEncontrada = (encontrados / maior) * 100;
  return (
    <div className="space-y-2" role="img" aria-label={`${encontrados} registros observados; referência proporcional de ${esperado.toLocaleString("pt-BR")}`}>
      <div>
        <div className="mb-1 flex justify-between gap-3 text-[11px] text-tinta-suave"><span>Observado</span><span className="numeros">{encontrados.toLocaleString("pt-BR")}</span></div>
        <div className="h-2 rounded-full bg-nevoa"><div className="h-full rounded-full bg-ouro ring-1 ring-inset ring-marinho/35" style={{ width: `${larguraEncontrada}%` }} /></div>
      </div>
      <div>
        <div className="mb-1 flex justify-between gap-3 text-[11px] text-tinta-suave"><span>Referência proporcional</span><span className="numeros">{esperado.toLocaleString("pt-BR")}</span></div>
        <div className="h-2 rounded-full bg-nevoa"><div className="h-full min-w-px rounded-full border border-dashed border-marinho/55 bg-marinho/10" style={{ width: `${larguraEsperada}%` }} /></div>
      </div>
    </div>
  );
}
