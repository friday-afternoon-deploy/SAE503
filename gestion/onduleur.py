"""Mission 1 - Lecture de l'onduleur virtuel.

L'onduleur renvoie, pour une heure de la journée (0 à 23), un JSON au format
SolarMAN contenant une liste "dataList" avec notamment :
  - DPi_t1    : Total DC Input Power (production solaire en W)
  - E_Puse_t1 : Total Consumption Power (consommation de la maison en W)
  - PG_Pt1    : Total Grid Power (différence en W : négatif = achat réseau, positif = surplus)
"""

import logging

import requests

URL = "http://digichrone.hd.free.fr/sae503/lecture.php"
DELAI_S = 5

CLES_DATALIST = {
    "production": "DPi_t1",
    "consommation": "E_Puse_t1",
    "surplus": "PG_Pt1",
}


def lire(heure: int) -> dict | None:
    """Renvoie {"production": W, "consommation": W, "surplus": W} ou None si erreur."""
    if not 0 <= heure <= 23:
        raise ValueError("l'heure doit être comprise entre 0 et 23")
    try:
        reponse = requests.get(URL, params={"heure": heure}, timeout=DELAI_S)
        reponse.raise_for_status()
        donnees = reponse.json()
    except (requests.RequestException, ValueError) as e:
        logging.error("Lecture de l'onduleur impossible (heure=%s) : %s", heure, e)
        return None

    data_list = donnees.get("dataList")
    if not isinstance(data_list, list):
        logging.error("Champ dataList absent ou invalide : %s", donnees)
        return None

    valeurs_par_cle = {}
    for item in data_list:
        cle = item.get("key")
        valeur = item.get("value")
        if cle is not None and valeur is not None:
            try:
                valeurs_par_cle[cle] = float(valeur)
            except (TypeError, ValueError):
                pass

    resultat = {
        nom: valeurs_par_cle.get(cle_api)
        for nom, cle_api in CLES_DATALIST.items()
    }

    if resultat["surplus"] is None and None not in (resultat["production"], resultat["consommation"]):
        resultat["surplus"] = resultat["production"] - resultat["consommation"]

    if None in resultat.values():
        logging.error("Champs manquants dans le JSON de l'onduleur : %s", donnees)
        return None

    return resultat


if __name__ == "__main__":
    # Test rapide sur les 24h : python gestion/onduleur.py
    for h in range(24):
        print(f"{h:02d}h ->", lire(h))