import re
from typing import Optional

from src.models.procurement import RawProcurement


def clean_source_text(text: str) -> str:
    """
    Uniformiza espaços e quebras de linha do texto extraído do DOM.

    O PNCP pode renderizar os mesmos campos em linhas separadas
    ou em uma única sequência de texto.
    """

    return " ".join(text.split())


def extract_pncp_id(text: str) -> Optional[str]:
    """Extrai o identificador oficial da contratação no PNCP."""

    result = re.search(
        r"\d{14}-\d-\d{6}/\d{4}",
        text,
    )

    if result is None:
        return None

    return result.group(0)


def extract_date(text: str) -> Optional[str]:
    """Extrai a data associada ao campo 'Última Atualização'."""

    result = re.search(
        r"Última Atualização:\s*(\d{2}/\d{2}/\d{4})",
        text,
        re.IGNORECASE,
    )

    if result is None:
        return None

    return result.group(1)


def extract_between_labels(
    text: str,
    start_label: str,
    end_label: str,
) -> Optional[str]:
    """Extrai o conteúdo localizado entre dois rótulos do card."""

    pattern = (
        re.escape(start_label)
        + r"\s*(.*?)\s*"
        + re.escape(end_label)
    )

    result = re.search(
        pattern,
        text,
        re.IGNORECASE,
    )

    if result is None:
        return None

    value = result.group(1).strip()

    return value or None


def extract_object(text: str) -> Optional[str]:
    """Extrai o objeto, último campo exibido no card."""

    result = re.search(
        r"Objeto:\s*(.+)$",
        text,
        re.IGNORECASE,
    )

    if result is None:
        return None

    value = result.group(1).strip()

    return value or None


def extract_title(text: str) -> Optional[str]:
    """Extrai o texto anterior ao identificador PNCP."""

    marker = "Id contratação PNCP:"

    marker_position = text.lower().find(
        marker.lower()
    )

    if marker_position == -1:
        return None

    title = text[:marker_position].strip()

    return title or None


def parse_procurement_card(
    text: str,
    href: str,
) -> RawProcurement:
    """
    Interpreta a estrutura de um card do PNCP.

    Os valores ainda não são normalizados nesta etapa.
    """

    text = clean_source_text(text)

    return RawProcurement(
        title=extract_title(text),
        pncp_id=extract_pncp_id(text),
        modality=extract_between_labels(
            text=text,
            start_label="Modalidade da Contratação:",
            end_label="Última Atualização:",
        ),
        last_update=extract_date(text),
        organization=extract_between_labels(
            text=text,
            start_label="Órgão:",
            end_label="Local:",
        ),
        location=extract_between_labels(
            text=text,
            start_label="Local:",
            end_label="Objeto:",
        ),
        object_description=extract_object(text),
        href=href,
    )