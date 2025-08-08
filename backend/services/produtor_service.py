from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import Produtor
from pydantic import BaseModel, constr, validator
import re
from auth import verify_token

router = APIRouter(
    prefix="/produtores",
    tags=["Produtores"],
)


# ==== Schemas ====
class ProdutorBase(BaseModel):
    nome: str
    cpf: constr(min_length=11, max_length=14)
    
    @validator('cpf')
    def validate_cpf(cls, v):
        # Remove caracteres não numéricos
        cpf = re.sub(r'[^0-9]', '', v)
        
        # Verifica tamanho
        if len(cpf) != 11:
            raise ValueError('CPF deve conter 11 dígitos')
        
        # Verifica se todos os dígitos são iguais
        if cpf == cpf[0] * 11:
            raise ValueError('CPF inválido')
        
        # Validação do primeiro dígito verificador
        soma = 0
        for i in range(9):
            soma += int(cpf[i]) * (10 - i)
        resto = soma % 11
        digito1 = 0 if resto < 2 else 11 - resto
        
        if digito1 != int(cpf[9]):
            raise ValueError('CPF inválido')
        
        # Validação do segundo dígito verificador
        soma = 0
        for i in range(10):
            soma += int(cpf[i]) * (11 - i)
        resto = soma % 11
        digito2 = 0 if resto < 2 else 11 - resto
        
        if digito2 != int(cpf[10]):
            raise ValueError('CPF inválido')
        
        # Retorna CPF formatado (opcional)
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"


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
    produtor: ProdutorCreate, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """
    Cria um novo produtor. O CPF deve ser único e válido.
    """
    # Formata CPF para armazenar apenas dígitos
    cpf_digits = re.sub(r'[^0-9]', '', produtor.cpf)
    
    # Verifica se CPF já está cadastrado
    cpf_existente = db.query(Produtor).filter(Produtor.cpf == cpf_digits).first()
    if cpf_existente:
        raise HTTPException(status_code=400, detail="CPF já cadastrado.")

    novo_produtor = Produtor(
        nome=produtor.nome.strip(),  # Remove espaços extras
        cpf=cpf_digits
    )
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
    current_user: dict = Depends(verify_token)
):
    """
    Lista produtores com filtros opcionais por nome e CPF, e suporte a paginação.
    """
    query = db.query(Produtor)

    if nome:
        query = query.filter(Produtor.nome.ilike(f"%{nome.strip()}%"))
    if cpf:
        # Remove formatação do CPF para busca
        cpf_digits = re.sub(r'[^0-9]', '', cpf)
        query = query.filter(Produtor.cpf == cpf_digits)

    produtores = query.offset(skip).limit(limit).all()
    return produtores


@router.get(
    "/{produtor_id}",
    response_model=ProdutorOut,
    summary="Obter produtor por ID",
    response_description="Dados do produtor",
)
def obter_produtor(
    produtor_id: int, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
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
    produtor_id: int, 
    dados: ProdutorCreate, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """
    Atualiza informações de um produtor existente.
    """
    produtor = db.query(Produtor).filter(Produtor.id == produtor_id).first()
    if not produtor:
        raise HTTPException(status_code=404, detail="Produtor não encontrado.")

    # Formata CPF para armazenar apenas dígitos
    cpf_digits = re.sub(r'[^0-9]', '', dados.cpf)
    
    # Verifica se CPF já está cadastrado em outro produtor
    cpf_existente = (
        db.query(Produtor)
        .filter(Produtor.cpf == cpf_digits, Produtor.id != produtor_id)
        .first()
    )
    if cpf_existente:
        raise HTTPException(status_code=400, detail="CPF já cadastrado para outro produtor.")

    produtor.nome = dados.nome.strip()
    produtor.cpf = cpf_digits

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
    produtor_id: int, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
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