from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import Produtor
from pydantic import BaseModel, constr

router = APIRouter(
    prefix="/produtores",
    tags=["Produtores"],
)


# ==== Schemas ====
class ProdutorBase(BaseModel):
    nome: str
    cpf: constr(min_length=11, max_length=14)


class ProdutorCreate(ProdutorBase):
    pass


class ProdutorOut(ProdutorBase):
    id: int

    class Config:
        orm_mode = True


# ==== Endpoints ====

@router.post(
    "/",
    response_model=ProdutorOut,
    status_code=201,
    summary="Criar novo produtor",
    response_description="Dados do produtor criado",
)
def criar_produtor(
    produtor: ProdutorCreate, db: Session = Depends(get_db)
):
    """
    Cria um novo produtor. O CPF deve ser único.
    """
    cpf_existente = db.query(Produtor).filter(Produtor.cpf == produtor.cpf).first()
    if cpf_existente:
        raise HTTPException(status_code=400, detail="CPF já cadastrado.")

    novo_produtor = Produtor(**produtor.dict())
    db.add(novo_produtor)
    db.commit()
    db.refresh(novo_produtor)
    return novo_produtor


@router.get(
    "/",
    response_model=List[ProdutorOut],
    summary="Listar produtores",
    response_description="Lista de produtores cadastrados",
)
def listar_produtores(
    nome: Optional[str] = Query(None, description="Filtrar pelo nome"),
    cpf: Optional[str] = Query(None, description="Filtrar pelo CPF"),
    skip: int = Query(0, ge=0, description="Número de itens a pular (paginação)"),
    limit: int = Query(10, ge=1, le=100, description="Número máximo de itens"),
    db: Session = Depends(get_db),
):
    """
    Lista produtores com filtros opcionais por nome e CPF, e suporte a paginação.
    """
    query = db.query(Produtor)

    if nome:
        query = query.filter(Produtor.nome.ilike(f"%{nome}%"))
    if cpf:
        query = query.filter(Produtor.cpf == cpf)

    produtores = query.offset(skip).limit(limit).all()
    return produtores


@router.get(
    "/{produtor_id}",
    response_model=ProdutorOut,
    summary="Obter produtor por ID",
    response_description="Dados do produtor",
)
def obter_produtor(
    produtor_id: int, db: Session = Depends(get_db)
):
    """
    Retorna os dados de um produtor específico pelo ID.
    """
    produtor = db.query(Produtor).filter(Produtor.id == produtor_id).first()
    if not produtor:
        raise HTTPException(status_code=404, detail="Produtor não encontrado.")
    return produtor


@router.put(
    "/{produtor_id}",
    response_model=ProdutorOut,
    summary="Atualizar produtor",
    response_description="Dados atualizados do produtor",
)
def atualizar_produtor(
    produtor_id: int, dados: ProdutorCreate, db: Session = Depends(get_db)
):
    """
    Atualiza informações de um produtor existente.
    """
    produtor = db.query(Produtor).filter(Produtor.id == produtor_id).first()
    if not produtor:
        raise HTTPException(status_code=404, detail="Produtor não encontrado.")

    cpf_existente = (
        db.query(Produtor)
        .filter(Produtor.cpf == dados.cpf, Produtor.id != produtor_id)
        .first()
    )
    if cpf_existente:
        raise HTTPException(status_code=400, detail="CPF já cadastrado para outro produtor.")

    produtor.nome = dados.nome
    produtor.cpf = dados.cpf

    db.commit()
    db.refresh(produtor)
    return produtor


@router.delete(
    "/{produtor_id}",
    status_code=204,
    summary="Excluir produtor",
    response_description="Produtor excluído com sucesso",
)
def deletar_produtor(
    produtor_id: int, db: Session = Depends(get_db)
):
    """
    Exclui um produtor pelo ID.
    """
    produtor = db.query(Produtor).filter(Produtor.id == produtor_id).first()
    if not produtor:
        raise HTTPException(status_code=404, detail="Produtor não encontrado.")

    db.delete(produtor)
    db.commit()
    return None
