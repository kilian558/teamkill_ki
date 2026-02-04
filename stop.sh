#!/bin/bash
# Stop-Script für TK-Witz-Bot

BLUE='\033[0;34m'
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${BLUE}Stoppe TK-Witz-Bot...${NC}"

pm2 stop tk-witz-bot

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Bot erfolgreich gestoppt${NC}"
else
    echo -e "${RED}✗ Fehler beim Stoppen des Bots${NC}"
    exit 1
fi

pm2 status
