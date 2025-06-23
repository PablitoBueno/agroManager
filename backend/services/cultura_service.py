from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, constr
from db import get_db
from models import Cultura
from auth import verify_token


router = APIRouter(
    prefix="/culturas",
    tags=["Culturas"],
)


class CulturaBase(BaseModel):
    nome: constr(min_length=2, max_length=100)


class CulturaCreate(CulturaBase):
    pass


class CulturaOut(CulturaBase):
    id: int

    class Config:
        orm_mode = True


@router.post(
    "/",
    response_model=CulturaOut,
    status_code=201,
    summary="Criar cultura",
)
def criar_cultura(
    cultura: CulturaCreate,
    db: Session = Depends(get_db),
    current_user = Depends(verify_token)
):
    cultura_existente = db.query(Cultura).filter(
        Cultura.nome.ilike(cultura.nome),
        Cultura.usuario_id == current_user["user_id"]
    ).first()

    if cultura_existente:
        raise HTTPException(status_code=400, detail="Cultura já cadastrada.")

    nova_cultura = Cultura(**cultura.dict(), usuario_id=current_user["user_id"])
    db.add(nova_cultura)
    db.commit()
    db.refresh(nova_cultura)
    return nova_cultura


@router.get(
    "/",
    response_model=List[CulturaOut],
    summary="Listar minhas culturas",
)
def listar_culturas(
    nome: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(verify_token)
):
    query = db.query(Cultura).filter(Cultura.usuario_id == current_user["user_id"])

    if nome:
        query = query.filter(Cultura.nome.ilike(f"%{nome}%"))

    return query.all()
