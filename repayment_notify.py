#!/usr/bin/env python3
"""Automated due date notification daemon for fava-docker using fava-repayment and cron schedule."""

import datetime
import logging
import os
import shutil
import signal
import subprocess
import sys
import threading
from croniter import croniter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [repayment-notify] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("repayment_notify")

stop_event = threading.Event()


def handle_shutdown(signum, _frame):
    logger.info(f"Received shutdown signal ({signum}). Stopping repayment notification service...")
    stop_event.set()


signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)


def resolve_beancount_file() -> str:
    """Resolve and validate the path to the primary Beancount ledger file."""
    bf = os.environ.get("BEANCOUNT_FILE", "main.bean").strip()
    if not os.path.isabs(bf):
        bf = os.path.join(os.environ.get("WORKSPACE_DIR", "/workspace"), bf)
    return bf


def run_repayment_notify() -> None:
    """Invoke 'fava-repayment notify' via subprocess with configured environment variables."""
    beancount_file = resolve_beancount_file()
    if not os.path.isfile(beancount_file):
        logger.warning(f"Beancount ledger file '{beancount_file}' not found. Skipping notification check.")
        return

    cli_bin = shutil.which("fava-repayment") or "fava-repayment"
    cmd = [cli_bin, "notify", beancount_file]

    apprise_url = os.environ.get("APPRISE_API_URL", "").strip()
    if apprise_url:
        cmd.extend(["--apprise-url", apprise_url] )

    urls = os.environ.get("APPRISE_URLS", "").strip()
    if urls:
        cmd.extend(["--urls", urls])

    key = os.environ.get("APPRISE_KEY", "").strip()
    if key:
        cmd.extend(["--key", key])

    tags = os.environ.get("APPRISE_TAGS", "").strip()
    if tags:
        cmd.extend(["--tags", tags])

    days = os.environ.get("REPAYMENT_NOTIFY_DAYS", "").strip()
    if days:
        cmd.extend(["--days", days])

    state_file = os.environ.get(
        "REPAYMENT_NOTIFY_STATE_FILE",
        os.path.join(os.environ.get("WORKSPACE_DIR", "/workspace"), ".fava_repayment_state.json"),
    ).strip()
    if state_file:
        cmd.extend(["--state-file", state_file])

    include_overdue = os.environ.get("REPAYMENT_NOTIFY_INCLUDE_OVERDUE", "true").strip().lower()
    if include_overdue in ("0", "false", "no", "off"):
        cmd.append("--no-overdue")

    dry_run = os.environ.get("REPAYMENT_NOTIFY_DRY_RUN", "false").strip().lower()
    if dry_run in ("1", "true", "yes", "on"):
        cmd.append("--dry-run")

    logger.info("Executing repayment due date notification check...")
    try:
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
        if res.stdout.strip():
            for line in res.stdout.strip().splitlines():
                logger.info(f"[cli] {line}")
        if res.stderr.strip():
            for line in res.stderr.strip().splitlines():
                logger.error(f"[cli] {line}")

        if res.returncode == 0:
            logger.info("Repayment notification check completed successfully.")
        else:
            logger.warning(f"Repayment notification check exited with status code {res.returncode}.")
    except Exception as e:
        logger.error(f"Failed to execute '{' '.join(cmd)}': {e}")


def main():
    cron_expr = os.environ.get("REPAYMENT_NOTIFY_CRON", "").strip()
    if not cron_expr or cron_expr.lower() in ("0", "false", "no", "off", "disabled"):
        logger.info("REPAYMENT_NOTIFY_CRON is not set or disabled. Exiting repayment notification service.")
        return

    now = datetime.datetime.now(datetime.timezone.utc)
    try:
        iter_cron = croniter(cron_expr, now)
    except Exception as e:
        logger.error(f"Invalid cron expression '{cron_expr}': {e}")
        sys.exit(1)

    beancount_file = resolve_beancount_file()
    logger.info(
        f"Repayment notification service started for '{beancount_file}' with cron schedule: '{cron_expr}'"
    )

    while not stop_event.is_set():
        now = datetime.datetime.now(datetime.timezone.utc)
        next_time = iter_cron.get_next(datetime.datetime)
        wait_seconds = (next_time - now).total_seconds()
        if wait_seconds < 0:
            wait_seconds = 0

        logger.info(
            f"Next scheduled notification check at {next_time.strftime('%Y-%m-%d %H:%M:%S UTC')} (in {int(wait_seconds)}s)"
        )

        # Wait until next trigger time or shutdown signal
        if stop_event.wait(timeout=wait_seconds):
            break

        if not stop_event.is_set():
            logger.info("Triggering scheduled repayment notification check...")
            run_repayment_notify()

    logger.info("Repayment notification service stopped.")


if __name__ == "__main__":
    main()
