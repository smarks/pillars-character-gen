#!/bin/bash
# Install git hooks from scripts/hooks/ to .git/hooks/
# This makes the hooks available for git to use

set -e

# Get the repository root directory
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

HOOKS_SOURCE="$REPO_ROOT/scripts/hooks"
HOOKS_TARGET="$REPO_ROOT/.git/hooks"

if [ ! -d "$HOOKS_SOURCE" ]; then
    echo "Error: Hooks directory not found: $HOOKS_SOURCE"
    exit 1
fi

if [ ! -d "$HOOKS_TARGET" ]; then
    echo "Error: Git hooks directory not found: $HOOKS_TARGET"
    echo "Are you in a git repository?"
    exit 1
fi

echo "Installing git hooks..."
echo "  Source: $HOOKS_SOURCE"
echo "  Target: $HOOKS_TARGET"
echo ""

# Install each hook
for hook in "$HOOKS_SOURCE"/*; do
    if [ -f "$hook" ]; then
        hook_name=$(basename "$hook")
        target_hook="$HOOKS_TARGET/$hook_name"
        
        # Copy the hook
        cp "$hook" "$target_hook"
        chmod +x "$target_hook"
        
        echo "  ✓ Installed: $hook_name"
    fi
done

echo ""
echo "✅ Git hooks installed successfully!"
echo ""
echo "The pre-commit hook will now run automatically on git commit."
echo "It will:"
echo "  - Auto-fix linting issues"
echo "  - Check code formatting"
echo "  - Run tests"
echo ""

