from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class ProcurementResponse(BaseModel):
    pncp_id: str
    title: str
    modality: Optional[str]
    last_update: Optional[date]
    organization: Optional[str]
    city: Optional[str]
    state: Optional[str]
    object_description: Optional[str]
    url: str
    first_seen_at: datetime
    last_seen_at: datetime
    updated_at: datetime


class ProcurementListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[ProcurementResponse]


class HealthResponse(BaseModel):
    status: str
    database_records: int