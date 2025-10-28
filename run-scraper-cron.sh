#!/bin/bash
# Wrapper script for cron jobs to avoid exceeding crontab line length limits
# Usage: ./run-scraper-cron.sh <config_id>

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_ID="${1}"

if [ -z "$CONFIG_ID" ]; then
    echo "Error: Config ID required"
    exit 1
fi

# Source environment variables
if [ -f "$SCRIPT_DIR/.env" ]; then
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
fi

# API configuration
FASTAPI_BASE_URL="${FASTAPI_BASE_URL:-http://localhost:8933}"
FASTAPI_API_KEY="${FASTAPI_API_KEY:-}"
FASTAPI_API_KEY_HEADER="${FASTAPI_API_KEY_HEADER:-X-API-Key}"
HEALTHCHECK_TIMEOUT="${SCRAPER_HEALTHCHECK_TIMEOUT:-10}"
HEALTHCHECK_RETRIES="${SCRAPER_HEALTHCHECK_RETRIES:-3}"

# Log file
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/cron.log"

# Fetch config from API
RESPONSE=$(curl -fsS -H "$FASTAPI_API_KEY_HEADER: $FASTAPI_API_KEY" \
    "$FASTAPI_BASE_URL/api/configs/$CONFIG_ID" 2>/dev/null || echo "")

if [ -z "$RESPONSE" ]; then
    echo "Failed to fetch config $CONFIG_ID" >&2
    exit 1
fi

# Extract healthcheck URL if present
HEALTHCHECK_URL=$(echo "$RESPONSE" | python3 -c "import sys,json; data=json.load(sys.stdin); print(data.get('healthcheck_ping_url', ''))" 2>/dev/null || echo "")

# Build and run scrape command
cd "$SCRIPT_DIR"

PYTHON_EXEC="${SCRAPER_PYTHON:-$(which python3)}"
VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python3"

if [ -f "$VENV_PYTHON" ]; then
    PYTHON_EXEC="$VENV_PYTHON"
fi

# Run the scraper
"$PYTHON_EXEC" -m app.cli run-config "$CONFIG_ID" >> "$LOG_FILE" 2>&1
STATUS=$?

# Send health check pings
send_healthcheck() {
    local health_status="$1"
    local health_url="$FASTAPI_BASE_URL/api/cron/health/$CONFIG_ID"

    # Internal health check
    curl -fsS -m "$HEALTHCHECK_TIMEOUT" --retry "$HEALTHCHECK_RETRIES" \
        -X POST \
        -H "Content-Type: application/json" \
        -H "$FASTAPI_API_KEY_HEADER: $FASTAPI_API_KEY" \
        -d "{\"status\":\"$health_status\"}" \
        "$health_url" >/dev/null 2>&1 || true

    # External healthcheck (if configured)
    if [ -n "$HEALTHCHECK_URL" ]; then
        if [ "$health_status" = "ok" ]; then
            curl -fsS -m "$HEALTHCHECK_TIMEOUT" --retry "$HEALTHCHECK_RETRIES" \
                "$HEALTHCHECK_URL" >/dev/null 2>&1 || true
        else
            curl -fsS -m "$HEALTHCHECK_TIMEOUT" --retry "$HEALTHCHECK_RETRIES" \
                "$HEALTHCHECK_URL/fail" >/dev/null 2>&1 || true
        fi
    fi
}

if [ $STATUS -eq 0 ]; then
    send_healthcheck "ok"
else
    send_healthcheck "fail"
fi

exit $STATUS
