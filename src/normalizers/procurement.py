from datetime import date, datetime
from typing import Optional

from src.models.procurement import Procurement, RawProcurement


PNCP_BASE_URL = "https://pncp.gov.br"


def clean_text(value: Optional[str]) -> Optional[str]:
    """Normaliza espaços e converte textos vazios em None."""

    if value is None:
        return None

    normalized = " ".join(value.split())

    return normalized or None


def normalize_date(value: Optional[str]) -> Optional[date]:
    """Converte datas do PNCP no formato DD/MM/YYYY."""

    value = clean_text(value)

    if value is None:
        return None

    try:
        return datetime.strptime(
            value,
            "%d/%m/%Y",
        ).date()

    except ValueError as error:
        raise ValueError(
            f"Data inválida recebida: {value}"
        ) from error


def normalize_location(
    value: Optional[str],
) -> tuple[Optional[str], Optional[str]]:
    """Separa localização no formato cidade/UF."""

    value = clean_text(value)

    if value is None:
        return None, None

    if "/" not in value:
        return value, None

    city, state = value.rsplit("/", 1)

    city = clean_text(city)
    state = clean_text(state)

    if state:
        state = state.upper()

    return city, state


def normalize_detail_url(href: str) -> str:
    """
    Converte links relativos do catálogo para a rota navegável
    correspondente no PNCP.
    """

    href = href.strip()

    if href.startswith(("http://", "https://")):
        return href

    if href.startswith("/app/"):
        return f"{PNCP_BASE_URL}{href}"

    if href.startswith("/editais/"):
        return f"{PNCP_BASE_URL}/app{href}"

    return f"{PNCP_BASE_URL}/{href.lstrip('/')}"


def normalize_procurement(raw: RawProcurement) -> Procurement:
    """Transforma uma contratação bruta em um registro normalizado."""

    title = clean_text(raw.title)
    pncp_id = clean_text(raw.pncp_id)

    if title is None:
        raise ValueError(
            "Contratação sem título."
        )

    if pncp_id is None:
        raise ValueError(
            "Contratação sem ID PNCP."
        )

    city, state = normalize_location(
        raw.location
    )

    return Procurement(
        title=title,
        pncp_id=pncp_id,
        modality=clean_text(raw.modality),
        last_update=normalize_date(raw.last_update),
        organization=clean_text(raw.organization),
        city=city,
        state=state,
        object_description=clean_text(
            raw.object_description
        ),
        url=normalize_detail_url(raw.href),
    )