
from fastapi import FastAPI
import uvicorn

import db
from auth import router as auth_router
from services.stats_service import router as stats_router
from services.usuario_service import router as user_router
from services.cultura_service import router as cultura_router
from services.producao_service import router as producao_router
from services.estoque_service import router as estoque_router

# Inicializa banco
db.init_db()

app = FastAPI(title="API de Gestão Agrícola")

# Rotas da API
app.include_router(auth_router)
app.include_router(stats_router)
app.include_router(user_router)
app.include_router(cultura_router)
app.include_router(producao_router)
app.include_router(estoque_router)

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
