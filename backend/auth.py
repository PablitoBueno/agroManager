from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import hashlib
import jwt  # PyJWT
import logging

from db import get_db
from models import Usuario
from config import settings

router = APIRouter(prefix="/auth", tags=["Auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Em memória apenas para protótipo (em produção, usar Redis ou banco)
BLACKLIST = set()

# Configuração de logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def gerar_hash(senha: str) -> str:
    """Gera hash SHA-256 para senhas."""
    return hashlib.sha256(senha.encode()).hexdigest()

def authenticate_user(db: Session, email: str, senha: str) -> Usuario:
    """Autentica usuário com email e senha."""
    try:
        user = db.query(Usuario).filter(Usuario.email == email).first()
        if not user or user.senha != gerar_hash(senha):
            logger.warning(f"Tentativa de login falha para: {email}")
            return None
        return user
    except Exception as e:
        logger.error(f"Erro na autenticação: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno no servidor"
        )

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Cria token JWT com dados do usuário e expiração."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

@router.post("/login", response_model=dict)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> dict:
    """
    Autentica usuário e retorna token JWT contendo:
    - sub: email do usuário
    - user_id: ID do usuário
    """
    try:
        user = authenticate_user(db, form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciais incorretas",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        token = create_access_token({
            "sub": user.email,
            "user_id": user.id
        })
        
        logger.info(f"Login bem-sucedido para: {user.email}")
        return {"access_token": token, "token_type": "bearer"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno no servidor"
        )

@router.post("/logout", response_model=dict)
def logout(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Invalida token atual (adiciona à blacklist).
    """
    try:
        BLACKLIST.add(token)
        logger.info(f"Token invalidado: {token[:10]}...")
        return {"msg": "Logout realizado com sucesso."}
    except Exception as e:
        logger.error(f"Erro no logout: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao processar logout"
        )

def verify_token(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Verifica token e retorna payload contendo:
    - email: email do usuário
    - user_id: ID do usuário
    """
    try:
        # Verifica se token está na blacklist
        if token in BLACKLIST:
            logger.warning("Tentativa de uso de token invalidado")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Token inválido"
            )
        
        # Decodifica token
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        
        # Verifica campos obrigatórios
        email = payload.get("sub")
        user_id = payload.get("user_id")
        
        if not email or not user_id:
            logger.error("Token com campos incompletos")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Token inválido"
            )
            
        return {"email": email, "user_id": user_id}
    
    except jwt.ExpiredSignatureError:
        logger.warning("Token expirado")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Token expirado"
        )
    
    except jwt.PyJWTError as e:
        logger.error(f"Erro JWT: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Token inválido"
        )
    
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(f"Erro na verificação do token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno na autenticação"
        )