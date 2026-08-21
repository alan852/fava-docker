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
- **Git Integration**: Built-in Git support with automatic workspace repository initialization, compatible with [`fava-git`](https://github.com/Evernight/fava-git).
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
| **[fava-investor](https://github.com/redstreet/fava_investor)** | Extension | Investment analytics, asset allocation, and capital gains tracking. |
| **[fava-portfolio-returns](https://github.com/andreasgerstmayr/fava-portfolio-returns)** | Extension | Calculate and display portfolio returns (IRR, time-weighted returns). |
| **[fava-currency-tracker](https://github.com/Evernight/fava-currency-tracker)** | Extension | Multi-currency portfolio tracker and valuations. |
| **[fava-git](https://github.com/Evernight/fava-git)** | Extension | Version control integration and history view in Fava. |
| **[beantab](https://github.com/Evernight/beantab)** | Extension | Tabular editor and transaction helpers. |
| **[beancount_interpolate](https://github.com/redstreet/beancount_interpolate)** | Plugin | Interpolation and automated leg calculations. |
| **[beancount-reds-plugins](https://github.com/redstreet/beancount_reds_plugins)** | Plugin | Collection of plugins for asset tracking and zero-sum operations. |
| **[beancount_share](https://github.com/redstreet/beancount_share)** | Plugin | Split expenses and shared-cost accounting. |
| **[beancount-lazy-plugins](https://github.com/Evernight/beancount-lazy-plugins)** | Plugin | Performance optimization and lazy plugin loading. |

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
| `GIT_AUTHOR_NAME` | `fava` | Fallback author name for Git commits via `fava-git`. |
| `GIT_AUTHOR_EMAIL` | `fava@homelab` | Fallback author email for Git commits via `fava-git`. |

---

## 📁 Sample Ledger Configuration

To enable installed plugins in your Beancount ledger (`main.bean`), include options and plugin declarations like:

```beancount
option "title" "Personal Ledger"
option "operating_currency" "USD"
option "operating_currency" "EUR"

;; Fava Extensions
2020-01-01 custom "fava-extension" "fava_dashboards"
2020-01-01 custom "fava-extension" "fava_investor"
2020-01-01 custom "fava-extension" "fava_portfolio_returns"
2020-01-01 custom "fava-extension" "fava_git"
2020-01-01 custom "fava-extension" "fava_currency_tracker"
2020-01-01 custom "fava-extension" "beantab"

;; Beancount Plugins
plugin "beancount_interpolate"
plugin "beancount_share"

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

## 🔄 CI/CD & Releases

Automated multi-platform builds (`amd64` and `arm64`) are managed via GitHub Actions:
- Pull requests and branch pushes run validation builds.
- Pushing a semantic version tag (e.g. `git tag v1.0.0 && git push origin v1.0.0`) automatically builds and publishes the release image to GitHub Container Registry (`ghcr.io/alan852/fava-docker`).

---

## 📄 License

This project is licensed under the **GNU General Public License v3.0** (GPLv3). See the [LICENSE](LICENSE) file for details.