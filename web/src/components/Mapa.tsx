// HU-003: mapa interativo de regiões. Clicar num bairro inclui ou tira da seleção
// (é a mesma seleção do filtro de regiões, HU-004 RN03).
import { useEffect, useMemo, useRef } from "react";
import L from "leaflet";
import { MapContainer, Pane, TileLayer, useMap } from "react-leaflet";
import { useMapa, useOfertaMapa, useRegioes, useSegmentos } from "@/hooks/dados";
import { num } from "@/lib/formato";
import { useSelecao, type CorMapa } from "@/lib/selecao";
import { PINO_SVG } from "./Marca";

const ESCALAS: Record<CorMapa, string[]> = {
  populacao: ["#edf7f3", "#c7e7dd", "#88cbbc", "#3f9f91", "#176b62"],
  renda: ["#fff8e6", "#f4e1a1", "#dfbd4e", "#b8891d", "#76570d"],
  oferta: ["#fff2e9", "#f7ccb5", "#ed9b78", "#d5654c", "#963b3e"],
};
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

function corPara(valor: number | null | undefined, cortes: number[], escala: string[]) {
  if (valor == null) return "#ffffff";
  let i = 0;
  while (i < cortes.length && valor > cortes[i]) i++;
  return escala[i];
}

export function useLegenda() {
  const { cor, segmento } = useSelecao();
  const regioes = useRegioes();
  const oferta = useOfertaMapa(segmento);
  const segmentos = useSegmentos();
  const nomeSeg = segmentos.data?.find((s) => s.id_categoria === segmento)?.nome;

  return useMemo(() => {
    const valores = new Map<number, number | null>();
    const quantidades = new Map<number, number>();
    if (oferta.data) oferta.data.forEach((o) => quantidades.set(o.id_regiao, o.quantidade));
    if (cor === "oferta" && oferta.data) oferta.data.forEach((o) => valores.set(o.id_regiao, o.por_10k_hab));
    else
      regioes.data?.forEach((r) => valores.set(r.id_regiao, cor === "renda" ? r.renda : r.populacao));
    const lista = [...valores.values()].filter((v): v is number => v != null);
    const cortes = quebras(lista);
    const escala = ESCALAS[cor];
    const titulo =
      cor === "populacao"
        ? "Moradores por bairro (Censo 2022)"
        : cor === "renda"
          ? "Renda média domiciliar (Censo 2010)"
          : `${nomeSeg ?? "Estabelecimentos"} por 10 mil habitantes`;
    const fmt = (v: number) => (cor === "renda" ? `R$ ${num(v)}` : num(v, cor === "oferta" ? 1 : 0));
    return { valores, quantidades, cortes, escala, titulo, fmt, min: Math.min(...lista), max: Math.max(...lista) };
  }, [cor, oferta.data, regioes.data, nomeSeg]);
}

function CamadaBairros({ legenda }: { legenda: ReturnType<typeof useLegenda> }) {
  const map = useMap();
  const mapa = useMapa();
  const { regioes, alternarRegiao, cor } = useSelecao();
  const camada = useRef<L.GeoJSON | null>(null);
  const mascara = useRef<L.Polygon | null>(null);
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
        });
      },
    });
    g.addTo(map);
    camada.current = g;
    const mundo: L.LatLngExpression[] = [[-85, -180], [-85, 180], [85, 180], [85, -180]];
    const bairros: L.LatLngExpression[][] = [];
    for (const feature of mapa.data.features) {
      const geometria = feature.geometry;
      if (geometria.type === "Polygon") bairros.push(geometria.coordinates[0].map(([lng, lat]) => [lat, lng]));
      if (geometria.type === "MultiPolygon") {
        geometria.coordinates.forEach((poligono) => bairros.push(poligono[0].map(([lng, lat]) => [lat, lng])));
      }
    }
    mascara.current = L.polygon([mundo, ...bairros], {
      pane: "mascara",
      stroke: false,
      fillColor: "#f3f2ee",
      fillOpacity: 1,
      fillRule: "evenodd",
      interactive: false,
    }).addTo(map);
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
      });
    }
    function dica(p: Props) {
      const { legenda: lg, regioes: sel, cor: c } = estado.current;
      const v = lg.valores.get(p.id_regiao);
      const valor = v == null ? "indisponível" : lg.fmt(v);
      const acao = sel.includes(p.id_regiao) ? "Clique para tirar da seleção" : "Clique para incluir na seleção";
      if (c === "oferta") {
        const quantidade = lg.quantidades.get(p.id_regiao);
        const total = quantidade == null ? "indisponível" : num(quantidade);
        return `<strong style="font-size:13.5px">${p.nome}</strong><br/>Empresas formais: ${total}<br/>Por 10 mil moradores: ${valor}<br/><span style="opacity:.7">${acao}</span>`;
      }
      const rotulo = c === "populacao" ? "Moradores" : "Renda média";
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
        fillColor: selecionado ? "#DDBA43" : corPara(legenda.valores.get(p.id_regiao), legenda.cortes, legenda.escala),
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
          url="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}"
          maxNativeZoom={16}
          maxZoom={18}
          attribution='Tiles &copy; Esri, HERE, Garmin, OpenStreetMap contributors and the GIS user community | Bairros: Prefeitura do Recife'
        />
        <Pane name="rotulos" style={{ zIndex: 450, pointerEvents: "none" }}>
          <TileLayer
            url="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Reference/MapServer/tile/{z}/{y}/{x}"
            maxNativeZoom={16}
            maxZoom={18}
            pane="rotulos"
          />
        </Pane>
        <Pane name="mascara" style={{ zIndex: 460, pointerEvents: "none" }} />
        <Pane name="pinos" style={{ zIndex: 660, pointerEvents: "none" }} />
        <CamadaBairros legenda={legenda} />
        <ZoomCanto />
        <AjustaTamanho />
      </MapContainer>
      <p className="pointer-events-none absolute left-3 top-3 z-[500] max-w-64 rounded-md bg-white/95 px-3 py-2 text-[11.5px] leading-snug text-tinta-suave shadow-sm">
        Clique no mapa ou use <strong className="text-marinho">Procurar bairro</strong> para navegar pelo teclado.
      </p>
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
  if (!legenda.cortes.length) return null;
  const faixas = [legenda.min, ...legenda.cortes, legenda.max];
  return (
    <div className="pointer-events-none absolute bottom-3 left-3 z-[500] w-60 rounded-md bg-white/95 p-3 shadow-[0_6px_24px_rgb(25_33_74/0.14)]">
      <p className="text-[12.5px] font-semibold leading-tight text-marinho">{legenda.titulo}</p>
      <div className="mt-2 flex h-2.5 overflow-hidden rounded-full">
        {legenda.escala.map((c) => (
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
      </div>
    </div>
  );
}
