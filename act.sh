#!/bin/bash
# Helper script for running GitHub Actions workflows locally with act
# Usage: ./act.sh [command] [options]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if act is installed
if ! command -v act >/dev/null 2>&1; then
    echo "Error: act is not installed."
    echo ""
    echo "Install it with:"
    echo "  brew install act  # macOS"
    echo "  # or download from: https://github.com/nektos/act/releases"
    exit 1
fi

# Check if Docker is running (but don't fail if check fails - act will handle it)
if ! docker info >/dev/null 2>&1; then
    echo "Warning: Could not connect to Docker."
    echo "Please ensure Docker Desktop is running."
    echo "Continuing anyway - act will report if Docker is needed..."
    echo ""
fi

COMMAND="${1:-list}"

case "$COMMAND" in
    list|l)
        echo "Available workflows and jobs:"
        act -l
        ;;
    test|t)
        echo "Running test job..."
        act -j test "${@:2}"
        ;;
    lint|lint)
        echo "Running lint job..."
        act -j lint "${@:2}"
        ;;
    push|p)
        echo "Simulating push event (runs all jobs)..."
        act push "${@:2}"
        ;;
    pr)
        echo "Simulating pull request event..."
        act pull_request "${@:2}"
        ;;
    dry-run|dry|n)
        echo "Dry run - showing what would execute:"
        act -n "${@:2}"
        ;;
    verbose|v)
        echo "Running with verbose output..."
        act -v "${@:2}"
        ;;
    help|h|--help|-h)
        echo "Usage: ./act.sh [command] [options]"
        echo ""
        echo "Commands:"
        echo "  list, l          List available workflows and jobs"
        echo "  test, t          Run only the test job"
        echo "  lint             Run only the lint job"
        echo "  push, p          Simulate push event (runs all jobs)"
        echo "  pr               Simulate pull request event"
        echo "  dry-run, dry, n  Show what would run without executing"
        echo "  verbose, v       Run with verbose output"
        echo "  help, h          Show this help message"
        echo ""
        echo "Examples:"
        echo "  ./act.sh list              # List workflows"
        echo "  ./act.sh test              # Run test job"
        echo "  ./act.sh test -P ubuntu-latest=catthehacker/ubuntu:act-latest"
        echo "  ./act.sh push -v           # Run all jobs with verbose output"
        echo ""
        echo "For more options, see: act --help"
        ;;
    *)
        echo "Unknown command: $COMMAND"
        echo "Run './act.sh help' for usage information"
        exit 1
        ;;
esac

