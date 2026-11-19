"""Geração do arquivo exportado (HU-010): PDF com a identidade do PontoZero ou CSV.

O conteúdo vem das mesmas funções que alimentam a tela (comparação e análise),
então o arquivo reflete exatamente o que o usuário está vendo (RN01).
"""

from __future__ import annotations

import csv
import io
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from ..config import AVISO_NAO_RECOMENDACAO, config

ASSETS = Path(__file__).resolve().parents[1] / "assets"

MARINHO = colors.HexColor("#19214A")
OURO = colors.HexColor("#DDBA43")
NEVOA = colors.HexColor("#E4E7F0")
TINTA_SUAVE = colors.HexColor("#5B6385")
PAPEL = colors.HexColor("#F6F7FB")


def br(valor: float | None, casas: int = 0) -> str:
    if valor is None:
        return "indisponível"
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def formata(valor: float | None, unidade: str, pdf: bool = True) -> str:
    if valor is None:
        return "indisponível"
    if pdf:
        # a fonte Helvetica embutida não desenha o "²"
        unidade = unidade.replace("²", "<super>2</super>")
    if unidade == "R$ por mês":
        return "R$ " + br(valor, 2)
    if unidade.startswith("pessoas") or unidade.startswith("km"):
        return br(valor, 2) + " " + unidade
    return br(valor, 0) + " " + unidade


def _estilos():
    base = ParagraphStyle("base", fontName="Helvetica", fontSize=9, leading=12.5, textColor=MARINHO, alignment=TA_LEFT)
    return {
        "base": base,
        "suave": ParagraphStyle("suave", parent=base, textColor=TINTA_SUAVE, fontSize=8, leading=11),
        "titulo": ParagraphStyle("titulo", parent=base, fontName="Helvetica-Bold", fontSize=20, leading=24),
        "h2": ParagraphStyle("h2", parent=base, fontName="Helvetica-Bold", fontSize=12, leading=16, spaceBefore=10, spaceAfter=6),
        "celula": ParagraphStyle("celula", parent=base, fontSize=8.5, leading=11),
        "celula_b": ParagraphStyle("celula_b", parent=base, fontName="Helvetica-Bold", fontSize=8.5, leading=11),
        "aviso": ParagraphStyle("aviso", parent=base, fontName="Helvetica-Bold", fontSize=9, leading=12.5),
    }


def gerar_pdf(comparacao: dict, analise: dict, usuario: dict | None) -> bytes:
    buf = io.BytesIO()
    est = _estilos()
    gerado = datetime.now(config.fuso)

    def rodape(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(NEVOA)
        canvas.line(18 * mm, 16 * mm, A4[0] - 18 * mm, 16 * mm)
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(TINTA_SUAVE)
        canvas.drawString(18 * mm, 11 * mm, "PontoZero, projeto acadêmico da CESAR School. " + AVISO_NAO_RECOMENDACAO)
        canvas.drawRightString(A4[0] - 18 * mm, 6.5 * mm, f"página {doc.page}")
        cesar = ASSETS / "cesar-school.png"
        if cesar.exists():
            canvas.drawImage(str(cesar), 18 * mm, 4.5 * mm, width=6.5 * mm, height=6 * mm, mask="auto")
        canvas.restoreState()

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=22 * mm,
        title="PontoZero: relatório de análise territorial",
        author="PontoZero",
    )
    historia = []

    logo = Image(str(ASSETS / "pontozero.png"), width=34 * mm, height=34 * mm * 216 / 407)
    cab = Table(
        [[logo, Paragraph(f"Gerado em {gerado:%d/%m/%Y às %H:%M}" + (f"<br/>por {usuario['nome']} ({usuario['empresa']})" if usuario else ""), est["suave"])]],
        colWidths=[60 * mm, None],
    )
    cab.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (1, 0), (1, 0), "RIGHT")]))
    historia += [cab, Spacer(1, 8 * mm)]

    segmento = analise["segmento"]["nome"]
    nomes = [r["nome"] for r in comparacao["regioes"]]
    historia.append(Paragraph(f"{segmento} em {', '.join(nomes[:-1])} e {nomes[-1]}", est["titulo"]))
    historia.append(Spacer(1, 2 * mm))
    historia.append(Paragraph("Comparação de regiões e da oferta observada com a referência municipal. Recife, PE.", est["suave"]))
    historia.append(Spacer(1, 5 * mm))

    aviso = Table([[Paragraph(AVISO_NAO_RECOMENDACAO, est["aviso"])]], colWidths=[None])
    aviso.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FBF4DC")),
                ("LINEBEFORE", (0, 0), (0, -1), 3, OURO),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    historia.append(aviso)

    # ---------------------------------------------------------------- análise
    historia.append(Paragraph("Oferta observada e referência", est["h2"]))
    linhas = [[Paragraph("Região", est["celula_b"]), Paragraph("Resultado", est["celula_b"]),
               Paragraph("Observados", est["celula_b"]), Paragraph("Referência", est["celula_b"]),
               Paragraph("Motivo", est["celula_b"])]]
    for r in analise["resultados"]:
        rotulo = r["rotulo"]
        if r["classificacao"] == "oferta_observada_baixa":
            rotulo = f"<font color='#8A6A0B'><b>{rotulo}</b></font>"
        linhas.append(
            [
                Paragraph(r["nome"], est["celula_b"]),
                Paragraph(rotulo, est["celula"]),
                Paragraph(br(r["encontrados"]), est["celula"]),
                Paragraph(br(r["esperado"], 1), est["celula"]),
                Paragraph(r["motivo"], est["celula"]),
            ]
        )
    t = Table(linhas, colWidths=[34 * mm, 38 * mm, 22 * mm, 20 * mm, None], repeatRows=1)
    t.setStyle(_estilo_tabela())
    historia.append(t)
    historia.append(Spacer(1, 3 * mm))
    crit = "<br/>".join(f"<b>{c['nome']}:</b> {c['regra']}" for c in analise["criterios"])
    historia.append(Paragraph(crit, est["suave"]))

    # ------------------------------------------------------------- comparação
    cabec = [Paragraph("Indicador", est["celula_b"])] + [Paragraph(n, est["celula_b"]) for n in nomes]
    corpo = [cabec]
    for linha in comparacao["linhas"]:
        corpo.append(
            [Paragraph(linha["rotulo"], est["celula"])]
            + [Paragraph(formata(v["valor"], linha["unidade"]), est["celula"]) for v in linha["valores"]]
        )
    if comparacao.get("oferta"):
        o = comparacao["oferta"]
        corpo.append(
            [Paragraph(f"Estabelecimentos ({o['segmento']})", est["celula"])]
            + [Paragraph("Sem registro" if v["status_dado"] == "sem_registro_observado" else br(v["quantidade"]), est["celula"]) for v in o["valores"]]
        )
        corpo.append(
            [Paragraph("Por 10 mil habitantes", est["celula"])]
            + [Paragraph("—" if v["status_dado"] == "sem_registro_observado" else br(v["por_10k_hab"], 2), est["celula"]) for v in o["valores"]]
        )
    largura = (A4[0] - 36 * mm - 40 * mm) / len(nomes)
    tc = Table(corpo, colWidths=[40 * mm] + [largura] * len(nomes), repeatRows=1)
    tc.setStyle(_estilo_tabela())
    historia.append(KeepTogether([Paragraph("Comparação lado a lado", est["h2"]), tc]))

    # ----------------------------------------------------------------- fontes
    fontes = {}
    for f in comparacao["fontes"] + analise["fontes"]:
        chave = (f["fonte"], f["data_texto"])
        fontes.setdefault(chave, set()).update(f["usada_em"])
    tf = [[Paragraph("Fonte", est["celula_b"]), Paragraph("Data de referência", est["celula_b"]), Paragraph("Usada em", est["celula_b"])]]
    for (fonte, data), usos in fontes.items():
        tf.append([Paragraph(fonte, est["celula"]), Paragraph(_data_br(data), est["celula"]), Paragraph(", ".join(sorted(usos)), est["celula"])])
    tabela_fontes = Table(tf, colWidths=[70 * mm, 34 * mm, None], repeatRows=1)
    tabela_fontes.setStyle(_estilo_tabela())
    historia.append(KeepTogether([Paragraph("Fontes dos dados", est["h2"]), tabela_fontes]))

    historia.append(Paragraph("Avisos", est["h2"]))
    for a in dict.fromkeys(comparacao["avisos"] + analise["avisos"]):
        historia.append(Paragraph("• " + a, est["base"]))

    doc.build(historia, onFirstPage=rodape, onLaterPages=rodape)
    return buf.getvalue()


def _data_br(texto: str) -> str:
    if len(texto) == 10 and texto[4] == "-":
        a, m, d = texto.split("-")
        return f"{d}/{m}/{a}"
    return texto


def _estilo_tabela() -> TableStyle:
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), PAPEL),
            ("LINEBELOW", (0, 0), (-1, 0), 0.8, MARINHO),
            ("LINEBELOW", (0, 1), (-1, -1), 0.4, NEVOA),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ]
    )


def gerar_csv(comparacao: dict, analise: dict) -> bytes:
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=";")
    nomes = [r["nome"] for r in comparacao["regioes"]]
    w.writerow(["PontoZero", "Relatório de análise territorial"])
    w.writerow(["Gerado em", datetime.now(config.fuso).strftime("%d/%m/%Y %H:%M")])
    w.writerow(["Segmento", analise["segmento"]["nome"]])
    w.writerow(["Regiões", ", ".join(nomes)])
    w.writerow([])
    w.writerow(["Oferta observada e referência"])
    w.writerow(["Região", "Resultado", "Observados", "Referência proporcional", "Relação observado/referência", "Motivo"])
    for r in analise["resultados"]:
        w.writerow([r["nome"], r["rotulo"], r["encontrados"], br(r["esperado"], 1), br(r["cobertura"], 2), r["motivo"]])
    w.writerow([])
    w.writerow(["Critérios"])
    for c in analise["criterios"]:
        w.writerow([c["nome"], c["regra"]])
    w.writerow([])
    w.writerow(["Comparação"])
    w.writerow(["Indicador", "Unidade"] + nomes)
    for linha in comparacao["linhas"]:
        w.writerow([linha["rotulo"], linha["unidade"]] + [br(v["valor"], 2) if v["valor"] is not None else "indisponível" for v in linha["valores"]])
    if comparacao.get("oferta"):
        o = comparacao["oferta"]
        w.writerow([f"Estabelecimentos ({o['segmento']})", "estabelecimentos"] + [("sem registro" if v["status_dado"] == "sem_registro_observado" else v["quantidade"]) for v in o["valores"]])
        w.writerow(["Por 10 mil habitantes", "estabelecimentos"] + [("indisponível" if v["status_dado"] == "sem_registro_observado" else br(v["por_10k_hab"], 2)) for v in o["valores"]])
    w.writerow([])
    w.writerow(["Fonte", "Data de referência", "Usada em"])
    vistas = set()
    for f in comparacao["fontes"] + analise["fontes"]:
        chave = (f["fonte"], f["data_texto"])
        if chave in vistas:
            continue
        vistas.add(chave)
        w.writerow([f["fonte"], _data_br(f["data_texto"]), ", ".join(f["usada_em"])])
    w.writerow([])
    w.writerow(["Avisos"])
    for a in dict.fromkeys(comparacao["avisos"] + analise["avisos"]):
        w.writerow([a])
    # BOM para o Excel abrir os acentos corretamente
    return ("﻿" + buf.getvalue()).encode("utf-8")
