#!/bin/bash
# Restart-Script für TK-Witz-Bot

BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${BLUE}Starte TK-Witz-Bot neu...${NC}"

pm2 restart tk-witz-bot

echo -e "${GREEN}✓ Bot neu gestartet${NC}"
pm2 status
