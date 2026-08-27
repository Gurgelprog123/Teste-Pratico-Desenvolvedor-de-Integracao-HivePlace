from datetime import date

from src.models.procurement import Procurement
from src.repositories.procurement_repository import (
    ProcurementRepository,
    SaveStatus,
)


def create_procurement(
    object_description: str = "Aquisição de equipamentos de copa",
) -> Procurement:
    """Cria uma contratação padrão para os testes."""

    return Procurement(
        title="Aviso de Contratação Direta nº 14/2026",
        pncp_id="26989350002160-1-000010/2026",
        modality="Dispensa",
        last_update=date(2026, 8, 27),
        organization="FUNDACAO NACIONAL DE SAUDE",
        city="Belo Horizonte",
        state="MG",
        object_description=object_description,
        url=(
            "https://pncp.gov.br/app/editais/"
            "26989350002160/2026/10"
        ),
    )


def test_first_save_inserts_record(
    temporary_database,
):
    repository = ProcurementRepository()
    procurement = create_procurement()

    status = repository.save(procurement)

    assert status == SaveStatus.INSERTED
    assert repository.count() == 1


def test_same_record_is_idempotent(
    temporary_database,
):
    """Salvar novamente o mesmo registro não deve duplicá-lo."""

    repository = ProcurementRepository()
    procurement = create_procurement()

    first_status = repository.save(procurement)
    second_status = repository.save(procurement)

    assert first_status == SaveStatus.INSERTED
    assert second_status == SaveStatus.DUPLICATE
    assert repository.count() == 1


def test_changed_record_is_updated(
    temporary_database,
):
    """O mesmo PNCP ID com conteúdo alterado deve ser atualizado."""

    repository = ProcurementRepository()

    original = create_procurement(
        object_description="Aquisição de equipamentos de copa"
    )

    changed = create_procurement(
        object_description=(
            "Aquisição de equipamentos de copa e cozinha"
        )
    )

    first_status = repository.save(original)
    second_status = repository.save(changed)

    assert first_status == SaveStatus.INSERTED
    assert second_status == SaveStatus.UPDATED
    assert repository.count() == 1

    persisted = repository.find_by_pncp_id(
        changed.pncp_id
    )

    assert persisted is not None
    assert (
        persisted["object_description"]
        == "Aquisição de equipamentos de copa e cozinha"
    )