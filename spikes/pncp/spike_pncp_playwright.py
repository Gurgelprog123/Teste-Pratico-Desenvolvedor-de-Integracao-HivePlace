from playwright.sync_api import sync_playwright


URL = "https://pncp.gov.br/app/editais?pagina=1"
PROCUREMENT_SELECTOR = 'a[href^="/editais/"]'


def main() -> None:
    """
    Verifica se o catálogo do PNCP pode ser acessado e renderizado
    corretamente com Playwright.
    """

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=False
        )

        try:
            page = browser.new_page()

            response = page.goto(
                URL,
                wait_until="domcontentloaded",
                timeout=30000,
            )

            print(
                "Status HTTP:",
                response.status if response else "sem resposta",
            )
            print("Título:", page.title())
            print("URL final:", page.url)

            procurement_links = page.locator(
                PROCUREMENT_SELECTOR
            )

            procurement_links.first.wait_for(
                state="visible",
                timeout=15000,
            )

            print(
                "Links de contratações encontrados:",
                procurement_links.count(),
            )

            first_link = procurement_links.first

            print(
                "Primeiro href:",
                first_link.get_attribute("href"),
            )
            print(
                "Primeiro registro:",
                first_link.inner_text().strip()[:1000],
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