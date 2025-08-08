from datetime import date
from typing import Optional, Any
from sqlalchemy.orm import Query
from sqlalchemy import and_
from models import Producao, Estoque

def aplicar_filtros_producao(
    query: Query,
    data_inicial: Optional[date] = None,
    data_final: Optional[date] = None,
    cultura_id: Optional[int] = None
) -> Query:
    """
    Aplica filtros a uma query de produção agrícola.
    
    Parâmetros:
        query: Query base a ser filtrada
        data_inicial: Filtra produções com data_colheita >= data_inicial
        data_final: Filtra produções com data_colheita <= data_final
        cultura_id: Filtra por ID de cultura específica
    
    Retorna:
        Query filtrada
    """
    # Filtro por data inicial
    if data_inicial:
        query = query.filter(Producao.data_colheita >= data_inicial)
    
    # Filtro por data final
    if data_final:
        query = query.filter(Producao.data_colheita <= data_final)
    
    # Filtro por cultura
    if cultura_id is not None:
        query = query.filter(Producao.cultura_id == cultura_id)
    
    return query


def aplicar_filtros_estoque(
    query: Query,
    produto: Optional[str] = None,
    fornecedor: Optional[str] = None,
    validade_inicial: Optional[date] = None,
    validade_final: Optional[date] = None
) -> Query:
    """
    Aplica filtros a uma query de estoque.
    
    Parâmetros:
        query: Query base a ser filtrada
        produto: Filtra por nome do produto (busca parcial case-insensitive)
        fornecedor: Filtra por fornecedor (busca parcial case-insensitive)
        validade_inicial: Filtra itens com validade >= data especificada
        validade_final: Filtra itens com validade <= data especificada
    
    Retorna:
        Query filtrada
    """
    # Filtro por nome do produto
    if produto:
        query = query.filter(Estoque.produto_nome.ilike(f"%{produto.strip()}%"))
    
    # Filtro por fornecedor
    if fornecedor:
        query = query.filter(Estoque.fornecedor.ilike(f"%{fornecedor.strip()}%"))
    
    # Filtro por validade
    if validade_inicial or validade_final:
        filtro_validade = []
        
        if validade_inicial:
            filtro_validade.append(Estoque.validade >= validade_inicial)
        
        if validade_final:
            filtro_validade.append(Estoque.validade <= validade_final)
            
        query = query.filter(and_(*filtro_validade))
    
    return query


def aplicar_filtros_generico(
    query: Query,
    **filtros: Any
) -> Query:
    """
    Aplica filtros genéricos de igualdade a uma query.
    
    Parâmetros:
        query: Query base a ser filtrada
        filtros: Pares chave-valor onde:
            - chave = nome do campo
            - valor = valor para filtro de igualdade
    
    Retorna:
        Query filtrada
    """
    for campo, valor in filtros.items():
        if valor is not None:
            # Obtém o modelo da query
            model = query.column_descriptions[0]['entity']
            
            # Verifica se o campo existe no modelo
            if hasattr(model, campo):
                query = query.filter(getattr(model, campo) == valor)
    
    return query