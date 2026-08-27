from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class RawProcurement:
    """
    Representa os dados extraídos diretamente da página do PNCP,
    antes da etapa de normalização.
    """

    title: Optional[str]
    pncp_id: Optional[str]
    modality: Optional[str]
    last_update: Optional[str]
    organization: Optional[str]
    location: Optional[str]
    object_description: Optional[str]
    href: str


@dataclass
class Procurement:
    """
    Representa uma contratação já normalizada e pronta
    para persistência.
    """

    title: str
    pncp_id: str
    modality: Optional[str]
    last_update: Optional[date]
    organization: Optional[str]
    city: Optional[str]
    state: Optional[str]
    object_description: Optional[str]
    url: str