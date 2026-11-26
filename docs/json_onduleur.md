
# Format JSON de l'onduleur virtuel (lecture.php)

## Requête
GET http://digichrone.hd.free.fr/sae503/lecture.php?heure=<0..23>

## Exemple de réponse (à 13h)
```json
{
  "code": null,
  "success": true,
  "requestId": "fc38639a0f06e37d",
  "deviceSn": "SM1231456",
  "deviceId": 203142301,
  "deviceType": "INVERTER",
  "deviceState": 1,
  "collectionTime": 1733233241,
  "dataList": [
    {"key": "SN1", "value": "SM123456", "unit": null, "name": "SN"},
    {"key": "SYSTIM1", "value": "24-12-03 13:00:00", "unit": null, "name": "System Time"},
    {"key": "DPi_t1", "value": "1000.00", "unit": "W", "name": "Total DC Input Power"},
    {"key": "PG_Pt1", "value": "400.00", "unit": "W", "name": "Total Grid Power"},
    {"key": "E_Puse_t1", "value": "600.00", "unit": "W", "name": "Total Consumption Power"},
    {"key": "INV_ST1", "value": "Grid connected", "unit": null, "name": "Inverter status"}
  ]
}
```
