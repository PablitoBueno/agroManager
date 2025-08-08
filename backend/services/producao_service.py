from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from pydantic import BaseModel

from db import get_db
from models import Producao, Cultura
from auth import verify_token
from services.filtro_service import aplicar_filtros_producao

router = APIRouter(prefix="/producoes", tags=["Produções"])


# ==== Schemas ====
class ProducaoBase(BaseModel):
    cultura_id: int
    quantidade: float
    data_colheita: date

class ProducaoCreate(ProducaoBase):
    pass

class ProducaoOut(ProducaoBase):
    id: int
    usuario_id: int
    data_registro: date

    class Config:
        orm_mode = True


# ==== Endpoints ====
@router.post("/", response_model=ProducaoOut, status_code=201)
def criar_producao(
    producao: ProducaoCreate, 
    db: Session = Depends(get_db), 
    current_user: dict = Depends(verify_token)
):
    """
    Cria um novo registro de produção agrícola.
    - Verifica se a cultura pertence ao usuário autenticado
    - Garante que a data de colheita não é futura
    - Valida quantidade positiva
    """
    # Verifica se a cultura existe e pertence ao usuário
    cultura = db.query(Cultura).filter(
        Cultura.id == producao.cultura_id,
        Cultura.usuario_id == current_user["user_id"]
    ).first()
    
    if not cultura:
        raise HTTPException(
            status_code=404, 
            detail="Cultura não encontrada ou você não tem permissão para acessá-la."
        )
    
    # Validação adicional de dados
    if producao.quantidade <= 0:
        raise HTTPException(
            status_code=400, 
            detail="A quantidade deve ser maior que zero."
        )
    
    if producao.data_colheita > date.today():
        raise HTTPException(
            status_code=400, 
            detail="A data de colheita não pode ser futura."
        )
    
    nova_producao = Producao(
        cultura_id=producao.cultura_id,
        usuario_id=current_user["user_id"],
        quantidade=producao.quantidade,
        data_colheita=producao.data_colheita
    )
    
    db.add(nova_producao)
    db.commit()
    db.refresh(nova_producao)
    return nova_producao


@router.get("/", response_model=List[ProducaoOut])
def listar_producoes(
    data_inicial: Optional[date] = None,
    data_final: Optional[date] = None,
    cultura_id: Optional[int] = None,
    skip: int = 0,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """
    Lista registros de produção do usuário autenticado com filtros opcionais:
    - data_inicial: Filtra produções a partir desta data
    - data_final: Filtra produções até esta data
    - cultura_id: Filtra por ID de cultura específica
    - skip: Paginação (itens a pular)
    - limit: Limite máximo de itens por página (máx. 500)
    """
    query = db.query(Producao).filter(
        Producao.usuario_id == current_user["user_id"]
    )
    
    # Aplica filtros
    query = aplicar_filtros_producao(
        query, 
        data_inicial, 
        data_final, 
        cultura_id
    )
    
    # Ordena por data de colheita (mais recente primeiro)
    query = query.order_by(Producao.data_colheita.desc())
    
    # Paginação
    return query.offset(skip).limit(limit).all()


@router.get("/{producao_id}", response_model=ProducaoOut)
def obter_producao(
    producao_id: int, 
    db: Session = Depends(get_db), 
    current_user: dict = Depends(verify_token)
):
    """
    Obtém um registro de produção específico pelo ID.
    - Verifica se a produção pertence ao usuário autenticado
    """
    producao = db.query(Producao).filter(
        Producao.id == producao_id,
        Producao.usuario_id == current_user["user_id"]
    ).first()
    
    if not producao:
        raise HTTPException(
            status_code=404, 
            detail="Produção não encontrada ou você não tem permissão para acessá-la."
        )
    
    return producao


@router.put("/{producao_id}", response_model=ProducaoOut)
def atualizar_producao(
    producao_id: int, 
    dados: ProducaoCreate, 
    db: Session = Depends(get_db), 
    current_user: dict = Depends(verify_token)
):
    """
    Atualiza um registro de produção existente.
    - Verifica propriedade do registro
    - Valida nova cultura (se alterada)
    - Garante consistência dos dados
    """
    # Obtém a produção existente
    producao = db.query(Producao).filter(
        Producao.id == producao_id,
        Producao.usuario_id == current_user["user_id"]
    ).first()
    
    if not producao:
        raise HTTPException(status_code=404, detail="Produção não encontrada.")
    
    # Verifica se a nova cultura pertence ao usuário
    if dados.cultura_id != producao.cultura_id:
        nova_cultura = db.query(Cultura).filter(
            Cultura.id == dados.cultura_id,
            Cultura.usuario_id == current_user["user_id"]
        ).first()
        
        if not nova_cultura:
            raise HTTPException(
                status_code=400, 
                detail="Cultura não encontrada ou não pertence ao usuário."
            )
    
    # Validações de dados
    if dados.quantidade <= 0:
        raise HTTPException(
            status_code=400, 
            detail="A quantidade deve ser maior que zero."
        )
    
    if dados.data_colheita > date.today():
        raise HTTPException(
            status_code=400, 
            detail="A data de colheita não pode ser futura."
        )
    
    # Atualiza os campos
    producao.cultura_id = dados.cultura_id
    producao.quantidade = dados.quantidade
    producao.data_colheita = dados.data_colheita
    
    db.commit()
    db.refresh(producao)
    return producao


@router.delete("/{producao_id}", status_code=204)
def excluir_producao(
    producao_id: int, 
    db: Session = Depends(get_db), 
    current_user: dict = Depends(verify_token)
):
    """
    Exclui um registro de produção.
    - Verifica propriedade do registro
    - Operação irreversível
    """
    producao = db.query(Producao).filter(
        Producao.id == producao_id,
        Producao.usuario_id == current_user["user_id"]
    ).first()
    
    if not producao:
        raise HTTPException(status_code=404, detail="Produção não encontrada.")
    
    db.delete(producao)
    db.commit()
    return None