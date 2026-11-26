#"""Mission 2 - Pilotage des prises connectées.

#Interface commune (ne pas modifier sans prévenir la mission 1) :
#    allumer(identifiant)    -> bool
#    eteindre(identifiant)   -> bool
#    lire_etat(identifiant)  -> bool | None
#    lire_conso(identifiant) -> float | None   (en watts)

#Règles : aucune exception ne sort de ces fonctions ; en cas d'erreur, on écrit dans
#le journal et on renvoie False ou None. Délai maximal de 5 s par appel.
#"""

import logging
import os

import requests
from paho.mqtt import publish, subscribe

DELAI_S = 5
MAISON = os.getenv("MAISON", "maison1")
MQTT = {
    "hostname": os.getenv("MQTT_HOST", "localhost"),
    "port": int(os.getenv("MQTT_PORT", "1883")),
    "auth": {"username": os.getenv("MQTT_USER"), "password": os.getenv("MQTT_PASSWORD")},
}

# Correspondance identifiant -> matériel. Adresses IP à compléter.
PRISES = {
    "esp1":    {"type": "mqtt"},
    "shelly1": {"type": "shelly", "ip": "192.168.50.11", "canal": 0},
    "shelly2": {"type": "shelly", "ip": "192.168.50.11", "canal": 1},
    # Meross et eMylo passent par Node-RED (mission 3), qui fait la passerelle
    # entre MQTT et leur cloud : on les pilote donc en MQTT, comme l'ESP8266.
    "meross1": {"type": "mqtt"},
    "emylo1":  {"type": "mqtt"},
}


# ---------- interface commune -------------------------------------------------

def allumer(identifiant: str) -> bool:
    return _commander(identifiant, True)


def eteindre(identifiant: str) -> bool:
    return _commander(identifiant, False)


def lire_etat(identifiant: str) -> bool | None:
    try:
        prise = PRISES[identifiant]
        if prise["type"] == "mqtt":
            return _esp_lire(identifiant, "etat") == "ON"
        if prise["type"] == "shelly":
            return bool(_shelly_statut(prise)["output"])
        raise NotImplementedError(prise["type"])
    except Exception as e:
        logging.error("Lecture de l'état de %s impossible : %s", identifiant, e)
        return None


def lire_conso(identifiant: str) -> float | None:
    try:
        prise = PRISES[identifiant]
        if prise["type"] == "mqtt":
            return float(_esp_lire(identifiant, "conso"))
        if prise["type"] == "shelly":
            return float(_shelly_statut(prise)["apower"])
        raise NotImplementedError(prise["type"])
    except Exception as e:
        logging.error("Lecture de la consommation de %s impossible : %s", identifiant, e)
        return None


def _commander(identifiant: str, allume: bool) -> bool:
    try:
        prise = PRISES[identifiant]
        if prise["type"] == "mqtt":
            publish.single(f"{MAISON}/{identifiant}/set", "ON" if allume else "OFF", qos=1, **MQTT)
        elif prise["type"] == "shelly":
            _shelly_commander(prise, allume)
        else:
            raise NotImplementedError(prise["type"])
        return True
    except Exception as e:
        logging.error("Commande de %s impossible : %s", identifiant, e)
        return False


# ---------- Prises MQTT : ESP8266, et Meross / eMylo via Node-RED ---------------

def _esp_lire(identifiant: str, sujet: str) -> str:
    # Les topics etat et conso doivent être publiés avec retain (par l'ESP ou par
    # Node-RED), sinon cette lecture attend le prochain message.
    message = subscribe.simple(f"{MAISON}/{identifiant}/{sujet}", **MQTT)
    return message.payload.decode()


# ---------- Shelly (HTTP local) -----------------------------------------------
# À VÉRIFIER : ces adresses correspondent à l'API Gen2 (/rpc/...).
# Pour une Shelly Gen1 : http://IP/relay/0?turn=on et http://IP/status

def _shelly_commander(prise: dict, allume: bool):
    url = f"http://{prise['ip']}/rpc/Switch.Set"
    params = {"id": prise["canal"], "on": "true" if allume else "false"}
    requests.get(url, params=params, timeout=DELAI_S).raise_for_status()


def _shelly_statut(prise: dict) -> dict:
    url = f"http://{prise['ip']}/rpc/Switch.GetStatus"
    reponse = requests.get(url, params={"id": prise["canal"]}, timeout=DELAI_S)
    reponse.raise_for_status()
    return reponse.json()


# ---------- Meross (cloud) et eMylo (Tuya) ------------------------------------
# Pilotés par les flux Node-RED de la mission 3, qui traduisent :
#   maison1/<identifiant>/set  (ON / OFF)  -> commande vers le cloud de la prise
#   état et consommation de la prise       -> maison1/<identifiant>/etat et /conso (retain)
