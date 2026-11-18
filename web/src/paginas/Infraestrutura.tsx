// Tela para a avaliação de Infraestrutura de Software: mostra, ao vivo, os três
// containers, a comunicação entre eles e a prova de que os dados vivem no volume.
import { forwardRef, useRef } from "react";
import { Database, Globe, HardDrive, Server, Monitor } from "lucide-react";
import { AnimatedBeam } from "@/components/ui/animated-beam";
import { NumberTicker } from "@/components/ui/number-ticker";
import { LogoCesar } from "@/components/Marca";
import { useStatus } from "@/hooks/dados";
import { dataHora, duracao } from "@/lib/formato";
import { cn } from "@/lib/utils";

const No = forwardRef<
  HTMLDivElement,
  { titulo: string; detalhe: string; icone: React.ReactNode; ok?: boolean | null; extra?: React.ReactNode; className?: string }
>(({ titulo, detalhe, icone, ok, extra, className }, ref) => (
  <div ref={ref} className={cn("relative z-10 flex w-full flex-col gap-1 rounded-lg border border-nevoa bg-white p-4 shadow-[0_4px_18px_rgb(25_33_74/0.07)]", className)}>
    <div className="flex items-start gap-2.5">
      <span className="flex size-9 shrink-0 items-center justify-center rounded-md bg-marinho text-ouro [&_svg]:size-[18px]">{icone}</span>
      <div className="min-w-0">
        <p className="semi-larga flex items-center gap-2 text-[15px] font-bold leading-tight text-marinho">
          {titulo}
          {ok != null && (
            <span className={cn("inline-flex items-center gap-1 whitespace-nowrap rounded-full px-1.5 py-px text-[11px] font-semibold", ok ? "bg-[#e3f4ea] text-[#1f7a46]" : "bg-destructive/10 text-destructive")}>
              <span className={cn("size-1.5 rounded-full", ok ? "bg-[#1f9d55]" : "bg-destructive")} />
              {ok ? "no ar" : "fora do ar"}
            </span>
          )}
        </p>
        <p className="mt-0.5 text-[12px] leading-snug text-tinta-suave">{detalhe}</p>
      </div>
    </div>
    {extra && <div className="mt-2 text-[12.5px] leading-snug text-tinta-suave">{extra}</div>}
  </div>
));
No.displayName = "No";

const APP = ["empresa", "usuario", "analise", "regiao_analise", "relatorio"];
const CARGA = ["regiao", "indicador", "estabelecimento", "categoria"];

export function Infraestrutura() {
  const status = useStatus();
  const s = status.data;
  const apiOk = status.isError ? false : s ? true : null;
  const dbOk = status.isError ? false : s ? !!s.banco : null;

  const caixa = useRef<HTMLDivElement>(null);
  const navegador = useRef<HTMLDivElement>(null);
  const web = useRef<HTMLDivElement>(null);
  const api = useRef<HTMLDivElement>(null);
  const db = useRef<HTMLDivElement>(null);
  const volume = useRef<HTMLDivElement>(null);

  return (
    <div className="mx-auto w-full max-w-6xl flex-1 px-4 py-8 sm:px-6">
      <header className="max-w-2xl">
        <h1 className="larga text-[30px] font-extrabold leading-tight text-marinho">Como o PontoZero roda</h1>
        <p className="mt-2 text-[15.5px] text-tinta-suave">
          Três containers ligados pelo Docker Compose. O banco grava num volume: desligar e religar os containers não apaga os dados.
        </p>
      </header>

      <div ref={caixa} className="relative mt-8 grid gap-6 md:grid-cols-4 md:gap-8">
        <No ref={navegador} titulo="Seu navegador" detalhe="http://localhost:8080" icone={<Monitor />} extra={<>Você está aqui. Tudo passa pela porta 8080 do container web.</>} />
        <No
          ref={web}
          titulo="web"
          detalhe="Nginx com o React compilado"
          icone={<Globe />}
          ok={apiOk == null ? null : true}
          extra={<>Entrega as telas e repassa /api para o container api.</>}
        />
        <No
          ref={api}
          titulo="api"
          detalhe="Python 3.12 e FastAPI, porta 8000"
          icone={<Server />}
          ok={apiOk}
          extra={
            s ? (
              <>
                Container <code className="font-semibold text-marinho">{s.api.container}</code>
                <br />
                No ar há {duracao(s.api.segundos_no_ar)}
              </>
            ) : status.isError ? (
              "Sem resposta da API."
            ) : (
              "Consultando..."
            )
          }
        />
        <No
          ref={db}
          titulo="db"
          detalhe="PostgreSQL 16, porta 5432"
          icone={<Database />}
          ok={dbOk}
          extra={
            s?.banco ? (
              <>
                Ligado desde {dataHora(s.banco.ligado_em)}
                <br />
                Endereço interno {s.banco.ip ?? "?"}, usuário {s.banco.usuario}
              </>
            ) : (
              "Sem resposta do banco."
            )
          }
        />
        <div className="md:col-start-4">
          <No
            ref={volume}
            titulo="volume pgdata"
            detalhe="/var/lib/postgresql/data"
            icone={<HardDrive />}
            extra={
              s?.banco?.volume_inicializado_em ? (
                <>
                  Criado em <strong className="text-marinho">{dataHora(s.banco.volume_inicializado_em)}</strong>
                  <br />
                  {s.banco.tamanho} de dados
                </>
              ) : (
                "Aguardando o banco."
              )
            }
          />
        </div>
        <AnimatedBeam containerRef={caixa} fromRef={navegador} toRef={web} duration={3} ativo={apiOk !== false} />
        <AnimatedBeam containerRef={caixa} fromRef={web} toRef={api} duration={3} delay={0.4} ativo={apiOk === true} />
        <AnimatedBeam containerRef={caixa} fromRef={api} toRef={db} duration={3} delay={0.8} ativo={dbOk === true} />
        <AnimatedBeam containerRef={caixa} fromRef={db} toRef={volume} duration={3} delay={1.2} ativo={dbOk === true} />
      </div>

      <div className="mt-10 grid gap-6 lg:grid-cols-[1.3fr_1fr]">
        <section className="rounded-lg border border-nevoa bg-white p-5">
          <h2 className="semi-larga text-[17px] font-bold text-marinho">O que está guardado no volume</h2>
          <div className="mt-4 grid gap-6 sm:grid-cols-2">
            <Contagens titulo="Criado por quem usa o app" tabelas={APP} contagens={s?.banco?.contagens} />
            <Contagens titulo="Carregado na criação do banco" tabelas={CARGA} contagens={s?.banco?.contagens} />
          </div>
        </section>
        <section className="rounded-lg bg-marinho p-5 text-white">
          <h2 className="semi-larga text-[17px] font-bold">Teste de persistência</h2>
          <p className="mt-1 text-[14px] text-white/75">
            Crie uma conta e salve uma análise. Depois rode, na pasta do projeto:
          </p>
          <pre className="mt-3 overflow-x-auto rounded-md bg-black/25 p-3 text-[13px] leading-relaxed text-ouro">
{`docker compose down
docker compose up -d`}
          </pre>
          <p className="mt-3 text-[14px] text-white/75">
            Ao voltar, “ligado desde” muda, mas a data de criação do volume e as contagens continuam as mesmas. Só{" "}
            <code className="text-white">docker compose down -v</code> apaga o volume.
          </p>
        </section>
      </div>

      <footer className="mt-10 flex flex-wrap items-center gap-4 border-t border-nevoa pt-6">
        <LogoCesar className="h-11" />
        <div className="text-[13px] leading-relaxed text-tinta-suave">
          <p className="font-semibold text-marinho">Projeto final em conjunto: Infraestrutura de Software e Banco de Dados</p>
          <p>Bacharelado em Sistemas de Informação, CESAR School, 2026.2. Equipe 2 do PontoZero.</p>
        </div>
      </footer>
    </div>
  );
}

function Contagens({ titulo, tabelas, contagens }: { titulo: string; tabelas: string[]; contagens?: Record<string, number> }) {
  return (
    <div>
      <p className="text-[13px] text-tinta-suave">{titulo}</p>
      <dl className="mt-2 divide-y divide-nevoa">
        {tabelas.map((t) => (
          <div key={t} className="flex items-baseline justify-between py-1.5">
            <dt className="font-mono text-[13px] text-marinho">{t}</dt>
            <dd className="larga text-[18px] font-extrabold text-marinho">
              {contagens ? <NumberTicker value={contagens[t] ?? 0} /> : "–"}
            </dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
