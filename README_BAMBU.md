# Bambu Lab Discord Bot

Ein Discord Bot der den Status und Statistiken eines Bambu Lab 3D-Druckers in Discord anzeigt.

## Features

- 🖨️ **Echtzeit-Status**: Zeigt den aktuellen Drucker-Status (idle, printing, paused, complete)
- 📊 **Fortschrittsanzeige**: Visueller Fortschrittsbalken und Prozentanzeige
- 🌡️ **Temperatur-Überwachung**: Düsen- und Druckbett-Temperaturen
- ⏱️ **Zeitinformationen**: Verstrichene und verbleibende Druckzeit
- 🔢 **Layer-Information**: Aktueller Layer und Gesamt-Layer
- 🧵 **Filament-Verbrauch**: Anzeige des verwendeten Filaments
- 📈 **Statistiken**: Gesamte Drucke, Erfolgsrate, Gesamtdruckzeit
- 🚀 **MQTT Integration**: Echtzeit-Updates direkt vom Drucker

## Voraussetzungen

- Python 3.8 oder höher
- Discord Bot Token (siehe Setup)
- Bambu Lab Drucker im gleichen Netzwerk (für MQTT)
- Drucker Access Code (8-stelliger Code vom Drucker-Display)
- Drucker Seriennummer

## Installation

1. Repository klonen:
```bash
git clone https://github.com/kilian558/teamkill_ki.git
cd teamkill_ki
```

2. Dependencies installieren:
```bash
pip install -r requirements.txt
```

3. Umgebungsvariablen konfigurieren:
```bash
cp .env.example .env
# Dann .env bearbeiten und Werte eintragen
```

## Konfiguration

### Discord Bot erstellen

1. Gehe zu [Discord Developer Portal](https://discord.com/developers/applications)
2. Klicke auf "New Application"
3. Gebe dem Bot einen Namen
4. Gehe zu "Bot" im linken Menü
5. Klicke auf "Add Bot"
6. Aktiviere unter "Privileged Gateway Intents":
   - MESSAGE CONTENT INTENT
7. Kopiere den Token (das ist dein `DISCORD_BOT_TOKEN`)
8. Gehe zu "OAuth2" > "URL Generator"
9. Wähle Scopes: `bot`
10. Wähle Bot Permissions: 
    - Send Messages
    - Embed Links
    - Read Message History
11. Kopiere die generierte URL und öffne sie im Browser
12. Wähle deinen Discord Server aus und autorisiere den Bot

### Bambu Lab Drucker konfigurieren

1. **Drucker IP finden**:
   - Im Drucker Display: Settings > Network > IP Address

2. **Access Code finden**:
   - Im Drucker Display: Settings > Network > Access Code
   - 8-stelliger Code (z.B. "12345678")

3. **Seriennummer finden**:
   - Im Drucker Display: Settings > Device > Serial Number
   - Format: "01S00A12345678" (Beispiel)

### .env Datei

Erstelle eine `.env` Datei im Projektverzeichnis:

```env
# Discord Bot Token
DISCORD_BOT_TOKEN=dein_discord_bot_token_hier

# Bambu Lab Drucker Konfiguration
BAMBU_PRINTER_IP=192.168.1.100
BAMBU_ACCESS_CODE=12345678
BAMBU_SERIAL=01S00A12345678

# Optional: Channel ID für automatische Updates
# STATUS_CHANNEL_ID=123456789012345678
```

## Verwendung

### Lokal starten

```bash
python bambu_bot.py
```

### Discord Befehle

- `!status` - Zeigt vollständigen Drucker-Status
- `!stats` - Zeigt Drucker-Statistiken
- `!temp` - Zeigt nur Temperaturen
- `!progress` - Zeigt Druck-Fortschritt
- `!help_printer` - Zeigt alle Befehle

## Deployment auf Render

### Schritt 1: Repository zu GitHub pushen

```bash
git add .
git commit -m "Add Bambu Lab Discord Bot"
git push origin main
```

### Schritt 2: Render konfigurieren

1. Gehe zu [Render.com](https://render.com) und erstelle einen Account
2. Klicke auf "New +" > "Web Service"
3. Verbinde dein GitHub Repository
4. Konfiguriere den Service:
   - **Name**: bambu-lab-bot
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bambu_bot.py`
   - **Instance Type**: Free (oder höher für 24/7 Betrieb)

### Schritt 3: Environment Variables in Render

Füge folgende Environment Variables in Render hinzu:

- `DISCORD_BOT_TOKEN` = dein_discord_bot_token
- `BAMBU_PRINTER_IP` = drucker_ip_adresse
- `BAMBU_ACCESS_CODE` = 8_stelliger_code
- `BAMBU_SERIAL` = drucker_seriennummer

**WICHTIG**: Für MQTT-Verbindung muss der Render-Server im gleichen Netzwerk wie der Drucker sein, oder du musst Port-Forwarding/VPN einrichten.

### Alternative: Lokaler Betrieb mit Render Deploy Hook

Wenn der Drucker nur im lokalen Netzwerk erreichbar ist:

1. Lasse den Bot lokal auf einem Raspberry Pi / Server laufen
2. Nutze einen Prozess-Manager wie `systemd` oder `pm2` für automatischen Neustart

#### Beispiel systemd Service (Linux):

```bash
sudo nano /etc/systemd/system/bambu-bot.service
```

Inhalt:
```ini
[Unit]
Description=Bambu Lab Discord Bot
After=network.target

[Service]
Type=simple
User=dein_benutzer
WorkingDirectory=/pfad/zu/teamkill_ki
ExecStart=/usr/bin/python3 bambu_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Dann:
```bash
sudo systemctl daemon-reload
sudo systemctl enable bambu-bot
sudo systemctl start bambu-bot
sudo systemctl status bambu-bot
```

## Architektur

- **bambu_bot.py**: Hauptbot mit Discord Commands
- **bambu_mqtt.py**: MQTT Client für Echtzeit-Updates
- **main.py**: Original Hell Let Loose Bot (nicht relevant für Bambu Lab)

## Troubleshooting

### Bot verbindet sich nicht mit Drucker

- Überprüfe IP-Adresse: `ping <drucker_ip>`
- Stelle sicher dass der Drucker im gleichen Netzwerk ist
- Überprüfe Access Code im Drucker Display
- Überprüfe dass MQTT auf dem Drucker aktiviert ist

### Bot ist online aber reagiert nicht auf Befehle

- Überprüfe dass MESSAGE CONTENT INTENT aktiviert ist
- Überprüfe Bot Permissions im Discord Server
- Prüfe Logs: Der Bot sollte "Bot ist online und bereit!" loggen

### MQTT Verbindung fehlschlägt

- Port 8883 muss erreichbar sein
- Firewall könnte Port blockieren
- Drucker könnte MQTT deaktiviert haben (normalerweise aktiv)

### Demo-Modus

Wenn keine Drucker-Konfiguration vorhanden ist, läuft der Bot im Demo-Modus mit zufälligen Daten. Nützlich zum Testen der Discord-Integration.

## Sicherheit

- **NIEMALS** .env Datei committen
- .env ist bereits in .gitignore
- Nutze sichere Access Codes
- Beschränke Bot-Permissions auf notwendiges Minimum

## Lizenz

MIT License

## Support

Bei Fragen oder Problemen erstelle ein Issue im GitHub Repository.

## Credits

Entwickelt für Bambu Lab X1 Carbon und andere Bambu Lab Drucker.
