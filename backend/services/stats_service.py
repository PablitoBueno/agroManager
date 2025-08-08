from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date

from db import get_db
from models import Producao
from auth import verify_token
from services.filtro_service import aplicar_filtros_producao

router = APIRouter(prefix="/stats", tags=["Estatísticas"])

@router.get("/producao")
def estatisticas_producao(
    data_inicial: Optional[date] = None,
    data_final: Optional[date] = None,
    cultura_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """
    Retorna estatísticas agregadas sobre a produção agrícola:
    - Total de registros
    - Soma total da quantidade produzida
    - Média da quantidade por produção
    - Menor quantidade registrada
    - Maior quantidade registrada
    
    Filtros opcionais:
    - data_inicial: Filtra produções a partir desta data
    - data_final: Filtra produções até esta data
    - cultura_id: Filtra por ID específico de cultura
    """
    # Base query com filtro de usuário
    query = db.query(Producao).filter(Producao.usuario_id == current_user["user_id"])
    
    # Aplica filtros adicionais
    query = aplicar_filtros_producao(query, data_inicial, data_final, cultura_id)
    
    # Obtém todos os registros filtrados
    dados = query.all()

    if not dados:
        return {
            "mensagem": "Nenhuma produção encontrada com os filtros aplicados.",
            "quantidade_registros": 0,
            "soma_quantidade": 0.0,
            "media_quantidade": 0.0,
            "minimo_quantidade": 0.0,
            "maximo_quantidade": 0.0
        }

    # Extrai as quantidades para cálculos
    quantidades = [float(p.quantidade) for p in dados]

    # Calcula estatísticas
    soma_quantidade = sum(quantidades)
    media_quantidade = soma_quantidade / len(quantidades)
    
    return {
        "quantidade_registros": len(quantidades),
        "soma_quantidade": round(soma_quantidade, 2),
        "media_quantidade": round(media_quantidade, 2),
        "minimo_quantidade": round(min(quantidades), 2),
        "maximo_quantidade": round(max(quantidades), 2)
    }