/*
  SAE 503 - Mission 2 : ESP8266 = prise connectée simulée (MQTT)

  Topics (contrat du groupe), avec MAISON="maison1" et OBJET="esp1" :
    maison1/esp1/set    <- ON / OFF          (reçu, QoS 1)
    maison1/esp1/etat   -> ON / OFF          (publié, retenu)
    maison1/esp1/conso  -> puissance en W    (publié toutes les 30 s et à chaque changement)
    maison1/esp1/dispo  -> online / offline  (retenu ; "offline" = dernière volonté du broker)

  La LED de la carte représente la prise (sur NodeMCU/Wemos, la LED est allumée quand la broche est à LOW).
  Bibliothèque : PubSubClient (Nick O'Leary).
*/
#include <ESP8266WiFi.h>
#include <PubSubClient.h>

// ---------------------------------------------------------------- à adapter
const char* WIFI_SSID = "SAE-GR3IOM";
const char* WIFI_PASS = "A_REMPLACER";      // NE JAMAIS envoyer le vrai mot de passe sur GitHub
const char* MQTT_HOST = "192.168.50.136";   // IP du broker (le Pi). Sert à tes tests ; l'IP finale sera confirmée à l'intégration
const uint16_t MQTT_PORT = 1883;
const char* MQTT_USER = "gestion";                 // vide pour le broker de test ; sera rempli avec le compte de la Mission 3
const char* MQTT_PASS = "mqtt";

const char* MAISON = "maison1";
const char* OBJET  = "esp1";
const int PUISSANCE_W = 1700;               // puissance de l'appareil simulé (chauffe-eau) quand la prise est ON
const unsigned long PERIODE_CONSO_MS = 30000;
// ----------------------------------------------------------------

char tSet[48], tEtat[48], tConso[48], tDispo[48];
WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);
bool allume = false;
unsigned long dernierConso = 0;

void appliquer(bool on) {
  allume = on;
  digitalWrite(LED_BUILTIN, on ? LOW : HIGH);   // LED allumée = prise ON
}

void publierEtat() {
  mqtt.publish(tEtat, allume ? "ON" : "OFF", true);   // true = message retenu
}

void publierConso() {
  char buf[12];
  snprintf(buf, sizeof(buf), "%d", allume ? PUISSANCE_W : 0);
  mqtt.publish(tConso, buf);
  dernierConso = millis();
}

void onMessage(char* topic, byte* payload, unsigned int len) {
  String msg;
  for (unsigned int i = 0; i < len; i++) msg += (char)payload[i];
  msg.trim();
  msg.toUpperCase();
  Serial.printf("Message reçu sur %s : %s\n", topic, msg.c_str());
  if (msg == "ON") appliquer(true);
  else if (msg == "OFF") appliquer(false);
  else return;                                  // message inconnu : on ignore
  publierEtat();
  publierConso();
}

void connecterWifi() {
  Serial.printf("Connexion au Wi-Fi %s ", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) { delay(500); Serial.print("."); }
  Serial.printf("\nWi-Fi OK, IP = %s\n", WiFi.localIP().toString().c_str());
}

void connecterMqtt() {
  while (!mqtt.connected()) {
    String id = String("esp-") + OBJET + "-" + String(ESP.getChipId(), HEX);
    Serial.printf("Connexion MQTT à %s ... ", MQTT_HOST);
    bool ok;
    if (strlen(MQTT_USER) > 0)
      ok = mqtt.connect(id.c_str(), MQTT_USER, MQTT_PASS, tDispo, 1, true, "offline");  // dernière volonté
    else
      ok = mqtt.connect(id.c_str(), NULL, NULL, tDispo, 1, true, "offline");
    if (ok) {
      Serial.println("OK");
      mqtt.subscribe(tSet, 1);                  // QoS 1 pour les ordres
      mqtt.publish(tDispo, "online", true);
      publierEtat();
      publierConso();
    } else {
      Serial.printf("échec (code %d), nouvel essai dans 3 s\n", mqtt.state());
      delay(3000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(LED_BUILTIN, OUTPUT);
  appliquer(false);                             // au démarrage : prise éteinte

  snprintf(tSet,   sizeof(tSet),   "%s/%s/set",   MAISON, OBJET);
  snprintf(tEtat,  sizeof(tEtat),  "%s/%s/etat",  MAISON, OBJET);
  snprintf(tConso, sizeof(tConso), "%s/%s/conso", MAISON, OBJET);
  snprintf(tDispo, sizeof(tDispo), "%s/%s/dispo", MAISON, OBJET);

  connecterWifi();
  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  mqtt.setCallback(onMessage);
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) connecterWifi();
  if (!mqtt.connected()) connecterMqtt();
  mqtt.loop();
  if (millis() - dernierConso >= PERIODE_CONSO_MS) publierConso();
}
