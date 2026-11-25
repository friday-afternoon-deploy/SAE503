"""Mission 1 - Prises simulées, avec exactement la même interface que prises/prises.py.

Permet de tester la logique sans matériel : PRISES_FACTICES=1 dans le fichier .env.
"""

PUISSANCES_W = {"esp1": 1700, "shelly1": 1500, "shelly2": 1200, "meross1": 2300, "emylo1": 800}
_etats: dict[str, bool] = {}


def allumer(identifiant: str) -> bool:
    _etats[identifiant] = True
    print(f"[factice] {identifiant} allumée")
    return True


def eteindre(identifiant: str) -> bool:
    _etats[identifiant] = False
    print(f"[factice] {identifiant} éteinte")
    return True


def lire_etat(identifiant: str) -> bool | None:
    return _etats.get(identifiant, False)


def lire_conso(identifiant: str) -> float | None:
    return float(PUISSANCES_W.get(identifiant, 0)) if lire_etat(identifiant) else 0.0
