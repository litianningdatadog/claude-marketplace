#!/usr/bin/env bash
# install.sh — bootstrap the claude-skills CLI
# Usage: curl -fsSL https://litianningdatadog.github.io/claude-skills/install.sh | bash

set -euo pipefail

INSTALL_DIR="${HOME}/.local/bin"
SCRIPT_NAME="claude-skills"
PAGES_BASE="https://litianningdatadog.github.io/claude-skills"
REGISTRY_URL="${PAGES_BASE}/registry.json"

echo "Installing claude-skills..."

# 1. Create install directory
mkdir -p "$INSTALL_DIR"

# 2. Download the claude-skills script
curl -fsSL "${PAGES_BASE}/claude-skills" -o "${INSTALL_DIR}/${SCRIPT_NAME}"
chmod +x "${INSTALL_DIR}/${SCRIPT_NAME}"

# 3. Check PATH
if ! echo ":${PATH}:" | grep -q ":${INSTALL_DIR}:"; then
    echo ""
    echo "NOTE: ${INSTALL_DIR} is not on your PATH."
    echo "Add this line to your shell config (~/.zshrc or ~/.bashrc):"
    echo ""
    echo "  export PATH=\"\${HOME}/.local/bin:\${PATH}\""
    echo ""
    echo "Then restart your terminal or run: source ~/.zshrc"
    echo ""
fi

# 4. Register the official source
"${INSTALL_DIR}/${SCRIPT_NAME}" add "$REGISTRY_URL"

# 5. Done
echo ""
echo "claude-skills installed successfully!"
echo ""
echo "  claude-skills list              # browse available skills"
echo "  claude-skills install <name>    # install a skill"
