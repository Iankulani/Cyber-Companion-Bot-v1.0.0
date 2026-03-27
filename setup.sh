#!/bin/bash
# Setup script for Cyber Companion Bot

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          🔷 CYBER COMPANION BOT - INSTALLATION SCRIPT         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check Python version
echo -e "${GREEN}🔍 Checking Python version...${NC}"
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.7.0"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then 
    echo -e "${GREEN}✅ Python $python_version detected${NC}"
else
    echo -e "${RED}❌ Python 3.7 or higher required (found $python_version)${NC}"
    exit 1
fi

# Check pip
echo -e "${GREEN}🔍 Checking pip...${NC}"
if command -v pip3 &> /dev/null; then
    echo -e "${GREEN}✅ pip3 detected${NC}"
else
    echo -e "${RED}❌ pip3 not found${NC}"
    exit 1
fi

# Create directories
echo -e "${GREEN}📁 Creating directories...${NC}"
mkdir -p .cyber_companion
mkdir -p reports
mkdir -p scan_results
mkdir -p temp
mkdir -p logs
mkdir -p backups

echo -e "${GREEN}✅ Directories created${NC}"

# Install dependencies
echo -e "${GREEN}📦 Installing Python dependencies...${NC}"
pip3 install --upgrade pip
pip3 install -r requirements.txt

# Check for system tools
echo -e "${GREEN}🔧 Checking system tools...${NC}"
tools=("nmap" "curl" "wget" "nc" "ssh" "ping" "traceroute" "dig" "whois")
missing_tools=()

for tool in "${tools[@]}"; do
    if command -v $tool &> /dev/null; then
        echo -e "${GREEN}✅ $tool${NC}"
    else
        echo -e "${YELLOW}⚠️  $tool not found${NC}"
        missing_tools+=($tool)
    fi
done

if [ ${#missing_tools[@]} -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}⚠️  Some tools are missing. Install them with:${NC}"
    echo -e "${BLUE}  sudo apt-get install ${missing_tools[@]}${NC}"
fi

# Create configuration
echo ""
echo -e "${GREEN}⚙️  Configuring application...${NC}"
if [ ! -f ".cyber_companion/config.json" ]; then
    cat > .cyber_companion/config.json <<EOF
{
    "version": "1.0.0",
    "environment": "development",
    "logging": {
        "level": "INFO",
        "file": "logs/cyber_companion.log"
    }
}
EOF
    echo -e "${GREEN}✅ Default configuration created${NC}"
fi

# Ask for Discord setup
echo ""
echo -e "${BLUE}🤖 Discord Bot Setup${NC}"
read -p "Do you want to configure Discord bot? (y/n): " setup_discord
if [[ $setup_discord == "y" || $setup_discord == "Y" ]]; then
    read -p "Enter Discord bot token: " discord_token
    read -p "Enter command prefix (default: !): " discord_prefix
    discord_prefix=${discord_prefix:-"!"}
    
    cat > .cyber_companion/discord_config.json <<EOF
{
    "token": "$discord_token",
    "enabled": true,
    "prefix": "$discord_prefix"
}
EOF
    echo -e "${GREEN}✅ Discord configuration saved${NC}"
fi

# Ask for Telegram setup
echo ""
echo -e "${BLUE}📱 Telegram Bot Setup${NC}"
read -p "Do you want to configure Telegram bot? (y/n): " setup_telegram
if [[ $setup_telegram == "y" || $setup_telegram == "Y" ]]; then
    read -p "Enter API ID: " api_id
    read -p "Enter API Hash: " api_hash
    
    cat > .cyber_companion/telegram_config.json <<EOF
{
    "api_id": "$api_id",
    "api_hash": "$api_hash",
    "enabled": true
}
EOF
    echo -e "${GREEN}✅ Telegram configuration saved${NC}"
fi

# Set permissions
echo ""
echo -e "${GREEN}🔒 Setting permissions...${NC}"
chmod 755 .cyber_companion
chmod 755 reports scan_results temp logs
chmod 600 .cyber_companion/*.json 2>/dev/null || true

# Create .env file for Docker
echo ""
echo -e "${GREEN}🐳 Creating .env file for Docker...${NC}"
if [ ! -f ".env" ]; then
    cat > .env <<EOF
# Cyber Companion Bot Environment Variables
DISCORD_TOKEN=${discord_token:-}
TELEGRAM_API_ID=${api_id:-}
TELEGRAM_API_HASH=${api_hash:-}
CYBER_COMPANION_ENV=development
EOF
    echo -e "${GREEN}✅ .env file created${NC}"
fi

# Run initial test
echo ""
echo -e "${GREEN}🧪 Running initial test...${NC}"
if python3 -c "import sys; sys.path.insert(0, '.'); import cyber_companion_bot" 2>/dev/null; then
    echo -e "${GREEN}✅ Application imports successfully${NC}"
else
    echo -e "${RED}❌ Failed to import application${NC}"
fi

# Show completion message
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                 ✅ INSTALLATION COMPLETE!                       ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📖 To run the application:${NC}"
echo -e "  ${GREEN}python3 cyber_companion_bot.py${NC}"
echo ""
echo -e "${BLUE}🐳 To run with Docker:${NC}"
echo -e "  ${GREEN}docker-compose up -d${NC}"
echo ""
echo -e "${BLUE}🛠️  Useful commands:${NC}"
echo -e "  ${GREEN}make help${NC} - Show all make commands"
echo -e "  ${GREEN}make run${NC} - Run the application"
echo -e "  ${GREEN}make docker-build${NC} - Build Docker image"
echo -e "  ${GREEN}make docker-run${NC} - Run with Docker"
echo ""
echo -e "${YELLOW}⚠️  Remember to use this tool responsibly and only on authorized systems!${NC}"
echo -e "${YELLOW}⚠️  Logs are stored in logs/ directory${NC}"
echo ""