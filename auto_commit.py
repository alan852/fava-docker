#!/usr/bin/env python3
"""Automated Git commit daemon for fava-docker workspace based on configurable cron schedule."""

import datetime
import logging
import os
import signal
import subprocess
import sys
import threading
from croniter import croniter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [auto-commit] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("auto_commit")

stop_event = threading.Event()


def handle_shutdown(signum, _frame):
    logger.info(f"Received shutdown signal ({signum}). Stopping auto-commit service...")
    stop_event.set()


signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)


def is_git_repo(path: str) -> bool:
    """Checks if the given directory is inside a Git work tree."""
    res = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=path,
        capture_output=True,
        text=True,
    )
    return res.returncode == 0


def commit_workspace(workspace_dir: str, message_template: str) -> None:
    """Checks for unstaged/untracked changes in the workspace and creates a git commit if needed."""
    if not os.path.exists(workspace_dir):
        logger.warning(f"Workspace directory '{workspace_dir}' does not exist.")
        return

    if not is_git_repo(workspace_dir):
        logger.warning(
            f"Directory '{workspace_dir}' is not a Git repository. Skipping auto-commit."
        )
        return

    # Check for modifications, deletions, or untracked files
    status_res = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=workspace_dir,
        capture_output=True,
        text=True,
    )
    if status_res.returncode != 0:
        logger.error(f"git status failed: {status_res.stderr.strip()}")
        return

    changes = status_res.stdout.strip()
    if not changes:
        logger.info("No modifications detected in workspace. Nothing to commit.")
        return

    # Stage all changes
    add_res = subprocess.run(
        ["git", "add", "-A"],
        cwd=workspace_dir,
        capture_output=True,
        text=True,
    )
    if add_res.returncode != 0:
        logger.error(f"git add failed: {add_res.stderr.strip()}")
        return

    # Format commit message with current UTC timestamp
    now = datetime.datetime.now(datetime.timezone.utc)
    try:
        commit_msg = now.strftime(message_template)
    except Exception:
        commit_msg = now.strftime("Auto-commit: %Y-%m-%d %H:%M:%S UTC")

    commit_res = subprocess.run(
        ["git", "commit", "-m", commit_msg],
        cwd=workspace_dir,
        capture_output=True,
        text=True,
    )
    if commit_res.returncode == 0:
        logger.info(f"Successfully committed changes: \"{commit_msg}\"")
    else:
        logger.error(f"git commit failed: {commit_res.stderr.strip()}")


def main():
    cron_expr = os.environ.get("AUTO_COMMIT_CRON", "").strip()
    if not cron_expr or cron_expr.lower() in ("0", "false", "no", "off", "disabled"):
        logger.info("AUTO_COMMIT_CRON is not set or disabled. Exiting auto-commit service.")
        return

    workspace_dir = os.environ.get("WORKSPACE_DIR", "/workspace")
    msg_template = os.environ.get(
        "AUTO_COMMIT_MESSAGE", "Auto-commit: %Y-%m-%d %H:%M:%S UTC"
    )

    now = datetime.datetime.now(datetime.timezone.utc)
    try:
        iter_cron = croniter(cron_expr, now)
    except Exception as e:
        logger.error(f"Invalid cron expression '{cron_expr}': {e}")
        sys.exit(1)

    logger.info(
        f"Auto-commit service started for '{workspace_dir}' with cron schedule: '{cron_expr}'"
    )

    while not stop_event.is_set():
        now = datetime.datetime.now(datetime.timezone.utc)
        next_time = iter_cron.get_next(datetime.datetime)
        wait_seconds = (next_time - now).total_seconds()
        if wait_seconds < 0:
            wait_seconds = 0

        logger.info(
            f"Next scheduled commit at {next_time.strftime('%Y-%m-%d %H:%M:%S UTC')} (in {int(wait_seconds)}s)"
        )

        # Wait until next trigger time or shutdown signal
        if stop_event.wait(timeout=wait_seconds):
            break

        if not stop_event.is_set():
            logger.info("Triggering scheduled workspace commit...")
            commit_workspace(workspace_dir, msg_template)

    logger.info("Auto-commit service stopped.")


if __name__ == "__main__":
    main()
