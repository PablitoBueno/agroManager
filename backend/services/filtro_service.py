from datetime import date
from typing import Optional
from sqlalchemy.orm import Query

def aplicar_filtros_producao(query: Query,
                              data_inicial: Optional[date] = None,
                              data_final: Optional[date] = None,
                              cultura_id: Optional[int] = None) -> Query:
    if data_inicial:
        query = query.filter_by(data_colheita__gte=data_inicial)
    if data_final:
        query = query.filter_by(data_colheita__lte=data_final)
    if cultura_id:
        query = query.filter_by(cultura_id=cultura_id)
    return query

def aplicar_filtros_generico(query: Query, **kwargs) -> Query:
    for campo, valor in kwargs.items():
        if valor is not None:
            query = query.filter(getattr(query.column_descriptions[0]['entity'], campo) == valor)
    return query
