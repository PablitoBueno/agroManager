from fastapi import APIRouter, HTTPException, Depends, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date 

from db import get_db
from models import Estoque
from auth import verify_token

router = APIRouter(
    prefix="/estoque",
    tags=["Estoque"]
)


# === Schemas ===
from pydantic import BaseModel, constr, condecimal

class EstoqueCreate(BaseModel):
    produto_nome: constr(min_length=2, max_length=100)
    quantidade_estoque: condecimal(gt=0)
    validade: Optional[date]
    fornecedor: Optional[constr(max_length=100)]

class EstoqueOut(EstoqueCreate):
    id: int
    usuario_id: int
    data_registro: datetime

    class Config:
        orm_mode = True


# === Endpoints ===
@router.post("/", response_model=EstoqueOut, status_code=status.HTTP_201_CREATED)
def criar_item(
    item: EstoqueCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    novo = Estoque(
        produto_nome=item.produto_nome,
        quantidade_estoque=item.quantidade_estoque,
        validade=item.validade,
        fornecedor=item.fornecedor,
        usuario_id=current_user["user_id"]
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo

@router.get("/", response_model=List[EstoqueOut])
def listar_estoque(
    produto: Optional[str] = Query(None, description="Filtrar por nome do produto (parcial)"),
    fornecedor: Optional[str] = Query(None, description="Filtrar por fornecedor"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    query = db.query(Estoque).filter(Estoque.usuario_id == current_user["user_id"])
    if produto:
        query = query.filter(Estoque.produto_nome.ilike(f"%{produto}%"))
    if fornecedor:
        query = query.filter(Estoque.fornecedor.ilike(f"%{fornecedor}%"))
    return query.offset(skip).limit(limit).all()

@router.put("/{item_id}", response_model=EstoqueOut)
def atualizar_item(
    item_id: int,
    dados: EstoqueCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    item = db.query(Estoque).filter(Estoque.id == item_id, Estoque.usuario_id == current_user["user_id"]).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado.")
    for field, value in dados.dict().items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    item = db.query(Estoque).filter(Estoque.id == item_id, Estoque.usuario_id == current_user["user_id"]).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado.")
    db.delete(item)
    db.commit()
