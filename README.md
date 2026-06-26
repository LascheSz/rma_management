<div align="center">

<img src="static/description/icon.jpeg" width="100" alt="RMA Management"/>

# RMA Management

**Professionelle Rückgabeverwaltung mit automatischer Warenklassifizierung für Odoo**

[![Odoo](https://img.shields.io/badge/Odoo-19.0-875A7B?style=for-the-badge&logo=odoo&logoColor=white)](https://www.odoo.com)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![License](https://img.shields.io/badge/Lizenz-Proprietär-DC143C?style=for-the-badge)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-28A745?style=for-the-badge)]()

> ⚠️ **Proprietäre Software – ausschließlich für MSV Systemhaus Martin Schlaak GmbH**

</div>

---

## 📖 Inhaltsverzeichnis

- [Was ist RMA Management?](#-was-ist-rma-management)
- [Funktionsübersicht](#-funktionsübersicht)
- [Installation](#-installation)
- [Konfiguration](#️-konfiguration)
- [Benutzerhandbuch](#-benutzerhandbuch)
  - [Phase 1 – RMA erstellen](#phase-1️⃣--rma-erstellen)
  - [Phase 2 – Mengenprüfung](#phase-2️⃣--mengenprüfung)
  - [Phase 3 – Seriennummern prüfen](#phase-3️⃣--seriennummern-prüfen-optional)
  - [Phase 4 – Folgebelege](#phase-4️⃣--folgebelege-verarbeiten)
- [Warenklassen](#-warenklassen-a--b--c-ware)
- [Seriennummern & Qualitätsklassen](#-seriennummern--qualitätsklassen)
- [Rückgabefristen](#-rückgabefristen)
- [Audit-Log](#-audit-log)
- [Berechtigungen](#-berechtigungen)
- [Technische Referenz](#️-technische-referenz)

---

## 🎯 Was ist RMA Management?

Das **RMA Management Modul** steuert den vollständigen Rückgabeprozess – von der Rückgabeanfrage über den Wareneingang bis zur qualitätsbasierten Einlagerung. Es ist direkt in Odoos Lager- und Verkaufsmodul integriert und erfordert keine Parallelführung in externen Systemen.

```
Kunde möchte zurückgeben
        │
        ▼
  ┌─────────────┐
  │ RMA erstellen│  ← aus dem Verkaufsauftrag heraus
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │ RMA-Eingang │  ← Lagerbeleg wird automatisch angelegt
  └──────┬──────┘
         │
         ▼
  ┌─────────────────────────────────────┐
  │         Mengenprüfung               │  ← Ware wird klassifiziert
  │  🟢 A-Ware │ 🟡 B-Ware │ 🔴 C-Ware │
  └──────┬──────────────────────────────┘
         │
         ▼
  Automatische Folgebelege je Klasse
```

---

## ✨ Funktionsübersicht

<table>
<tr>
<td width="50%">

### 📋 Kernfunktionen
| | Funktion |
|---|---|
| 🔄 | RMA-Erstellung aus Verkaufsauftrag |
| ⚖️ | Mengenprüfung mit A/B/C-Klassifizierung |
| 📦 | Automatische Folgebelege je Warenklasse |
| 🔢 | Seriennummernverfolgung mit Q-Klasse |
| 📸 | Prüffotos & Anhänge am Beleg |
| 📅 | Automatische Rückgabefristkontrolle |

</td>
<td width="50%">

### ⚙️ Technische Features
| | Feature |
|---|---|
| 📊 | Vollständiger Audit-Trail |
| 🔐 | Rollenbasiertes Berechtigungssystem |
| 🏭 | Flexible Lagerort-Konfiguration |
| 🛠️ | Konfigurierbare Vorgangsarten |
| 🏷️ | Frei definierbare Rückgabegründe |
| 🔗 | Direkte Verlinkung zu Lagerbelegen |

</td>
</tr>
</table>

---

## 📦 Installation

```bash
# 1. Repository in das Addons-Verzeichnis klonen
cd /pfad/zu/odoo/custom-addons
git clone https://github.com/LascheSz/rma_management.git

# 2. Odoo neu starten und Modul installieren
python odoo-bin -d <datenbank> -u rma_management

# 3. In Odoo: Apps → "RMA Management" suchen → Installieren
```

> 💡 **Hinweis:** Das Modul legt beim ersten Start automatisch alle benötigten Lagerorte und Vorgangsarten an. Eine manuelle Konfiguration ist optional.

---

## ⚙️ Konfiguration

Öffnen Sie: **Lager → Konfiguration → Einstellungen → RMA Management**

### 📍 Lagerorte

| Lagerort | Zweck | Standard (automatisch) |
|----------|-------|----------------------|
| **RMA-Eingangslager** | Wo die zurückgesendete Ware ankommt | `WH/Stock/RMA` |
| **Prüflager (B-Ware)** | Lager für prüfbedürftige Ware | `WH/Stock/RMA-Prüflager B-Ware` |
| **C-Ware / Schrottlager** | Lager für defekte, unverkäufliche Ware | `WH/Stock/RMA-Schrottlager` |

> 🔧 Lassen Sie die Felder **leer**, um die automatisch erzeugten Standardlagerorte zu verwenden. Eigene Lagerorte können jederzeit ausgewählt werden.

---

### 🔄 Vorgangsarten

| Feld | Beschreibung | Standard |
|------|-------------|---------|
| **RMA-Eingang** | Vorgangsart für den Wareneingang | `RMA-Eingang` (auto) |
| **A-Ware Transfer** | Für neuwertige Ware ins Hauptlager | Normaler Wareneingang |
| **B-Ware Transfer** | Für prüfbedürftige Ware ins Prüflager | `RMA-Prüflager B-Ware` (auto) |
| **C-Ware / Schrott** | Für defekte Ware ins Schrottlager | `RMA Schrottlager C-Ware` (auto) |

---

### 🏷️ Rückgabegründe

Legen Sie fest, welche Gründe bei der RMA-Erstellung auswählbar sind:

```
☑ Defekt
☑ Beschädigt
☑ Falsch geliefert
☑ Nicht gewünscht
☑ Sonstiges
+ Eigene Gründe können jederzeit ergänzt werden
```

---

### ⏱️ Rückgabefrist & Seriennummern

| Einstellung | Beschreibung | Standard |
|-------------|-------------|---------|
| **RMA Rückgabefrist (Tage)** | Standardfrist für alle Kunden | 14 Tage |
| **RMA Seriennummern** | Aktiviert Seriennummernauswahl & Q-Klassen-Prüfung | ✅ Aktiv |

> 💡 Individuelle Fristen pro Kunde können direkt im Kundenstamm (`Kontakt → Rückgabefrist`) gepflegt werden und überschreiben den globalen Standard.

---

## 📘 Benutzerhandbuch

### Phase 1️⃣ – RMA erstellen

<table>
<tr>
<td width="40%">

**Wo:** Verkauf → Aufträge → Auftrag öffnen

</td>
<td width="60%">

**Voraussetzung:** Mindestens ein bereits gelieferter Artikel im Auftrag

</td>
</tr>
</table>

**Schritte:**

```
1. Verkaufsauftrag des Kunden öffnen
   └── Verkauf → Aufträge → [Auftrag wählen]

2. Menü "Aktion" → "RMA erstellen"
   └── Der RMA-Wizard öffnet sich

3. Rückgabegrund wählen
   └── z. B. "Defekt"

4. Rückgabemengen pro Artikel eintragen
   └── Nur Mengen ≤ bereits gelieferter Menge möglich

5. Optional: Seriennummern auswählen (bei serialisierten Artikeln)
   └── Barcode-Button 🔢 je Zeile anklicken

6. "Lieferschein erstellen" klicken
   └── → RMA-Eingangsbeleg wird angelegt
```

> ⚠️ **Rückgabefrist überschritten?** Wenn die Rückgabefrist des Kunden abgelaufen ist, erscheint ein Bestätigungsdialog. Der Beleg kann trotzdem erstellt werden – die Entscheidung liegt beim Mitarbeiter.

---

### Phase 2️⃣ – Mengenprüfung

Die Mengenprüfung ist der Kernprozess: Hier wird die zurückgegebene Ware bewertet und auf die Lager verteilt.

**Wo:** Lager → RMA Management → Mengenprüfung

```
1. RMA-Eingang auswählen
   └── Nur Belege vom Typ "RMA-Eingang" werden angezeigt

2. Prüffotos hochladen (optional)
   └── Kamerabereich "Prüf-Fotos / Anhänge" nutzen
   └── Fotos werden automatisch an alle Folgebelege angehängt

3. Mengen auf A/B/C aufteilen:

   ┌────────────────┬──────────┬──────────┬──────────┐
   │ Artikel        │ Erwartet │ Retourenm.│ Eingeg.  │
   ├────────────────┼──────────┼──────────┼──────────┤
   │ Laptop-NT      │    5     │          │          │
   │ 🟢 A-Ware      │          │          │    2     │
   │ 🟡 B-Ware      │          │          │    2     │
   │ 🔴 C-Ware      │          │          │    1     │
   └────────────────┴──────────┴──────────┴──────────┘
   
   ⚠️ Summe A + B + C muss = Erwartete Menge

4. "Durchführen" klicken
   └── Folgebelege werden automatisch erzeugt
   └── RMA-Eingang wird automatisch validiert
```

---

### Phase 3️⃣ – Seriennummern prüfen (optional)

Wenn Artikel **Seriennummern** haben und die Seriennummern-Option aktiviert ist:

```
1. Barcode-Button 🔢 in der Zeile anklicken
   └── Öffnet den Seriennummern-Dialog

2. Jeder Seriennummer eine Qualitätsklasse zuweisen:

   ┌─────────────┬────────────┐
   │ Seriennummer│  Q-Klasse  │
   ├─────────────┼────────────┤
   │ SN-001      │ 🟢 A-Ware  │
   │ SN-002      │ 🟡 B-Ware  │
   │ SN-003      │ 🔴 C-Ware  │
   └─────────────┴────────────┘

3. "Übernehmen" klicken
   └── Mengen werden automatisch in A/B/C übertragen
   └── Seriennummern werden in die Folgebelege übertragen
```

> ✅ Die Seriennummern erscheinen mit ihrer Q-Klasse direkt in den Folgebelegen und im ursprünglichen RMA-Eingangsbeleg.

---

### Phase 4️⃣ – Folgebelege verarbeiten

Nach der Mengenprüfung werden automatisch bis zu drei Folgebelege erstellt:

<table>
<tr>
<td align="center" width="33%">

### 🟢 A-Ware
**Wareneingang**
`WH/IN/xxxxx`

Neuwertige Ware direkt zurück ins Hauptlager

</td>
<td align="center" width="33%">

### 🟡 B-Ware
**Interne Umbuchung**
`RMA/PRUEF/xxxxx`

Prüfbedürftige Ware ins Prüflager zur weiteren Bewertung

</td>
<td align="center" width="33%">

### 🔴 C-Ware
**Interne Umbuchung**
`RMA/SCHROTT/xxxxx`

Defekte Ware ins Schrottlager

</td>
</tr>
</table>

```
Folgebeleg öffnen
    │
    ├── Seriennummern sind bereits vorbelegt (falls verwendet)
    ├── Prüffotos sind angehängt
    └── "Validieren" klicken → Ware ist eingelagert ✅
```

---

## 🎨 Warenklassen – A / B / C-Ware

| Klasse | Symbol | Zustand | Lagerort | Nächster Schritt |
|--------|--------|---------|----------|-----------------|
| **A-Ware** | 🟢 | Neuwertig, kein Mangel erkennbar | Hauptlager / Verkaufslager | Direkt wieder verkaufen |
| **B-Ware** | 🟡 | Gebraucht, leichte Mängel oder prüfbedürftig | Prüflager | Qualitätsprüfung → Entscheidung |
| **C-Ware** | 🔴 | Defekt, nicht mehr verkaufsfähig | Schrottlager | Entsorgen oder Teile verwerten |

Zusätzlich können bei der Mengenprüfung Mengen für **Umtausch** und **Rückerstattung** vorgemerkt werden – diese werden im Notizfeld des RMA-Eingangs dokumentiert.

---

## 🔢 Seriennummern & Qualitätsklassen

> Aktivierbar unter: **Einstellungen → RMA Seriennummern**

Wenn ein Artikel seriennummernpflichtig ist **und** die Seriennummern beim Erstellen der RMA ausgewählt wurden, erscheint in der Mengenprüfung pro Zeile ein Barcode-Button.

**Ablauf:**

```
RMA erstellt mit SN-001, SN-002, SN-003
          │
          ▼
    Mengenprüfung öffnen
          │
          ▼
    🔢 Barcode-Button klicken
          │
          ▼
    ┌────────────────────────────┐
    │  SN-001  →  🟢 A-Ware     │
    │  SN-002  →  🟡 B-Ware     │
    │  SN-003  →  🔴 C-Ware     │
    └────────────────────────────┘
          │
          ▼
    Mengen werden automatisch gesetzt
    Seriennummern werden auf Folgebelege übertragen
    Q-Klasse wird auf dem RMA-Eingangsbeleg gespeichert
```

**Sichtbarkeit:** Die Q-Klasse ist auf jedem Lagerbeleg in der Registerkarte **"Detaillierte Vorgänge"** und in der Spalte **"RMA Q-Klasse"** sichtbar.

---

## 📅 Rückgabefristen

Das Modul überwacht automatisch, ob die Rückgabefrist eines Kunden eingehalten wird.

```
Rückgabefrist pro Kunde (Priorität):
  1. Individuelle Frist am Kundenstamm  ← höchste Priorität
  2. Standard aus den RMA-Einstellungen  ← Fallback (z. B. 14 Tage)
```

**Anzeige im RMA-Wizard:**

| Feld | Beschreibung |
|------|-------------|
| **Rückgabefrist (Tage)** | Erlaubte Tage ab Lieferdatum |
| **Fristdatum** | Berechnetes Ablaufdatum |
| **Fristhinweis** | Ampel-Text (grün / rot) |

Ist die Frist abgelaufen, erscheint beim Erstellen des Belegs ein **Bestätigungsdialog**:

```
┌──────────────────────────────────────────┐
│  ⚠️  Rückgabefrist überschritten         │
│                                          │
│  Die Frist ist seit X Tagen abgelaufen.  │
│  Möchten Sie trotzdem fortfahren?        │
│                                          │
│  [ Ja, trotzdem erstellen ]  [ Nein ]    │
└──────────────────────────────────────────┘
```

---

## 📊 Audit-Log

Alle RMA-Aktivitäten werden vollständig protokolliert.

**Wo:** RMA Management → Übersicht → Audit-Log

**Erfasste Ereignisse:**

| Ereignis | Wann |
|----------|------|
| 🆕 RMA-Eingang erstellt | Beim Erstellen des RMA-Belegs |
| ✅ Mengenprüfung abgeschlossen | Nach dem "Durchführen" |
| 📸 Anhänge hinzugefügt | Automatisch bei Fotos |

**Jeder Eintrag enthält:**

```
📅  Datum & Uhrzeit
👤  Benutzer
📋  Beschreibung der Aktion
🔗  Verknüpfter Lagerbeleg
📦  Erzeugte Folgebelege
📝  Mengendetails (A/B/C-Aufteilung, Seriennummern)
```

---

## 🔐 Berechtigungen

### 👤 RMA Benutzer
```
✅ RMA-Aufträge erstellen und bearbeiten
✅ Mengenprüfung durchführen
✅ Seriennummern-Qualitätsklassen vergeben
✅ Prüffotos hochladen
✅ Rückgabegründe lesen
✅ Audit-Log lesen
```

### 👨‍💼 RMA Manager
```
✅ Alle Rechte des RMA Benutzers
✅ Rückgabegründe anlegen und bearbeiten
✅ RMA-Einstellungen konfigurieren
✅ Audit-Log-Einträge bearbeiten
```

> 💡 Benutzerrechte vergeben: **Einstellungen → Benutzer → [Benutzer wählen] → RMA Management**

---

## 🛠️ Technische Referenz

### Abhängigkeiten

```python
'depends': ['sale_management', 'stock', 'base', 'product', 'web']
```

### Datenmodelle

| Modell | Typ | Beschreibung |
|--------|-----|-------------|
| `rma.reason` | Stammdaten | Rückgabegründe |
| `rma.order` | TransientModel | Wizard: RMA-Erstellung |
| `rma.order.line` | TransientModel | Positionen der RMA-Erstellung |
| `rma.splitting` | TransientModel | Wizard: Mengenprüfung |
| `rma.splitting.line` | TransientModel | Prüfpositionen (A/B/C) |
| `rma.splitting.serial.line` | TransientModel | Seriennummern-Q-Klassen |
| `rma.audit.log` | Model | Audit-Trail |
| `rma.stock.configuration` | AbstractModel | Lager-Konfigurationsservice |
| `rma.deadline.confirmation` | TransientModel | Fristüberschreitungs-Dialog |

### Erweiterungen auf Odoo-Standardmodellen

| Modell | Erweiterung |
|--------|------------|
| `stock.picking` | RMA-Status, Grund, Anhänge, Q-Klassen-Übersicht |
| `stock.move.line` | `rma_quality_class` – Q-Klasse pro Seriennummer |
| `res.partner` | `rma_return_deadline_days` – Individuelle Rückgabefrist |
| `sale.order` | RMA-Eingang-Flag |

### Automatisch angelegte Konfiguration

Beim ersten Start erzeugt das Modul automatisch (falls nicht in Einstellungen hinterlegt):

```
Lagerorte:
  ├── WH/Stock/RMA                    (Eingangsort)
  ├── WH/Stock/RMA-Prüflager B-Ware  (B-Ware Prüflager)
  └── WH/Stock/RMA-Schrottlager      (C-Ware / Schrott)

Vorgangsarten:
  ├── RMA-Eingang       (code: incoming)
  ├── RMA-Prüflager     (code: internal → Prüflager)
  └── RMA-Schrottlager  (code: internal → Schrottlager)
```

---

## ❓ Häufige Fragen

<details>
<summary><b>🔢 Muss ich Seriennummern verwenden?</b></summary>

Nein. Die Seriennummernfunktion ist optional und kann unter **Einstellungen → RMA Seriennummern** deaktiviert werden. Ohne Seriennummern werden nur Mengen eingegeben.

</details>

<details>
<summary><b>📷 Wo erscheinen die Prüffotos?</b></summary>

Fotos, die in der Mengenprüfung hochgeladen werden, erscheinen automatisch:
- Am ursprünglichen **RMA-Eingangsbeleg** (Registerkarte "RMA Prüfung")
- An **allen erzeugten Folgebelegen** (A-, B-, C-Ware)

</details>

<details>
<summary><b>🔁 Kann ein RMA-Eingang erneut geprüft werden?</b></summary>

Nein. Sobald die Mengenprüfung mit "Durchführen" abgeschlossen wurde, wird der Beleg gesperrt (`RMA vollständig verarbeitet`). Eine erneute Prüfung ist nicht möglich – bei Bedarf muss ein neuer RMA-Eingang erstellt werden.

</details>

<details>
<summary><b>📦 Was passiert mit Umtausch und Rückerstattung?</b></summary>

Die Spalten **"Umtausch"** und **"Rückerstattung"** in der Mengenprüfung sind Vormerkungen für nachgelagerte Prozesse. Die Mengen werden im Notizfeld des RMA-Eingangs dokumentiert, erzeugen aber **keine** automatischen Buchungen – das muss manuell in Verkauf/Buchhaltung erfolgen.

</details>

<details>
<summary><b>⚙️ Kann ich eigene Lagerorte verwenden?</b></summary>

Ja. Unter **Einstellungen → RMA Lagerorte** können beliebige bestehende Odoo-Lagerorte ausgewählt werden. Die automatisch erzeugten Standardlagerorte werden dann ignoriert.

</details>

---

## 📄 Lizenz

> ⚠️ **PROPRIETÄRE SOFTWARE**

Dieses Modul ist **Eigentum der MSV Systemhaus Martin Schlaak GmbH**.

| | |
|---|---|
| ✅ **Erlaubt** | Nutzung durch MSV Systemhaus Martin Schlaak GmbH und autorisierte Partner |
| ❌ **Verboten** | Weitergabe, Veröffentlichung, kommerzielle Nutzung ohne Genehmigung, Reverse Engineering |

**© 2026 MSV Systemhaus Martin Schlaak GmbH – Alle Rechte vorbehalten**

Vollständige Lizenzbestimmungen: [LICENSE](LICENSE)

---

<div align="center">

**Made with ❤️ by MSV Systemhaus Martin Schlaak GmbH**

[📧 info@msv-systemhaus.de](mailto:info@msv-systemhaus.de) · [🌐 msv-systemhaus.de](https://msv-systemhaus.de) · [🐛 Issues](https://github.com/LascheSz/rma_management/issues)

---

`Version 1.0` · `Odoo 19` · `Stand: Juni 2026`

</div>
