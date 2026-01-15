import requests
import time
import os
from dotenv import load_dotenv
from openai import OpenAI
import urllib3

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

print("Geladene Server-URLs:")
for url in CRCON_BASE_URLS:
    print(f" - {url}")

HEADERS = {
    "Authorization": f"Bearer {CRCON_TOKEN}",
    "Content-Type": "application/json"
}

VERIFY_SSL = False

KEYWORDS = ["tk", "teamkill", "team kill", "friendly fire", "sorry tk", "tk'ed", "teamkilled"]

COOLDOWN_SECONDS = 60  # Pro Spieler pro Server – verhindert Spam
LOG_LIMIT = 200

CHAT_ENDPOINT = "get_historical_logs"
PM_ENDPOINT = "message_player"

grok_client = OpenAI(api_key=XAI_API_KEY, base_url="https://api.x.ai/v1")

# Pro Server: last_max_id, seen_log_ids, player_cooldowns (dict player_id -> last_time)
server_states = {
    url: {"last_max_id": 0, "seen_log_ids": set(), "player_cooldowns": {}}
    for url in CRCON_BASE_URLS
}

def get_joke():
    """Harmlose, kreative Witze – allgemein über Teamkills, immer positiv-lustig"""
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
        print(f"Grok Fehler: {e}")
        return "In HLL sind Teamkills wie unerwartete Plot-Twists – hält die Runde spannend!"


def get_recent_logs(base_url):
    try:
        payload = {"limit": LOG_LIMIT}
        response = requests.post(
            f"{base_url}{CHAT_ENDPOINT}",
            json=payload,
            headers=HEADERS,
            verify=VERIFY_SSL,
            timeout=10
        )
        if response.status_code == 200:
            return response.json().get("result", [])
        else:
            print(f"Log-Error für {base_url}: {response.status_code}")
    except Exception as e:
        print(f"Exception Logs ({base_url}): {e}")
    return []


def send_private_message(base_url, player_id, player_name, text):
    try:
        payload = {"player_id": player_id, "message": text}
        response = requests.post(
            f"{base_url}{PM_ENDPOINT}",
            json=payload,
            headers=HEADERS,
            verify=VERIFY_SSL,
            timeout=10
        )
        if response.status_code == 200:
            port = base_url.split(":")[-1].split("/")[0]
            print(f"PM an {player_name} ({player_id}) via Port {port} gesendet")
            return True
        else:
            print(f"PM-Fehler via {base_url}: {response.status_code}")
            return False
    except Exception as e:
        print(f"Exception PM ({base_url}): {e}")
        return False


def log_to_discord(server_url, player_name, player_id, original_message, joke):
    if not DISCORD_WEBHOOK_URL:
        return
    try:
        port = server_url.split(":")[-1].split("/")[0]
        log_text = (
            f"**TK-Witz ausgelöst** (Port {port})\n"
            f"Spieler: {player_name} ({player_id})\n"
            f"Nachricht: {original_message}\n"
            f"Witz: {joke}\n"
            f"<t:{int(time.time())}:R>"
        )
        requests.post(DISCORD_WEBHOOK_URL, json={"content": log_text}, timeout=10)
    except Exception as e:
        print(f"Discord Log Fehler: {e}")


print("TK-Witz-Bot gestartet – harmlose Witze bei TK-Chats (kein Spam, Cooldown pro Spieler)!")
while True:
    current_time = time.time()

    for base_url in CRCON_BASE_URLS:
        normalized_url = base_url if base_url.endswith("/") else base_url + "/"

        state = server_states[normalized_url]

        logs = get_recent_logs(normalized_url)
        if not logs:
            continue

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

            player_name = log.get("player1_name") or log.get("player_name") or "Unbekannt"
            player_id = log.get("player1_id") or log.get("player_id")
            if not player_id:
                continue

            message_text = str(log.get("content", "")).lower()

            if any(keyword.lower() in message_text for keyword in KEYWORDS):
                # Cooldown pro Spieler prüfen
                last_time = state["player_cooldowns"].get(player_id, 0)
                if current_time - last_time < COOLDOWN_SECONDS:
                    continue  # Zu früh für diesen Spieler

                joke = get_joke()
                pm_text = f"{joke}\n\ndiscord.gg/gbg-hll"

                success = send_private_message(normalized_url, player_id, player_name, pm_text)
                if success:
                    state["seen_log_ids"].add(log_id)
                    state["player_cooldowns"][player_id] = current_time
                    log_to_discord(normalized_url, player_name, player_id, log.get("content", ""), joke)
                    port = normalized_url.split(":")[-1].split("/")[0]
                    print(f"Harmloser TK-Witz auf Port {port} an {player_name} gesendet")

        # Aufräumen
        if len(state["seen_log_ids"]) > 2000:
            state["seen_log_ids"] = set(list(state["seen_log_ids"])[-1000:])

        time.sleep(2)

    time.sleep(10)