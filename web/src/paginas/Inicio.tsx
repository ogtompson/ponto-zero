import { ArrowRight, BarChart3, MapPinned, Search, ShieldCheck, Store } from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";

const PASSOS = [
  {
    numero: "01",
    titulo: "Defina o que você procura",
    texto: "Escolha um segmento e os bairros de Recife que fazem sentido para sua ideia ou operação.",
  },
  {
    numero: "02",
    titulo: "Compare o território",
    texto: "Consulte população, renda e oferta comercial com as mesmas métricas em todas as regiões.",
  },
  {
    numero: "03",
    titulo: "Aprofunde as hipóteses",
    texto: "Entenda quais regiões merecem investigação adicional e por que foram sinalizadas.",
  },
];

export function Inicio() {
  return (
    <div className="flex-1 bg-white">
      <section className="border-b border-nevoa">
        <div className="mx-auto grid w-full max-w-7xl gap-10 px-5 py-16 sm:px-8 sm:py-20 lg:grid-cols-[1.05fr_.95fr] lg:items-center lg:gap-16 lg:py-24">
          <div>
            <p className="text-sm font-bold uppercase tracking-[0.14em] text-ouro-escuro">Inteligência territorial para decisões comerciais</p>
            <h1 className="larga mt-4 max-w-3xl text-[40px] font-extrabold leading-[1.02] text-marinho sm:text-[54px]">
              Comece pelo território antes de escolher o endereço.
            </h1>
            <p className="mt-6 max-w-2xl text-[17px] leading-relaxed text-tinta-suave sm:text-[19px]">
              Compare bairros do Recife, relacione demanda potencial e oferta local e reconheça possíveis oportunidades para abrir um negócio ou uma nova unidade.
            </p>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Button asChild size="lg" className="h-12 px-5">
                <Link to="/explorar">Explorar o mapa <ArrowRight /></Link>
              </Button>
              <Button asChild size="lg" variant="outline" className="h-12 px-5">
                <a href="#como-funciona">Entender como funciona</a>
              </Button>
            </div>
            <p className="mt-4 flex max-w-xl items-start gap-2 text-[13px] leading-relaxed text-tinta-fraca">
              <ShieldCheck className="mt-0.5 size-4 shrink-0 text-marinho-3" aria-hidden="true" />
              Uma análise preliminar com fontes e limitações visíveis. Não é recomendação de investimento nem substitui estudo de viabilidade.
            </p>
          </div>

          <div className="relative mx-auto w-full max-w-xl" aria-label="Exemplo da análise territorial do PontoZero">
            <div className="rounded-lg border border-nevoa bg-papel p-3 shadow-[0_20px_60px_rgb(25_33_74/0.14)] sm:p-5">
              <div className="flex items-center justify-between border-b border-nevoa pb-4">
                <div>
                  <p className="text-[12px] font-bold uppercase tracking-wider text-tinta-fraca">Análise em andamento</p>
                  <p className="mt-1 font-bold text-marinho">Cafeteria em Recife</p>
                </div>
                <span className="rounded-full bg-ouro-claro px-3 py-1 text-xs font-bold text-ouro-escuro">3 bairros</span>
              </div>
              <div className="grid gap-3 py-4 sm:grid-cols-3">
                <Resumo icone={<MapPinned />} rotulo="Território" valor="Boa Viagem" />
                <Resumo icone={<Store />} rotulo="Oferta observada" valor="6,4 / 10 mil" />
                <Resumo icone={<BarChart3 />} rotulo="População" valor="122 mil" />
              </div>
              <div className="rounded-md bg-white p-4">
                <div className="flex items-center gap-2 text-sm font-bold text-marinho">
                  <Search className="size-4 text-ouro-escuro" /> Hipótese para aprofundar
                </div>
                <p className="mt-2 text-[13px] leading-relaxed text-tinta-suave">
                  A oferta observada pode estar abaixo da referência municipal. Confira cobertura, fontes e comparação antes de avançar.
                </p>
                <div className="mt-4 flex gap-1.5" aria-hidden="true">
                  <span className="h-2 flex-[3] rounded-full bg-marinho" />
                  <span className="h-2 flex-[2] rounded-full bg-marinho-3" />
                  <span className="h-2 flex-1 rounded-full bg-ouro" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="como-funciona" className="scroll-mt-20 bg-papel">
        <div className="mx-auto w-full max-w-7xl px-5 py-16 sm:px-8 sm:py-20">
          <div className="max-w-2xl">
            <p className="text-sm font-bold uppercase tracking-[0.14em] text-ouro-escuro">Da ideia à investigação</p>
            <h2 className="larga mt-3 text-[30px] font-extrabold leading-tight text-marinho sm:text-[38px]">Uma análise espacial em três movimentos.</h2>
            <p className="mt-3 text-[16px] leading-relaxed text-tinta-suave">O PontoZero organiza a triagem inicial; a decisão final continua sendo sua.</p>
          </div>
          <ol className="mt-10 grid border-y border-nevoa md:grid-cols-3 md:divide-x md:divide-nevoa">
            {PASSOS.map((passo) => (
              <li key={passo.numero} className="border-b border-nevoa py-7 last:border-b-0 md:border-b-0 md:px-7 md:first:pl-0 md:last:pr-0">
                <span className="numeros text-sm font-extrabold text-ouro-escuro">{passo.numero}</span>
                <h3 className="semi-larga mt-3 text-xl font-bold text-marinho">{passo.titulo}</h3>
                <p className="mt-2 text-[14.5px] leading-relaxed text-tinta-suave">{passo.texto}</p>
              </li>
            ))}
          </ol>
          <div className="mt-10 flex flex-col items-start justify-between gap-5 sm:flex-row sm:items-center">
            <div>
              <p className="font-bold text-marinho">Sua análise pode começar sem cadastro.</p>
              <p className="mt-1 text-sm text-tinta-suave">Crie uma conta somente quando quiser salvar e retomar o estudo.</p>
            </div>
            <Button asChild variant="ouro" size="lg">
              <Link to="/explorar">Começar uma análise <ArrowRight /></Link>
            </Button>
          </div>
        </div>
      </section>
    </div>
  );
}

function Resumo({ icone, rotulo, valor }: { icone: React.ReactNode; rotulo: string; valor: string }) {
  return (
    <div className="rounded-md border border-nevoa bg-white p-3">
      <span className="text-marinho-3 [&_svg]:size-4">{icone}</span>
      <p className="mt-3 text-[11px] font-semibold uppercase tracking-wide text-tinta-fraca">{rotulo}</p>
      <p className="mt-0.5 text-[13.5px] font-bold text-marinho">{valor}</p>
    </div>
  );
}
