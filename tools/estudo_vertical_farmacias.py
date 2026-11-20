"""Estudo reproduzível da vertical de farmácias do PontoZero.

O script trabalha em duas etapas:
1. recorta os dados oficiais do Censo 2022 para Recife;
2. consulta, de forma paginada, o recorte CNPJ/CNAE no Minha Receita.

Os arquivos brutos e resultados ficam em tools/dados/externos, fora do Git.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sqlite3
import time
import unicodedata
import urllib.parse
import urllib.request
import zipfile
from collections import Counter
from pathlib import Path
from statistics import median
from xml.etree import ElementTree as ET


RAIZ = Path(__file__).resolve().parents[1]
EXTERNOS = RAIZ / "tools" / "dados" / "externos"
IBGE = EXTERNOS / "ibge"
SAIDA = EXTERNOS / "estudo_farmacias"
CODIGO_RECIFE = "2611606"
CNAES_FARMACIA = {4771701, 4771702, 4771703}


def normalizar(texto: str | None) -> str:
    valor = unicodedata.normalize("NFKD", texto or "")
    return re.sub(r"[^A-Z0-9 ]", "", valor.encode("ascii", "ignore").decode().upper()).strip()


def numero(valor: str | None) -> float | None:
    if valor is None or valor.strip() in {"", "-", "X", "..."}:
        return None
    return float(valor.replace(".", "").replace(",", ".")) if "," in valor else float(valor)


def _coluna_indice(referencia: str) -> int:
    letras = re.match(r"[A-Z]+", referencia).group(0)
    indice = 0
    for letra in letras:
        indice = indice * 26 + ord(letra) - 64
    return indice - 1


def ler_xlsx(caminho: Path, planilha: int = 0) -> list[list[str]]:
    """Leitor mínimo de XLSX, suficiente para os dicionários do IBGE."""
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(caminho) as arquivo:
        compartilhadas: list[str] = []
        if "xl/sharedStrings.xml" in arquivo.namelist():
            raiz = ET.fromstring(arquivo.read("xl/sharedStrings.xml"))
            for item in raiz.findall("m:si", ns):
                compartilhadas.append("".join(no.text or "" for no in item.iter() if no.tag.endswith("}t")))

        xml = ET.fromstring(arquivo.read(f"xl/worksheets/sheet{planilha + 1}.xml"))
        resultado: list[list[str]] = []
        for linha in xml.findall(".//m:sheetData/m:row", ns):
            valores: dict[int, str] = {}
            for celula in linha.findall("m:c", ns):
                indice = _coluna_indice(celula.attrib["r"])
                tipo = celula.attrib.get("t")
                bruto = celula.find("m:v", ns)
                if bruto is None:
                    inline = celula.find("m:is", ns)
                    valor = "" if inline is None else "".join(no.text or "" for no in inline.iter() if no.tag.endswith("}t"))
                elif tipo == "s":
                    valor = compartilhadas[int(bruto.text)]
                else:
                    valor = bruto.text or ""
                valores[indice] = valor
            if valores:
                resultado.append([valores.get(i, "") for i in range(max(valores) + 1)])
        return resultado


def linhas_zip_csv(caminho: Path):
    with zipfile.ZipFile(caminho) as arquivo:
        nome = arquivo.namelist()[0]
        with arquivo.open(nome) as binario:
            texto = io.TextIOWrapper(binario, encoding="latin1", newline="")
            leitor = csv.DictReader(texto, delimiter=";")
            for linha in leitor:
                # Os agregados do próprio IBGE alternam CD_SETOR e CD_setor.
                if "CD_setor" in linha and "CD_SETOR" not in linha:
                    linha["CD_SETOR"] = linha.pop("CD_setor")
                yield linha


def dicionario_variaveis(caminho: Path) -> dict[str, str]:
    variaveis: dict[str, str] = {}
    for indice_planilha in range(6):
        try:
            linhas = ler_xlsx(caminho, indice_planilha)
        except KeyError:
            break
        for linha in linhas:
            for indice, valor in enumerate(linha):
                if re.fullmatch(r"[vV]\d{4,6}", valor.strip()):
                    descricao = " | ".join(x.strip() for x in linha[indice + 1 :] if x.strip())
                    variaveis[valor.lower()] = descricao
    return variaveis


def inspecionar_dicionarios() -> None:
    geral = dicionario_variaveis(IBGE / "dicionario_setores.xlsx")
    renda = dicionario_variaveis(IBGE / "dicionario_renda.xlsx")
    print("Variáveis básicas:")
    for chave in [f"v{i:04d}" for i in range(1, 10)]:
        print(chave, geral.get(chave))
    print("\nVariáveis de renda:")
    for chave, descricao in renda.items():
        print(chave, descricao)
    print("\nVariáveis demográficas relacionadas a idade avançada:")
    for chave, descricao in geral.items():
        texto = normalizar(descricao)
        if any(termo in texto for termo in ("60 ANOS", "65 ANOS", "IDOS")):
            print(chave, descricao)


def extrair_censo() -> dict:
    SAIDA.mkdir(parents=True, exist_ok=True)
    basico = [linha for linha in linhas_zip_csv(IBGE / "setores_basico.zip") if linha["CD_MUN"] == CODIGO_RECIFE]
    codigos = {linha["CD_SETOR"] for linha in basico}
    renda = {linha["CD_SETOR"]: linha for linha in linhas_zip_csv(IBGE / "setores_renda.zip") if linha["CD_SETOR"] in codigos}
    demografia = {
        linha["CD_SETOR"]: linha
        for linha in linhas_zip_csv(IBGE / "setores_demografia.zip")
        if linha["CD_SETOR"] in codigos
    }

    registros = []
    for linha in basico:
        codigo = linha["CD_SETOR"]
        item = {
            "codigo_setor": codigo,
            "bairro": linha["NM_BAIRRO"],
            "subdistrito": linha["NM_SUBDIST"],
            "area_km2": numero(linha["AREA_KM2"]),
            "populacao": numero(linha["v0001"]),
            "domicilios": numero(linha["v0002"]),
            "moradores_por_domicilio": numero(linha["v0005"]),
            "responsaveis_com_renda": numero(renda.get(codigo, {}).get("V06001")),
            "renda_media_responsavel": numero(renda.get(codigo, {}).get("V06004")),
            "renda_mediana_responsavel": numero(renda.get(codigo, {}).get("V06006")),
            # O total 60+ combina as faixas exaustivas 60–69 e 70+.
            "populacao_60_mais": sum(
                numero(demografia.get(codigo, {}).get(chave)) or 0
                for chave in ("V01040", "V01041")
            ),
        }
        registros.append(item)

    destino = SAIDA / "setores_recife.json"
    destino.write_text(json.dumps(registros, ensure_ascii=False, indent=2), encoding="utf-8")
    resumo = {
        "setores_basicos": len(basico),
        "setores_com_renda": len(renda),
        "setores_com_demografia": len(demografia),
        "populacao_somada": int(sum(x["populacao"] or 0 for x in registros)),
        "domicilios_somados": int(sum(x["domicilios"] or 0 for x in registros)),
        "bairros": len({normalizar(x["bairro"]) for x in registros if x["bairro"]}),
    }
    print(json.dumps(resumo, ensure_ascii=False, indent=2))
    return resumo


def _obter_json(url: str, tentativas: int = 4) -> dict:
    ultimo: Exception | None = None
    for tentativa in range(tentativas):
        try:
            requisicao = urllib.request.Request(url, headers={"User-Agent": "PontoZero-academic/1.0"})
            with urllib.request.urlopen(requisicao, timeout=120) as resposta:
                return json.load(resposta)
        except Exception as erro:  # repetição controlada para instabilidade/429
            ultimo = erro
            time.sleep(2 ** tentativa)
    raise RuntimeError(f"Falha ao consultar {url}: {ultimo}")


def coletar_cnpj() -> dict:
    SAIDA.mkdir(parents=True, exist_ok=True)
    destino = SAIDA / "cnpj_farmacias_recife.json"
    if destino.exists():
        dados = json.loads(destino.read_text(encoding="utf-8"))
    else:
        dados: list[dict] = []
        cursor = None
        while True:
            parametros = {
                "municipio": CODIGO_RECIFE,
                "cnae": ",".join(str(x) for x in sorted(CNAES_FARMACIA)),
                "limit": "1024",
            }
            if cursor:
                parametros["cursor"] = cursor
            resposta = _obter_json("https://minhareceita.org/?" + urllib.parse.urlencode(parametros))
            pagina = resposta.get("data", [])
            dados.extend(pagina)
            print(f"CNPJ: {len(dados)} registros coletados")
            cursor = resposta.get("cursor")
            if not cursor:
                break
            time.sleep(0.5)
        destino.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")

    ativos = [x for x in dados if x.get("descricao_situacao_cadastral") == "ATIVA"]
    principal = [x for x in ativos if x.get("cnae_fiscal") in CNAES_FARMACIA]
    com_endereco = [x for x in ativos if x.get("logradouro") and x.get("numero") and x.get("cep")]
    principal_com_endereco = [x for x in principal if x.get("logradouro") and x.get("numero") and x.get("cep")]
    bairros = Counter(normalizar(x.get("bairro")) for x in ativos if x.get("bairro"))
    resumo = {
        "registros_encontrados": len(dados),
        "ativos": len(ativos),
        "ativos_cnae_principal": len(principal),
        "ativos_apenas_cnae_secundario": len(ativos) - len(principal),
        "ativos_com_endereco_completo": len(com_endereco),
        "ativos_cnae_principal_com_endereco_completo": len(principal_com_endereco),
        "bairros_cadastrais_distintos": len(bairros),
        "bairros_mais_frequentes": bairros.most_common(10),
        "data_base": _obter_json("https://minhareceita.org/updated"),
    }
    (SAIDA / "resumo_cnpj.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(resumo, ensure_ascii=False, indent=2))
    return resumo


def diagnosticar() -> None:
    setores = json.loads((SAIDA / "setores_recife.json").read_text(encoding="utf-8"))
    cnpjs = json.loads((SAIDA / "cnpj_farmacias_recife.json").read_text(encoding="utf-8"))
    ativos = [
        x for x in cnpjs
        if x.get("descricao_situacao_cadastral") == "ATIVA" and x.get("cnae_fiscal") in CNAES_FARMACIA
    ]
    por_bairro = Counter(normalizar(x.get("bairro")) for x in ativos if x.get("bairro"))
    fonte_atual = json.loads((RAIZ / "tools" / "dados" / "pontozero-dados.json").read_text(encoding="utf-8"))
    farmacias_osm = [x for x in fonte_atual["osm"]["elements"] if x.get("tags", {}).get("amenity") == "pharmacy"]
    osm_por_bairro = Counter(
        normalizar(x.get("tags", {}).get("addr:suburb"))
        for x in farmacias_osm if x.get("tags", {}).get("addr:suburb")
    )

    agregado: dict[str, dict] = {}
    for setor in setores:
        bairro = normalizar(setor["bairro"])
        if not bairro:
            continue
        item = agregado.setdefault(bairro, {
            "bairro": setor["bairro"], "populacao": 0, "domicilios": 0, "area_km2": 0,
            "populacao_60_mais": 0, "soma_renda_ponderada": 0, "peso_renda": 0,
        })
        item["populacao"] += setor["populacao"] or 0
        item["domicilios"] += setor["domicilios"] or 0
        item["area_km2"] += setor["area_km2"] or 0
        item["populacao_60_mais"] += setor["populacao_60_mais"] or 0
        if setor["renda_media_responsavel"] is not None and setor["responsaveis_com_renda"]:
            item["soma_renda_ponderada"] += setor["renda_media_responsavel"] * setor["responsaveis_com_renda"]
            item["peso_renda"] += setor["responsaveis_com_renda"]

    linhas = []
    for chave, item in agregado.items():
        farmacias = por_bairro.get(chave, 0)
        pop = item["populacao"]
        area = item["area_km2"]
        linhas.append({
            "bairro": item["bairro"], "populacao": pop, "domicilios": item["domicilios"], "area_km2": area,
            "populacao_60_mais": item["populacao_60_mais"],
            "percentual_60_mais": round(item["populacao_60_mais"] * 100 / pop, 2) if pop else None,
            "renda_media_responsavel_ponderada": round(item["soma_renda_ponderada"] / item["peso_renda"], 2) if item["peso_renda"] else None,
            "farmacias_cnpj_ativas": farmacias,
            "farmacias_osm_com_bairro": osm_por_bairro.get(chave, 0),
            "habitantes_por_farmacia": round(pop / farmacias, 1) if farmacias else None,
            "farmacias_por_10k": round(farmacias * 10000 / pop, 2) if pop and farmacias else None,
            "farmacias_por_km2": round(farmacias / area, 2) if area and farmacias else None,
        })
    linhas.sort(key=lambda x: x["populacao"], reverse=True)
    (SAIDA / "diagnostico_bairros.json").write_text(json.dumps(linhas, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Bairros censitários agregados: {len(linhas)}")
    print(f"CNPJs ativos sem correspondência exata de bairro: {sum(v for k, v in por_bairro.items() if k not in agregado)}")
    for linha in linhas[:10]:
        print(linha)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("acao", choices=["dicionario", "censo", "cnpj", "diagnostico", "tudo"])
    args = parser.parse_args()
    if args.acao == "dicionario":
        inspecionar_dicionarios()
    if args.acao in {"censo", "tudo"}:
        extrair_censo()
    if args.acao in {"cnpj", "tudo"}:
        coletar_cnpj()
    if args.acao in {"diagnostico", "tudo"}:
        diagnosticar()


if __name__ == "__main__":
    main()
