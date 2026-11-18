"""Senhas (bcrypt) e sessão (JWT em cookie httpOnly)."""

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Cookie, HTTPException, Response

from .config import config
from .db import consulta_um

COOKIE = "pz_sessao"


def gerar_hash(senha: str) -> str:
    return bcrypt.hashpw(senha.encode(), bcrypt.gensalt(rounds=12)).decode()


def confere_senha(senha: str, hash_salvo: str) -> bool:
    try:
        return bcrypt.checkpw(senha.encode(), hash_salvo.encode())
    except ValueError:
        return False


def abrir_sessao(resposta: Response, id_usuario: int) -> None:
    expira = datetime.now(timezone.utc) + timedelta(hours=config.sessao_horas)
    token = jwt.encode({"sub": str(id_usuario), "exp": expira}, config.jwt_segredo, algorithm="HS256")
    resposta.set_cookie(
        COOKIE,
        token,
        httponly=True,
        samesite="lax",
        secure=config.cookie_seguro,
        max_age=config.sessao_horas * 3600,
        path="/",
    )


def encerrar_sessao(resposta: Response) -> None:
    resposta.delete_cookie(COOKIE, path="/")


def _usuario_do_token(token: str | None) -> dict | None:
    if not token:
        return None
    try:
        dados = jwt.decode(token, config.jwt_segredo, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None
    return consulta_um(
        """
        SELECT u.id_usuario, u.nome, u.email, u.perfil,
               e.id_empresa, e.nome AS empresa, e.segmento
        FROM usuario u JOIN empresa e ON e.id_empresa = u.id_empresa
        WHERE u.id_usuario = %s
        """,
        (int(dados["sub"]),),
    )


def usuario_opcional(pz_sessao: str | None = Cookie(default=None)) -> dict | None:
    return _usuario_do_token(pz_sessao)


def usuario_obrigatorio(pz_sessao: str | None = Cookie(default=None)) -> dict:
    usuario = _usuario_do_token(pz_sessao)
    if usuario is None:
        raise HTTPException(status_code=401, detail="Entre na sua conta para usar esta função.")
    return usuario
