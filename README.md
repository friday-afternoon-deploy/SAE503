# SAE 503 - Groupe 3 (parcours IOM)

Système de pilotage de la consommation électrique en fonction de la production solaire.
Toutes les 15 minutes, le script de gestion lit la production de l'onduleur, enregistre
les mesures en base et allume ou coupe les prises connectées pour consommer le surplus.

## Répartition

| Mission | Dossiers | Branche |
|---|---|---|
| 1 - Données et logique de décision | `bdd/`, `gestion/` | `mission1Semi` |
| 2 - Objets connectés | `prises/` | `mission2Aminata` |
| 3 - Infrastructure, Node-RED, supervision et sécurité | `docker-compose.yml`, `infra/` | `mission3Veronica` |

## Arborescence

```
SAE503/
├── README.md
├── .gitignore
├── .env.exemple            modèle du fichier .env (à copier en .env)
├── requirements.txt        bibliothèques Python
├── docker-compose.yml      MariaDB, Mosquitto, Grafana, Node-RED
├── bdd/
│   ├── schema.sql          création des tables
│   └── donnees_test.sql    maison et objets de test
├── gestion/
│   ├── main.py             boucle principale (toutes les 15 min, ou mode démo)
│   ├── onduleur.py         lecture de l'onduleur virtuel
│   ├── decision.py         règles de mise en marche et d'arrêt
│   └── prises_factices.py  prises simulées pour les tests
├── prises/
│   ├── prises.py           pilotage des vraies prises
│   └── esp8266/esp8266.ino programme de l'ESP8266
├── infra/
│   ├── mosquitto/mosquitto.conf
│   └── grafana/
└── docs/                   études, schémas, exemples JSON
```

## Services (Raspberry Pi, adresse 192.168.50.10)

| Service | Port | Rôle |
|---|---|---|
| MariaDB | 3306 | Base de données (maison, objet, mesure) |
| Mosquitto | 1883 | Broker MQTT |
| Grafana | 3000 | Supervision |
| Node-RED | 1880 | Passerelle MQTT vers les prises cloud (Meross, eMylo) |
| phpMyAdmin | 8080 | Interface web d'administration de la base MariaDB |


## Installation

1. Copier `.env.exemple` en `.env` et remplir les mots de passe.
2. Lancer les services : `docker compose up -d`
   (la base est créée automatiquement à partir de `bdd/`).
3. Installer les bibliothèques Python : `pip install -r requirements.txt`
4. Lancer le script de gestion : `python gestion/main.py`
   - `MODE_DEMO=1` dans `.env` rejoue une journée de 24 h en 4 minutes ;
   - `PRISES_FACTICES=1` utilise les prises simulées au lieu des vraies.

## Règles de travail

- Une branche par mission ; `main` ne contient que du code testé.
- Chacun modifie le dossier de sa mission. Prévenir les autres avant de modifier
  un fichier commun (`bdd/schema.sql`, `docker-compose.yml`, `.env.exemple`).
- `git pull` avant de commencer, commits réguliers avec un message clair.
- Le fichier `.env` n'est jamais envoyé sur GitHub.
