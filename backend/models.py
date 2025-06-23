from sqlalchemy import (
    Column, Integer, String, Text, TIMESTAMP,
    ForeignKey, Numeric, Date
)
from sqlalchemy.orm import declarative_base, relationship  # Adicione relationship aqui
from datetime import datetime, date

Base = declarative_base()

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    cpf = Column(String(15), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    senha = Column(String(255), nullable=False)
    data_criacao = Column(TIMESTAMP, default=datetime.utcnow)

    # Relacionamentos
    culturas = relationship(
        "Cultura", 
        back_populates="usuario", 
        cascade="all, delete-orphan"
    )
    producoes = relationship(
        "Producao", 
        back_populates="usuario", 
        cascade="all, delete-orphan"
    )
    estoque = relationship(
        "Estoque", 
        back_populates="usuario", 
        cascade="all, delete-orphan"
    )


class Cultura(Base):
    __tablename__ = "culturas"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    descricao = Column(Text, nullable=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    
    # Relacionamento bidirecional
    usuario = relationship("Usuario", back_populates="culturas")
    
    # Relacionamento com produções
    producoes = relationship(
        "Producao", 
        back_populates="cultura", 
        cascade="all, delete-orphan"
    )


class Producao(Base):
    __tablename__ = "producao"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    cultura_id = Column(Integer, ForeignKey("culturas.id", ondelete="CASCADE"), nullable=False)
    quantidade = Column(Numeric(10, 2), nullable=False)
    data_colheita = Column(Date, nullable=False)
    data_registro = Column(TIMESTAMP, default=datetime.utcnow)
    
    # Relacionamentos bidirecionais
    usuario = relationship("Usuario", back_populates="producoes")
    cultura = relationship("Cultura", back_populates="producoes")


class Estoque(Base):
    __tablename__ = "estoque"

    id = Column(Integer, primary_key=True, index=True)
    produto_nome = Column(String(100), nullable=False)
    quantidade_estoque = Column(Numeric(10, 2), nullable=False)
    validade = Column(Date, nullable=True)
    fornecedor = Column(String(100), nullable=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    data_registro = Column(TIMESTAMP, default=datetime.utcnow)
    
    # Relacionamento bidirecional
    usuario = relationship("Usuario", back_populates="estoque")