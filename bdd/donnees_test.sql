-- Mission 1 - Données de test
-- Puissances et priorités à ajuster selon les appareils branchés pour la démonstration.

USE sae503;

INSERT INTO maison (nom) VALUES ('Maison 1');

INSERT INTO objet (id_maison, identifiant, nom, type, puissance_w, priorite) VALUES
  (1, 'onduleur1', 'Onduleur virtuel',  'onduleur', NULL, NULL),
  (1, 'esp1',      'Chauffe-eau',       'esp8266',  1700, 1),
  (1, 'shelly1',   'Lave-linge',        'shelly',   1500, 2),
  (1, 'shelly2',   'Lave-vaisselle',    'shelly',   1200, 3),
  (1, 'meross1',   'Recharge véhicule', 'meross',   2300, 4),
  (1, 'emylo1',    'Pompe de piscine',  'emylo',     800, 5);
