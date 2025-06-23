from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel, EmailStr, constr
import hashlib

from db import get_db
from models import Usuario
from auth import verify_token


router = APIRouter(
    prefix="/usuarios",
    tags=["Usuário"],
)


def gerar_hash(senha: str) -> str:
    return hashlib.sha256(senha.encode()).hexdigest()


# ==== Schemas ====
class UsuarioCreate(BaseModel):
    nome: constr(min_length=2, max_length=100)
    cpf: constr(min_length=11, max_length=14)
    email: EmailStr
    senha: constr(min_length=6, max_length=100)


class UsuarioOut(BaseModel):
    id: int
    nome: str
    cpf: str
    email: EmailStr

    class Config:
        orm_mode = True


# ==== Endpoints ====

@router.post(
    "/",
    response_model=UsuarioOut,
    status_code=status.HTTP_201_CREATED,
    summary="Criar usuário (produtor)",
)
def criar_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    if db.query(Usuario).filter(Usuario.email == usuario.email).first():
        raise HTTPException(status_code=400, detail="E-mail já cadastrado.")

    if db.query(Usuario).filter(Usuario.cpf == usuario.cpf).first():
        raise HTTPException(status_code=400, detail="CPF já cadastrado.")

    senha_hash = gerar_hash(usuario.senha)

    novo_usuario = Usuario(
        nome=usuario.nome,
        cpf=usuario.cpf,
        email=usuario.email,
        senha=senha_hash,
    )

    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)
    return novo_usuario


@router.get(
    "/me",
    response_model=UsuarioOut,
    summary="Obter meus dados",
)
def obter_meus_dados(
    current_user = Depends(verify_token),
    db: Session = Depends(get_db),
):
    usuario = db.query(Usuario).filter(Usuario.id == current_user["user_id"]).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    return usuario
