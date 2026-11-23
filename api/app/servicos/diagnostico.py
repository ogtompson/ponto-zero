"""Contrato explicável do diagnóstico territorial.

Este módulo não acessa banco nem atribui nota. Ele transforma evidências já
coletadas em dimensões independentes, preservando fonte, data e limitações.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable


VERSAO_METODOLOGIA = "2026.11.4"

INTERPRETACAO_CONTRASTE = {
    "populacao": "Diferença de escala da demanda residente; não inclui pessoas que apenas circulam na região.",
    "densidade": "Diferença de concentração residencial; o desenho e a área do bairro influenciam a medida.",
    "oferta_por_10k": "Diferença de pressão cadastral da oferta formal; menor intensidade não comprova oportunidade.",
}


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


def _sintese_regiao(nome: str, dimensoes: list[dict]) -> dict:
    evidencias = {
        evidencia["indicador"]: evidencia
        for dimensao in dimensoes
        for evidencia in dimensao["evidencias"]
    }
    populacao = evidencias.get("populacao", {})
    densidade = evidencias.get("densidade", {})
    oferta_10k = evidencias.get("oferta_por_10k", {})

    sinais = []
    if populacao.get("disponivel"):
        sinais.append(
            f"População residente na faixa {populacao['faixa']} entre os bairros do Recife "
            f"(percentil {populacao['percentil']:.1f})."
        )
    if densidade.get("disponivel"):
        sinais.append(
            f"Densidade demográfica na faixa {densidade['faixa']} da comparação municipal "
            f"(percentil {densidade['percentil']:.1f})."
        )
    oferta_zero = oferta_10k.get("disponivel") and oferta_10k.get("valor") == 0
    if oferta_zero:
        sinais.append("A base formal não observou estabelecimentos do recorte neste bairro; isso não confirma ausência de oferta.")
    elif oferta_10k.get("disponivel"):
        sinais.append(
            f"Oferta formal por moradores na faixa {oferta_10k['faixa']} "
            f"(percentil {oferta_10k['percentil']:.1f}); isso indica intensidade cadastral, não oportunidade confirmada."
        )

    atencoes = []
    if oferta_zero:
        atencoes.append("A falta de registro formal não comprova demanda não atendida e deve ser verificada em campo.")
    elif oferta_10k.get("faixa") == "alta":
        atencoes.append("A pressão aparente da oferta formal é elevada e merece validação na microárea.")
    elif oferta_10k.get("faixa") == "baixa":
        atencoes.append("A menor oferta formal pode ser um sinal para investigar, mas não comprova demanda não atendida.")
    atencoes.append("Acesso, fluxo e polos geradores ainda não possuem evidência suficiente nesta versão.")
    atencoes.append("A renda disponível é histórica e deve ser tratada apenas como contexto aproximado.")

    faixa_demanda = populacao.get("faixa", "indisponível")
    faixa_oferta = "sem registro observado" if oferta_zero else oferta_10k.get("faixa", "indisponível")
    leitura = (
        f"{nome} combina demanda residente em faixa {faixa_demanda} e pressão da oferta formal em faixa "
        f"{faixa_oferta} na comparação entre bairros. A leitura prioriza onde aprofundar a investigação, não uma decisão de investimento."
    )
    return {
        "leitura": leitura,
        "sinais": sinais[:3],
        "atencoes": atencoes[:3],
        "dimensoes_disponiveis": sum(d["status"] == "disponivel" for d in dimensoes),
        "dimensoes_parciais": sum(d["status"] == "parcial" for d in dimensoes),
        "dimensoes_insuficientes": sum(d["status"] == "insuficiente" for d in dimensoes),
        "proximo_passo": "Validar a microárea, concorrentes relevantes e fluxo nos horários do segmento antes de decidir.",
    }


def _comparacao_selecionados(resultados: list[dict]) -> dict | None:
    if len(resultados) < 2:
        return None

    por_indicador: dict[str, list[dict]] = defaultdict(list)
    for regiao in resultados:
        for dimensao in regiao["dimensoes"]:
            for evidencia in dimensao["evidencias"]:
                if evidencia["indicador"] not in INTERPRETACAO_CONTRASTE or evidencia["valor"] is None:
                    continue
                por_indicador[evidencia["indicador"]].append({
                    "id_regiao": regiao["id_regiao"],
                    "nome": regiao["nome"],
                    "valor": evidencia["valor"],
                    "percentil": evidencia["percentil"],
                    "rotulo": evidencia["rotulo"],
                    "unidade": evidencia["unidade"],
                })

    contrastes = []
    for indicador, valores in por_indicador.items():
        if len(valores) < 2:
            continue
        ordenados = sorted(valores, key=lambda item: (item["valor"], item["nome"]))
        menor, maior = ordenados[0], ordenados[-1]
        if menor["valor"] == maior["valor"]:
            continue
        percentis = [item["percentil"] for item in (menor, maior)]
        distancia = abs(percentis[1] - percentis[0]) if all(item is not None for item in percentis) else 0
        contrastes.append({
            "indicador": indicador,
            "rotulo": maior["rotulo"],
            "unidade": maior["unidade"],
            "maior": {chave: maior[chave] for chave in ("id_regiao", "nome", "valor", "percentil")},
            "menor": {chave: menor[chave] for chave in ("id_regiao", "nome", "valor", "percentil")},
            "distancia_percentil": round(distancia, 1),
            "interpretacao": INTERPRETACAO_CONTRASTE[indicador],
        })

    contrastes.sort(key=lambda item: (-item["distancia_percentil"], item["rotulo"]))
    contrastes = contrastes[:3]
    if not contrastes:
        return None
    nomes = ", ".join(item["rotulo"].lower() for item in contrastes)
    return {
        "leitura": f"Entre os bairros selecionados, os maiores contrastes mensuráveis aparecem em {nomes}.",
        "contrastes": contrastes,
        "proximo_passo": "Use os contrastes para escolher o que validar em campo; eles não formam ranking nem apontam um bairro vencedor.",
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
                "oferta_por_10k", "Oferta formal por 10 mil moradores", "estabelecimentos/10 mil hab.",
                linha_10k, universo_oferta, qualidade="aproximada",
                explica="Compara a intensidade cadastral da oferta formal com a população residente; não mede capacidade ou qualidade.",
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
                "Compara duas formas de concentração da oferta formal ativa; valores altos significam maior pressão aparente.",
                [
                    "A base cadastral não inclui negócios informais nem mede porte, capacidade, qualidade ou faturamento.",
                    "O recorte depende dos CNAEs definidos para o segmento e pode abranger atividades similares.",
                ],
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
            "sintese": _sintese_regiao(regiao["nome"], dimensoes),
        })

    return {
        "versao_metodologia": VERSAO_METODOLOGIA,
        "segmento": segmento,
        "sem_score": True,
        "regioes": resultados,
        "comparacao": _comparacao_selecionados(resultados),
        "avisos": [
            "O diagnóstico organiza evidências e não recomenda investimento.",
            "Percentis representam posição relativa entre os 94 bairros, não probabilidade de sucesso.",
        ],
    }
