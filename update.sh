#!/bin/bash
# Update-Script für TK-Witz-Bot

BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   TK-Witz-Bot Update Script            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Update Dependencies
echo -e "${BLUE}→ Aktualisiere Python Dependencies...${NC}"
pip3 install -r requirements.txt --upgrade --quiet

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Dependencies aktualisiert${NC}"
else
    echo -e "${RED}✗ Fehler beim Aktualisieren der Dependencies${NC}"
    exit 1
fi

# Restart Bot
echo -e "${BLUE}→ Starte Bot neu...${NC}"
pm2 restart tk-witz-bot

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Bot erfolgreich neu gestartet${NC}"
else
    echo -e "${RED}✗ Fehler beim Neustart${NC}"
    exit 1
fi

echo ""
pm2 status
echo ""
echo -e "${GREEN}✓ Update abgeschlossen!${NC}"
