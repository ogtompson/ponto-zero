import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import {
  api,
  ErroApi,
  type AnaliseSalva,
  type Regiao,
  type RespostaAnalise,
  type RespostaComparacao,
  type RespostaDiagnostico,
  type RespostaIndicadores,
  type RespostaOferta,
  type Segmento,
  type Status,
  type Usuario,
} from "@/lib/api";

const lista = (ids: number[]) => ids.join(",");

export const useSegmentos = () =>
  useQuery({ queryKey: ["segmentos"], queryFn: () => api.get<Segmento[]>("/segmentos"), staleTime: Infinity });

export const useRegioes = () =>
  useQuery({ queryKey: ["regioes"], queryFn: () => api.get<Regiao[]>("/regioes"), staleTime: Infinity });

export const useMapa = () =>
  useQuery({
    queryKey: ["mapa"],
    queryFn: () => api.get<GeoJSON.FeatureCollection<GeoJSON.Geometry, { id_regiao: number; nome: string; lat: number; lng: number }>>("/mapa/bairros"),
    staleTime: Infinity,
  });

export const useOfertaMapa = (segmento: number | null) =>
  useQuery({
    queryKey: ["oferta-mapa", segmento],
    queryFn: () => api.get<{ id_regiao: number; quantidade: number; por_10k_hab: number | null }[]>(`/oferta/mapa?segmento=${segmento}`),
    enabled: segmento != null,
    staleTime: Infinity,
  });

export const useIndicadores = (ids: number[]) =>
  useQuery({
    queryKey: ["indicadores", lista(ids)],
    queryFn: () => api.get<RespostaIndicadores>(`/indicadores?regioes=${lista(ids)}`),
    enabled: ids.length > 0,
    placeholderData: keepPreviousData,
  });

export const useOferta = (segmento: number | null, ids: number[]) =>
  useQuery({
    queryKey: ["oferta", segmento, lista(ids)],
    queryFn: () => api.get<RespostaOferta>(`/oferta?segmento=${segmento}${ids.length ? `&regioes=${lista(ids)}` : ""}`),
    enabled: segmento != null,
    placeholderData: keepPreviousData,
  });

export const useComparacao = (segmento: number | null, ids: number[]) =>
  useQuery({
    queryKey: ["comparacao", segmento, lista(ids)],
    queryFn: () => api.get<RespostaComparacao>(`/comparacao?regioes=${lista(ids)}${segmento ? `&segmento=${segmento}` : ""}`),
    enabled: ids.length >= 2,
    placeholderData: keepPreviousData,
  });

export const useAnalise = (segmento: number | null, ids: number[]) =>
  useQuery({
    queryKey: ["analise", segmento, lista(ids)],
    queryFn: () => api.get<RespostaAnalise>(`/analise?segmento=${segmento}&regioes=${lista(ids)}`),
    enabled: segmento != null && ids.length >= 2,
    placeholderData: keepPreviousData,
  });

export const useDiagnostico = (segmento: number | null, ids: number[]) =>
  useQuery({
    queryKey: ["diagnostico", segmento, lista(ids)],
    queryFn: () => api.get<RespostaDiagnostico>(`/diagnostico?segmento=${segmento}&regioes=${lista(ids)}`),
    enabled: segmento != null && ids.length > 0,
    placeholderData: keepPreviousData,
  });

export const useSessao = () =>
  useQuery({
    queryKey: ["sessao"],
    queryFn: async () => {
      try {
        return await api.get<Usuario>("/auth/sessao");
      } catch (e) {
        if (e instanceof ErroApi && e.status === 401) return null;
        throw e;
      }
    },
    staleTime: 60_000,
  });

export const useStatus = () =>
  useQuery({
    queryKey: ["status"],
    queryFn: () => api.get<Status>("/status"),
    refetchInterval: 4000,
    retry: false,
  });

export const useAnalisesSalvas = (ativo: boolean) =>
  useQuery({
    queryKey: ["analises"],
    queryFn: () => api.get<AnaliseSalva[]>("/analises"),
    enabled: ativo,
  });

export function useSnapshotDaSelecao(segmento: number | null, regioes: number[]) {
  const [params] = useSearchParams();
  const id = params.get("analise") ? Number(params.get("analise")) : null;
  const query = useQuery({
    queryKey: ["analise-salva", id],
    queryFn: () => api.get<AnaliseSalva>(`/analises/${id}`),
    enabled: id != null && !Number.isNaN(id),
  });
  const snapshot = query.data?.snapshot;
  const mesmaSelecao =
    snapshot &&
    snapshot.selection.segmento.id_categoria === segmento &&
    snapshot.selection.regioes.length === regioes.length &&
    snapshot.selection.regioes.every((r) => regioes.includes(r));
  return { ...query, snapshot: mesmaSelecao ? snapshot : null, id };
}

export function useSair() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.post<void>("/auth/logout"),
    onSuccess: () => {
      qc.setQueryData(["sessao"], null);
      qc.removeQueries({ queryKey: ["analises"] });
      toast("Você saiu da sua conta.");
    },
  });
}
