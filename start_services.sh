#!/bin/bash
set -euo pipefail

# Initialize git repository if not present
if [ ! -d "/workspace/.git" ]; then
    echo "Initializing new Git repository in /workspace..."
    git init /workspace
fi

# Set default git identity only if not already configured
if [ -z "$(git config --get user.name 2>/dev/null || true)" ]; then
    git config --local user.name "${GIT_AUTHOR_NAME:-fava}"
fi

if [ -z "$(git config --get user.email 2>/dev/null || true)" ]; then
    git config --local user.email "${GIT_AUTHOR_EMAIL:-fava@homelab}"
fi

BEANCOUNT_FILE="${BEANCOUNT_FILE:-main.bean}"

# Normalize to absolute path required by Fava when BEANCOUNT_FILE environment variable is present
if [[ "${BEANCOUNT_FILE}" != /* ]]; then
    BEANCOUNT_FILE="/workspace/${BEANCOUNT_FILE}"
fi
export BEANCOUNT_FILE

# If the specified beancount file doesn't exist, create a basic template so Fava can start
if [ ! -f "${BEANCOUNT_FILE}" ]; then
    echo "Warning: ${BEANCOUNT_FILE} not found. Creating minimal starter ledger..."
    cat << 'EOF' > "${BEANCOUNT_FILE}"
option "title" "Personal Ledger"
option "operating_currency" "USD"

1970-01-01 open Assets:Checking USD
1970-01-01 open Income:Salary USD
1970-01-01 open Expenses:General USD
EOF
fi

# Start scheduled auto-commit service if configured
if [ -n "${AUTO_COMMIT_CRON:-}" ]; then
    echo "Starting auto-commit daemon with cron schedule: '${AUTO_COMMIT_CRON}'..."
    python3 /scripts/auto_commit.py &
fi

echo "Starting Fava with ledger: ${BEANCOUNT_FILE}..."
exec fava "${BEANCOUNT_FILE}" "$@"