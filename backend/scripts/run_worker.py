"""Run QUANT background jobs outside the API process."""
from __future__ import annotations

import logging
import time

from core.config import get_settings
from db.supabase_client import get_supabase_client
from services.jobs import JobRunner


def main() -> None:
    settings = get_settings()
    db = get_supabase_client()
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("quant.worker")
    while True:
        runs = JobRunner(db).run_once()
        if runs:
            logger.info("processed_jobs count=%s statuses=%s", len(runs), [row["status"] for row in runs])
        time.sleep(settings.worker_poll_seconds)


if __name__ == "__main__":
    main()
