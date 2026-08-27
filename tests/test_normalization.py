from datetime import date

import pytest

from src.models.procurement import RawProcurement
from src.normalizers.procurement import (
    clean_text,
    normalize_date,
    normalize_detail_url,
    normalize_location,
    normalize_procurement,
)


def test_clean_text():
    value = "  Contratação   de \n  equipamentos  "

    result = clean_text(value)

    assert result == "Contratação de equipamentos"


def test_clean_text_empty_becomes_none():
    assert clean_text("   ") is None


def test_normalize_date():
    result = normalize_date("27/08/2026")

    assert result == date(2026, 8, 27)


def test_invalid_date_raises_error():
    """Uma data inválida deve produzir erro de normalização."""

    with pytest.raises(ValueError):
        normalize_date("99/99/2026")


def test_normalize_location():
    city, state = normalize_location("Belo Horizonte/MG")

    assert city == "Belo Horizonte"
    assert state == "MG"


def test_location_without_state():
    """Preserva a cidade quando a UF não está disponível."""

    city, state = normalize_location("Brasília")

    assert city == "Brasília"
    assert state is None


def test_normalize_relative_detail_url():
    """Converte a URL relativa do catálogo para a rota navegável."""

    result = normalize_detail_url(
        "/editais/26989350002160/2026/10"
    )

    assert result == (
        "https://pncp.gov.br/app/editais/"
        "26989350002160/2026/10"
    )


def test_normalize_procurement():
    """Valida a transformação completa do registro coletado."""

    raw = RawProcurement(
        title="  Aviso de Contratação Direta nº 14/2026  ",
        pncp_id="26989350002160-1-000010/2026",
        modality="Dispensa",
        last_update="27/08/2026",
        organization="FUNDACAO NACIONAL DE SAUDE",
        location="Belo Horizonte/MG",
        object_description=(
            "  Aquisição de equipamentos de copa  "
        ),
        href="/editais/26989350002160/2026/10",
    )

    result = normalize_procurement(raw)

    assert result.title == "Aviso de Contratação Direta nº 14/2026"
    assert result.pncp_id == "26989350002160-1-000010/2026"
    assert result.last_update == date(2026, 8, 27)
    assert result.city == "Belo Horizonte"
    assert result.state == "MG"
    assert (
        result.object_description
        == "Aquisição de equipamentos de copa"
    )
    assert result.url == (
        "https://pncp.gov.br/app/editais/"
        "26989350002160/2026/10"
    )


def test_procurement_without_pncp_id_is_invalid():
    """O PNCP ID é obrigatório para o registro normalizado."""

    raw = RawProcurement(
        title="Edital de teste",
        pncp_id=None,
        modality="Dispensa",
        last_update="27/08/2026",
        organization="Órgão de teste",
        location="Brasília/DF",
        object_description="Teste",
        href="/editais/teste",
    )

    with pytest.raises(
        ValueError,
        match="ID PNCP",
    ):
        normalize_procurement(raw)