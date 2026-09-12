#!/bin/bash
# start.sh — wsteczna kompatybilność, deleguje do ./dashboard
ROOT="$(cd "$(dirname "$0")" && pwd)"
exec "$ROOT/dashboard" "$@"
