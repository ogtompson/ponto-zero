import { useState } from "react";
import { Link, NavLink } from "react-router-dom";
import { Check, LogOut, Menu, UserRound } from "lucide-react";
import { Button } from "@/components/ui/button";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { useSair, useSessao } from "@/hooks/dados";
import { cn } from "@/lib/utils";
import { DialogoConta } from "./DialogoConta";
import { LogoPontoZero } from "./Marca";

const LINKS = [
  { para: "/", texto: "Início" },
  { para: "/explorar", texto: "Explorar" },
  { para: "/analises", texto: "Minhas análises" },
];

export function Cabecalho() {
  const sessao = useSessao();
  const sair = useSair();
  const [conta, setConta] = useState(false);
  const u = sessao.data;

  return (
    <header className="z-[600] flex min-h-14 shrink-0 items-center gap-3 border-b border-nevoa bg-white px-3 sm:px-4">
      <Link to="/" aria-label="PontoZero, início" className="shrink-0 rounded-sm">
        <LogoPontoZero className="h-[30px]" />
      </Link>
      <nav className="hidden min-w-0 items-center gap-0.5 md:flex" aria-label="Principal">
        {LINKS.map((l) => (
          <NavLink
            key={l.para}
            to={l.para}
            end={l.para === "/"}
            className={({ isActive }) =>
              cn(
                "whitespace-nowrap rounded-md px-2.5 py-1.5 text-[14px] font-semibold transition-colors",
                isActive ? "text-marinho shadow-[inset_0_-2px_0_#DDBA43]" : "text-tinta-suave hover:text-marinho",
              )
            }
          >
            {l.texto}
          </NavLink>
        ))}
      </nav>
      <div className="ml-auto shrink-0">
        {u ? (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm" className="gap-2">
                <span className="flex size-7 items-center justify-center rounded-full bg-marinho text-[12px] font-bold text-ouro">
                  {u.nome.trim()[0]?.toUpperCase()}
                </span>
                <span className="hidden max-w-36 truncate sm:inline">{u.nome.split(" ")[0]}</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel>
                <span className="block font-semibold text-marinho">{u.nome}</span>
                {u.empresa}
                {u.segmento ? `, ${u.segmento}` : ""}
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem asChild>
                <Link to="/analises">
                  <UserRound /> Minhas análises
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem onSelect={() => sair.mutate()}>
                <LogOut /> Sair
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        ) : (
          <Button size="sm" onClick={() => setConta(true)} disabled={sessao.isLoading}>
            Entrar
          </Button>
        )}
      </div>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="icon" className="md:hidden" aria-label="Abrir menu principal">
            <Menu />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-56">
          <DropdownMenuLabel>Navegação</DropdownMenuLabel>
          <DropdownMenuSeparator />
          {LINKS.map((l) => (
            <DropdownMenuItem key={l.para} asChild>
              <NavLink to={l.para} end={l.para === "/"} className="min-h-11">
                {({ isActive }) => (
                  <>
                    <Check className={cn(isActive ? "opacity-100" : "opacity-0")} aria-hidden="true" />
                    {l.texto}
                  </>
                )}
              </NavLink>
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>
      <DialogoConta aberto={conta} aoMudar={setConta} />
    </header>
  );
}
