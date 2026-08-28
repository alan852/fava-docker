# fava-docker

A lightweight, secure, and batteries-included Docker image for [Beancount](https://beancount.github.io/) and [Fava](https://beancount.github.io/fava/) plain-text accounting, pre-loaded with popular plugins, dashboards, and automated Git tracking.

[![Docker Image](https://img.shields.io/badge/ghcr.io-alan852%2Ffava--docker-blue?logo=docker)](https://github.com/alan852/fava-docker/pkgs/container/fava-docker)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![Platforms: amd64 / arm64](https://img.shields.io/badge/platforms-linux%2Famd64%20%7C%20linux%2Farm64-lightgrey)](https://github.com/alan852/fava-docker)

---

## ✨ Features

- **Multi-Architecture Support**: Built for both `linux/amd64` and `linux/arm64` (Raspberry Pi, Apple Silicon, ARM servers).
- **Python 3.12 Multi-Stage Build**: Minimal attack surface with dependencies isolated in `/opt/venv`.
- **Batteries Included**: Curated collection of essential Beancount plugins and Fava extensions pre-installed.
- **Supply Chain Security**: Direct Git dependencies pinned to immutable commit hashes.
- **Git Integration**: Built-in Git support with automatic workspace repository initialization, compatible with [`fava-git`](https://github.com/alan852/fava-git).
- **Process Management & Healthcheck**: Managed by [`dumb-init`](https://github.com/Yelp/dumb-init) for graceful shutdowns and built-in Docker `HEALTHCHECK`.
- **Permission Friendly**: Supports custom user and group IDs (`PUID` / `PGID`) to match host file ownership and prevent permission conflicts.
- **Localhost by Default**: Safe local network defaults to protect unauthenticated financial ledger data.

---

## 🔒 Security & Privacy Notice

> [!IMPORTANT]
> **Fava does not include built-in authentication or access control.**
> - By default, the provided `docker-compose.yml` binds to **`127.0.0.1:5000`** (localhost only).
> - If you plan to access Fava across your local network or the internet, **always put it behind an authenticated reverse proxy** (e.g., [Authelia](https://www.authelia.com/), [Authentik](https://goauthentik.io/), [Traefik Basic Auth](https://doc.traefik.io/traefik/middlewares/http/basicauth/), [Nginx Proxy Manager](https://nginxproxymanager.com/), [Tailscale](https://tailscale.com/), or Cloudflare Access).
> - Never expose port `5000` directly to the public internet.

---

## 📦 Included Plugins & Extensions

| Package | Type | Description |
| :--- | :--- | :--- |
| **[beancount](https://github.com/beancount/beancount)** | Core | Plain text, double-entry bookkeeping computer language. |
| **[fava](https://github.com/beancount/fava)** | Core | Web interface for Beancount. |
| **[fava-dashboards](https://github.com/andreasgerstmayr/fava-dashboards)** | Extension | Custom interactive dashboards and visualization panels. |
| **[fava-git](https://github.com/alan852/fava-git)** | Extension | Version control integration and history view in Fava. |
| **[beancount-lazy-plugins](https://github.com/Evernight/beancount-lazy-plugins)** | Plugin | Performance optimization and lazy plugin loading. |
| **[fava-uk-tax-return](https://github.com/alan852/beancount-fava-plugin-uk-tax-return)** | Extension | UK Self Assessment income tax return calculation and reporting. |
| **[fava-repayment](https://github.com/alan852/beancount-fava-plugin-repayment)** | Extension | Credit card statement settlement and repayment tracking. |

---

## 🚀 Quick Start

### 1. Using Docker Compose (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/alan852/fava-docker.git
   cd fava-docker
   ```

2. Copy the template and configure environment variables:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` to match your user ID (`id -u`) and group ID (`id -g`).

3. Place your ledger file in `example_data/main.bean` (or mount your existing ledger directory).

4. Start the container:
   ```bash
   docker compose up -d
   ```

5. Open your browser and navigate to:
   ```
   http://127.0.0.1:5000
   ```

### 2. Using Docker CLI

```bash
docker run -d \
  --name fava \
  --user $(id -u):$(id -g) \
  -p 127.0.0.1:5000:5000 \
  -e TZ=Europe/London \
  -e BEANCOUNT_FILE=main.bean \
  -v /path/to/your/ledger:/workspace \
  ghcr.io/alan852/fava-docker:latest
```

---

## ⚙️ Configuration & Environment Variables

| Variable | Default | Description |
| :--- | :--- | :--- |
| `BEANCOUNT_FILE` | `main.bean` | Name of the primary Beancount file inside `/workspace`. |
| `FAVA_HOST` | `0.0.0.0` | Container-internal bind address (keep `0.0.0.0` inside container). |
| `PUID` | `1000` | Host user ID for file permission alignment. |
| `PGID` | `1000` | Host group ID for file permission alignment. |
| `TZ` | `Europe/London` | Container timezone. |
| `GIT_AUTHOR_NAME` | `fava` | Fallback author name for Git commits via `fava-git` or auto-commit. |
| `GIT_AUTHOR_EMAIL` | `fava@homelab` | Fallback author email for Git commits via `fava-git` or auto-commit. |
| `AUTO_COMMIT_CRON` | *(disabled)* | Standard 5-field cron expression (e.g. `*/15 * * * *` or `0 * * * *`) for automatic workspace Git commits. |
| `AUTO_COMMIT_MESSAGE` | `Auto-commit: %Y-%m-%d %H:%M:%S UTC` | Commit message template with `strftime` formatting tokens. |

---

## 📁 Sample Ledger Configuration

To enable installed plugins in your Beancount ledger (`main.bean`), include options and plugin declarations like:

```beancount
option "title" "Personal Ledger"
option "operating_currency" "USD"
option "operating_currency" "EUR"

;; Fava Extensions
2020-01-01 custom "fava-extension" "fava_dashboards"
2020-01-01 custom "fava-extension" "fava_git"
2020-01-01 custom "fava-extension" "fava_uk_tax_return"
2020-01-01 custom "fava-extension" "fava_repayment"

;; Accounts & Opening Balances
1970-01-01 open Assets:Checking:USD USD
1970-01-01 open Income:Salary:Tech USD
1970-01-01 open Expenses:Groceries USD

2024-01-15 * "Supermarket" "Groceries"
  Expenses:Groceries        54.20 USD
  Assets:Checking:USD      -54.20 USD
```

---

## 🛠️ Building Locally

```bash
# Build local multi-stage Docker image
docker build -t fava-docker:local .

# Run the locally built image
docker run -d \
  --name fava \
  -p 127.0.0.1:5000:5000 \
  -v $(pwd)/example_data:/workspace \
  fava-docker:local
```

---

## 🔄 CI/CD & Automation

- **Multi-Platform Container Builds**: Automated multi-architecture builds (`linux/amd64` and `linux/arm64`) using Docker Buildx and QEMU, published to GitHub Container Registry (`ghcr.io/alan852/fava-docker`).
- **Automated Upstream Dependency Updates**: A scheduled GitHub Actions workflow (`auto-update-dependencies`) runs weekly to check upstream Beancount and Fava plugin repositories for new commits, update `requirements.txt`, tag new patch versions, and rebuild the published containers.
- **Manual / Tagged Releases**: Pushing a semantic version tag (e.g. `git tag v1.1.0 && git push origin v1.1.0`) triggers an immediate build and release.

---

## 📄 License

This project is licensed under the **GNU General Public License v3.0** (GPLv3). See the [LICENSE](LICENSE) file for details.