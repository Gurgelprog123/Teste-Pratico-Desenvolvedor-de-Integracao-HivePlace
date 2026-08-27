import time

from playwright.sync_api import sync_playwright

from src.scrapers.pncp import parse_procurement_card


BASE_URL = "https://pncp.gov.br/app/editais"
PROCUREMENT_SELECTOR = 'a[href^="/editais/"]'

PAGES_TO_TEST = 3
REQUEST_INTERVAL_SECONDS = 1.0


def collect_page(page, page_number: int):
    """
    Coleta registros de uma página do catálogo para validar
    paginação e ocorrência de links duplicados no DOM.
    """

    url = f"{BASE_URL}?pagina={page_number}"

    print(f"Acessando página {page_number}: {url}")

    response = page.goto(
        url,
        wait_until="domcontentloaded",
        timeout=30000,
    )

    if response is None:
        raise RuntimeError(
            "Página não retornou resposta HTTP."
        )

    if response.status >= 400:
        raise RuntimeError(
            f"Erro HTTP {response.status}"
        )

    links = page.locator(PROCUREMENT_SELECTOR)

    links.first.wait_for(
        state="visible",
        timeout=15000,
    )

    # O catálogo pode renderizar mais de um link para o mesmo edital.
    links_by_href = {}

    for index in range(links.count()):
        link = links.nth(index)

        href = link.get_attribute("href")
        text = link.inner_text().strip()

        if not href or not text:
            continue

        previous_text = links_by_href.get(href)

        if (
            previous_text is None
            or len(text) > len(previous_text)
        ):
            links_by_href[href] = text

    records_by_pncp_id = {}

    for href, text in links_by_href.items():
        record = parse_procurement_card(
            text=text,
            href=href,
        )

        if record.pncp_id:
            records_by_pncp_id[
                record.pncp_id
            ] = record

    print(
        f"Links encontrados: {links.count()} | "
        f"Links únicos: {len(links_by_href)} | "
        f"Registros únicos: {len(records_by_pncp_id)}"
    )

    return list(
        records_by_pncp_id.values()
    )


def main() -> None:
    """
    Valida a paginação do catálogo e verifica duplicidades
    entre páginas consecutivas do PNCP.
    """

    all_records = {}

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=False
        )

        try:
            page = browser.new_page()

            for page_number in range(
                1,
                PAGES_TO_TEST + 1,
            ):
                records = collect_page(
                    page,
                    page_number,
                )

                duplicates_between_pages = 0

                for record in records:
                    if record.pncp_id in all_records:
                        duplicates_between_pages += 1
                        continue

                    all_records[
                        record.pncp_id
                    ] = record

                print(
                    f"Duplicados em páginas anteriores: "
                    f"{duplicates_between_pages}"
                )
                print(
                    f"Total acumulado: "
                    f"{len(all_records)}"
                )

                if page_number < PAGES_TO_TEST:
                    time.sleep(
                        REQUEST_INTERVAL_SECONDS
                    )

            print(
                f"Resultado final: {PAGES_TO_TEST} páginas, "
                f"{len(all_records)} registros únicos."
            )

        except Exception as error:
            print(
                "Erro durante o spike:",
                error,
            )

        finally:
            browser.close()


if __name__ == "__main__":
    main()