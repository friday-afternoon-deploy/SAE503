#"""Mission 1 - Règles de mise en marche et d'arrêt des prises.

#Principe : le surplus de production est un « budget » de puissance.
#On parcourt les appareils par ordre de priorité (1 = le plus prioritaire) et on
#allume chaque appareil dont la puissance tient encore dans le budget restant.
#Les autres sont éteints.

#Hypothèse à valider : la consommation renvoyée par l'onduleur virtuel ne tient pas
#compte des appareils pilotés (l'onduleur est simulé). Le budget est donc le surplus
#de l'onduleur, sans y ajouter la puissance des appareils déjà allumés.
#Si on passe un jour sur un vrai onduleur, il faudra ajouter cette puissance au surplus.
#"""

MARGE_W = 100  # marge de sécurité pour éviter d'acheter au réseau


def decider(surplus_w: float, objets: list[dict]) -> list[tuple[str, str]]:
    """Renvoie la liste des actions à effectuer.

    objets : liste de dict avec les clés identifiant, puissance_w, priorite, etat.
    Résultat : liste de (identifiant, "allumer" ou "eteindre"), uniquement pour
    les prises dont l'état doit changer.
    """
    budget = surplus_w - MARGE_W
    actions = []
    pilotables = [o for o in objets if o.get("priorite") is not None and o.get("puissance_w")]
    for objet in sorted(pilotables, key=lambda o: o["priorite"]):
        doit_etre_allume = objet["puissance_w"] <= budget
        if doit_etre_allume:
            budget -= objet["puissance_w"]
        if doit_etre_allume and not objet["etat"]:
            actions.append((objet["identifiant"], "allumer"))
        elif not doit_etre_allume and objet["etat"]:
            actions.append((objet["identifiant"], "eteindre"))
    return actions


if __name__ == "__main__":
    # Test rapide : python gestion/decision.py
    appareils = [
        {"identifiant": "esp1", "puissance_w": 1700, "priorite": 1, "etat": False},
        {"identifiant": "shelly1", "puissance_w": 1500, "priorite": 2, "etat": False},
        {"identifiant": "shelly2", "puissance_w": 1200, "priorite": 3, "etat": True},
        {"identifiant": "meross1", "puissance_w": 2300, "priorite": 4, "etat": True},
    ]
    for surplus in (-500, 0, 1000, 2000, 3500, 7000):
        print(f"surplus {surplus:>5} W ->", decider(surplus, appareils))
