from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date

from db import get_db
from models import Producao
from auth import verify_token
from services.filtro_service import aplicar_filtros_generico

router = APIRouter(prefix="/stats", tags=["Estatísticas"])

@router.get("/producao")
def estatisticas_producao(data_inicial: Optional[date] = None,
                           data_final: Optional[date] = None,
                           cultura_id: Optional[int] = None,
                           db: Session = Depends(get_db),
                           current_user: dict = Depends(verify_token)):
    query = db.query(Producao).filter(Producao.usuario_id == current_user["user_id"])
    query = aplicar_filtros_producao(query, data_inicial, data_final, cultura_id)
    dados = query.all()

    if not dados:
        return {"mensagem": "Nenhuma produção encontrada com esses filtros."}

    quantidades = [p.quantidade for p in dados]

    return {
        "quantidade_registros": len(quantidades),
        "soma_quantidade": sum(quantidades),
        "media_quantidade": round(sum(quantidades) / len(quantidades), 2) if quantidades else 0,
        "minimo_quantidade": min(quantidades),
        "maximo_quantidade": max(quantidades)
    }

