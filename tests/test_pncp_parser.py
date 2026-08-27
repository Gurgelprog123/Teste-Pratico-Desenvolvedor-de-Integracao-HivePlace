from pathlib import Path

from bs4 import BeautifulSoup

from src.scrapers.pncp import parse_procurement_card


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "pncp_catalog.html"
)


def load_fixture() -> BeautifulSoup:
    """
    Carrega a fixture local do catálogo.

    Os testes do parser não realizam requisições ao PNCP.
    """

    html = FIXTURE_PATH.read_text(
        encoding="utf-8"
    )

    return BeautifulSoup(
        html,
        "html.parser",
    )


def test_parse_multiline_procurement():
    soup = load_fixture()

    element = soup.select_one(
        ".procurement-multiline"
    )

    assert element is not None

    href = element.get("href")

    assert isinstance(href, str)

    text = element.get_text(
        "\n",
        strip=True,
    )

    result = parse_procurement_card(
        text=text,
        href=href,
    )

    assert result.title == "Edital nº 002/2026"
    assert (
        result.pncp_id
        == "18457192000125-1-000025/2026"
    )
    assert (
        result.modality
        == "Concorrência - Eletrônica"
    )
    assert result.last_update == "27/08/2026"
    assert (
        result.organization
        == "MUNICIPIO DE GURINHATA"
    )
    assert result.location == "Gurinhatã/MG"
    assert result.object_description == (
        "CONTRATAÇÃO DE EMPRESA PARA "
        "EXECUÇÃO DE OBRA REFORMA DA "
        "ESCOLA MUNICIPAL JOSÉ MARTINS "
        "ALAMEU"
    )
    assert (
        result.href
        == "/editais/18457192000125/2026/25"
    )


def test_parse_flat_procurement():
    """
    Protege contra regressão no tratamento de cards
    cujo conteúdo é retornado em uma única linha.
    """

    soup = load_fixture()

    element = soup.select_one(
        ".procurement-flat"
    )

    assert element is not None

    href = element.get("href")

    assert isinstance(href, str)

    text = element.get_text(
        " ",
        strip=True,
    )

    result = parse_procurement_card(
        text=text,
        href=href,
    )

    assert result.last_update == "27/08/2026"
    assert (
        result.organization
        == "MUNICIPIO DE GURINHATA"
    )
    assert result.location == "Gurinhatã/MG"
    assert (
        result.modality
        == "Concorrência - Eletrônica"
    )
    assert result.object_description is not None
    assert result.object_description.startswith(
        "CONTRATAÇÃO DE EMPRESA"
    )


def test_parse_procurement_without_id():
    """
    Um card incompleto não deve gerar artificialmente
    um identificador PNCP.
    """

    text = (
        "Edital nº 123/2026 "
        "Modalidade da Contratação: Dispensa "
        "Última Atualização: 27/08/2026 "
        "Órgão: MUNICIPIO TESTE "
        "Local: Brasília/DF "
        "Objeto: Objeto de teste"
    )

    result = parse_procurement_card(
        text=text,
        href="/editais/teste",
    )

    assert result.pncp_id is None