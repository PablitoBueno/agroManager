from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from db import get_db
from models import Producao, Cultura
from auth import verify_token
from services.filtro_service import aplicar_filtros_producao


router = APIRouter(prefix="/producoes", tags=["Produções"])

@router.post("/", status_code=201)
def criar_producao(cultura_id: int, quantidade: float, data_colheita: date, db: Session = Depends(get_db), current_user: dict = Depends(verify_token)):
    cultura = db.query(Cultura).filter(Cultura.id == cultura_id, Cultura.usuario_id == current_user["user_id"]).first()
    if not cultura:
        raise HTTPException(status_code=404, detail="Cultura não encontrada.")
    producao = Producao(
        cultura_id=cultura_id,
        usuario_id=current_user["user_id"],
        quantidade=quantidade,
        data_colheita=data_colheita
    )
    db.add(producao)
    db.commit()
    db.refresh(producao)
    return producao

@router.get("/")
def listar_producoes(data_inicial: Optional[date] = None,
                      data_final: Optional[date] = None,
                      cultura_id: Optional[int] = None,
                      db: Session = Depends(get_db),
                      current_user: dict = Depends(verify_token)):
    query = db.query(Producao).filter(Producao.usuario_id == current_user["user_id"])
    query = aplicar_filtros_producao(query, data_inicial, data_final, cultura_id)
    return query.all()

@router.delete("/{producao_id}")
def excluir_producao(producao_id: int, db: Session = Depends(get_db), current_user: dict = Depends(verify_token)):
    producao = db.query(Producao).filter(Producao.id == producao_id, Producao.usuario_id == current_user["user_id"]).first()
    if not producao:
        raise HTTPException(status_code=404, detail="Produção não encontrada.")
    db.delete(producao)
    db.commit()
    return {"detail": "Produção excluída com sucesso."}

