import os
from datetime import datetime, timezone

from playwright.sync_api import sync_playwright

from src.crawlers.pncp_catalog import PncpCatalogCrawler
from src.database.connection import DATABASE_PATH, initialize_database
from src.logging_config import LOG_FILE, configure_logging
from src.normalizers.procurement import normalize_procurement
from src.repositories.procurement_repository import (
    ProcurementRepository,
    SaveStatus,
)


MAX_RECORDS = int(os.getenv("PNCP_MAX_RECORDS", "100"))
MAX_PAGES = int(os.getenv("PNCP_MAX_PAGES", "25"))
REQUEST_INTERVAL_SECONDS = float(
    os.getenv("PNCP_REQUEST_INTERVAL", "1.0")
)
HEADLESS = os.getenv(
    "PNCP_HEADLESS",
    "false",
).strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}

logger = configure_logging()


def main() -> None:
    """
    Executa o fluxo principal de coleta do PNCP.

    A execução percorre o catálogo público, normaliza os registros
    encontrados e persiste os dados no SQLite. Ao final, registra
    um resumo com estatísticas da coleta e do processamento.
    """

    execution_started_at = datetime.now(timezone.utc)

    logger.info("INÍCIO DA EXECUÇÃO PNCP")
    logger.info("Limite de registros: %s", MAX_RECORDS)
    logger.info("Limite de páginas: %s", MAX_PAGES)
    logger.info(
        "Intervalo entre páginas: %.1fs",
        REQUEST_INTERVAL_SECONDS,
    )
    logger.info("Browser headless: %s", HEADLESS)

    # Garante que o banco esteja disponível antes da coleta.
    initialize_database()
    repository = ProcurementRepository()

    logger.info("Banco SQLite: %s", DATABASE_PATH)

    collected = 0
    normalized = 0
    inserted = 0
    updated = 0
    duplicates = 0
    normalization_errors = 0
    persistence_errors = 0

    # O PNCP é uma aplicação renderizada via JavaScript,
    # por isso a coleta utiliza um navegador com Playwright.
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=HEADLESS
        )

        try:
            page = browser.new_page()

            crawler = PncpCatalogCrawler(
                page=page,
                request_interval_seconds=REQUEST_INTERVAL_SECONDS,
                max_retries=3,
                backoff_base_seconds=1.0,
            )

            raw_records = crawler.discover(
                max_records=MAX_RECORDS,
                max_pages=MAX_PAGES,
            )

            collected = len(raw_records)

            logger.info(
                "Iniciando processamento de %s registros.",
                collected,
            )

            # Cada registro é tratado individualmente para que uma
            # falha de normalização ou persistência não interrompa toda a execução.
            for raw in raw_records:
                try:
                    procurement = normalize_procurement(raw)
                    normalized += 1

                except Exception as error:
                    normalization_errors += 1

                    logger.error(
                        "Erro de normalização em %s: %s",
                        raw.pncp_id,
                        error,
                    )
                    continue

                try:
                    status = repository.save(procurement)

                    if status == SaveStatus.INSERTED:
                        inserted += 1

                    elif status == SaveStatus.UPDATED:
                        updated += 1

                    elif status == SaveStatus.DUPLICATE:
                        duplicates += 1

                except Exception as error:
                    persistence_errors += 1

                    logger.error(
                        "Erro de persistência em %s: %s",
                        procurement.pncp_id,
                        error,
                    )

        finally:
            browser.close()

    database_total = repository.count()

    execution_finished_at = datetime.now(timezone.utc)
    duration = execution_finished_at - execution_started_at

    # Consolida as métricas da execução para facilitar
    # acompanhamento e diagnóstico pelo arquivo de log.
    logger.info("RESUMO DA EXECUÇÃO")
    logger.info(
        "Páginas tentadas: %s",
        crawler.stats.pages_attempted,
    )
    logger.info(
        "Páginas concluídas: %s",
        crawler.stats.pages_succeeded,
    )
    logger.info(
        "Páginas com erro: %s",
        crawler.stats.pages_failed,
    )
    logger.info(
        "Retries executados: %s",
        crawler.stats.retries,
    )
    logger.info(
        "Duplicados durante descoberta: %s",
        crawler.stats.duplicate_records,
    )
    logger.info(
        "Erros de parser: %s",
        crawler.stats.parser_errors,
    )
    logger.info("Registros coletados: %s", collected)
    logger.info("Registros normalizados: %s", normalized)
    logger.info("Novos inseridos: %s", inserted)
    logger.info("Atualizados: %s", updated)
    logger.info(
        "Duplicados/inalterados: %s",
        duplicates,
    )
    logger.info(
        "Erros de normalização: %s",
        normalization_errors,
    )
    logger.info(
        "Erros de persistência: %s",
        persistence_errors,
    )
    logger.info("Total no banco: %s", database_total)
    logger.info(
        "Duração: %.2f segundos",
        duration.total_seconds(),
    )
    logger.info("Arquivo de log: %s", LOG_FILE)
    logger.info("FIM DA EXECUÇÃO PNCP")


if __name__ == "__main__":
    main()