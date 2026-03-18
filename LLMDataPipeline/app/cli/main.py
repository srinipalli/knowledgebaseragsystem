from __future__ import annotations

import time

import typer

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.graph.workflow import IngestionWorkflow
from app.services.discovery import discover_files

app = typer.Typer(help="Folder-based document ingestion pipeline.")
logger = get_logger(__name__)


@app.command()
def scan_once() -> None:
    """Process the current contents of the input folder once."""
    configure_logging()
    settings = get_settings()
    workflow = IngestionWorkflow(settings)
    for file_path in discover_files(settings):
        result = workflow.run(file_path)
        logger.info("file_processed", file_path=str(file_path), result=result.get("result"))


@app.command()
def watch_folder() -> None:
    """Continuously poll the input folder and process new files."""
    configure_logging()
    settings = get_settings()
    workflow = IngestionWorkflow(settings)
    while True:
        files = discover_files(settings)
        if not files:
            logger.info("watch_idle", input_dir=str(settings.input_dir))
        for file_path in files:
            result = workflow.run(file_path)
            logger.info("file_processed", file_path=str(file_path), result=result.get("result"))
        time.sleep(settings.poll_interval_seconds)


if __name__ == "__main__":
    app()
