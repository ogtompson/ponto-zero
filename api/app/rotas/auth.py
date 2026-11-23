"""Cadastro, login e logout (HU-001 e HU-002). Nenhuma outra função depende disso."""

import re

import psycopg
from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel

from ..db import conexao, consulta_um
from ..seguranca import (
    abrir_sessao,
    confere_senha,
    encerrar_sessao,
    gerar_hash,
    usuario_opcional,
)
from ..servicos.territorio import erro

router = APIRouter(prefix="/auth", tags=["conta"])

EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class Cadastro(BaseModel):
    nome: str = ""
    email: str = ""
    senha: str = ""
    empresa: str = ""
    segmento: str | None = None


class Login(BaseModel):
    email: str = ""
    senha: str = ""


def _valida_email(email: str) -> str:
    email = email.strip().lower()
    if not email:
        raise erro(422, "Informe o e-mail.", "email")
    if not EMAIL.match(email) or len(email) > 100:
        raise erro(422, "Digite um e-mail válido, como nome@empresa.com.", "email")
    return email


@router.post("/cadastro", status_code=201, summary="Criar conta (HU-001)")
def cadastrar(dados: Cadastro, resposta: Response):
    nome = dados.nome.strip()
    if not nome:
        raise erro(422, "Informe seu nome.", "nome")
    email = _valida_email(dados.email)
    if len(dados.senha) < 8:
        raise erro(422, "A senha precisa ter pelo menos 8 caracteres.", "senha")
    empresa = dados.empresa.strip() or f"Empresa de {nome.split()[0]}"
    segmento = (dados.segmento or "").strip() or None
    if segmento and not consulta_um("SELECT 1 FROM categoria WHERE nome = %s", (segmento,)):
        raise erro(422, "Escolha um segmento da lista.", "segmento")

    with conexao() as conn:
        if conn.execute("SELECT 1 FROM usuario WHERE lower(email) = %s", (email,)).fetchone():
            raise erro(409, "Este e-mail já está em uso.", "email")
        try:
            id_empresa = conn.execute(
                "INSERT INTO empresa (nome, segmento) VALUES (%s, %s) RETURNING id_empresa",
                (empresa[:100], segmento),
            ).fetchone()["id_empresa"]
            usuario = conn.execute(
                """
                INSERT INTO usuario (nome, email, senha, perfil, id_empresa)
                VALUES (%s, %s, %s, 'analista', %s)
                RETURNING id_usuario, nome, email, perfil
                """,
                (nome[:100], email, gerar_hash(dados.senha), id_empresa),
            ).fetchone()
        except psycopg.errors.UniqueViolation:
            raise erro(409, "Este e-mail já está em uso.", "email")

    abrir_sessao(resposta, usuario["id_usuario"])
    return {**usuario, "empresa": empresa, "segmento": segmento, "id_empresa": id_empresa}


@router.post("/login", summary="Entrar (HU-002)")
def entrar(dados: Login, resposta: Response):
    if not dados.email.strip():
        raise erro(422, "Informe o e-mail.", "email")
    if not dados.senha:
        raise erro(422, "Informe a senha.", "senha")
    linha = consulta_um(
        """
        SELECT u.id_usuario, u.nome, u.email, u.perfil, u.senha,
               e.id_empresa, e.nome AS empresa, e.segmento
        FROM usuario u JOIN empresa e ON e.id_empresa = u.id_empresa
        WHERE lower(u.email) = %s
        """,
        (dados.email.strip().lower(),),
    )
    # RN03: a mensagem não revela qual campo está errado
    if not linha or not confere_senha(dados.senha, linha["senha"]):
        raise erro(401, "E-mail ou senha inválidos")
    linha.pop("senha")
    abrir_sessao(resposta, linha["id_usuario"])
    return linha


@router.post("/logout", status_code=204, summary="Sair (HU-002)")
def sair():
    resposta = Response(status_code=204)
    encerrar_sessao(resposta)
    return resposta


@router.get("/sessao", summary="Usuário da sessão atual")
def sessao(usuario: dict | None = Depends(usuario_opcional)):
    return usuario if usuario is not None else Response(status_code=204)
