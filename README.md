<div align="center">

<img src="static/description/icon.jpeg" width="100" alt="RMA Management"/>

# RMA Management

**Professionelle Rückgabeverwaltung mit KI-Klassifizierung und Kundenportal für Odoo**

[![Odoo](https://img.shields.io/badge/Odoo-19.0-875A7B?style=for-the-badge&logo=odoo&logoColor=white)](https://www.odoo.com)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![License](https://img.shields.io/badge/Lizenz-Proprietär-DC143C?style=for-the-badge)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-28A745?style=for-the-badge)]()

> **Proprietäre Software – ausschließlich für MSV Systemhaus Martin Schlaak GmbH**

</div>

---

## Inhaltsverzeichnis

- [Was ist RMA Management?](#was-ist-rma-management)
- [Funktionsübersicht](#funktionsübersicht)
- [Installation](#installation)
- [Konfiguration](#konfiguration)
- [Benutzerhandbuch](#benutzerhandbuch)
  - [Kundenportal](#kundenportal)
  - [Phase 1 – RMA erstellen](#phase-1--rma-erstellen)
  - [Phase 2 – Mengenprüfung](#phase-2--mengenprüfung)
  - [Phase 3 – Seriennummern prüfen](#phase-3--seriennummern-prüfen-optional)
  - [Phase 4 – Folgebelege](#phase-4--folgebelege-verarbeiten)
- [KI-Klassifizierung](#ki-klassifizierung)
- [Warenklassen](#warenklassen--a--b--c-ware)
- [Reparaturaufträge](#reparaturaufträge-b-ware)
- [Rückgabefristen](#rückgabefristen)
- [Auswertung](#auswertung)
- [Audit-Log](#audit-log)
- [Berechtigungen](#berechtigungen)
- [Technische Referenz](#technische-referenz)

---

## Was ist RMA Management?

Das **RMA Management Modul** steuert den vollständigen Rückgabeprozess – von der Kundenanfrage über das Kundenportal, den Wareneingang und die qualitätsbasierte Klassifizierung bis zur automatischen Weiterverarbeitung. Es ist direkt in Odoos Lager-, Verkaufs- und Reparaturmodul integriert.

```
Kunde → Portal /rma/anfrage    ODER    Mitarbeiter direkt
              │                                │
              ▼                                │
    Portal-Anfrage im Backend                  │
    Genehmigen → E-Mail an Kunde               │
              │                                │
              └──────────────┬─────────────────┘
                             ▼
                    RMA-Erstellung
                  (Referenz auswählen)
                             │
                             ▼
                       RMA-Eingang
                    (Lagerbeleg auto.)
                             │
                             ▼
              ┌──────────────────────────────┐
              │         Mengenprüfung         │
              │  A-Ware │ B-Ware │ C-Ware    │
              └──────────────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
          Hauptlager    Reparatur-      Schrottlager
                         auftrag
```

---

## Funktionsübersicht

### Kernfunktionen

| Funktion | Beschreibung |
|---|---|
| Kundenportal | Öffentliche Seite `/rma/anfrage` — Verifizierung per E-Mail + Rechnungsnummer |
| RMA-Erstellung | Aus Verkaufsauftrag oder genehmigter Portal-Anfrage |
| Mengenprüfung | A/B/C-Klassifizierung mit automatischen Folgebelegen |
| KI-Klassifizierung | Produktfoto hochladen → KI schlägt A/B/C-Ware vor |
| Seriennummernverfolgung | Q-Klasse pro Seriennummer, Barcode-Scanner |
| Reparaturaufträge | B-Ware erzeugt automatisch `repair.order` |
| Rückgabefristkontrolle | Pro Kunde konfigurierbar, Bestätigungsdialog bei Überschreitung |
| Auswertung | Filtern nach Kunde, Artikel, Q-Klasse, Prozentanteile |
| Audit-Trail | Vollständiges Protokoll aller RMA-Ereignisse |

---

## Installation

```bash
# 1. Repository in das Addons-Verzeichnis klonen
cd /pfad/zu/odoo/custom-addons
git clone https://github.com/LascheSz/rma_management.git

# 2. Odoo neu starten mit Modul-Update
python odoo-bin -c odoo.conf -d <datenbank> -u rma_management

# 3. In Odoo: Apps → "RMA Management" suchen → Installieren
```

**Abhängigkeiten:** `sale_management`, `stock`, `repair`, `portal`, `account`, `mail`

Das Modul legt beim ersten Start automatisch alle benötigten Lagerorte und Vorgangsarten an.

---

## Konfiguration

**Wo:** Lager → Konfiguration → Einstellungen → RMA Management

### Lagerorte

| Lagerort | Zweck | Standard |
|----------|-------|----------|
| RMA-Eingangslager | Wo die zurückgesendete Ware ankommt | `WH/Bestand/RMA` |
| Prüflager (B-Ware) | Lager für prüfbedürftige Ware | `WH/Bestand/RMA-Prüflager B-Ware` |
| C-Ware / Schrottlager | Lager für defekte, unverkäufliche Ware | `RMA-Schrottlager` |

Felder leer lassen → automatisch erzeugte Standardlagerorte werden verwendet.

### Vorgangsarten

| Feld | Standard |
|------|---------|
| RMA-Eingang | `msv Systemhaus: RMA-Eingang` |
| B-Ware Transfer | `msv Systemhaus: RMA-Prüflager B-Ware` |
| C-Ware / Schrott | `msv Systemhaus: RMA Schrottlager C-Ware` |

### Weitere Einstellungen

| Einstellung | Beschreibung | Standard |
|-------------|-------------|---------|
| RMA Rückgabefrist (Tage) | Standardfrist für alle Kunden | 14 Tage |
| RMA Seriennummern | Aktiviert Seriennummernauswahl und Q-Klassen-Prüfung | Aktiv |

Individuelle Fristen pro Kunde: Kontakt → Rückgabefrist

### KI-API-Schlüssel

Unter Einstellungen → Technisch → Parameter → Systemparameter:

| Parameter | Beschreibung |
|-----------|-------------|
| `ai.openai_key` | OpenAI API-Key (bevorzugt, Modell: gpt-4o) |
| `ai.google_key` | Google API-Key als Fallback (Modell: gemini-2.5-flash) |

---

## Benutzerhandbuch

### Kundenportal

Kunden können unter **`/rma/anfrage`** eigenständig eine Rückgabe beantragen — ohne Odoo-Login.

**Ablauf für den Kunden:**

```
1. URL aufrufen: /rma/anfrage
2. E-Mail-Adresse + Rechnungsnummer eingeben
3. System prüft die Verifizierung
4. Artikel und Rückgabemengen auswählen + Grund angeben
5. Absenden → Bestätigungsseite
```

**Ablauf im Backend (Mitarbeiter):**

```
Portal-Anfragen → Anfrage öffnen
    │
    ├── Positionen und gewünschte Mengen prüfen
    ├── "Genehmigen & E-Mail senden"
    │       └── Kunde erhält E-Mail mit Rücksendeadresse und Anfrage-Nr.
    │
    └── Nach Wareneingang: In RMA-Erstellung die Anfrage als Referenz auswählen
            └── Mengen werden automatisch vorbelegt (anpassbar)
```

---

### Phase 1 – RMA erstellen

**Wo:** RMA Management → Erstellung — oder — Verkauf → Auftrag → "RMA erstellen"

```
1. Referenz auswählen
   └── Kombinierte Liste: Portal-Anfragen [Anfrage] und Verkaufsaufträge [Auftrag]
   └── Bei Portal-Anfrage: Verkaufsauftrag, Grund und Mengen werden automatisch vorbelegt

2. Rückgabegrund prüfen / anpassen

3. Rückgabemengen pro Artikel eintragen
   └── Nur Mengen ≤ bereits gelieferter Menge möglich
   └── Bei Portal-Anfrage: vorbelegt aus Kundenangabe, jederzeit anpassbar

4. Optional: Seriennummern auswählen (bei serialisierten Artikeln)
   └── Barcode-Button je Zeile anklicken oder Scanner verwenden

5. "Lieferschein erstellen" klicken
   └── RMA-Eingangsbeleg wird angelegt
   └── Portal-Anfrage wechselt auf Status "In Bearbeitung"
```

> **Rückgabefrist überschritten?** Ein Bestätigungsdialog erscheint — der Beleg kann trotzdem erstellt werden.

---

### Phase 2 – Mengenprüfung

**Wo:** RMA Management → Mengenprüfung

```
1. RMA-Eingang auswählen

2. Optional: KI-Klassifizierung nutzen
   └── Kamera-Icon je Zeile → Foto hochladen → KI schlägt A/B/C vor → Übernehmen

3. Optional: Prüffotos hochladen
   └── Werden automatisch an alle Folgebelege angehängt

4. Mengen auf A/B/C aufteilen
   └── Summe A + B + C muss = Erwartete Menge

5. "Durchführen" klicken
   └── Folgebelege werden automatisch erzeugt
   └── B-Ware: Reparaturaufträge werden automatisch angelegt
   └── RMA-Eingang wird automatisch validiert
```

---

### Phase 3 – Seriennummern prüfen (optional)

Wenn Artikel Seriennummern haben und die Option aktiviert ist:

```
1. Barcode-Button in der Zeile anklicken

2. Jeder Seriennummer eine Qualitätsklasse zuweisen
   SN-001 → A-Ware
   SN-002 → B-Ware
   SN-003 → C-Ware

3. "Übernehmen" klicken
   └── Mengen werden automatisch in A/B/C übertragen
   └── Seriennummern werden in die Folgebelege übertragen
```

Die Q-Klasse ist auf jedem Lagerbeleg in der Registerkarte "RMA Prüfung" sichtbar.

---

### Phase 4 – Folgebelege verarbeiten

Nach der Mengenprüfung entstehen automatisch bis zu drei Folgebelege:

| Klasse | Beleg | Ziel |
|--------|-------|------|
| A-Ware | Wareneingang | Direkt zurück ins Hauptlager |
| B-Ware | Interne Umbuchung + Reparaturauftrag | Prüflager + repair.order |
| C-Ware | Interne Umbuchung | Schrottlager |

Prüffotos und Seriennummern sind bereits an den Folgebelegen angehängt.

---

## KI-Klassifizierung

Der KI-Inspektor ist in der Mengenprüfung je Zeile per Kamera-Icon erreichbar.

**Ablauf:**

```
1. Kamera-Icon in der Prüfposition anklicken
2. Produktfoto hochladen
3. Optional: Hinweise an die KI eingeben ("Verpackung beschädigt, Gerät ok")
4. "Klassifizieren" klicken
   └── KI analysiert das Bild
   └── Ergebnis: A-Ware / B-Ware / C-Ware mit Begründung
5. "Vorschlag übernehmen" klicken
   └── Q-Klasse wird auf die Prüfposition übertragen
```

**API-Priorität:** OpenAI (`gpt-4o`) → Google (`gemini-2.5-flash`)

---

## Warenklassen – A / B / C-Ware

| Klasse | Zustand | Lagerort | Nächster Schritt |
|--------|---------|----------|-----------------|
| A-Ware | Neuwertig, kein Mangel | Hauptlager | Direkt wieder verkaufen |
| B-Ware | Gebraucht, leichte Mängel | Prüflager | Reparaturauftrag → Entscheidung |
| C-Ware | Defekt, nicht verkaufsfähig | Schrottlager | Entsorgen oder Teile verwerten |

---

## Reparaturaufträge (B-Ware)

B-Ware erzeugt nach der Mengenprüfung automatisch `repair.order`-Einträge im Reparaturmodul:

- **Seriennummernpflichtige Artikel:** Ein Reparaturauftrag pro Seriennummer
- **Mengenware:** Ein Reparaturauftrag mit der gesamten B-Ware-Menge

Die Reparaturaufträge sind am RMA-Eingangsbeleg über den Smart-Button "Reparaturen" sichtbar.

---

## Rückgabefristen

```
Priorität:
  1. Individuelle Frist am Kundenstamm  (Kontakt → Rückgabefrist)
  2. Standard aus den RMA-Einstellungen (Standard: 14 Tage)
```

Ist die Frist abgelaufen, erscheint beim Erstellen ein Bestätigungsdialog. Der Beleg kann trotzdem erstellt werden — die Entscheidung liegt beim Mitarbeiter. Das Ereignis wird im Audit-Log protokolliert.

---

## Auswertung

**Wo:** RMA Management → Auswertung

Filterbar nach:

- Kunde
- Artikel
- Q-Klasse (Nur A-Ware / Nur B-Ware / Nur C-Ware / Gemischt)
- Datum

Jeder Eintrag zeigt Prozentanteile (A/B/C) und die dominante Qualitätsklasse. Gruppierung nach Kunde, Artikel oder Q-Klasse möglich.

---

## Audit-Log

**Wo:** RMA Management → Übersicht → Audit-Log

| Ereignis | Wann |
|----------|------|
| RMA-Eingang erstellt | Beim Erstellen des RMA-Belegs |
| Fristüberschreitung bestätigt | Nach Bestätigungsdialog |
| Mengenprüfung abgeschlossen | Nach "Durchführen" |

Jeder Eintrag enthält Datum, Benutzer, verknüpfte Belege und Mengendetails. Zusätzlich wird jeder Eintrag in den Chatter der betroffenen Belege und Verkaufsaufträge geschrieben.

---

## Berechtigungen

### RMA Benutzer

- RMA-Aufträge erstellen und bearbeiten
- Mengenprüfung durchführen
- Seriennummern-Qualitätsklassen vergeben
- KI-Klassifizierung nutzen
- Portal-Anfragen bearbeiten und genehmigen
- Prüffotos hochladen
- Audit-Log lesen

### RMA Manager

- Alle Rechte des RMA Benutzers
- Rückgabegründe anlegen und bearbeiten
- RMA-Einstellungen konfigurieren
- Audit-Log-Einträge bearbeiten

Benutzerrechte vergeben: Einstellungen → Benutzer → [Benutzer wählen] → RMA Management

---

## Technische Referenz

### Datenmodelle

| Modell | Typ | Beschreibung |
|--------|-----|-------------|
| `rma.reason` | Model | Rückgabegründe (Stammdaten) |
| `rma.order` | TransientModel | Wizard: RMA-Erstellung |
| `rma.order.line` | TransientModel | Positionen der RMA-Erstellung |
| `rma.splitting` | TransientModel | Wizard: Mengenprüfung |
| `rma.splitting.line` | TransientModel | Prüfpositionen (A/B/C) |
| `rma.splitting.serial.line` | TransientModel | Seriennummern-Q-Klassen |
| `rma.ai.inspector` | TransientModel | KI-Klassifizierungs-Wizard |
| `rma.portal.request` | Model | Kunden-Portal-Anfrage |
| `rma.portal.request.line` | Model | Positionen der Portal-Anfrage |
| `rma.ref.proxy` | Model (SQL-View) | Union-View: Portal-Anfragen + Verkaufsaufträge |
| `rma.analytics` | Model | Auswertungseinträge |
| `rma.audit.log` | Model | Audit-Trail |
| `rma.stock.configuration` | AbstractModel | Lager-Konfigurationsservice |
| `rma.deadline.confirmation` | TransientModel | Fristüberschreitungs-Dialog |

### Erweiterungen auf Odoo-Standardmodellen

| Modell | Erweiterung |
|--------|------------|
| `stock.picking` | RMA-Status, Grund, Anhänge, Q-Klassen-Übersicht, Reparatur-Smart-Button |
| `stock.move.line` | `rma_quality_class` – Q-Klasse pro Seriennummer |
| `res.partner` | `rma_return_deadline_days` – Individuelle Rückgabefrist |
| `sale.order` | RMA-Eingang-Flag, Smart-Button, Aktion "RMA erstellen" |

### Öffentliche Routen

| Route | Methode | Beschreibung |
|-------|---------|-------------|
| `/rma/anfrage` | GET | Einstiegsseite Portal (E-Mail + Rechnungsnummer) |
| `/rma/anfrage/verify` | POST | Verifizierung — prüft E-Mail gegen Rechnung |
| `/rma/anfrage/submit` | POST | Anfrage absenden — erzeugt `rma.portal.request` |

### Automatisch angelegte Konfiguration

Beim ersten Start erzeugt das Modul automatisch:

```
Lagerorte:
  WH/Bestand/RMA                    (Eingangsort)
  WH/Bestand/RMA-Prüflager B-Ware  (B-Ware Prüflager)
  RMA-Schrottlager                  (C-Ware / Schrott)

Vorgangsarten:
  msv Systemhaus: RMA-Eingang
  msv Systemhaus: RMA-Prüflager B-Ware
  msv Systemhaus: RMA Schrottlager C-Ware

Sequenz:
  RMA/P/00001  (Portal-Anfragen)
```

---

## Lizenz

**PROPRIETÄRE SOFTWARE**

Dieses Modul ist Eigentum der MSV Systemhaus Martin Schlaak GmbH.

- Erlaubt: Nutzung durch MSV Systemhaus Martin Schlaak GmbH und autorisierte Partner
- Verboten: Weitergabe, Veröffentlichung, kommerzielle Nutzung ohne Genehmigung, Reverse Engineering

**© 2026 MSV Systemhaus Martin Schlaak GmbH – Alle Rechte vorbehalten**

---

<div align="center">

[info@msv-systemhaus.de](mailto:info@msv-systemhaus.de) · [msv-systemhaus.de](https://msv-systemhaus.de) · [Issues](https://github.com/LascheSz/rma_management/issues)

`Version 1.0` · `Odoo 19` · `Stand: Juni 2026`

</div>
