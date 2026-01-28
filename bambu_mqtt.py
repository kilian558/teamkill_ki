"""
MQTT Integration für Bambu Lab Drucker
Nutzt paho-mqtt für Echtzeit-Updates vom Drucker
"""

import json
import logging
import ssl
from typing import Callable, Optional
import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)


class BambuLabMQTT:
    """
    MQTT Client für Bambu Lab Drucker
    Verbindet sich mit dem lokalen MQTT-Broker des Druckers
    """
    
    def __init__(self, printer_ip: str, access_code: str, serial: str):
        """
        Initialisiert MQTT Client
        
        Args:
            printer_ip: IP-Adresse des Druckers im lokalen Netzwerk
            access_code: Access Code vom Drucker (8-stelliger Code)
            serial: Seriennummer des Druckers
        """
        self.printer_ip = printer_ip
        self.access_code = access_code
        self.serial = serial
        self.client = None
        self.connected = False
        self.callback = None
        
        # MQTT Topics
        self.report_topic = f"device/{serial}/report"
        self.request_topic = f"device/{serial}/request"
        
    def set_callback(self, callback: Callable):
        """Setzt Callback-Funktion für Drucker-Updates"""
        self.callback = callback
        
    def on_connect(self, client, userdata, flags, rc):
        """Callback wenn Verbindung hergestellt wurde"""
        if rc == 0:
            logger.info(f"Mit Bambu Lab Drucker verbunden: {self.printer_ip}")
            self.connected = True
            # Subscribe zu Report Topic
            client.subscribe(self.report_topic)
            logger.info(f"Subscribed zu: {self.report_topic}")
            # Request initial status
            self.request_status()
        else:
            logger.error(f"Verbindung fehlgeschlagen mit Code: {rc}")
            self.connected = False
            
    def on_disconnect(self, client, userdata, rc):
        """Callback bei Verbindungsverlust"""
        logger.warning(f"Verbindung zum Drucker verloren: {rc}")
        self.connected = False
        
    def on_message(self, client, userdata, msg):
        """Callback für eingehende Nachrichten"""
        try:
            payload = json.loads(msg.payload.decode())
            logger.debug(f"Nachricht empfangen: {payload.keys()}")
            
            # Parse Drucker-Status
            if "print" in payload:
                print_data = payload["print"]
                status_data = self._parse_print_status(print_data)
                
                # Call callback mit parsed data
                if self.callback:
                    self.callback(status_data)
                    
        except json.JSONDecodeError as e:
            logger.error(f"JSON Parse Fehler: {e}")
        except Exception as e:
            logger.error(f"Fehler beim Verarbeiten der Nachricht: {e}")
            
    def _parse_print_status(self, print_data: dict) -> dict:
        """
        Parsed Drucker-Status aus MQTT Payload
        
        Args:
            print_data: Print-Daten aus MQTT Nachricht
            
        Returns:
            Dictionary mit standardisiertem Status
        """
        # Status Mapping
        status_map = {
            "IDLE": "idle",
            "RUNNING": "printing",
            "PAUSE": "paused",
            "FINISH": "complete",
            "FAILED": "error"
        }
        
        gcode_state = print_data.get("gcode_state", "UNKNOWN")
        status = status_map.get(gcode_state, "unknown")
        
        # Parse alle relevanten Daten
        parsed = {
            "status": status,
            "progress": print_data.get("mc_percent", 0),
            "nozzle_temp": print_data.get("nozzle_temper", 0),
            "bed_temp": print_data.get("bed_temper", 0),
            "target_nozzle_temp": print_data.get("nozzle_target_temper", 0),
            "target_bed_temp": print_data.get("bed_target_temper", 0),
            "layer_num": print_data.get("layer_num", 0),
            "total_layers": print_data.get("total_layer_num", 0),
            "print_time": print_data.get("mc_print_stage", 0),  # in Minuten
            "remaining_time": print_data.get("mc_remaining_time", 0),  # in Minuten
            "filename": print_data.get("subtask_name", "Unbekannt"),
            "speed_level": print_data.get("spd_lvl", 2),  # 1=silent, 2=standard, 3=sport, 4=ludicrous
            "wifi_signal": print_data.get("wifi_signal", ""),
            "chamber_temp": print_data.get("chamber_temper", 0)
        }
        
        return parsed
        
    def connect(self):
        """Stellt Verbindung zum Drucker her"""
        try:
            self.client = mqtt.Client(client_id=f"bambu_discord_{self.serial}")
            
            # Setze Username und Password
            self.client.username_pw_set("bblp", self.access_code)
            
            # Callbacks registrieren
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect
            self.client.on_message = self.on_message
            
            # TLS konfigurieren (Bambu Lab nutzt selbst-signierte Zertifikate)
            self.client.tls_set(cert_reqs=ssl.CERT_NONE)
            self.client.tls_insecure_set(True)
            
            # Verbinde mit Drucker (Port 8883 für MQTT mit TLS)
            logger.info(f"Verbinde mit {self.printer_ip}:8883...")
            self.client.connect(self.printer_ip, 8883, keepalive=60)
            
            # Starte Loop in separatem Thread
            self.client.loop_start()
            
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Verbinden: {e}")
            return False
            
    def disconnect(self):
        """Trennt Verbindung zum Drucker"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
            logger.info("Verbindung zum Drucker getrennt")
            
    def request_status(self):
        """Fordert aktuellen Status vom Drucker an"""
        if not self.connected:
            logger.warning("Nicht verbunden, kann keinen Status anfordern")
            return
            
        try:
            # Pushall Request - fordert kompletten Status an
            request = {
                "pushing": {
                    "sequence_id": "0",
                    "command": "pushall"
                }
            }
            
            payload = json.dumps(request)
            self.client.publish(self.request_topic, payload)
            logger.debug("Status-Request gesendet")
            
        except Exception as e:
            logger.error(f"Fehler beim Senden des Status-Requests: {e}")
            
    def is_connected(self) -> bool:
        """Gibt zurück ob Verbindung besteht"""
        return self.connected
