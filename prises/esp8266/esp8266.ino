// Mission 2 - ESP8266 : prise simulée pilotée en MQTT
// Bibliothèque nécessaire (Arduino IDE) : PubSubClient (Nick O'Leary)
// Carte : « NodeMCU 1.0 (ESP-12E Module) » ou équivalent
//
// Topics (identifiant esp1, maison maison1) :
//   maison1/esp1/set    <- ON / OFF        (ordre reçu)
//   maison1/esp1/etat   -> ON / OFF        (retenu)
//   maison1/esp1/conso  -> puissance en W  (retenu)
//   maison1/esp1/dispo  -> online / offline (retenu, message de dernière volonté)

#include <ESP8266WiFi.h>
#include <PubSubClient.h>

// ---- À compléter (ne pas envoyer les vrais mots de passe sur GitHub) ----
const char* WIFI_SSID     = "a_remplacer";
const char* WIFI_PASSWORD = "a_remplacer";
const char* MQTT_HOST     = "192.168.50.10";   // adresse du Raspberry Pi
const int   MQTT_PORT     = 1883;
const char* MQTT_USER     = "esp1";
const char* MQTT_PASSWORD = "a_remplacer";
// --------------------------------------------------------------------------

const char* TOPIC_SET   = "maison1/esp1/set";
const char* TOPIC_ETAT  = "maison1/esp1/etat";
const char* TOPIC_CONSO = "maison1/esp1/conso";
const char* TOPIC_DISPO = "maison1/esp1/dispo";

const int   BROCHE_SORTIE = LED_BUILTIN;   // remplacer par la broche du relais
const bool  SORTIE_INVERSEE = true;        // la LED intégrée s'allume à l'état bas
const int   PUISSANCE_SIMULEE_W = 1700;    // chauffe-eau simulé
const unsigned long PERIODE_CONSO_MS = 30000;

WiFiClient wifi;
PubSubClient mqtt(wifi);
bool allume = false;
unsigned long dernierEnvoi = 0;

void appliquerSortie() {
  digitalWrite(BROCHE_SORTIE, (allume != SORTIE_INVERSEE) ? HIGH : LOW);
}

void publierEtat() {
  mqtt.publish(TOPIC_ETAT, allume ? "ON" : "OFF", true);
  String conso = String(allume ? PUISSANCE_SIMULEE_W : 0);
  mqtt.publish(TOPIC_CONSO, conso.c_str(), true);
  dernierEnvoi = millis();
}

void recevoir(char* topic, byte* payload, unsigned int longueur) {
  String message;
  for (unsigned int i = 0; i < longueur; i++) message += (char)payload[i];
  message.trim();
  if (message == "ON")  allume = true;
  else if (message == "OFF") allume = false;
  else return;
  appliquerSortie();
  publierEtat();
  Serial.println("Ordre reçu : " + message);
}

void connecterWifi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connexion Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println(" OK, IP : " + WiFi.localIP().toString());
}

void connecterMqtt() {
  while (!mqtt.connected()) {
    Serial.print("Connexion MQTT...");
    // Message de dernière volonté : "offline" publié par le broker si l'ESP disparaît
    if (mqtt.connect("esp1", MQTT_USER, MQTT_PASSWORD, TOPIC_DISPO, 1, true, "offline")) {
      Serial.println(" OK");
      mqtt.publish(TOPIC_DISPO, "online", true);
      mqtt.subscribe(TOPIC_SET, 1);
      publierEtat();
    } else {
      Serial.print(" échec, code ");
      Serial.println(mqtt.state());
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(BROCHE_SORTIE, OUTPUT);
  appliquerSortie();
  connecterWifi();
  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  mqtt.setCallback(recevoir);
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) connecterWifi();
  if (!mqtt.connected()) connecterMqtt();
  mqtt.loop();
  if (millis() - dernierEnvoi > PERIODE_CONSO_MS) publierEtat();
}
