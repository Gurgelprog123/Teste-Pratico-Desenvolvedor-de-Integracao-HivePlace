from sqlite3 import Row
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from src.api.schemas import (
    HealthResponse,
    ProcurementListResponse,
    ProcurementResponse,
)
from src.repositories.procurement_repository import ProcurementRepository


router = APIRouter()
repository = ProcurementRepository()


def row_to_procurement_response(row: Row) -> ProcurementResponse:
    """Converte uma linha do SQLite para o formato público da API."""

    return ProcurementResponse(
        pncp_id=row["pncp_id"],
        title=row["title"],
        modality=row["modality"],
        last_update=row["last_update"],
        organization=row["organization"],
        city=row["city"],
        state=row["state"],
        object_description=row["object_description"],
        url=row["url"],
        first_seen_at=row["first_seen_at"],
        last_seen_at=row["last_seen_at"],
        updated_at=row["updated_at"],
    )


@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["system"],
)
def health():
    return HealthResponse(
        status="ok",
        database_records=repository.count(),
    )


@router.get(
    "/procurements",
    response_model=ProcurementListResponse,
    tags=["procurements"],
)
def list_procurements(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    state: Optional[str] = Query(
        default=None,
        min_length=2,
        max_length=2,
        description="Filtra pela UF. Exemplo: MG",
    ),
    modality: Optional[str] = Query(
        default=None,
        description="Filtra pela modalidade. Exemplo: Dispensa",
    ),
    organization: Optional[str] = Query(
        default=None,
        description="Busca parcial pelo nome do órgão.",
    ),
    search: Optional[str] = Query(
        default=None,
        description="Busca textual em título, objeto e órgão.",
    ),
):
    rows = repository.list(
        limit=limit,
        offset=offset,
        state=state,
        modality=modality,
        organization=organization,
        search=search,
    )

    total = repository.count_filtered(
        state=state,
        modality=modality,
        organization=organization,
        search=search,
    )

    items = [
        row_to_procurement_response(row)
        for row in rows
    ]

    return ProcurementListResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=items,
    )


@router.get(
    "/procurements/{pncp_id:path}",
    response_model=ProcurementResponse,
    tags=["procurements"],
)
def get_procurement(pncp_id: str):
    row = repository.find_by_pncp_id(pncp_id)

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Contratação não encontrada.",
        )

    return row_to_procurement_response(row)