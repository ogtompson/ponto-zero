import { useEffect, useState } from "react";
import { ArrowLeft, ArrowRight, BarChart3, Building2, Check, MapPinned, Search, Store, UserRound } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { FormularioConta } from "@/components/DialogoConta";
import { LogoPontoZero, Pino } from "@/components/Marca";
import { useSegmentos, useSessao } from "@/hooks/dados";
import { cn } from "@/lib/utils";

type Etapa = "splash" | "apresentacao" | "acesso" | "onboarding";
type Objetivo = "primeiro-negocio" | "nova-unidade" | "explorar";
type Momento = "descobrindo" | "comparando" | "planejando";

const OBJETIVOS: { valor: Objetivo; titulo: string; texto: string; icone: React.ReactNode }[] = [
  { valor: "primeiro-negocio", titulo: "Abrir meu primeiro negócio", texto: "Estou transformando uma ideia em uma decisão de localização.", icone: <UserRound /> },
  { valor: "nova-unidade", titulo: "Abrir uma nova unidade", texto: "Já tenho uma operação e quero avaliar outro território.", icone: <Building2 /> },
  { valor: "explorar", titulo: "Explorar possibilidades", texto: "Quero entender bairros e segmentos antes de definir um plano.", icone: <Search /> },
];

const MOMENTOS: { valor: Momento; texto: string }[] = [
  { valor: "descobrindo", texto: "Ainda estou descobrindo" },
  { valor: "comparando", texto: "Já estou comparando regiões" },
  { valor: "planejando", texto: "Estou planejando a abertura" },
];

export function Inicio() {
  const splashVista = typeof window !== "undefined" && sessionStorage.getItem("pontozero:splash-vista") === "1";
  const [etapa, setEtapa] = useState<Etapa>(splashVista ? "apresentacao" : "splash");
  const sessao = useSessao();

  useEffect(() => {
    if (etapa !== "splash") return;
    const reduzido = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const tempo = window.setTimeout(() => {
      sessionStorage.setItem("pontozero:splash-vista", "1");
      setEtapa("apresentacao");
    }, reduzido ? 800 : 2300);
    return () => window.clearTimeout(tempo);
  }, [etapa]);

  if (etapa === "splash") return <Splash />;

  return (
    <div className="min-h-dvh bg-white">
      {etapa === "apresentacao" && <Apresentacao aoContinuar={() => setEtapa("acesso")} />}
      {etapa === "acesso" && (
        <Acesso
          nome={sessao.data?.nome}
          aoVoltar={() => setEtapa("apresentacao")}
          aoContinuar={() => setEtapa("onboarding")}
        />
      )}
      {etapa === "onboarding" && <Onboarding aoVoltar={() => setEtapa("acesso")} />}
    </div>
  );
}

function Splash() {
  return (
    <div className="fixed inset-0 z-[2000] flex items-center justify-center overflow-hidden bg-marinho text-white" role="status" aria-label="Carregando PontoZero">
      <div className="pz-splash flex flex-col items-center">
        <Pino tamanho={64} className="pz-splash-pino drop-shadow-[0_12px_24px_rgb(0_0_0/0.24)]" />
        <LogoPontoZero claro className="pz-splash-logo mt-6 h-[74px]" />
        <span className="pz-splash-linha mt-7 h-0.5 w-28 origin-left bg-ouro" aria-hidden="true" />
      </div>
    </div>
  );
}

function Apresentacao({ aoContinuar }: { aoContinuar: () => void }) {
  return (
    <div className="mx-auto flex min-h-dvh w-full max-w-7xl flex-col px-5 py-6 sm:px-8 lg:py-8">
      <header className="flex items-center justify-between">
        <LogoPontoZero className="h-10" />
        <span className="hidden text-sm font-semibold text-tinta-fraca sm:block">Inteligência territorial para decisões comerciais</span>
      </header>
      <div className="grid flex-1 gap-12 py-12 lg:grid-cols-[1.05fr_.95fr] lg:items-center lg:gap-16 lg:py-16">
        <div>
          <h1 className="larga max-w-3xl text-[42px] font-extrabold leading-[1.02] text-marinho sm:text-[58px]">Antes do endereço, entenda onde sua análise deve começar.</h1>
          <p className="mt-6 max-w-2xl text-[17px] leading-relaxed text-tinta-suave sm:text-[19px]">
            O PontoZero reúne dados territoriais e oferta local para ajudar você a investigar possíveis oportunidades de abertura ou expansão em Recife.
          </p>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <Button size="lg" className="h-12 px-5" onClick={aoContinuar}>Conhecer o PontoZero <ArrowRight /></Button>
            <Button asChild size="lg" variant="ghost" className="h-12 px-5"><Link to="/explorar">Ir direto ao mapa</Link></Button>
          </div>
          <p className="mt-4 max-w-xl text-[12.5px] leading-relaxed text-tinta-fraca">Uma ferramenta de triagem. Não é recomendação de investimento nem substitui estudo de viabilidade.</p>
        </div>
        <Fluxo />
      </div>
    </div>
  );
}

function Fluxo() {
  const itens = [
    { icone: <Store />, titulo: "Escolha seu segmento", texto: "Comece pela ideia de negócio que quer investigar." },
    { icone: <MapPinned />, titulo: "Compare bairros", texto: "Observe território e oferta com critérios consistentes." },
    { icone: <BarChart3 />, titulo: "Aprofunde hipóteses", texto: "Entenda onde vale buscar mais evidências." },
  ];
  return (
    <div className="rounded-lg border border-nevoa bg-papel p-5 shadow-[0_20px_60px_rgb(25_33_74/0.12)] sm:p-7">
      <p className="text-xs font-bold uppercase tracking-wider text-tinta-fraca">O que você vai fazer</p>
      <ol className="mt-3 divide-y divide-nevoa">
        {itens.map((item, i) => (
          <li key={item.titulo} className="flex gap-4 py-5">
            <span className="flex size-10 shrink-0 items-center justify-center rounded-md bg-marinho text-ouro [&_svg]:size-[18px]">{item.icone}</span>
            <div>
              <p className="font-bold text-marinho"><span className="mr-2 text-ouro-escuro numeros">0{i + 1}</span>{item.titulo}</p>
              <p className="mt-1 text-sm leading-relaxed text-tinta-suave">{item.texto}</p>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}

function Acesso({ nome, aoVoltar, aoContinuar }: { nome?: string; aoVoltar: () => void; aoContinuar: () => void }) {
  const [modo, setModo] = useState<"escolha" | "entrar" | "criar">("escolha");
  if (modo !== "escolha") {
    return (
      <EtapaCentral numero="01 de 03" titulo={modo === "entrar" ? "Entre na sua conta." : "Crie sua conta."} texto="Sua conta preserva análises e relatórios. Você também pode explorar sem cadastro." aoVoltar={() => setModo("escolha")}>
        <div className="mt-8"><FormularioConta abaInicial={modo} mostrarCabecalho={false} aoConcluir={aoContinuar} /></div>
      </EtapaCentral>
    );
  }
  return (
    <EtapaCentral numero="01 de 03" titulo="Como você quer continuar?" texto="A conta é opcional. Ela serve para preservar análises e retomar seus estudos depois." aoVoltar={aoVoltar}>
      <div className="mt-8 grid gap-3">
        {nome ? <Button size="lg" className="h-12" onClick={aoContinuar}>Continuar como {nome.split(" ")[0]} <ArrowRight /></Button> : (
          <><Button size="lg" className="h-12" onClick={() => setModo("criar")}>Criar minha conta <ArrowRight /></Button><Button size="lg" variant="outline" className="h-12" onClick={() => setModo("entrar")}>Já tenho uma conta</Button></>
        )}
        {!nome && <button onClick={aoContinuar} className="min-h-11 rounded-md px-4 text-sm font-semibold text-tinta-suave underline-offset-4 hover:text-marinho hover:underline">Continuar sem conta</button>}
      </div>
      <div className="mt-8 border-t border-nevoa pt-6 text-sm text-tinta-suave">
        <p className="font-bold text-marinho">Com uma conta você pode:</p>
        <ul className="mt-3 grid gap-2">
          <li className="flex gap-2"><Check className="mt-0.5 size-4 shrink-0 text-ouro-escuro" /> salvar análises com dados e metodologia preservados;</li>
          <li className="flex gap-2"><Check className="mt-0.5 size-4 shrink-0 text-ouro-escuro" /> reabrir comparações e acessar relatórios exportados.</li>
        </ul>
      </div>
    </EtapaCentral>
  );
}

function Onboarding({ aoVoltar }: { aoVoltar: () => void }) {
  const navegar = useNavigate();
  const segmentos = useSegmentos();
  const [passo, setPasso] = useState<"objetivo" | "contexto">("objetivo");
  const [objetivo, setObjetivo] = useState<Objetivo | null>(null);
  const [momento, setMomento] = useState<Momento | null>(null);
  const [segmento, setSegmento] = useState("");
  useEffect(() => {
    document.getElementById("conteudo-principal")?.scrollTo({ top: 0, behavior: "instant" });
  }, [passo]);
  function concluir() {
    if (!objetivo || !momento) return;
    localStorage.setItem("pontozero:onboarding", JSON.stringify({ objetivo, momento, segmento: segmento ? Number(segmento) : null }));
    navegar(segmento ? `/explorar?segmento=${segmento}` : "/explorar");
  }
  if (passo === "objetivo") {
    return (
      <EtapaCentral numero="02 de 03" titulo="O que você pretende fazer?" texto="Escolha a opção que mais se aproxima do seu objetivo agora. Isso não limita as análises que você poderá criar." aoVoltar={aoVoltar} largo>
      <fieldset className="mt-8">
        <legend className="sr-only">Objetivo principal</legend>
        <div className="mt-3 grid gap-3 md:grid-cols-3">
          {OBJETIVOS.map((item) => (
            <button key={item.valor} type="button" onClick={() => setObjetivo(item.valor)} aria-pressed={objetivo === item.valor} className={cn("min-h-28 rounded-lg border p-4 text-left transition-colors md:min-h-36", objetivo === item.valor ? "border-marinho bg-marinho text-white" : "border-nevoa bg-white hover:border-marinho-3") }>
              <span className={cn("[&_svg]:size-5", objetivo === item.valor ? "text-ouro" : "text-marinho-3")}>{item.icone}</span>
              <span className="mt-4 block font-bold">{item.titulo}</span>
              <span className={cn("mt-1 block text-[13px] leading-relaxed", objetivo === item.valor ? "text-white/70" : "text-tinta-suave")}>{item.texto}</span>
            </button>
          ))}
        </div>
      </fieldset>
        <div className="mt-8 flex flex-col-reverse gap-3 sm:flex-row sm:items-center sm:justify-between">
          <Button asChild variant="ghost" size="lg"><Link to="/explorar">Pular personalização</Link></Button>
          <Button size="lg" className="h-12" disabled={!objetivo} onClick={() => setPasso("contexto")}>Continuar <ArrowRight /></Button>
        </div>
      </EtapaCentral>
    );
  }

  return (
    <EtapaCentral numero="03 de 03" titulo="Em que momento você está?" texto="Uma última informação ajuda a preparar seu ponto de partida. O segmento é opcional e pode ser alterado no mapa." aoVoltar={() => setPasso("objetivo")}>
      <div className="mt-8 grid gap-7">
        <fieldset>
          <legend className="font-bold text-marinho">Seu momento atual</legend>
          <div className="mt-3 grid gap-2">
            {MOMENTOS.map((item) => (
              <button key={item.valor} type="button" onClick={() => setMomento(item.valor)} aria-pressed={momento === item.valor} className={cn("flex min-h-11 items-center justify-between rounded-md border px-3 text-left text-sm font-semibold", momento === item.valor ? "border-marinho bg-ouro-claro text-marinho" : "border-nevoa bg-white text-tinta-suave hover:border-marinho-3")}>{item.texto}{momento === item.valor && <Check className="size-4" />}</button>
            ))}
          </div>
        </fieldset>
        <div className="border-t border-nevoa pt-6">
          <label htmlFor="onboarding-segmento" className="font-bold text-marinho">Segmento para a primeira análise <span className="font-normal text-tinta-fraca">(opcional)</span></label>
          <select id="onboarding-segmento" value={segmento} onChange={(e) => setSegmento(e.target.value)} className="mt-3 h-11 w-full rounded-md border border-input bg-white px-3 text-[15px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
            <option value="">Ainda não sei</option>
            {segmentos.data?.map((item) => <option key={item.id_categoria} value={item.id_categoria}>{item.nome}</option>)}
          </select>
          <p className="mt-2 text-xs leading-relaxed text-tinta-fraca">O piloto possui apenas segmentos com dados disponíveis. Essa escolha já prepara o mapa.</p>
        </div>
      </div>
      <div className="mt-8 flex justify-end"><Button size="lg" className="h-12 w-full sm:w-auto" disabled={!momento} onClick={concluir}>Preparar meu mapa <ArrowRight /></Button></div>
    </EtapaCentral>
  );
}

function EtapaCentral({ numero, titulo, texto, aoVoltar, largo = false, children }: { numero: string; titulo: string; texto: string; aoVoltar: () => void; largo?: boolean; children: React.ReactNode }) {
  return (
    <div className="mx-auto flex min-h-dvh w-full flex-col px-5 py-6 sm:px-8">
      <header className="flex items-center justify-between"><LogoPontoZero className="h-10" /><span className="text-xs font-bold uppercase tracking-wider text-tinta-fraca">{numero}</span></header>
      <div className={cn("mx-auto my-auto w-full py-10", largo ? "max-w-5xl" : "max-w-md")}>
        <button onClick={aoVoltar} className="mb-7 flex min-h-9 items-center gap-2 rounded-md text-sm font-semibold text-tinta-suave hover:text-marinho"><ArrowLeft className="size-4" /> Voltar</button>
        <h1 className="larga text-[34px] font-extrabold leading-tight text-marinho sm:text-[42px]">{titulo}</h1>
        <p className="mt-3 max-w-2xl text-[15px] leading-relaxed text-tinta-suave">{texto}</p>
        {children}
      </div>
    </div>
  );
}
