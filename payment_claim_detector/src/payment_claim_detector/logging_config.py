"""Logging configuration."""

import logging
import sys
from pathlib import Path

from payment_claim_detector.settings import get_settings


def setup_logging() -> None:
    """Configure logging for the application."""
    settings = get_settings()

    logging.basicConfig(
        level=getattr(logging, settings.logging.level.upper()),
        format=settings.logging.format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(Path("payment_claim_detector.log")),
        ],
    )

    # Reduce noise from libraries
    logging.getLogger("pandas").setLevel(logging.WARNING)
    logging.getLogger("openpyxl").setLevel(logging.WARNING)