FROM mcr.microsoft.com/devcontainers/javascript-node:22-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

# Base tooling, nginx gateway, system Chromium (for the QA browser runner),
# and build deps that Rust crates commonly need.
RUN apt-get update && apt-get install -y --no-install-recommends \
      git jq curl ca-certificates ripgrep unzip \
      nginx chromium fonts-liberation \
      build-essential pkg-config libssl-dev \
      python3 python3-pip python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Tilt: check github.com/tilt-dev/tilt/releases for the current version
ARG TILT_VERSION=0.35.0
RUN case "$(dpkg --print-architecture)" in \
      amd64) T=x86_64 ;; \
      arm64) T=arm64 ;; \
      *) echo "unsupported arch" && exit 1 ;; \
    esac \
    && curl -fsSL "https://github.com/tilt-dev/tilt/releases/download/v${TILT_VERSION}/tilt.${TILT_VERSION}.linux.${T}.tar.gz" \
       | tar -xz -C /usr/local/bin tilt

# Playwright is the library browser-review.mjs drives; it uses the system Chromium.
RUN npm install -g @anthropic-ai/claude-code playwright yarn

RUN mkdir -p /home/node/.claude /home/node/.vscode-server \
    && chown -R node:node /home/node/.claude /home/node/.vscode-server

USER node
