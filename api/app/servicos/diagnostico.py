"""Contrato explicável do diagnóstico territorial.

Este módulo não acessa banco nem atribui nota. Ele transforma evidências já
coletadas em dimensões independentes, preservando fonte, data e limitações.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable


VERSAO_METODOLOGIA = "2026.11.2"


def percentil_empirico(valor: float | None, universo: Iterable[float | None]) -> float | None:
    if valor is None:
        return None
    validos = [float(item) for item in universo if item is not None]
    if not validos:
        return None
    return round(100 * sum(item <= float(valor) for item in validos) / len(validos), 1)


def faixa_percentil(percentil: float | None) -> str:
    if percentil is None:
        return "indisponivel"
    if percentil >= 67:
        return "alta"
    if percentil <= 33:
        return "baixa"
    return "intermediaria"


def _data_texto(valor) -> str:
    if not valor:
        return "data de referência não informada"
    return valor.isoformat() if hasattr(valor, "isoformat") else str(valor)


def _evidencia(
    tipo: str,
    rotulo: str,
    unidade: str,
    linha: dict | None,
    universo: list[float | None],
    *,
    qualidade: str = "adequada",
    explica: str,
) -> dict:
    valor = float(linha["valor"]) if linha and linha.get("valor") is not None else None
    percentil = percentil_empirico(valor, universo)
    return {
        "indicador": tipo,
        "rotulo": rotulo,
        "valor": valor,
        "unidade": unidade,
        "percentil": percentil,
        "faixa": faixa_percentil(percentil),
        "disponivel": valor is not None,
        "qualidade": qualidade if valor is not None else "insuficiente",
        "interpretacao": explica,
        "fonte": linha.get("fonte") if linha else None,
        "data_texto": _data_texto(linha.get("data_referencia")) if linha else None,
    }


def _dimensao(
    identificador: str,
    titulo: str,
    evidencias: list[dict],
    confianca: str,
    resumo: str,
    limitacoes: list[str],
) -> dict:
    disponiveis = sum(item["disponivel"] for item in evidencias)
    status = "insuficiente" if not disponiveis else "disponivel" if disponiveis == len(evidencias) else "parcial"
    return {
        "id": identificador,
        "titulo": titulo,
        "status": status,
        "confianca": confianca if disponiveis else "insuficiente",
        "resumo": resumo,
        "evidencias": evidencias,
        "limitacoes": limitacoes,
    }


def montar_diagnostico(
    segmento: dict,
    regioes: list[dict],
    indicadores: list[dict],
    ofertas: list[dict],
    meta_oferta: dict,
) -> dict:
    """Monta o diagnóstico sem ranking final e sem recomendação de investimento."""
    por_regiao: dict[int, dict[str, dict]] = defaultdict(dict)
    universos: dict[str, list[float | None]] = defaultdict(list)
    for linha in indicadores:
        valor = float(linha["valor"]) if linha.get("valor") is not None else None
        linha = {**linha, "valor": valor}
        por_regiao[linha["id_regiao"]][linha["tipo"]] = linha
        universos[linha["tipo"]].append(valor)

    oferta_por_regiao = {linha["id_regiao"]: linha for linha in ofertas}
    universo_oferta = [float(linha["por_10k_hab"]) if linha.get("por_10k_hab") is not None else None for linha in ofertas]
    universo_oferta_km2: list[float | None] = []
    for linha in ofertas:
        area = por_regiao.get(linha["id_regiao"], {}).get("area_km2", {}).get("valor")
        universo_oferta_km2.append(float(linha["quantidade"]) / float(area) if area else None)

    resultados = []
    for regiao in regioes:
        rid = regiao["id_regiao"]
        dados = por_regiao.get(rid, {})
        demanda = [
            _evidencia(
                "populacao", "População residente", "habitantes", dados.get("populacao"), universos["populacao"],
                explica="Dimensiona a escala da demanda residente; não mede pessoas que apenas circulam na região.",
            ),
            _evidencia(
                "domicilios", "Domicílios ocupados", "domicílios", dados.get("domicilios"), universos["domicilios"],
                explica="Representa a base de lares e não deve ser somada à população como evidência independente.",
            ),
            _evidencia(
                "densidade", "Densidade demográfica", "hab/km²", dados.get("densidade"), universos["densidade"],
                explica="Mostra concentração residencial e é sensível ao tamanho e ao desenho do bairro.",
            ),
        ]

        renda = _evidencia(
            "renda_media_domiciliar", "Renda média domiciliar", "R$ por mês",
            dados.get("renda_media_domiciliar"), universos["renda_media_domiciliar"],
            qualidade="aproximada",
            explica="É um contexto histórico; não representa poder de compra atual nem consumo do segmento.",
        )
        limitacoes_perfil = ["A renda disponível no produto é do Censo 2010."]
        if segmento["slug"] == "farmacia":
            limitacoes_perfil.append("A população por faixa etária estudada ainda não foi incorporada ao banco da aplicação.")

        oferta = oferta_por_regiao.get(rid, {})
        por_10k = float(oferta["por_10k_hab"]) if oferta.get("por_10k_hab") is not None else None
        area = dados.get("area_km2", {}).get("valor")
        por_km2 = float(oferta.get("quantidade", 0)) / float(area) if area else None
        linha_10k = {
            "valor": por_10k, "fonte": meta_oferta["fonte"], "data_referencia": meta_oferta.get("data_referencia")
        }
        linha_km2 = {
            "valor": por_km2, "fonte": meta_oferta["fonte"], "data_referencia": meta_oferta.get("data_referencia")
        }
        evidencias_oferta = [
            _evidencia(
                "oferta_por_10k", "Oferta observada por 10 mil moradores", "estabelecimentos/10 mil hab.",
                linha_10k, universo_oferta, qualidade="aproximada",
                explica="Compara intensidade da oferta observada com a população residente; não mede capacidade ou qualidade.",
            ),
            _evidencia(
                "oferta_por_km2", "Concentração física da oferta", "estabelecimentos/km²",
                linha_km2, universo_oferta_km2, qualidade="aproximada",
                explica="Mostra concentração espacial e deve ser lida junto com a oferta por moradores.",
            ),
        ]

        dimensoes = [
            _dimensao(
                "demanda_residente", "Demanda residente", demanda, "adequada",
                "Compara escala e concentração residencial sem inferir consumo.",
                ["Não inclui população flutuante, comportamento de compra ou gasto por categoria."],
            ),
            _dimensao(
                "perfil_publico", "Adequação do público", [renda], "aproximada",
                "O perfil disponível ainda é apenas um contexto socioeconômico parcial.", limitacoes_perfil,
            ),
            _dimensao(
                "oferta_local", "Pressão da oferta", evidencias_oferta, "aproximada",
                "Compara duas formas de concentração da oferta observada; valores altos significam maior pressão aparente.",
                ["A cobertura do OpenStreetMap é parcial; ausência de registro não confirma ausência de concorrentes."],
            ),
            _dimensao(
                "acesso_centralidade", "Acesso e centralidade", [], "insuficiente",
                "Ainda não há evidência suficiente para esta dimensão.",
                ["Faltam tempo de deslocamento, transporte, fluxo e polos geradores compatíveis com o segmento."],
            ),
        ]
        niveis = [d["confianca"] for d in dimensoes if d["id"] != "acesso_centralidade"]
        confianca_geral = "adequada" if niveis and all(n == "adequada" for n in niveis) else "aproximada"
        dimensoes.append(
            _dimensao(
                "confianca_dados", "Confiança dos dados", [], confianca_geral,
                "A leitura combina dados adequados e aproximações; as limitações permanecem visíveis.",
                ["Baixa confiança descreve a evidência, não a qualidade comercial do bairro."],
            )
        )
        dimensoes[-1]["status"] = "parcial"
        dimensoes[-1]["confianca"] = confianca_geral

        resultados.append({
            "id_regiao": rid,
            "nome": regiao["nome"],
            "dimensoes": dimensoes,
            "sintese": {
                "dimensoes_disponiveis": sum(d["status"] == "disponivel" for d in dimensoes),
                "dimensoes_parciais": sum(d["status"] == "parcial" for d in dimensoes),
                "dimensoes_insuficientes": sum(d["status"] == "insuficiente" for d in dimensoes),
                "proximo_passo": "Investigar as evidências divergentes e validar a microárea antes de decidir.",
            },
        })

    return {
        "versao_metodologia": VERSAO_METODOLOGIA,
        "segmento": segmento,
        "sem_score": True,
        "regioes": resultados,
        "avisos": [
            "O diagnóstico organiza evidências e não recomenda investimento.",
            "Percentis representam posição relativa entre os 94 bairros, não probabilidade de sucesso.",
        ],
    }
