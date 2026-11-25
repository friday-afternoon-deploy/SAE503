-- Mission 1 - Schéma de la base de données
-- Une maison possède plusieurs objets ; un objet possède plusieurs mesures.
-- L'onduleur est enregistré comme un objet de la maison.

CREATE DATABASE IF NOT EXISTS sae503 CHARACTER SET utf8mb4;
USE sae503;

CREATE TABLE IF NOT EXISTS maison (
  id_maison   INT AUTO_INCREMENT PRIMARY KEY,
  nom         VARCHAR(50)  NOT NULL,
  adresse     VARCHAR(255),
  actif       BOOLEAN      NOT NULL DEFAULT 1,       -- 0 = a quitté le groupe
  date_entree DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  date_sortie DATETIME     NULL
);

CREATE TABLE IF NOT EXISTS objet (
  id_objet    INT AUTO_INCREMENT PRIMARY KEY,
  id_maison   INT          NOT NULL,
  identifiant VARCHAR(30)  NOT NULL UNIQUE,          -- utilisé dans MQTT et prises.py
  nom         VARCHAR(50)  NOT NULL,
  type        ENUM('onduleur','esp8266','shelly','meross','emylo') NOT NULL,
  puissance_w INT,
  priorite    INT,                                   -- 1 = allumé en premier
  etat        BOOLEAN      NOT NULL DEFAULT 0,
  actif       BOOLEAN      NOT NULL DEFAULT 1,
  FOREIGN KEY (id_maison) REFERENCES maison(id_maison) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS mesure (
  id_mesure   BIGINT AUTO_INCREMENT PRIMARY KEY,
  id_objet    INT           NOT NULL,
  horodatage  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  type_mesure ENUM('production','consommation','surplus','puissance','etat') NOT NULL,
  valeur      DECIMAL(10,2) NOT NULL,
  FOREIGN KEY (id_objet) REFERENCES objet(id_objet) ON DELETE RESTRICT,
  INDEX idx_objet_date (id_objet, horodatage)
);
