// HU-003: mapa interativo de regiões. Clicar num bairro inclui ou tira da seleção
// (é a mesma seleção do filtro de regiões, HU-004 RN03).
import { useEffect, useMemo, useRef } from "react";
import L from "leaflet";
import { MapContainer, Pane, TileLayer, useMap } from "react-leaflet";
import { useMapa, useOferta, useOfertaMapa, useRegioes, useSegmentos } from "@/hooks/dados";
import { num } from "@/lib/formato";
import { useSelecao } from "@/lib/selecao";
import { PINO_SVG } from "./Marca";

const ESCALA = ["#eef0f7", "#c9cee3", "#98a2c9", "#5c69a3", "#2b3672"];
const MARCO_ZERO: [number, number] = [-8.0631, -34.8711];
const CENTRO_RECIFE: [number, number] = [-8.05, -34.93];

type Props = {
  id_regiao: number;
  nome: string;
  lat: number;
  lng: number;
};

function quebras(valores: number[]): number[] {
  const v = [...valores].sort((a, b) => a - b);
  if (!v.length) return [];
  return [0.2, 0.4, 0.6, 0.8].map((q) => v[Math.min(v.length - 1, Math.floor(q * v.length))]);
}

function corPara(valor: number | null | undefined, cortes: number[]) {
  if (valor == null) return "#ffffff";
  let i = 0;
  while (i < cortes.length && valor > cortes[i]) i++;
  return ESCALA[i];
}

export function useLegenda() {
  const { cor, segmento } = useSelecao();
  const regioes = useRegioes();
  const oferta = useOfertaMapa(segmento);
  const segmentos = useSegmentos();
  const nomeSeg = segmentos.data?.find((s) => s.id_categoria === segmento)?.nome;

  return useMemo(() => {
    const valores = new Map<number, number | null>();
    if (cor === "oferta" && oferta.data) oferta.data.forEach((o) => valores.set(o.id_regiao, o.por_10k_hab));
    else
      regioes.data?.forEach((r) => valores.set(r.id_regiao, cor === "renda" ? r.renda : r.populacao));
    const lista = [...valores.values()].filter((v): v is number => v != null);
    const cortes = quebras(lista);
    const titulo =
      cor === "populacao"
        ? "Moradores por bairro (Censo 2022)"
        : cor === "renda"
          ? "Renda média domiciliar (Censo 2010)"
          : `${nomeSeg ?? "Estabelecimentos"} por 10 mil habitantes`;
    const fmt = (v: number) => (cor === "renda" ? `R$ ${num(v)}` : num(v, cor === "oferta" ? 1 : 0));
    return { valores, cortes, titulo, fmt, min: Math.min(...lista), max: Math.max(...lista) };
  }, [cor, oferta.data, regioes.data, nomeSeg]);
}

function CamadaBairros({ legenda }: { legenda: ReturnType<typeof useLegenda> }) {
  const map = useMap();
  const mapa = useMapa();
  const { regioes, alternarRegiao, cor } = useSelecao();
  const camada = useRef<L.GeoJSON | null>(null);
  const pinos = useRef<L.LayerGroup | null>(null);
  const primeiraVez = useRef(true);

  // refs com o valor mais recente para os eventos do Leaflet
  const estado = useRef({ regioes, alternarRegiao, legenda, cor });
  estado.current = { regioes, alternarRegiao, legenda, cor };

  // cria a camada uma vez
  useEffect(() => {
    if (!mapa.data || camada.current) return;
    const g = L.geoJSON(mapa.data as GeoJSON.FeatureCollection, {
      onEachFeature: (feature, layer) => {
        const p = feature.properties as Props;
        layer.bindTooltip(() => dica(p), { sticky: true, className: "pz-dica", direction: "top", offset: [0, -8] });
        layer.on({
          click: () => estado.current.alternarRegiao(p.id_regiao),
          mouseover: (e) => (e.target as L.Path).setStyle({ weight: 2.4, color: "#19214A" }),
          mouseout: (e) => g.resetStyle(e.target as L.Path),
          keypress: (e) => {
            const tecla = (e as unknown as { originalEvent: KeyboardEvent }).originalEvent?.key;
            if (tecla === "Enter" || tecla === " ") estado.current.alternarRegiao(p.id_regiao);
          },
        });
      },
    });
    g.addTo(map);
    camada.current = g;
    pinos.current = L.layerGroup().addTo(map);
    map.fitBounds(g.getBounds(), { padding: [8, 8] });
    map.attributionControl.setPrefix('<a href="https://leafletjs.com">Leaflet</a>');

    // revelação a partir do Marco Zero (uma vez, na primeira carga)
    if (primeiraVez.current) {
      primeiraVez.current = false;
      g.eachLayer((l) => {
        const p = (l as L.Layer & { feature?: GeoJSON.Feature }).feature?.properties as Props;
        const el = (l as L.Path).getElement() as SVGElement | undefined;
        if (!el || !p) return;
        const d = Math.hypot(p.lat - MARCO_ZERO[0], p.lng - MARCO_ZERO[1]);
        el.classList.add("pz-bairro");
        el.style.animationDelay = `${Math.round(d * 9000)}ms`;
        el.setAttribute("tabindex", "0");
        el.setAttribute("role", "button");
        el.setAttribute("aria-label", `Bairro ${p.nome}`);
      });
    }
    function dica(p: Props) {
      const { legenda: lg, regioes: sel, cor: c } = estado.current;
      const v = lg.valores.get(p.id_regiao);
      const rotulo = c === "populacao" ? "Moradores" : c === "renda" ? "Renda média" : "Por 10 mil hab.";
      const valor = v == null ? "indisponível" : lg.fmt(v);
      const acao = sel.includes(p.id_regiao) ? "Clique para tirar da seleção" : "Clique para incluir na seleção";
      return `<strong style="font-size:13.5px">${p.nome}</strong><br/>${rotulo}: ${valor}<br/><span style="opacity:.7">${acao}</span>`;
    }
  }, [mapa.data, map]);

  // estilo: cor do indicador + destaque dos selecionados
  useEffect(() => {
    const g = camada.current;
    if (!g) return;
    const estilo = (feature?: GeoJSON.Feature) => {
      const p = feature?.properties as Props;
      const selecionado = regioes.includes(p.id_regiao);
      return {
        fillColor: selecionado ? "#DDBA43" : corPara(legenda.valores.get(p.id_regiao), legenda.cortes),
        fillOpacity: selecionado ? 0.62 : 0.78,
        color: selecionado ? "#19214A" : "#ffffff",
        weight: selecionado ? 2.6 : 0.9,
        dashArray: legenda.valores.get(p.id_regiao) == null && !selecionado ? "3 3" : undefined,
      } as L.PathOptions;
    };
    g.options.style = estilo as L.StyleFunction;
    g.setStyle(estilo as L.StyleFunction);
    g.eachLayer((l) => {
      const p = (l as L.Layer & { feature?: GeoJSON.Feature }).feature?.properties as Props;
      if (p && regioes.includes(p.id_regiao)) (l as L.Path).bringToFront();
    });

    // pinos da marca nos bairros escolhidos
    const grupo = pinos.current;
    if (!grupo || !mapa.data) return;
    grupo.clearLayers();
    for (const f of mapa.data.features) {
      const p = f.properties as Props;
      if (!regioes.includes(p.id_regiao)) continue;
      L.marker([p.lat, p.lng], {
        icon: L.divIcon({ html: `<span class="pz-pino-in">${PINO_SVG}</span>`, className: "pz-pino", iconSize: [26, 33], iconAnchor: [13, 33] }),
        interactive: false,
        keyboard: false,
        pane: "pinos",
      }).addTo(grupo);
    }
  }, [regioes, legenda, mapa.data]);

  return null;
}

function CamadaEstabelecimentos() {
  const map = useMap();
  const { segmento, regioes } = useSelecao();
  const oferta = useOferta(segmento, regioes);
  const grupo = useRef<L.LayerGroup | null>(null);

  useEffect(() => {
    if (!grupo.current) grupo.current = L.layerGroup().addTo(map);
    const g = grupo.current;
    g.clearLayers();
    if (!segmento || !oferta.data) return;
    const daCidade = regioes.length === 0;
    for (const e of oferta.data.estabelecimentos) {
      L.circleMarker([e.lat, e.lng], {
        radius: daCidade ? 3.2 : 5,
        fillColor: "#DDBA43",
        fillOpacity: 1,
        color: "#19214A",
        weight: daCidade ? 1 : 1.6,
        pane: "estabelecimentos",
      })
        .bindPopup(
          `<strong>${escapar(e.nome)}</strong><br/>${e.endereco ? escapar(e.endereco) + "<br/>" : ""}<span style="color:#596182">${escapar(e.regiao)}</span>`,
        )
        .addTo(g);
    }
  }, [oferta.data, segmento, regioes.length, map]);

  return null;
}

function escapar(t: string) {
  return t.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]!);
}

function AjustaTamanho() {
  const map = useMap();
  useEffect(() => {
    const el = map.getContainer();
    const obs = new ResizeObserver(() => map.invalidateSize());
    obs.observe(el);
    return () => obs.disconnect();
  }, [map]);
  return null;
}

export function Mapa() {
  const legenda = useLegenda();
  return (
    <div className="relative h-full w-full">
      <MapContainer
        center={CENTRO_RECIFE}
        zoom={12}
        minZoom={11}
        maxZoom={17}
        zoomControl={false}
        zoomSnap={0.25}
        className="h-full w-full"
        attributionControl
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a> | Bairros: Prefeitura do Recife'
        />
        <Pane name="rotulos" style={{ zIndex: 450, pointerEvents: "none" }}>
          <TileLayer url="https://{s}.basemaps.cartocdn.com/light_only_labels/{z}/{x}/{y}{r}.png" pane="rotulos" opacity={0.85} />
        </Pane>
        <Pane name="estabelecimentos" style={{ zIndex: 620 }} />
        <Pane name="pinos" style={{ zIndex: 660, pointerEvents: "none" }} />
        <CamadaBairros legenda={legenda} />
        <CamadaEstabelecimentos />
        <ZoomCanto />
        <AjustaTamanho />
      </MapContainer>
      <Legenda legenda={legenda} />
    </div>
  );
}

function ZoomCanto() {
  const map = useMap();
  useEffect(() => {
    const z = L.control.zoom({ position: "topright", zoomInTitle: "Aproximar", zoomOutTitle: "Afastar" });
    z.addTo(map);
    return () => {
      z.remove();
    };
  }, [map]);
  return null;
}

function Legenda({ legenda }: { legenda: ReturnType<typeof useLegenda> }) {
  const { segmento } = useSelecao();
  if (!legenda.cortes.length) return null;
  const faixas = [legenda.min, ...legenda.cortes, legenda.max];
  return (
    <div className="pointer-events-none absolute bottom-3 left-3 z-[500] w-60 rounded-md bg-white/95 p-3 shadow-[0_6px_24px_rgb(25_33_74/0.14)]">
      <p className="text-[12.5px] font-semibold leading-tight text-marinho">{legenda.titulo}</p>
      <div className="mt-2 flex h-2.5 overflow-hidden rounded-full">
        {ESCALA.map((c) => (
          <span key={c} className="flex-1" style={{ background: c }} />
        ))}
      </div>
      <div className="mt-1 flex justify-between text-[11px] text-tinta-suave numeros">
        <span>{legenda.fmt(faixas[0])}</span>
        <span>{legenda.fmt(faixas[faixas.length - 1])}</span>
      </div>
      <div className="mt-2 flex items-center gap-3 text-[11px] text-tinta-suave">
        <span className="flex items-center gap-1.5">
          <span className="inline-block size-3 rounded-[3px] border-2 border-marinho bg-ouro/70" /> escolhido
        </span>
        {segmento != null && (
          <span className="flex items-center gap-1.5">
            <span className="inline-block size-2.5 rounded-full border-[1.5px] border-marinho bg-ouro" /> estabelecimento
          </span>
        )}
      </div>
    </div>
  );
}
