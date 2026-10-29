#!/usr/bin/env bash
# Ejecuta los tests de la integración (o ruff / uv lock) en un contenedor Docker,
# porque Home Assistant no corre en Windows.
#
#   scripts/ha-test.sh [args de pytest]
#   scripts/ha-test.sh --ruff
#   scripts/ha-test.sh --lock
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
IMAGE="ghcr.io/astral-sh/uv:python3.14-trixie-slim"

case "${1:-}" in
    --ruff)
        shift
        CMD=(sh -c "uv run --locked --group ha ruff check custom_components tests && uv run --locked --group ha ruff format --check custom_components tests")
        ;;
    --lock)
        shift
        CMD=(uv lock)
        ;;
    *)
        CMD=(uv run --locked --group ha pytest "$@")
        ;;
esac

MSYS_NO_PATHCONV=1 docker run --rm \
    -v "${ROOT}:/work" \
    -v curenergia-venv:/work/.venv \
    -v curenergia-uvcache:/root/.cache/uv \
    -e UV_LINK_MODE=copy \
    -w /work \
    "$IMAGE" "${CMD[@]}"
