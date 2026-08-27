from playwright.sync_api import sync_playwright


CATALOG_URL = "https://pncp.gov.br/app/editais?pagina=1"
PROCUREMENT_SELECTOR = 'a[href^="/editais/"]'


def main() -> None:
    """
    Investiga a navegação do catálogo do PNCP para a página de detalhe.

    O objetivo deste spike é verificar se os dados adicionais do edital
    ficam disponíveis de forma estável após a navegação.
    """

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=False
        )

        try:
            page = browser.new_page()

            response = page.goto(
                CATALOG_URL,
                wait_until="domcontentloaded",
                timeout=30000,
            )

            print(
                "Status catálogo:",
                response.status if response else "sem resposta",
            )

            edital_links = page.locator(
                PROCUREMENT_SELECTOR
            )

            edital_links.first.wait_for(
                state="visible",
                timeout=15000,
            )

            print(
                "Links encontrados:",
                edital_links.count(),
            )

            first_edital = edital_links.first
            href = first_edital.get_attribute("href")

            print("Primeiro href:", href)

            url_before_click = page.url

            first_edital.click()

            page.wait_for_function(
                """
                previousUrl =>
                    window.location.href !== previousUrl
                """,
                arg=url_before_click,
                timeout=15000,
            )

            print(
                "URL após navegação:",
                page.url,
            )

            page.wait_for_timeout(3000)

            page_text = page.locator(
                "body"
            ).inner_text()

            keywords = [
                "Id contratação PNCP",
                "Modalidade",
                "Órgão",
                "Unidade",
                "Objeto",
                "Valor",
                "Situação",
                "Amparo legal",
                "Processo",
                "Publicação",
                "Proposta",
                "Itens",
                "Documentos",
            ]

            print("\nCampos encontrados:")

            for keyword in keywords:
                found = (
                    keyword.lower()
                    in page_text.lower()
                )

                print(
                    f"- {keyword}: {found}"
                )

            print("\nConteúdo inicial da página:")
            print(page_text[:3000])

        except Exception as error:
            print(
                "Erro durante o spike:",
                error,
            )

        finally:
            browser.close()


if __name__ == "__main__":
    main()