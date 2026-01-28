# Bambu Lab Discord Bot - Quick Start Guide

## 🚀 Schnellstart (5 Minuten)

### Schritt 1: Repository Setup
```bash
git clone https://github.com/kilian558/teamkill_ki.git
cd teamkill_ki
```

### Schritt 2: Dependencies installieren
```bash
pip install -r requirements.txt
```

### Schritt 3: Discord Bot erstellen

1. Gehe zu https://discord.com/developers/applications
2. Klicke "New Application"
3. Name: "Bambu Lab Status"
4. Tab "Bot" → "Add Bot"
5. Aktiviere "MESSAGE CONTENT INTENT" 
6. Kopiere den Token

### Schritt 4: Bot zu Discord Server einladen

1. Tab "OAuth2" → "URL Generator"
2. Scopes: `bot`
3. Permissions: "Send Messages", "Embed Links"
4. URL kopieren und im Browser öffnen
5. Server auswählen

### Schritt 5: Drucker-Informationen finden

**IP-Adresse:**
```
Drucker Display → Settings → Network → IP Address
Beispiel: 192.168.1.100
```

**Access Code:**
```
Drucker Display → Settings → Network → Access Code
Beispiel: 12345678 (8 Ziffern)
```

**Seriennummer:**
```
Drucker Display → Settings → Device → Serial Number
Beispiel: 01S00A12345678
```

### Schritt 6: .env Datei erstellen

```bash
cp .env.example .env
nano .env  # oder einen anderen Editor
```

Trage deine Werte ein:
```env
DISCORD_BOT_TOKEN=dein_bot_token_hier
BAMBU_PRINTER_IP=192.168.1.100
BAMBU_ACCESS_CODE=12345678
BAMBU_SERIAL=01S00A12345678
```

### Schritt 7: Bot starten

```bash
python bambu_bot.py
```

Du solltest sehen:
```
INFO - bambu_discord_bot ist online und bereit!
INFO - Verbinde mit Bambu Lab Drucker via MQTT...
INFO - ✅ MQTT Verbindung erfolgreich!
```

### Schritt 8: Testen

Gehe in deinen Discord Server und tippe:
```
!status
```

🎉 Fertig!

---

## 📱 Commands Übersicht

| Command | Beschreibung | Beispiel |
|---------|--------------|----------|
| `!status` | Vollständiger Status | Zeigt alles an |
| `!stats` | Statistiken | Gesamt-Drucke, Zeit, Filament |
| `!temp` | Nur Temperaturen | Düse & Bett |
| `!progress` | Druck-Fortschritt | Layer, Zeit, % |
| `!help_printer` | Hilfe | Alle Commands |

---

## 🐛 Troubleshooting

### Bot startet nicht

❌ **Error: "DISCORD_BOT_TOKEN fehlt"**
```bash
# .env Datei prüfen
cat .env | grep DISCORD_BOT_TOKEN
```

✅ **Lösung:** Token in .env eintragen

---

### Bot reagiert nicht auf Commands

❌ **Bot ist online aber antwortet nicht**

✅ **Lösung:** 
1. Discord Developer Portal öffnen
2. Bot → "Privileged Gateway Intents"
3. "MESSAGE CONTENT INTENT" aktivieren
4. Bot neu starten

---

### MQTT Verbindung fehlschlägt

❌ **Error: "MQTT Verbindung fehlgeschlagen"**

✅ **Lösungen:**
1. Ping testen: `ping 192.168.1.100`
2. Access Code im Drucker prüfen (8 Ziffern)
3. Drucker im gleichen Netzwerk?
4. Firewall blockiert Port 8883?

---

### Demo-Modus

ℹ️ Wenn keine Drucker-Config vorhanden ist, läuft der Bot im Demo-Modus mit Beispiel-Daten.

Das ist perfekt zum Testen der Discord-Integration!

---

## 🌐 Deployment auf Render

### Option A: Lokaler Betrieb (empfohlen)

Für MQTT muss der Bot im gleichen Netzwerk wie der Drucker sein.

**Empfehlung:** Raspberry Pi oder lokaler Server

```bash
# Systemd Service erstellen
sudo cp docs/bambu-bot.service /etc/systemd/system/
sudo systemctl enable bambu-bot
sudo systemctl start bambu-bot
```

### Option B: Cloud mit VPN

1. VPN zum lokalen Netzwerk
2. Render mit privater IP konfigurieren
3. Oder: Drucker-Port forwarding (NICHT empfohlen wegen Sicherheit)

---

## 📊 Beispiel Output

```
🖨️ Bambu Lab Drucker Status
━━━━━━━━━━━━━━━━━━━━━━━━━━

🖨️ Status: Printing
📄 Datei: benchy_v2.3mf
📊 Fortschritt: 67%

Progress Bar: [█████████████░░░░░░░] 67%

🌡️ Düse: 240°C / 240°C
🌡️ Druckbett: 70°C / 70°C
🔢 Layer: 187 / 280
⏱️ Druckzeit: 2h 20m
⏳ Verbleibend: 1h 5m
🧵 Filament: 42g
```

---

## 🔐 Sicherheit

- ✅ .env ist in .gitignore
- ✅ Niemals Token committen
- ✅ Access Code geheim halten
- ✅ Bot Permissions minimal halten

---

## 💡 Tipps

1. **Auto-Updates:** Setze `STATUS_CHANNEL_ID` für automatische Updates
2. **Mehrere Drucker:** Erweitere den Code für mehrere MQTT Clients
3. **Benachrichtigungen:** Füge Alerts bei Druckende hinzu
4. **Webcam:** Integriere Bambu Lab Webcam (TODO)

---

## 🆘 Support

Problem? → Erstelle ein Issue auf GitHub

## 📄 Lizenz

MIT License - siehe LICENSE Datei
