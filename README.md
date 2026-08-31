# Origin
⚠️ This is an unofficial third-party integration for JUDO devices. It is not affiliated with or endorsed by JUDO Wasseraufbereitung GmbH.

This integration was originally developed through the excellent work of  https://github.com/OStrama/judo_rest_api.git. Many thanks to his work.

The code was heavily modified, extended and adapted to the JUDO ZEWA/PROM i-Safe by tach2004.

# JUDO ZEWA iSafe Rest API
Home Assistant integration to connect to Judo Zewa/Prom iSafe directly via REST API based on this documentation:


https://judo.eu/ftp-upload/download/REST-API/RESTAPI_Kommandos.pdf
Some more basic info can be found here: https://judo.eu/app/uploads/2026/02/MANUAL_1702574_202601.pdf

Please have a look here to learn more about the communication module that provides the REST API:

https://judo.eu/produkte/connectivity-modul-wlan/

# JUDO ZEWA iSafe Rest API

This integration lets you monitor and control your Judo Zewa/Prom iSafe device locally through it's REST API.
![grafik](https://github.com/user-attachments/assets/a066a64c-d652-4c3f-bb40-f2dfc74238bc)

---

## Installation

### HACS (manually add Repository)

Add this repository to HACS.
* In the HACS GUI, select "Custom repositories"
* Enter the following repository URL: https://github.com/tach2004/JUDO-ZEWA-iSafe-Rest-API
* Category: Integration
* Now search in hacs for JUDO ZEWA iSafe Rest API, click on it and press the button at the bottom right “download”
* After adding the integration, restart Home Assistant.
* Now press the button "Add Integration" in Configuration -> Integrations to install it in Home assistant.
* Now under Configuration -> Integrations, "JUDO ZEWA iSafe Rest API" should be available.

### Manual install

Create a directory called `judo_rest_api` in the `<config directory>/custom_components/` directory on your Home Assistant
instance. Install this component by copying all files in `/custom_components/judo_rest_api/` folder from this repo into the
new `<config directory>/custom_components/judo_rest_api/` directory you just created.

This is how your custom_components directory should look like:

```bash
custom_components
├── judo_rest_api
│   ├── __init__.py
│   ├── ...
│   ├── ...
│   ├── ...
│   └── sensor.py  
```

---

## Configuration
![image](https://github.com/user-attachments/assets/36f25cdd-d969-4b80-bdf8-bdedd86e57ad)


The only mandatory parameters are:
* The IP-Address of your Judo water treatment device. The port should be ok at default (80) unless you changed it in the configuration of the connectivity module.
* The user name. The default value of the connectivity module is "admin". You can change it on the web interface of the connectivity module
* The password. The default value of the connectivity module is "Connectivity". You can change it on the web interface of the connectivity module

The "Device Postfix" has a default value of "". It can be used to add multiple devices to one home assistant. For compatibility this should be left empty. If you want to add another device, use a name that helps to identify the devices.
The "Scan interval" determines how often the REST API is polled. The default value is every 60 seconds. Too small values will cause more timeouts.

### ⚙️ Initial Setup: Setting Required Select Entities:

After the integration is configured and loaded for the first time, you must **manually initialize four specific select entities** by setting each one to a desired value once via the Home Assistant UI.

These are:

1. **Leakage Protection: Max Water Flow Rate**  
2. **Leakage Protection: Max Water Flow**  
3. **Leakage Protection: Max Water Flow Time**  
4. **Holiday Mode Write**

This step is required because the JUDO API expects all four values to be sent together as part of a **combined hex payload**. Unfortunately, these specific values **cannot be read back** from the JUDO system via the API.

That means:
- Home Assistant **cannot retrieve their current state** from the device.
- The values are stored **persistently within homeassistant**.
- You only need to perform this setup **once**, unless you reset or remove the integration.

---

***One more thing:***
I'm sure several people are wondering why, for example, the leakage protection is not displayed whether it is open or closed, or why no warning messages are displayed via HA in the event of a leak or anything else. Unfortunately, these and other status/messages etc. are not provided by Judo via the API. This is a great pity because it is technically feasible without any problems! I hope that this will be updated by Judo in the future!

---

# ❗️ Disclaimer

🇬🇧 English:

⚠️ Disclaimer and Legal Notice

This Home Assistant integration for JUDO devices is an independent, community-driven project. It is not affiliated with, endorsed by, or developed in cooperation with JUDO Wasseraufbereitung GmbH.

The integration is based solely on publicly available information and reverse engineering. It is provided as-is, and the use is at your own risk and responsibility.
The developers do not guarantee functionality, compatibility, or safety and are not liable for any direct or indirect damages resulting from the use of this integration.

This integration is provided free of charge and as an open-source project. It does not offer official support or services on behalf of JUDO. 

🚨All trademarks, product names, logos, and images are the property of their respective owners and are used here for identification purposes only. 
The use of these names, trademarks and brands appearing in these image files, do not imply endorsement
If any rights holder objects to the use of their assets, we will promptly remove or replace the affected material upon request.🚨

#  

🇩🇪 Deutsch:

⚠️ Haftungsausschluss und rechtlicher Hinweis

Diese Home Assistant-Integration für JUDO-Geräte ist ein unabhängiges, community-getriebenes Projekt. Sie steht in keiner Verbindung zur JUDO Wasseraufbereitung GmbH, 
wurde nicht von JUDO beauftragt oder unterstützt und basiert ausschließlich auf öffentlich zugänglichen Informationen sowie eigener Analyse

Die Nutzung dieser Integration erfolgt auf eigenes Risiko und in eigener Verantwortung. Es besteht keine Gewähr für Funktion, Sicherheit oder Kompatibilität mit Geräten von JUDO. Für etwaige Schäden oder Funktionsstörungen, die durch die Nutzung dieser Integration entstehen, wird keine Haftung übernommen.

Die Integration wird kostenlos und als Open-Source-Projekt bereitgestellt. Sie dient ausschließlich privaten, nicht-kommerziellen Zwecken.
Es wird kein offizieller Support oder Service im Namen von JUDO angeboten

🚨Alle verwendeten Marken, Produktnamen, Logos und Grafiken sind Eigentum der jeweiligen Rechteinhaber und dienen ausschließlich der identifikatorischen Darstellung. 
Die Verwendung dieser Namen, Marken und Markenzeichen in diesen Bilddateien impliziert keine Unterstützung oder Empfehlung durch die Markeninhaber
Sollte ein Rechteinhaber Einwände gegen die Verwendung haben, wird das betroffene Material auf Anfrage umgehend entfernt oder ersetzt.🚨

#

see: https://github.com/home-assistant/brands
