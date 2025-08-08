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
    """
    Cria uma nova cultura para o usuário autenticado.
    - O nome da cultura deve ser único para cada usuário
    - Nomes são comparados ignorando maiúsculas/minúsculas e espaços extras
    """
    # Normaliza o nome: remove espaços extras e converte para minúsculas
    nome_normalizado = cultura.nome.strip().lower()
    
    # Verifica se já existe cultura com mesmo nome para este usuário
    cultura_existente = db.query(Cultura).filter(
        Cultura.nome.ilike(f"%{nome_normalizado}%"),
        Cultura.usuario_id == current_user["user_id"]
    ).first()

    if cultura_existente:
        # Compara os nomes normalizados para evitar falsos positivos
        if cultura_existente.nome.strip().lower() == nome_normalizado:
            raise HTTPException(
                status_code=400, 
                detail="Já existe uma cultura com este nome cadastrada."
            )

    nova_cultura = Cultura(
        nome=cultura.nome.strip(),  # Remove espaços extras
        usuario_id=current_user["user_id"]
    )
    
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
    nome: Optional[str] = Query(None, description="Filtrar pelo nome da cultura"),
    skip: int = Query(0, ge=0, description="Número de itens a pular (paginação)"),
    limit: int = Query(100, ge=1, le=200, description="Número máximo de itens por página"),
    db: Session = Depends(get_db),
    current_user = Depends(verify_token)
):
    """
    Lista as culturas do usuário autenticado, com opção de filtro por nome.
    """
    query = db.query(Cultura).filter(Cultura.usuario_id == current_user["user_id"])

    if nome:
        # Remove espaços extras e faz busca case-insensitive
        nome_filtro = nome.strip()
        query = query.filter(Cultura.nome.ilike(f"%{nome_filtro}%"))

    # Adiciona paginação
    culturas = query.offset(skip).limit(limit).all()
    return culturas


@router.get(
    "/{cultura_id}",
    response_model=CulturaOut,
    summary="Obter cultura por ID",
)
def obter_cultura(
    cultura_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(verify_token)
):
    """
    Retorna os detalhes de uma cultura específica do usuário autenticado.
    """
    cultura = db.query(Cultura).filter(
        Cultura.id == cultura_id,
        Cultura.usuario_id == current_user["user_id"]
    ).first()
    
    if not cultura:
        raise HTTPException(
            status_code=404, 
            detail="Cultura não encontrada ou você não tem permissão para acessá-la."
        )
        
    return cultura


@router.put(
    "/{cultura_id}",
    response_model=CulturaOut,
    summary="Atualizar cultura",
)
def atualizar_cultura(
    cultura_id: int,
    dados: CulturaCreate,
    db: Session = Depends(get_db),
    current_user = Depends(verify_token)
):
    """
    Atualiza os dados de uma cultura existente.
    - Verifica se o novo nome já está em uso por outra cultura do mesmo usuário
    """
    cultura = db.query(Cultura).filter(
        Cultura.id == cultura_id,
        Cultura.usuario_id == current_user["user_id"]
    ).first()
    
    if not cultura:
        raise HTTPException(status_code=404, detail="Cultura não encontrada.")
    
    # Normaliza o novo nome para comparação
    novo_nome_normalizado = dados.nome.strip().lower()
    
    # Verifica se outra cultura já usa este nome
    cultura_com_mesmo_nome = db.query(Cultura).filter(
        Cultura.nome.ilike(f"%{novo_nome_normalizado}%"),
        Cultura.usuario_id == current_user["user_id"],
        Cultura.id != cultura_id
    ).first()
    
    if cultura_com_mesmo_nome:
        if cultura_com_mesmo_nome.nome.strip().lower() == novo_nome_normalizado:
            raise HTTPException(
                status_code=400, 
                detail="Já existe outra cultura com este nome."
            )
    
    cultura.nome = dados.nome.strip()
    db.commit()
    db.refresh(cultura)
    return cultura


@router.delete(
    "/{cultura_id}",
    status_code=204,
    summary="Excluir cultura",
)
def excluir_cultura(
    cultura_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(verify_token)
):
    """
    Exclui uma cultura específica.
    - Verifica se há produções associadas antes de permitir a exclusão
    """
    cultura = db.query(Cultura).filter(
        Cultura.id == cultura_id,
        Cultura.usuario_id == current_user["user_id"]
    ).first()
    
    if not cultura:
        raise HTTPException(status_code=404, detail="Cultura não encontrada.")
    
    # Verifica se há produções associadas
    producoes_associadas = db.query(Cultura).filter(
        Cultura.id == cultura_id
    ).join(Cultura.producoes).first()
    
    if producoes_associadas and producoes_associadas.producoes:
        raise HTTPException(
            status_code=400,
            detail="Não é possível excluir cultura com produções associadas."
        )
    
    db.delete(cultura)
    db.commit()
    return None