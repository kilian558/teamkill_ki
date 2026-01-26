import requests
import time
import os
import logging
import signal
import sys
from urllib.parse import urlparse
from collections import deque
from dotenv import load_dotenv
from openai import OpenAI
import urllib3

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

base_urls_env = os.getenv("CRCON_BASE_URLS")
if base_urls_env:
    CRCON_BASE_URLS = [url.strip() for url in base_urls_env.split(",") if url.strip()]
else:
    single_url = os.getenv("CRCON_BASE_URL")
    if single_url:
        CRCON_BASE_URLS = [single_url.strip()]
    else:
        raise ValueError("Weder CRCON_BASE_URLS noch CRCON_BASE_URL in .env definiert!")

CRCON_TOKEN = os.getenv("CRCON_TOKEN")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
XAI_API_KEY = os.getenv("XAI_API_KEY")

if not all([CRCON_BASE_URLS, CRCON_TOKEN, DISCORD_WEBHOOK_URL, XAI_API_KEY]):
    raise ValueError("Eine oder mehrere Variablen in .env fehlen!")

logger.info("Geladene Server-URLs:")
for url in CRCON_BASE_URLS:
    logger.info(f" - {url}")

HEADERS = {
    "Authorization": f"Bearer {CRCON_TOKEN}",
    "Content-Type": "application/json"
}

VERIFY_SSL = False

# Configuration constants
KEYWORDS = ["tk", "teamkill", "team kill", "friendly fire", "sorry tk", "tk'ed", "teamkilled"]
COOLDOWN_SECONDS = 60  # Pro Spieler pro Server – verhindert Spam
LOG_LIMIT = 200
REQUEST_TIMEOUT = 10  # Timeout for API requests in seconds
SEEN_LOG_IDS_MAX = 2000  # Maximum seen log IDs (deque maxlen)
SLEEP_BETWEEN_SERVERS = 2  # Sleep between server checks in seconds
SLEEP_BETWEEN_CYCLES = 10  # Sleep between full cycles in seconds

# API Endpoints
CHAT_ENDPOINT = "get_historical_logs"
PM_ENDPOINT = "message_player"

grok_client = OpenAI(api_key=XAI_API_KEY, base_url="https://api.x.ai/v1")

# Create a persistent session for connection pooling
session = requests.Session()

def cleanup_resources():
    """Clean up resources on shutdown."""
    logger.info("Shutting down bot, closing connections...")
    session.close()
    sys.exit(0)

# Register signal handlers for graceful shutdown
signal.signal(signal.SIGINT, lambda sig, frame: cleanup_resources())
signal.signal(signal.SIGTERM, lambda sig, frame: cleanup_resources())

def normalize_url(url):
    """Normalize URL by ensuring it ends with a slash."""
    return url if url.endswith("/") else url + "/"

def get_port_from_url(url):
    """Extract port from URL for display purposes."""
    parsed = urlparse(url)
    if parsed.port:
        return str(parsed.port)
    # Return default port based on scheme
    return "443" if parsed.scheme == "https" else "80"

# Normalize URLs at startup
CRCON_BASE_URLS = [normalize_url(url) for url in CRCON_BASE_URLS]

# Pro Server: last_max_id, seen_log_ids (deque), player_cooldowns (dict player_id -> last_time)
server_states = {
    url: {"last_max_id": 0, "seen_log_ids": deque(maxlen=SEEN_LOG_IDS_MAX), "player_cooldowns": {}}
    for url in CRCON_BASE_URLS
}

def get_joke():
    """
    Generate a harmless, creative joke about teamkills using AI.
    
    Returns:
        str: A friendly joke about teamkills in Hell Let Loose.
    """
    try:
        response = grok_client.chat.completions.create(
            model="grok-3",
            messages=[
                {"role": "system", "content": "Du bist ein freundlicher, lustiger Bot für die Hell Let Loose-Community. Mach einen kurzen, harmlosen Witz über Teamkills im Spiel – allgemein, positiv, gamer-mäßig, kreativ und variabel. Nie persönlich, nie 'du', nie sarkastisch oder beleidigend. Nur leichter Humor, wie ein netter Squad-Mate. 1-2 Sätze."},
                {"role": "user", "content": "Ein neuer, harmloser Witz über Teamkills in HLL."}
            ],
            max_tokens=80,
            temperature=1.0
        )
        joke = response.choices[0].message.content.strip()
        return joke or "Teamkills in HLL passieren jedem mal – das macht das Spiel so authentisch und spannend!"
    except Exception as e:
        logger.error(f"Grok API Fehler: {e}")
        return "In HLL sind Teamkills wie unerwartete Plot-Twists – hält die Runde spannend!"


def get_recent_logs(base_url):
    """
    Fetch recent chat logs from the server.
    
    Args:
        base_url (str): The base URL of the CRCON server.
        
    Returns:
        list: List of log entries, empty list on error.
    """
    try:
        payload = {"limit": LOG_LIMIT}
        response = session.post(
            f"{base_url}{CHAT_ENDPOINT}",
            json=payload,
            headers=HEADERS,
            verify=VERIFY_SSL,
            timeout=REQUEST_TIMEOUT
        )
        if response.status_code == 200:
            return response.json().get("result", [])
        else:
            logger.warning(f"Log-Error für {base_url}: HTTP {response.status_code}")
    except requests.exceptions.Timeout:
        logger.error(f"Timeout beim Abrufen der Logs von {base_url}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Netzwerkfehler beim Abrufen der Logs von {base_url}: {e}")
    except Exception as e:
        logger.error(f"Unerwarteter Fehler beim Abrufen der Logs von {base_url}: {e}")
    return []


def send_private_message(base_url, player_id, player_name, text):
    """
    Send a private message to a player.
    
    Args:
        base_url (str): The base URL of the CRCON server.
        player_id (str): The player's ID.
        player_name (str): The player's name.
        text (str): The message text to send.
        
    Returns:
        bool: True if message was sent successfully, False otherwise.
    """
    try:
        payload = {"player_id": player_id, "message": text}
        response = session.post(
            f"{base_url}{PM_ENDPOINT}",
            json=payload,
            headers=HEADERS,
            verify=VERIFY_SSL,
            timeout=REQUEST_TIMEOUT
        )
        if response.status_code == 200:
            port = get_port_from_url(base_url)
            logger.info(f"PM an {player_name} ({player_id}) via Port {port} gesendet")
            return True
        else:
            logger.warning(f"PM-Fehler via {base_url}: HTTP {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        logger.error(f"Timeout beim Senden der PM an {player_name} via {base_url}")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Netzwerkfehler beim Senden der PM via {base_url}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unerwarteter Fehler beim Senden der PM via {base_url}: {e}")
        return False


def log_to_discord(server_url, player_name, player_id, original_message, joke):
    """
    Log the teamkill joke event to Discord webhook.
    
    Args:
        server_url (str): The server URL where the event occurred.
        player_name (str): The player's name.
        player_id (str): The player's ID.
        original_message (str): The original chat message.
        joke (str): The joke that was sent.
    """
    if not DISCORD_WEBHOOK_URL:
        return
    try:
        port = get_port_from_url(server_url)
        log_text = (
            f"**TK-Witz ausgelöst** (Port {port})\n"
            f"Spieler: {player_name} ({player_id})\n"
            f"Nachricht: {original_message}\n"
            f"Witz: {joke}\n"
            f"<t:{int(time.time())}:R>"
        )
        session.post(DISCORD_WEBHOOK_URL, json={"content": log_text}, timeout=REQUEST_TIMEOUT)
    except requests.exceptions.Timeout:
        logger.error("Timeout beim Senden an Discord Webhook")
    except requests.exceptions.RequestException as e:
        logger.error(f"Netzwerkfehler beim Discord Logging: {e}")
    except Exception as e:
        logger.error(f"Unerwarteter Fehler beim Discord Logging: {e}")


def process_server_logs(base_url, state, current_time):
    """
    Process logs for a single server and send jokes when appropriate.
    
    Args:
        base_url (str): The server's base URL.
        state (dict): The server's state dictionary.
        current_time (float): The current timestamp.
    """
    logs = get_recent_logs(base_url)
    if not logs:
        return

    new_logs = [log for log in logs if log.get("id", 0) > state["last_max_id"]]

    if new_logs:
        state["last_max_id"] = max(log.get("id", 0) for log in logs)

    for log in reversed(new_logs):
        log_id = log.get("id")
        if log_id in state["seen_log_ids"]:
            continue

        log_type = log.get("type", "")
        if "CHAT" not in log_type:
            continue

        # Validate message content early to fail fast
        message_text = str(log.get("content", "")).lower().strip()
        if not message_text:
            continue

        player_name = log.get("player1_name") or log.get("player_name") or "Unbekannt"
        player_id = log.get("player1_id") or log.get("player_id")
        if not player_id:
            continue

        if any(keyword.lower() in message_text for keyword in KEYWORDS):
            # Cooldown pro Spieler prüfen
            last_time = state["player_cooldowns"].get(player_id, 0)
            if current_time - last_time < COOLDOWN_SECONDS:
                continue  # Zu früh für diesen Spieler

            joke = get_joke()
            pm_text = f"{joke}\n\ndiscord.gg/gbg-hll"

            success = send_private_message(base_url, player_id, player_name, pm_text)
            if success:
                state["seen_log_ids"].append(log_id)
                state["player_cooldowns"][player_id] = current_time
                log_to_discord(base_url, player_name, player_id, log.get("content", ""), joke)
                port = get_port_from_url(base_url)
                logger.info(f"Harmloser TK-Witz auf Port {port} an {player_name} gesendet")


def main():
    """Main loop that monitors servers and sends teamkill jokes."""
    logger.info("TK-Witz-Bot gestartet – harmlose Witze bei TK-Chats (kein Spam, Cooldown pro Spieler)!")
    logger.info(f"Überwachte Server: {len(CRCON_BASE_URLS)}")
    
    while True:
        current_time = time.time()

        for base_url in CRCON_BASE_URLS:
            state = server_states[base_url]
            process_server_logs(base_url, state, current_time)
            time.sleep(SLEEP_BETWEEN_SERVERS)

        time.sleep(SLEEP_BETWEEN_CYCLES)


if __name__ == "__main__":
    main()