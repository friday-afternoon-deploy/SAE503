# """Mission 1 - Boucle principale du script de gestion.

#À chaque cycle :
#  1. lecture de l'onduleur virtuel ;
#  2. enregistrement de la production, de la consommation et du surplus en base ;
#  3. décision : quelles prises allumer ou éteindre ;
#  4. envoi des ordres aux prises et enregistrement de leur état et de leur consommation.

#Fonctionnement normal : un cycle toutes les 15 minutes, avec l'heure réelle.
#Mode démo (MODE_DEMO=1) : rejoue les 24 heures de la journée, une heure toutes les 10 s.
#"""

import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv

RACINE = Path(__file__).resolve().parent.parent
load_dotenv(RACINE / ".env")
sys.path.insert(0, str(RACINE))

import onduleur  # noqa: E402
import decision  # noqa: E402

if os.getenv("PRISES_FACTICES", "1") == "1":
    import prises_factices as prises  # noqa: E402
else:
    from prises import prises  # noqa: E402

PERIODE_S = 15 * 60
PERIODE_DEMO_S = 10
MAISON = os.getenv("MAISON", "maison1")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def connexion():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        database=os.getenv("DB_NAME", "sae503"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


def charger_objets(bdd) -> list[dict]:
    """Objets actifs des maisons actives."""
    curseur = bdd.cursor(dictionary=True)
    curseur.execute(
        """SELECT o.id_objet, o.identifiant, o.type, o.puissance_w, o.priorite, o.etat
           FROM objet o JOIN maison m ON m.id_maison = o.id_maison
           WHERE o.actif = 1 AND m.actif = 1"""
    )
    objets = curseur.fetchall()
    curseur.close()
    return objets


def enregistrer_mesure(bdd, id_objet: int, type_mesure: str, valeur: float):
    curseur = bdd.cursor()
    curseur.execute(
        "INSERT INTO mesure (id_objet, type_mesure, valeur) VALUES (%s, %s, %s)",
        (id_objet, type_mesure, valeur),
    )
    curseur.close()


def enregistrer_etat(bdd, id_objet: int, etat: bool):
    curseur = bdd.cursor()
    curseur.execute("UPDATE objet SET etat = %s WHERE id_objet = %s", (int(etat), id_objet))
    curseur.close()


def cycle(bdd, heure: int):
    objets = charger_objets(bdd)
    onduleurs = [o for o in objets if o["type"] == "onduleur"]
    prises_pilotees = [o for o in objets if o["type"] != "onduleur"]
    if not onduleurs:
        logging.error("Aucun onduleur actif en base")
        return

    lecture = onduleur.lire(heure)
    if lecture is None:
        return
    logging.info("Heure %02d h : %s", heure, lecture)
    for type_mesure, valeur in lecture.items():
        enregistrer_mesure(bdd, onduleurs[0]["id_objet"], type_mesure, valeur)

    for identifiant, action in decision.decider(lecture["surplus"], prises_pilotees):
        ok = prises.allumer(identifiant) if action == "allumer" else prises.eteindre(identifiant)
        if not ok:
            logging.warning("%s : action %s échouée", identifiant, action)

    for objet in prises_pilotees:
        etat = prises.lire_etat(objet["identifiant"])
        conso = prises.lire_conso(objet["identifiant"])
        if etat is not None:
            enregistrer_etat(bdd, objet["id_objet"], etat)
            enregistrer_mesure(bdd, objet["id_objet"], "etat", int(etat))
        if conso is not None:
            enregistrer_mesure(bdd, objet["id_objet"], "puissance", conso)

    bdd.commit()


def main():
    mode_demo = os.getenv("MODE_DEMO", "0") == "1"
    bdd = connexion()
    heure_demo = 0
    try:
        while True:
            heure = heure_demo if mode_demo else datetime.now().hour
            try:
                cycle(bdd, heure)
            except mysql.connector.Error as e:
                logging.error("Erreur base de données : %s", e)
                bdd = connexion()
            heure_demo = (heure_demo + 1) % 24
            time.sleep(PERIODE_DEMO_S if mode_demo else PERIODE_S)
    except KeyboardInterrupt:
        logging.info("Arrêt du script")
    finally:
        bdd.close()


if __name__ == "__main__":
    main()
