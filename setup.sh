#!/usr/bin/env bash
# ResumeForge one-time setup (macOS / Linux). Safe to re-run.
set -euo pipefail
cd "$(dirname "$0")"

ok()   { printf '  \033[32m✓\033[0m %s\n' "$1"; }
warn() { printf '  \033[33m!\033[0m %s\n' "$1"; }

echo "ResumeForge setup"

if ! command -v uv >/dev/null 2>&1; then
  for candidate in "$HOME/.local/bin/uv" "$HOME/.cargo/bin/uv"; do
    [ -x "$candidate" ] && export PATH="$(dirname "$candidate"):$PATH"
  done
fi
if ! command -v uv >/dev/null 2>&1; then
  warn "uv (the Python tool runner) is not installed."
  echo "    Install it with:  curl -LsSf https://astral.sh/uv/install.sh | sh"
  echo "    (or: brew install uv), then open a new terminal and run ./setup.sh again."
  exit 1
fi
ok "uv $(uv --version | awk '{print $2}')"

uv sync --quiet
ok "Python environment ready (uv installs Python 3.12+ automatically if needed)"

uv run --quiet resumeforge db init >/dev/null
ok "Game database ready at data/resumes.db"

if uv run --quiet python -c "from tools.render_pdf import _find_chrome_binary as f; f()" >/dev/null 2>&1; then
  ok "Browser found for PDF rendering"
else
  warn "No Chrome/Chromium/Edge found. PDFs will be saved as HTML you can print to PDF."
  echo "    Install Google Chrome, or set RESUMEFORGE_CHROME=/path/to/browser."
fi

mkdir -p my_resumes
ok "Your own resumes go in my_resumes/ (private, never committed)"

echo
echo "Done. Open this folder in Claude Code and type:  /make-my-resume"
