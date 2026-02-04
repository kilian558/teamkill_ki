# TK-Witz-Bot für Hell Let Loose

Discord Bot, der automatisch lustige Kommentare sendet, wenn Spieler über Teamkills chatten.

## Features

✅ Multi-Server-Support  
✅ Intelligente Witze via Grok AI  
✅ Cooldown-System gegen Spam  
✅ Discord-Logging  
✅ Optimiert für pm2  
✅ Graceful Shutdown  
✅ Automatisches Memory Management  
✅ Detailliertes Error-Handling  

## Voraussetzungen

- **Linux Server** (Ubuntu/Debian empfohlen)
- **Python 3.8+**
- **Node.js & npm** (für pm2)
- **pm2** Process Manager

## Installation auf Linux

### 1. System-Pakete installieren

```bash
# Update System
sudo apt update && sudo apt upgrade -y

# Installiere Python3 und pip
sudo apt install python3 python3-pip -y

# Installiere Node.js und npm (falls nicht vorhanden)
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt install -y nodejs

# Installiere pm2 global
sudo npm install -g pm2
```

### 2. Bot-Dateien hochladen

```bash
# Erstelle Verzeichnis
mkdir -p ~/bots/tk-witz-bot
cd ~/bots/tk-witz-bot

# Lade deine Dateien hoch (z.B. via scp, sftp, oder git)
# Alle Dateien sollten in diesem Verzeichnis sein
```

### 3. Konfiguration

```bash
# Kopiere .env.example zu .env
cp .env.example .env

# Bearbeite .env mit deinen Credentials
nano .env
```

Fülle folgende Werte in der `.env` aus:
- `CRCON_BASE_URLS` - Deine CRCON Server URLs (komma-separiert)
- `CRCON_TOKEN` - Dein CRCON API Token
- `DISCORD_WEBHOOK_URL` - Discord Webhook für Logs
- `XAI_API_KEY` - Dein X.AI API Key für Grok

### 4. Python Dependencies installieren

```bash
pip3 install -r requirements.txt
```

### 5. Start-Script ausführbar machen

```bash
chmod +x start.sh
chmod +x main.py
```

### 6. Bot starten

```bash
./start.sh
```

## pm2 Befehle

```bash
# Status anzeigen
pm2 status

# Logs in Echtzeit anzeigen
pm2 logs tk-witz-bot

# Logs ohne Echtzeit
pm2 logs tk-witz-bot --lines 100

# Bot neustarten
pm2 restart tk-witz-bot

# Bot stoppen
pm2 stop tk-witz-bot

# Bot aus pm2 entfernen
pm2 delete tk-witz-bot

# pm2 beim Systemstart automatisch starten
pm2 startup
pm2 save
```

## Logs

Logs werden in `./logs/` gespeichert:
- `out.log` - Standard Output
- `err.log` - Fehler
- `combined.log` - Kombiniert

## Monitoring

```bash
# pm2 Monit (Terminal UI)
pm2 monit

# Detaillierte Infos
pm2 show tk-witz-bot
```

## Troubleshooting

### Bot startet nicht
```bash
# Prüfe Logs
pm2 logs tk-witz-bot --err

# Prüfe .env Konfiguration
cat .env

# Teste Python-Script manuell
python3 main.py
```

### Hoher Speicherverbrauch
```bash
# pm2 startet Bot automatisch neu bei >500MB (siehe ecosystem.config.js)
# Aktuellen Speicher prüfen:
pm2 status
```

### Dependencies-Fehler
```bash
# Reinstalliere Dependencies
pip3 install -r requirements.txt --force-reinstall
```

## Optimierungen im Code

Der Code wurde optimiert mit:
- ✅ Type Hints für bessere Code-Qualität
- ✅ Graceful Shutdown (SIGTERM/SIGINT handling)
- ✅ Detailliertes Exception Handling
- ✅ Timeout-Parameter für alle Requests
- ✅ Memory Management (automatisches Cleanup)
- ✅ Cooldown-Cleanup für alte Einträge
- ✅ Heartbeat-Logging alle 100 Iterationen
- ✅ Strukturierte Fehlerbehandlung

## Support

Bei Problemen:
1. Prüfe Logs: `pm2 logs tk-witz-bot`
2. Prüfe Status: `pm2 status`
3. Prüfe .env Konfiguration
4. Teste manuell: `python3 main.py`

## Lizenz

Private Nutzung für Hell Let Loose Community
