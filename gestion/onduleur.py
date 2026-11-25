"""Mission 1 - Lecture de l'onduleur virtuel.

L'onduleur renvoie, pour une heure de la journée (0 à 23), un JSON contenant
la production, la consommation et la différence entre les deux.
Différence négative : on achète au réseau. Positive : surplus injecté.
"""

import logging

import requests

URL = "http://digichrone.hd.free.fr/sae503/lecture.php"
DELAI_S = 5

# À COMPLÉTER une fois le JSON récupéré (voir docs/) : noms exacts des champs.
# En attendant, la fonction cherche un champ contenant ces mots-clés.
CHAMPS = {
    "production": ["prod"],
    "consommation": ["conso"],
    "surplus": ["diff", "surplus", "ecart"],
}


def _trouver(donnees: dict, mots_cles: list[str]):
    for cle, valeur in donnees.items():
        if any(mot in cle.lower() for mot in mots_cles):
            return float(valeur)
    return None


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

    resultat = {nom: _trouver(donnees, mots) for nom, mots in CHAMPS.items()}
    if resultat["surplus"] is None and None not in (resultat["production"], resultat["consommation"]):
        resultat["surplus"] = resultat["production"] - resultat["consommation"]
    if None in resultat.values():
        logging.error("Format JSON inattendu : %s", donnees)
        return None
    return resultat


if __name__ == "__main__":
    # Test rapide : python gestion/onduleur.py
    for h in (0, 10, 13, 19):
        print(h, lire(h))
