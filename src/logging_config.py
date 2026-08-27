import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOG_FILE = PROJECT_ROOT / "logs" / "pncp_collector.log"


def configure_logging() -> logging.Logger:
    """Configura logs no terminal e em arquivo com rotação."""

    LOG_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    logger = logging.getLogger("pncp_collector")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    # Evita adicionar os mesmos handlers em chamadas posteriores.
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger