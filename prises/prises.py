"""Mission 2 - Pilotage des prises connectées.

Interface commune (ne pas modifier sans prévenir la mission 1) :
    allumer(identifiant)    -> bool
    eteindre(identifiant)   -> bool
    lire_etat(identifiant)  -> bool | None
    lire_conso(identifiant) -> float | None   (en watts)

Règles : aucune exception ne sort de ces fonctions ; en cas d'erreur, on écrit dans
le journal et on renvoie False ou None. Délai maximal de 5 s par appel.
"""

import logging
import os

import requests
from paho.mqtt import publish, subscribe

DELAI_S = 5
DELAI_MEROSS_S = 10  # le cloud Meross est plus lent : connexion + découverte avant la commande
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
    # Meross : piloté directement en Python (bibliothèque meross-iot, cloud Meross).
    # "nom_appli" = nom de la prise dans l'application Meross.
    "meross1": {"type": "meross", "nom_appli": "prises meross"},
    # eMylo (Tuya) : passe par Node-RED (mission 3), qui fait la passerelle
    # entre MQTT et le cloud : on le pilote donc en MQTT, comme l'ESP8266.
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
        if prise["type"] == "meross":
            return bool(_meross(prise, "etat"))
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
        if prise["type"] == "meross":
            return float(_meross(prise, "conso"))
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
        elif prise["type"] == "meross":
            _meross(prise, "on" if allume else "off")
        else:
            raise NotImplementedError(prise["type"])
        return True
    except Exception as e:
        logging.error("Commande de %s impossible : %s", identifiant, e)
        return False


# ---------- Prises MQTT : ESP8266, et eMylo via Node-RED -----------------------

def _esp_lire(identifiant: str, sujet: str) -> str:
    # Les topics etat et conso doivent être publiés avec retain (par l'ESP ou par
    # Node-RED), sinon cette lecture attend le prochain message.
    message = subscribe.simple(f"{MAISON}/{identifiant}/{sujet}", **MQTT)
    return message.payload.decode()


# ---------- Shelly (HTTP local) -----------------------------------------------
# Shelly Pro 4PM, génération 2 (vérifié) : API /rpc/...
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


# ---------- Meross MSS310 (cloud, bibliothèque meross-iot) --------------------
# Identifiants lus dans les variables d'environnement MEROSS_EMAIL et MEROSS_PASSWORD
# (fichier .env, jamais dans le code). La bibliothèque est asynchrone : on l'enveloppe
# dans asyncio.run() pour garder des fonctions simples. Chaque appel se reconnecte
# au cloud (quelques secondes).

async def _meross_async(prise: dict, action: str):
    from meross_iot.http_api import MerossHttpClient
    from meross_iot.manager import MerossManager

    http = await MerossHttpClient.async_from_user_password(
        api_base_url=os.getenv("MEROSS_API", "https://iot.meross.com"),
        email=os.environ["MEROSS_EMAIL"], password=os.environ["MEROSS_PASSWORD"])
    manager = MerossManager(http_client=http)
    try:
        await manager.async_init()
        await manager.async_device_discovery()
        nom = prise["nom_appli"].lower()
        dev = next((d for d in manager.find_devices() if d.name.lower() == nom), None)
        if dev is None:
            raise LookupError(f"Prise Meross '{prise['nom_appli']}' introuvable sur le compte")
        await dev.async_update()
        if action == "on":
            await dev.async_turn_on(channel=0)
        elif action == "off":
            await dev.async_turn_off(channel=0)
        elif action == "etat":
            return dev.is_on(channel=0)
        elif action == "conso":
            return (await dev.async_get_instant_metrics(channel=0)).power  # en W
        else:
            raise ValueError(action)
    finally:
        manager.close()
        await http.async_logout()


def _meross(prise: dict, action: str):
    """action : 'on', 'off', 'etat' ou 'conso'."""
    import asyncio
    return asyncio.run(asyncio.wait_for(_meross_async(prise, action), timeout=DELAI_MEROSS_S))
