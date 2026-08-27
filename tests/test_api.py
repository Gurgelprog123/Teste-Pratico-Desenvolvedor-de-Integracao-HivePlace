from datetime import date

from fastapi.testclient import TestClient

from src.api.app import app
from src.models.procurement import Procurement
from src.repositories.procurement_repository import ProcurementRepository


def create_test_records() -> tuple[Procurement, Procurement]:
    """Insere dois registros conhecidos no banco temporário."""

    repository = ProcurementRepository()

    first = Procurement(
        title="Aviso de Contratação Direta nº 14/2026",
        pncp_id="26989350002160-1-000010/2026",
        modality="Dispensa",
        last_update=date(2026, 8, 27),
        organization="FUNDACAO NACIONAL DE SAUDE",
        city="Belo Horizonte",
        state="MG",
        object_description=(
            "Aquisição de eletrodomésticos "
            "e equipamentos de copa"
        ),
        url=(
            "https://pncp.gov.br/app/editais/"
            "26989350002160/2026/10"
        ),
    )

    second = Procurement(
        title="Edital nº 53/2026",
        pncp_id="00394452000103-1-018433/2026",
        modality="Pregão - Eletrônico",
        last_update=date(2026, 8, 27),
        organization="COMANDO DO EXERCITO",
        city="Curitiba",
        state="PR",
        object_description=(
            "Aquisição de dietas e suplementos para hospital"
        ),
        url=(
            "https://pncp.gov.br/app/editais/"
            "00394452000103/2026/18433"
        ),
    )

    repository.save(first)
    repository.save(second)

    return first, second


def test_health(temporary_database):
    create_test_records()

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "ok"
    assert body["database_records"] == 2


def test_list_procurements(temporary_database):
    create_test_records()

    with TestClient(app) as client:
        response = client.get("/procurements")

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 2
    assert len(body["items"]) == 2


def test_combined_filters(temporary_database):
    """Valida a combinação dos filtros disponíveis na listagem."""

    create_test_records()

    params = {
        "limit": 100,
        "offset": 0,
        "state": "MG",
        "modality": "Dispensa",
        "organization": "FUNDACAO NACIONAL DE SAUDE",
        "search": "equipamentos de copa",
    }

    with TestClient(app) as client:
        response = client.get(
            "/procurements",
            params=params,
        )

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 1
    assert len(body["items"]) == 1
    assert (
        body["items"][0]["pncp_id"]
        == "26989350002160-1-000010/2026"
    )


def test_get_procurement_by_id(temporary_database):
    """Valida um ID PNCP que contém '/' em sua composição."""

    first, _ = create_test_records()

    with TestClient(app) as client:
        response = client.get(
            f"/procurements/{first.pncp_id}"
        )

    assert response.status_code == 200

    body = response.json()

    assert body["pncp_id"] == first.pncp_id
    assert body["state"] == "MG"


def test_unknown_procurement_returns_404(
    temporary_database,
):
    with TestClient(app) as client:
        response = client.get(
            "/procurements/"
            "00000000000000-1-000000/2099"
        )

    assert response.status_code == 404
    assert (
        response.json()["detail"]
        == "Contratação não encontrada."
    )


def test_invalid_state_returns_422(
    temporary_database,
):
    with TestClient(app) as client:
        response = client.get(
            "/procurements",
            params={"state": "MGINVALIDO"},
        )

    assert response.status_code == 422