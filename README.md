# Origin
⚠️ This is an unofficial third-party integration for JUDO devices. It is not affiliated with or endorsed by JUDO Wasseraufbereitung GmbH.

This integration was originally developed through the excellent work of  https://github.com/OStrama/judo_rest_api.git. Many thanks to his work.

The code was heavily modified, extended and adapted to the JUDO ZEWA/PROM i-Safe by tach2004.

# JUDO ZEWA iSafe Rest API
Home Assistant integration to connect to Judo Zewa/Prom iSafe directly via REST API based on this documentation:<br>
https://judo.eu/ftp-upload/download/REST-API/RESTAPI_Kommandos.pdf <br>
Some more basic info can be found here:<br>
https://judo.eu/app/uploads/2026/02/MANUAL_1702574_202601.pdf

Please have a look here to learn more about the communication module that provides the REST API:<br>
https://judo.eu/produkte/connectivity-modul-wlan/

# JUDO ZEWA iSafe Rest API

This integration lets you monitor and control your Judo Zewa/Prom iSafe device locally through it's REST API.

![grafik](https://github.com/user-attachments/assets/9b70ea88-d02d-42bf-9441-4e0b09b5cb4c)

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

<img width="432" height="720" alt="grafik" src="https://github.com/user-attachments/assets/798d7145-c189-4359-9026-8220213f8cfc" />


The only mandatory parameters are:
* The IP-Address of your Judo water treatment device. The port should be ok at default (80) unless you changed it in the configuration of the connectivity module.
* The user name. The default value of the connectivity module is "admin". You can change it on the web interface of the connectivity module
* The password. The default value of the connectivity module is "Connectivity". You can change it on the web interface of the connectivity module

The "Device Postfix" has a default value of "". It can be used to add multiple devices to one home assistant. For compatibility this should be left empty. If you want to add another device, use a name that helps to identify the devices.

### ⏱️ Poll intervals

Four intervals can be configured, **all of them in seconds** (10 minutes = `600`).
They can be changed at any time via *Settings → Devices & Services → Judo → Reconfigure*.

| Field | Default | What it covers |
|---|---|---|
| **API poll interval** | `60` | The base cycle. Everything without its own interval is read here — most importantly the total water meter (`2800`), which feeds the water flow calculation. |
| **Leakage protection status** | `60` | The 32 bit status word `6900` (valve state, leak, all diagnostic entities). |
| **Settings & operating status** | `600` | Absence limits (`5E00`), learning mode (`6400`), microleakage setting (`6500`), leakage settings + holiday mode (`6800`). These rarely change. |
| **Judo clock** | `300` | `5900`, used only to compare the device clock against Home Assistant. |

A few notes:

* The three extra intervals are **not** multiples of the base cycle — they are real
  times. An address is read again once its interval has elapsed, checked at the start
  of every cycle. Setting a value lower than the base cycle simply means "every cycle".
* A failed read does **not** restart the timer, so it is retried on the next cycle.
* Right after you change a setting from Home Assistant, everything is read once more so
  the device confirms the new value immediately, instead of the UI showing an unverified
  value until the interval expires.
* Too small values will cause more timeouts. The JUDO answers one request at a time.

### ⚙️ Initial Setup

Nothing to do. All settings are read back from the device.

> **Exception: firmware without command `6800`** (see the firmware note below). There the four
> leakage settings cannot be read, so they need the one-time initialisation known from 1.2.x:
> set *Holiday Mode Write* and the three *Leakage Protection* values **once each**, in any order.
> Command `5000` writes all four together, so the first attempts report
> *"Erwartet 4 Werte, aber n erhalten"* and are not sent — each one is remembered, and the last
> one goes through. Run all four; stopping halfway leaves Home Assistant showing values the
> device has not received. The values are kept in `/config/judo_storage.json`.

> **⬆️ Upgrading from 1.2.x or earlier?**
>
> Older versions could not read the leakage protection settings back from the JUDO, so
> *Leakage Protection: Max Water Flow Rate / Max Water Flow / Max Water Flow Time* and
> *Holiday Mode Write* had to be initialised by hand once and were then stored inside
> Home Assistant. A change made directly on the device was never noticed.
>
> This is no longer necessary. Command `6800` ("read leakage settings") is now used, so these
> four values — including the holiday mode — are read straight from the device on every poll.
> The manual initialisation step is gone.
>
> Your existing `/config/judo_storage.json` may still contain the four keys. On a device that
> answers `6800` they are simply ignored; you can leave the file alone. On older firmware they are
> still in use — see *Initial Setup* above.

---

## 🆕 What this integration reads and controls

> **Firmware note.** The leakage protection status (`6900`), reading the leakage settings (`6800`)
> and acknowledging the learning mode (`6B00`) are reliably available from **connectivity module
> firmware 3.52 and device Firmware 1.39 (visible in the integration -> device info)** onwards. From version **2.0.1** the integration detects on its own whether the
> device supports these commands — on older firmware the affected entities are simply not created,
> and no errors or repeated warnings occur.
> 
### Leakage protection status (diagnostics)

The 32 bit status word (command `6900`) is decoded into **19 entities**, all filed under
**Diagnostics** on the device page:

| Entity | Type | Notes |
|---|---|---|
| Valve state | Sensor | opening / closing / open / closed |
| Microleakage check | Sensor | message and close / message only / check not possible / no microleakage detected |
| Leakage | Binary sensor | shown as a *problem* |
| Water quantity / flow / withdrawal time exceeded | Binary sensor | shown as a *problem* |
| Learning mode: quantity / flow / time exceeded | Binary sensor | shown as a *problem* |
| No water flow within 15 days | Binary sensor | shown as a *problem* |
| Homing, closed manually or U3, holiday mode, sleep mode | Binary sensor | |
| Learning mode finished / active, special rule mode active | Binary sensor | |
| Closed via LS input, sleep mode via LS input | Binary sensor | |

The microleakage result is **latched** by the device: it keeps reporting the outcome of the
last check until a new check produces a different result.

### Acknowledge learning mode

A single select entity (command `6B`) with three options:

* **Idle (no action)** — resting position, never sent to the device
* **Accept determined limits** — sends `6B0001`
* **Discard determined limits** — sends `6B0000`

After sending, the select jumps back to *Idle* on its own, so the same action can be triggered
again next time.

---

## 🔄 Polling behaviour

### ⚠️ The device handles only one request at a time

The connectivity module of the JUDO processes REST requests **strictly one after another**.
Sending several at once does not speed anything up — it slows the device down and, past a
certain point, makes it drop requests entirely.

Measured on a ZEWA/PROM i-SAFE, one full poll of 13 values:

| Requests in parallel | Result |
|---|---|
| **1 (sequential)** | **2.20 s — stable, recommended** |
| 2 | 2.19 s — no gain |
| 4 | 3.17 s — *slower*, occasional stalls of 0.3–1.0 s |
| unlimited | 7–10 s **and connection errors / lost values** |

`MAX_PARALLEL_REQUESTS` in `restobject.py` controls how many requests may run at once.
The number is set by `MAX_PARALLEL_REQUESTS` at the top of `restobject.py` and ships as
**`1`**. 
The tested and recommended value for this device is `1` — higher values measurably slowed the
device down and eventually made it drop requests. It brings no benefit on this hardware, so there is no
reason to change it. 

Instead of parallelising, the integration keeps the *number* of requests small:

* Addresses read by several entities (e.g. `6900` feeds 19 entities) are fetched **once per cycle**.
* Values that never change (device type, serial number, firmware version, installation date)
  are read **once at start-up**.
* `operating days` is read once per day; settings and status use their own intervals
  (see [Poll intervals](#️-poll-intervals) above).

### ⚠️ While the JUDO is busy, nothing can be read at all

Some operations block the REST API completely for as long as they run:

* **opening or closing the ball valve** — roughly 10 seconds
* **microleakage check**

During that time the device still answers with HTTP 200, but the payload is **empty**
(`data: ""`). No value can be read — not even one unrelated to the running operation.

This is normal device behaviour, not a fault, and the integration handles it: the affected
entities keep their last value, the event is logged at debug level only, and no warnings
are produced.

One consequence worth knowing: the valve states *opening* and *closing* are in practice
almost never visible. By the time the device answers again, the valve has already reached
its end position, so the entity goes straight from **open** to **closed** or back.

---

***One more thing:***

Earlier versions of this README said that JUDO does not expose the leakage protection status
over the API — whether the valve is open or closed, whether a leak was detected, and so on.
**That is no longer the case** for the ZEWA/PROM i-SAFE: command `6900` returns a bit coded
status word, and this integration decodes all 25 documented bits (see the table above).

Not everything is solved yet. The sleep mode duration still cannot be read back reliably:
command `66` returns a constant value on this device regardless of what was written, so the
duration is still stored inside Home Assistant. If you find a way to read it properly, please
open an issue.

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
