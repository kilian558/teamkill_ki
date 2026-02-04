#!/bin/bash
# Start-Script für TK-Witz-Bot mit pm2

# Farben für Output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   TK-Witz-Bot Startup Script          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Prüfe ob Python3 installiert ist
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python3 ist nicht installiert!${NC}"
    exit 1
fi

# Prüfe ob pip installiert ist
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}✗ pip3 ist nicht installiert!${NC}"
    exit 1
fi

# Prüfe ob pm2 installiert ist
if ! command -v pm2 &> /dev/null; then
    echo -e "${RED}✗ pm2 ist nicht installiert!${NC}"
    echo -e "${BLUE}Installiere mit: npm install -g pm2${NC}"
    exit 1
fi

# Erstelle logs Verzeichnis
if [ ! -d "logs" ]; then
    mkdir logs
    echo -e "${GREEN}✓ logs Verzeichnis erstellt${NC}"
fi

# Prüfe ob .env existiert
if [ ! -f ".env" ]; then
    echo -e "${RED}✗ .env Datei fehlt!${NC}"
    echo -e "${BLUE}Kopiere .env.example zu .env und fülle die Werte aus.${NC}"
    exit 1
fi

# Installiere Python Dependencies
echo -e "${BLUE}→ Installiere Python Dependencies...${NC}"
pip3 install -r requirements.txt --quiet
echo -e "${GREEN}✓ Dependencies installiert${NC}"

# Mache Python-Script ausführbar
chmod +x main.py

# Starte Bot mit pm2
echo -e "${BLUE}→ Starte Bot mit pm2...${NC}"
pm2 start ecosystem.config.js

# Zeige Status
pm2 status

echo ""
echo -e "${GREEN}✓ Bot erfolgreich gestartet!${NC}"
echo ""
echo -e "${BLUE}Nützliche Befehle:${NC}"
echo -e "  pm2 logs tk-witz-bot    - Logs anzeigen"
echo -e "  pm2 status              - Status prüfen"
echo -e "  pm2 restart tk-witz-bot - Bot neustarten"
echo -e "  pm2 stop tk-witz-bot    - Bot stoppen"
echo -e "  pm2 delete tk-witz-bot  - Bot entfernen"
echo ""
