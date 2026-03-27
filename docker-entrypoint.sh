#!/bin/bash
# Docker entrypoint script for Cyber Companion Bot

set -e

echo "🔷 Starting Cyber Companion Bot..."

# Create necessary directories
mkdir -p /app/.cyber_companion
mkdir -p /app/reports
mkdir -p /app/scan_results
mkdir -p /app/logs
mkdir -p /app/temp

# Set permissions
chmod 755 /app/.cyber_companion
chmod 755 /app/reports
chmod 755 /app/scan_results

# Check if config exists, if not create default
if [ ! -f "/app/.cyber_companion/config.json" ]; then
    echo "Creating default configuration..."
    cat > /app/.cyber_companion/config.json <<EOF
{
    "version": "1.0.0",
    "environment": "${CYBER_COMPANION_ENV:-development}",
    "logging": {
        "level": "INFO",
        "file": "/app/logs/cyber_companion.log"
    }
}
EOF
fi

# Export environment variables
export DISCORD_TOKEN="${DISCORD_TOKEN:-}"
export TELEGRAM_API_ID="${TELEGRAM_API_ID:-}"
export TELEGRAM_API_HASH="${TELEGRAM_API_HASH:-}"

# Print startup banner
echo "==========================================="
echo "🔷 Cyber Companion Bot v1.0.0"
echo "Environment: ${CYBER_COMPANION_ENV:-development}"
echo "Discord Bot: $([ -n "$DISCORD_TOKEN" ] && echo "Enabled" || echo "Disabled")"
echo "Telegram Bot: $([ -n "$TELEGRAM_API_ID" ] && echo "Enabled" || echo "Disabled")"
echo "==========================================="

# Check dependencies
echo "Checking dependencies..."
command -v nmap >/dev/null 2>&1 && echo "✅ nmap" || echo "⚠️  nmap not found"
command -v curl >/dev/null 2>&1 && echo "✅ curl" || echo "⚠️  curl not found"
command -v wget >/dev/null 2>&1 && echo "✅ wget" || echo "⚠️  wget not found"
command -v nc >/dev/null 2>&1 && echo "✅ netcat" || echo "⚠️  netcat not found"
command -v ping >/dev/null 2>&1 && echo "✅ ping" || echo "⚠️  ping not found"

echo "Starting application..."

# Execute the main command
exec python3 /app/cyber_companion_bot.py "$@"