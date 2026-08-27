from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.routes import router
from src.database.connection import initialize_database


API_VERSION = "1.0.0"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Inicializa os recursos necessários antes da API iniciar."""

    initialize_database()
    yield


app = FastAPI(
    title="PNCP Public Procurement API",
    description=(
        "API para consulta das contratações públicas coletadas do Portal Nacional de Contratações Públicas (PNCP)."
    ),
    version=API_VERSION,
    lifespan=lifespan,
)

app.include_router(router)


@app.get("/", tags=["system"])
def root():
    return {
        "name": "PNCP Public Procurement API",
        "version": API_VERSION,
        "docs": "/docs",
        "health": "/health",
    }