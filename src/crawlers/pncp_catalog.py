import time
from dataclasses import dataclass

from playwright.sync_api import (
    Page,
    TimeoutError as PlaywrightTimeoutError,
)

from src.logging_config import configure_logging
from src.models.procurement import RawProcurement
from src.scrapers.pncp import parse_procurement_card


CATALOG_URL = "https://pncp.gov.br/app/editais"
PROCUREMENT_SELECTOR = 'a[href^="/editais/"]'

logger = configure_logging()


class TransientPageError(Exception):
    """Erro temporário que permite uma nova tentativa."""


class PermanentPageError(Exception):
    """Erro que não deve ser resolvido apenas com retry."""


@dataclass
class CrawlerStats:
    pages_attempted: int = 0
    pages_succeeded: int = 0
    pages_failed: int = 0
    retries: int = 0
    duplicate_records: int = 0
    parser_errors: int = 0


class PncpCatalogCrawler:
    def __init__(
        self,
        page: Page,
        request_interval_seconds: float = 1.0,
        max_retries: int = 3,
        backoff_base_seconds: float = 1.0,
    ):
        self.page = page
        self.request_interval_seconds = request_interval_seconds
        self.max_retries = max_retries
        self.backoff_base_seconds = backoff_base_seconds
        self.stats = CrawlerStats()

    def _collect_page_once(
        self,
        page_number: int,
    ) -> list[RawProcurement]:
        """Executa uma tentativa de coleta de uma página."""

        url = f"{CATALOG_URL}?pagina={page_number}"

        response = self.page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=30000,
        )

        if response is None:
            raise TransientPageError(
                "PNCP não retornou resposta HTTP."
            )

        status = response.status

        if status == 429 or status >= 500:
            raise TransientPageError(
                f"PNCP retornou HTTP {status}"
            )

        if status >= 400:
            raise PermanentPageError(
                f"PNCP retornou HTTP {status}"
            )

        links = self.page.locator(PROCUREMENT_SELECTOR)

        links.first.wait_for(
            state="visible",
            timeout=15000,
        )

        # O PNCP pode renderizar mais de um <a> para a mesma
        # contratação. Mantemos o texto mais completo de cada URL.
        links_by_href: dict[str, str] = {}

        for index in range(links.count()):
            try:
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

            except Exception as error:
                logger.warning(
                    "Falha ao ler elemento DOM %s da página %s: %s",
                    index,
                    page_number,
                    error,
                )

        logger.info(
            "Página %s: %s links únicos",
            page_number,
            len(links_by_href),
        )

        records_by_pncp_id: dict[str, RawProcurement] = {}

        for href, text in links_by_href.items():
            try:
                raw = parse_procurement_card(
                    text=text,
                    href=href,
                )

                if raw.pncp_id is None:
                    self.stats.parser_errors += 1

                    logger.warning(
                        "Registro sem ID PNCP ignorado: %s",
                        href,
                    )
                    continue

                if raw.pncp_id in records_by_pncp_id:
                    continue

                records_by_pncp_id[raw.pncp_id] = raw

            except Exception as error:
                self.stats.parser_errors += 1

                logger.error(
                    "Erro ao interpretar registro %s: %s",
                    href,
                    error,
                )

                # Um registro inválido não interrompe a página.
                continue

        return list(records_by_pncp_id.values())

    def collect_page(
        self,
        page_number: int,
    ) -> list[RawProcurement]:
        """Coleta uma página com retry para falhas temporárias."""

        logger.info(
            "Acessando página %s",
            page_number,
        )

        for attempt in range(1, self.max_retries + 1):
            try:
                records = self._collect_page_once(
                    page_number
                )

                logger.info(
                    "Página %s processada: %s registros",
                    page_number,
                    len(records),
                )

                return records

            except (
                PlaywrightTimeoutError,
                TransientPageError,
            ) as error:
                if attempt >= self.max_retries:
                    raise TransientPageError(
                        f"Falha após {self.max_retries} tentativas. "
                        f"Último erro: {error}"
                    ) from error

                delay = (
                    self.backoff_base_seconds
                    * (2 ** (attempt - 1))
                )

                self.stats.retries += 1

                logger.warning(
                    "Falha temporária na página %s. "
                    "Tentativa %s/%s. "
                    "Nova tentativa em %.1fs. Erro: %s",
                    page_number,
                    attempt,
                    self.max_retries,
                    delay,
                    error,
                )

                time.sleep(delay)

            except PermanentPageError:
                raise

        return []

    def discover(
        self,
        max_records: int = 100,
        max_pages: int = 25,
    ) -> list[RawProcurement]:
        """
        Percorre o catálogo até atingir o limite de registros
        ou de páginas definido para a execução.
        """

        all_records: dict[str, RawProcurement] = {}

        for page_number in range(1, max_pages + 1):
            self.stats.pages_attempted += 1

            try:
                records = self.collect_page(
                    page_number
                )

                self.stats.pages_succeeded += 1

            except Exception as error:
                self.stats.pages_failed += 1

                logger.error(
                    "Página %s ignorada após falha: %s",
                    page_number,
                    error,
                )

                if page_number < max_pages:
                    time.sleep(
                        self.request_interval_seconds
                    )

                continue

            for record in records:
                pncp_id = record.pncp_id

                if pncp_id is None:
                    continue

                if pncp_id in all_records:
                    self.stats.duplicate_records += 1
                    continue

                all_records[pncp_id] = record

                if len(all_records) >= max_records:
                    logger.info(
                        "Limite de %s registros atingido.",
                        max_records,
                    )

                    return list(
                        all_records.values()
                    )

            logger.info(
                "Total acumulado: %s",
                len(all_records),
            )

            if page_number < max_pages:
                time.sleep(
                    self.request_interval_seconds
                )

        return list(all_records.values())