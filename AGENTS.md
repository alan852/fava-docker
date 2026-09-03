# AGENTS.md

Developer and AI agent guidelines for maintaining and extending the `fava-docker` repository.

---

## 1. Project Overview

`fava-docker` provides an opinionated, lightweight, and secure Docker container packaging:
- **[Beancount](https://github.com/beancount/beancount)** (plain-text double-entry accounting engine)
- **[Fava](https://github.com/beancount/fava)** (web interface for Beancount)
- Curated Beancount plugins and Fava extensions (investor analytics, dashboards, git tracking, multi-currency valuations, etc.)
- **[`dumb-init`](https://github.com/Yelp/dumb-init)** process supervisor for PID 1 signal forwarding and graceful container termination.

Container images are published to GitHub Container Registry at `ghcr.io/alan852/fava-docker`.

---

## 2. Repository Structure

```
fava-docker/
├── .env.example              # Environment variables template (TZ, PUID, PGID, etc.)
├── .github/
│   └── workflows/
│       ├── auto-update.yml   # Scheduled/manual automated dependency update & rebuild
│       └── docker.yml        # CI/CD workflow for GHCR multi-arch builds (amd64/arm64)
├── .gitignore                # Git ignore rules protecting secrets and ledger data
├── Dockerfile                # Multi-stage Dockerfile based on python:3.12-slim
├── LICENSE                   # GNU General Public License v3.0
├── README.md                 # User-facing documentation & quickstart guide
├── AGENTS.md                 # Developer & agent maintenance guide
├── auto_commit.py            # Cron-based automated workspace Git commit daemon
├── docker-compose.yml        # Compose definition for local deployment and testing
├── example_data/             # Mount directory for sample/user Beancount ledger files
├── repayment_notify.py       # Cron-based credit card due date notification daemon (Apprise-API)
├── requirements.txt          # Python dependencies with pinned Git commit hashes
└── start_services.sh         # Container entrypoint script
```

---

## 3. Architecture & Key Components

### 3.1 Dockerfile
- **Multi-Stage Build**:
  - `builder` stage: Installs build tools and installs all Python packages into `/opt/venv`.
  - `runtime` stage: Minimal `python:3.12-slim` image containing only runtime dependencies (`git`, `dumb-init`), copied `/opt/venv`, and startup scripts (`start_services.sh`, `auto_commit.py`, `repayment_notify.py`).
- **Git Compatibility**: Configures system-wide safe directory `git config --system --add safe.directory '*'` to permit Git tracking regardless of host `PUID`/`PGID`.
- **Healthcheck**: Python standard library healthcheck polling `http://127.0.0.1:5000`.
- **Entrypoint**: `/usr/bin/dumb-init -- /scripts/start_services.sh`.

### 3.2 Startup Script (`start_services.sh`)
- Enforces `set -euo pipefail`.
- Initializes a Git repository in `/workspace` only if `.git` is not already present.
- Sets fallback Git identities (`GIT_AUTHOR_NAME`, `GIT_AUTHOR_EMAIL`) only if not previously configured, avoiding overwriting existing user repo configs.
- Supports configurable ledger filenames via `BEANCOUNT_FILE` (default: `main.bean`).
- Automatically generates a minimal starter ledger if the target file does not exist, preventing startup crashes.
- Starts optional background daemons if configured:
  - `auto_commit.py` when `AUTO_COMMIT_CRON` is set.
  - `repayment_notify.py` when `REPAYMENT_NOTIFY_CRON` is set.
- Executes Fava via `exec fava "${BEANCOUNT_FILE}" "$@"` so `dumb-init` supervises Fava directly.

### 3.3 Scheduled Daemons
- **`auto_commit.py`**: Monitors workspace changes and creates automated Git commits on a cron schedule (`AUTO_COMMIT_CRON`).
- **`repayment_notify.py`**: Evaluates credit card statement due dates and sends alerts via Apprise-API (`fava-repayment notify`) on a cron schedule (`REPAYMENT_NOTIFY_CRON`).

### 3.4 Dependencies (`requirements.txt`)
- PyPI packages and Git repositories.
- All Git repositories are pinned to specific, immutable commit SHAs to ensure supply chain integrity and reproducible builds.

### 3.4 CI/CD Workflows
- **`docker.yml`**: Supports multi-architecture builds (`linux/amd64` and `linux/arm64`) using QEMU and Docker Buildx. Publishes tagged releases to `ghcr.io/alan852/fava-docker` exclusively on semver tags (`v*.*.*`).
- **`auto-update.yml`**: Runs on a weekly cron schedule (or manual trigger). Checks upstream Git repositories for newer commits, updates `requirements.txt`, creates and tags a patch release, and publishes the rebuilt multi-arch images.

---

## 4. Security & Sensitive Information Guidelines

- **Financial Data Privacy**: Accounting ledgers contain sensitive personal financial data. Always default port bindings in compose/example files to `127.0.0.1:5000:5000` (localhost) rather than `0.0.0.0:5000`.
- **Reverse Proxy Authentication**: Fava has no built-in auth; always advise users to place external deployments behind an authenticated reverse proxy.
- **Git Ignore Safeguards**: Never commit `.env`, `*.bean`, `*.beancount`, `*.ledger`, `*.csv`, `*.ofx`, `*.qif`, or `*.pdf` files. Maintain `.env.example` as the clean configuration template.
- **Dependency Integrity**: When adding Git-based dependencies in `requirements.txt`, always pin to a full-length commit hash (`@commit_sha`).

---

## 5. Development & Maintenance Workflows

### 5.1 Local Build & Test
```bash
# Build image locally
docker build -t fava-docker:local .

# Run with docker compose
cp .env.example .env
docker compose up
```
Navigate to `http://127.0.0.1:5000` to verify that Fava and all extensions load cleanly.

### 5.2 Adding or Updating Dependencies
1. Modify `requirements.txt`. For Git dependencies, query the latest commit hash:
   ```bash
   git ls-remote https://github.com/<owner>/<repo> HEAD
   ```
2. Rebuild the container and verify startup without import errors.
3. Update table in `README.md` if new extensions/plugins are added.

### 5.3 Releasing New Versions
1. Commit all changes to `main`.
2. Tag and push a semver tag:
   ```bash
   git tag v1.1.1
   git push origin v1.1.1
   ```
3. Monitor build and multi-arch publishing in GitHub Actions.
