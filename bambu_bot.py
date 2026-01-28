"""
Discord Bot für Bambu Lab 3D Drucker Status und Statistiken
Zeigt Echtzeit-Status, Temperaturen, Fortschritt und Statistiken im Discord an
"""

import discord
from discord.ext import commands, tasks
import os
import logging
import asyncio
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
import aiohttp
from bambu_mqtt import BambuLabMQTT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configuration
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
BAMBU_PRINTER_IP = os.getenv("BAMBU_PRINTER_IP")
BAMBU_ACCESS_CODE = os.getenv("BAMBU_ACCESS_CODE")
BAMBU_SERIAL = os.getenv("BAMBU_SERIAL")
STATUS_CHANNEL_ID = os.getenv("STATUS_CHANNEL_ID")  # Optional: Channel für Auto-Updates

if not DISCORD_BOT_TOKEN:
    raise ValueError("DISCORD_BOT_TOKEN fehlt in .env!")

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Global state
printer_data = {
    "status": "Unbekannt",
    "progress": 0,
    "nozzle_temp": 0,
    "bed_temp": 0,
    "target_nozzle_temp": 0,
    "target_bed_temp": 0,
    "layer_num": 0,
    "total_layers": 0,
    "print_time": 0,
    "remaining_time": 0,
    "filename": "Kein Druck",
    "last_update": None,
    "filament_used": 0,
    "error": None
}

# Statistics tracking
statistics = {
    "total_prints": 0,
    "successful_prints": 0,
    "failed_prints": 0,
    "total_print_time": 0,
    "total_filament_used": 0,
    "last_print_date": None
}


class BambuLabAPI:
    """
    API Client für Bambu Lab Drucker
    Unterstützt sowohl lokale MQTT als auch HTTP Fallback
    """
    
    def __init__(self, printer_ip, access_code, serial):
        self.printer_ip = printer_ip
        self.access_code = access_code
        self.serial = serial
        self.base_url = f"http://{printer_ip}" if printer_ip else None
        
    async def get_printer_status(self):
        """
        Holt den aktuellen Drucker-Status
        
        HINWEIS: Bambu Lab Drucker verwenden MQTT für Echtzeit-Updates.
        Diese Implementierung ist ein Platzhalter für HTTP-basierte Abfragen.
        Für echte Implementierung sollte paho-mqtt verwendet werden.
        """
        if not self.base_url:
            return self._get_mock_data()
        
        try:
            async with aiohttp.ClientSession() as session:
                # Bambu Lab verwendet MQTT, aber wir versuchen HTTP als Fallback
                headers = {"Authorization": f"Bearer {self.access_code}"}
                async with session.get(
                    f"{self.base_url}/api/status",
                    headers=headers,
                    timeout=10
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.warning(f"HTTP Status {response.status} vom Drucker")
                        return self._get_mock_data()
        except Exception as e:
            logger.error(f"Fehler beim Abrufen des Druckerstatus: {e}")
            return self._get_mock_data()
    
    def _get_mock_data(self):
        """Mock Daten für Demonstrationszwecke wenn kein Drucker verbunden"""
        import random
        return {
            "status": random.choice(["idle", "printing", "paused", "complete"]),
            "progress": random.randint(0, 100),
            "nozzle_temp": random.randint(200, 250),
            "bed_temp": random.randint(50, 80),
            "target_nozzle_temp": 240,
            "target_bed_temp": 70,
            "layer_num": random.randint(10, 200),
            "total_layers": 250,
            "print_time": random.randint(3600, 18000),
            "remaining_time": random.randint(1800, 7200),
            "filename": "test_model.3mf",
            "filament_used": random.randint(10, 50)
        }


# Initialisiere API Client und MQTT
bambu_api = BambuLabAPI(BAMBU_PRINTER_IP, BAMBU_ACCESS_CODE, BAMBU_SERIAL)
bambu_mqtt = None

if BAMBU_PRINTER_IP and BAMBU_ACCESS_CODE and BAMBU_SERIAL:
    bambu_mqtt = BambuLabMQTT(BAMBU_PRINTER_IP, BAMBU_ACCESS_CODE, BAMBU_SERIAL)
    
    def mqtt_callback(data):
        """Callback für MQTT Updates"""
        global printer_data
        printer_data.update(data)
        printer_data["last_update"] = datetime.now()
        printer_data["error"] = None
        logger.debug(f"MQTT Update empfangen: {data.get('status')}")
    
    bambu_mqtt.set_callback(mqtt_callback)


async def update_printer_data():
    """Aktualisiert die globalen Druckerdaten"""
    global printer_data
    try:
        data = await bambu_api.get_printer_status()
        printer_data.update(data)
        printer_data["last_update"] = datetime.now()
        printer_data["error"] = None
    except Exception as e:
        logger.error(f"Fehler beim Update der Druckerdaten: {e}")
        printer_data["error"] = str(e)


def get_status_emoji(status):
    """Gibt das passende Emoji für den Status zurück"""
    status_emojis = {
        "idle": "💤",
        "printing": "🖨️",
        "paused": "⏸️",
        "complete": "✅",
        "error": "❌",
        "preparing": "⏳"
    }
    return status_emojis.get(status.lower(), "❓")


def format_time(seconds):
    """Formatiert Sekunden in lesbares Format"""
    if seconds <= 0:
        return "0m"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def create_status_embed():
    """Erstellt ein Discord Embed mit dem aktuellen Drucker-Status"""
    embed = discord.Embed(
        title="🖨️ Bambu Lab Drucker Status",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    
    status = printer_data.get("status", "Unbekannt")
    emoji = get_status_emoji(status)
    
    embed.add_field(
        name=f"{emoji} Status",
        value=status.capitalize(),
        inline=True
    )
    
    if printer_data.get("filename") and printer_data["filename"] != "Kein Druck":
        embed.add_field(
            name="📄 Datei",
            value=printer_data["filename"],
            inline=True
        )
    
    if status == "printing" or printer_data.get("progress", 0) > 0:
        progress = printer_data.get("progress", 0)
        embed.add_field(
            name="📊 Fortschritt",
            value=f"{progress}%",
            inline=True
        )
        
        # Progress Bar
        bar_length = 20
        filled = int(bar_length * progress / 100)
        bar = "█" * filled + "░" * (bar_length - filled)
        embed.add_field(
            name="Progress Bar",
            value=f"`{bar}`",
            inline=False
        )
    
    # Temperaturen
    nozzle_temp = printer_data.get("nozzle_temp", 0)
    target_nozzle = printer_data.get("target_nozzle_temp", 0)
    bed_temp = printer_data.get("bed_temp", 0)
    target_bed = printer_data.get("target_bed_temp", 0)
    
    embed.add_field(
        name="🌡️ Düse",
        value=f"{nozzle_temp}°C / {target_nozzle}°C",
        inline=True
    )
    embed.add_field(
        name="🌡️ Druckbett",
        value=f"{bed_temp}°C / {target_bed}°C",
        inline=True
    )
    
    # Layer Info
    if printer_data.get("total_layers", 0) > 0:
        layer_num = printer_data.get("layer_num", 0)
        total_layers = printer_data.get("total_layers", 0)
        embed.add_field(
            name="🔢 Layer",
            value=f"{layer_num} / {total_layers}",
            inline=True
        )
    
    # Zeitinformationen
    if printer_data.get("print_time", 0) > 0:
        print_time = format_time(printer_data.get("print_time", 0))
        embed.add_field(
            name="⏱️ Druckzeit",
            value=print_time,
            inline=True
        )
    
    if printer_data.get("remaining_time", 0) > 0:
        remaining = format_time(printer_data.get("remaining_time", 0))
        embed.add_field(
            name="⏳ Verbleibend",
            value=remaining,
            inline=True
        )
    
    # Filament
    if printer_data.get("filament_used", 0) > 0:
        filament = printer_data.get("filament_used", 0)
        embed.add_field(
            name="🧵 Filament",
            value=f"{filament}g",
            inline=True
        )
    
    # Letztes Update
    if printer_data.get("last_update"):
        embed.set_footer(text=f"Letztes Update: {printer_data['last_update'].strftime('%H:%M:%S')}")
    
    if printer_data.get("error"):
        embed.add_field(
            name="⚠️ Warnung",
            value=f"Keine Verbindung zum Drucker. Zeige Demo-Daten.",
            inline=False
        )
    
    return embed


def create_statistics_embed():
    """Erstellt ein Discord Embed mit Statistiken"""
    embed = discord.Embed(
        title="📊 Drucker Statistiken",
        color=discord.Color.green(),
        timestamp=datetime.now()
    )
    
    embed.add_field(
        name="🖨️ Gesamt Drucke",
        value=str(statistics["total_prints"]),
        inline=True
    )
    embed.add_field(
        name="✅ Erfolgreich",
        value=str(statistics["successful_prints"]),
        inline=True
    )
    embed.add_field(
        name="❌ Fehlgeschlagen",
        value=str(statistics["failed_prints"]),
        inline=True
    )
    
    if statistics["total_prints"] > 0:
        success_rate = (statistics["successful_prints"] / statistics["total_prints"]) * 100
        embed.add_field(
            name="📈 Erfolgsrate",
            value=f"{success_rate:.1f}%",
            inline=True
        )
    
    total_time = format_time(statistics["total_print_time"])
    embed.add_field(
        name="⏱️ Gesamt Druckzeit",
        value=total_time,
        inline=True
    )
    
    embed.add_field(
        name="🧵 Gesamt Filament",
        value=f"{statistics['total_filament_used']}g",
        inline=True
    )
    
    if statistics["last_print_date"]:
        embed.add_field(
            name="📅 Letzter Druck",
            value=statistics["last_print_date"].strftime("%d.%m.%Y %H:%M"),
            inline=False
        )
    
    return embed


@bot.event
async def on_ready():
    """Event: Bot ist bereit"""
    logger.info(f'{bot.user} ist online und bereit!')
    logger.info(f'Bot läuft in {len(bot.guilds)} Server(n)')
    
    # Verbinde mit Drucker via MQTT wenn konfiguriert
    if bambu_mqtt:
        logger.info("Verbinde mit Bambu Lab Drucker via MQTT...")
        if bambu_mqtt.connect():
            logger.info("✅ MQTT Verbindung erfolgreich!")
        else:
            logger.warning("⚠️ MQTT Verbindung fehlgeschlagen, verwende HTTP Fallback")
    else:
        logger.warning("⚠️ Keine Drucker-Konfiguration, verwende Demo-Modus")
    
    # Starte Background Task
    if not update_status_task.is_running():
        update_status_task.start()
    
    logger.info("Status-Update Task gestartet")


@bot.command(name='status')
async def status_command(ctx):
    """
    Zeigt den aktuellen Drucker-Status an
    
    Verwendung: !status
    """
    await update_printer_data()
    embed = create_status_embed()
    await ctx.send(embed=embed)


@bot.command(name='stats')
async def stats_command(ctx):
    """
    Zeigt Drucker-Statistiken an
    
    Verwendung: !stats
    """
    embed = create_statistics_embed()
    await ctx.send(embed=embed)


@bot.command(name='temp')
async def temp_command(ctx):
    """
    Zeigt nur die Temperaturen an
    
    Verwendung: !temp
    """
    await update_printer_data()
    
    embed = discord.Embed(
        title="🌡️ Temperaturen",
        color=discord.Color.orange(),
        timestamp=datetime.now()
    )
    
    nozzle_temp = printer_data.get("nozzle_temp", 0)
    target_nozzle = printer_data.get("target_nozzle_temp", 0)
    bed_temp = printer_data.get("bed_temp", 0)
    target_bed = printer_data.get("target_bed_temp", 0)
    
    embed.add_field(
        name="🔥 Düse (Nozzle)",
        value=f"**{nozzle_temp}°C** / {target_nozzle}°C",
        inline=False
    )
    embed.add_field(
        name="🛏️ Druckbett (Bed)",
        value=f"**{bed_temp}°C** / {target_bed}°C",
        inline=False
    )
    
    await ctx.send(embed=embed)


@bot.command(name='progress')
async def progress_command(ctx):
    """
    Zeigt Druck-Fortschritt und Zeit an
    
    Verwendung: !progress
    """
    await update_printer_data()
    
    if printer_data.get("status") != "printing":
        await ctx.send("ℹ️ Momentan läuft kein Druck.")
        return
    
    embed = discord.Embed(
        title="📊 Druck-Fortschritt",
        color=discord.Color.purple(),
        timestamp=datetime.now()
    )
    
    progress = printer_data.get("progress", 0)
    bar_length = 20
    filled = int(bar_length * progress / 100)
    bar = "█" * filled + "░" * (bar_length - filled)
    
    embed.add_field(
        name="Fortschritt",
        value=f"`{bar}` {progress}%",
        inline=False
    )
    
    if printer_data.get("filename"):
        embed.add_field(
            name="📄 Datei",
            value=printer_data["filename"],
            inline=False
        )
    
    if printer_data.get("layer_num") and printer_data.get("total_layers"):
        embed.add_field(
            name="🔢 Layer",
            value=f"{printer_data['layer_num']} / {printer_data['total_layers']}",
            inline=True
        )
    
    if printer_data.get("print_time"):
        print_time = format_time(printer_data["print_time"])
        embed.add_field(
            name="⏱️ Verstrichene Zeit",
            value=print_time,
            inline=True
        )
    
    if printer_data.get("remaining_time"):
        remaining = format_time(printer_data["remaining_time"])
        embed.add_field(
            name="⏳ Verbleibende Zeit",
            value=remaining,
            inline=True
        )
    
    await ctx.send(embed=embed)


@bot.command(name='help_printer')
async def help_printer_command(ctx):
    """
    Zeigt alle verfügbaren Befehle an
    
    Verwendung: !help_printer
    """
    embed = discord.Embed(
        title="🤖 Bambu Lab Bot Befehle",
        description="Hier sind alle verfügbaren Befehle:",
        color=discord.Color.blue()
    )
    
    commands_list = [
        ("!status", "Zeigt den vollständigen Drucker-Status"),
        ("!stats", "Zeigt Drucker-Statistiken"),
        ("!temp", "Zeigt nur die Temperaturen"),
        ("!progress", "Zeigt Druck-Fortschritt und Zeit"),
        ("!help_printer", "Zeigt diese Hilfe")
    ]
    
    for cmd, desc in commands_list:
        embed.add_field(
            name=cmd,
            value=desc,
            inline=False
        )
    
    embed.set_footer(text="Entwickelt für Bambu Lab Drucker")
    
    await ctx.send(embed=embed)


@tasks.loop(minutes=1)
async def update_status_task():
    """
    Background Task: Aktualisiert Drucker-Daten regelmäßig
    Optional: Postet Updates in einen bestimmten Channel
    """
    await update_printer_data()
    
    # Optional: Auto-Update in Status Channel
    if STATUS_CHANNEL_ID:
        try:
            channel = bot.get_channel(int(STATUS_CHANNEL_ID))
            if channel and printer_data.get("status") == "printing":
                # Nur Updates während des Druckens
                # Hier könnte man eine Logik implementieren um nur bei bestimmten Änderungen zu posten
                pass
        except Exception as e:
            logger.error(f"Fehler beim Auto-Update: {e}")


@update_status_task.before_loop
async def before_update_status_task():
    """Wartet bis der Bot bereit ist"""
    await bot.wait_until_ready()


def main():
    """Hauptfunktion zum Starten des Bots"""
    if not DISCORD_BOT_TOKEN:
        logger.error("DISCORD_BOT_TOKEN nicht gesetzt!")
        return
    
    logger.info("Starte Bambu Lab Discord Bot...")
    
    try:
        bot.run(DISCORD_BOT_TOKEN)
    except KeyboardInterrupt:
        logger.info("Bot wird beendet...")
    except Exception as e:
        logger.error(f"Fehler beim Starten des Bots: {e}")


if __name__ == "__main__":
    main()
