# 🔄 RMA Management - Intelligentes Rückgabemanagementsystem für Odoo

> **Professionelle Rückgabeverwaltung mit automatischer Warenklassifizierung**

[![Odoo Version](https://img.shields.io/badge/Odoo-16.0%2B-blue?style=flat-square)](https://www.odoo.com)
[![License](https://img.shields.io/badge/License-LGPL--3.0-green?style=flat-square)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=flat-square)](https://www.python.org)

---

## 🎯 Was ist RMA Management?

Das **RMA Management Modul** ist eine vollständige Lösung für die Verwaltung von Rückgaben in Ihrem Odoo-System. Es automatisiert den kompletten Prozess von der Rückgabeanfrage über die Qualitätsprüfung bis zur intelligenten Klassifizierung der Ware in:

- **🟢 A-Ware** - Neuwertig, sofort wiederverkaufsbereit
- **🟡 B-Ware** - Muss geprüft werden, Entscheidung nach QS erforderlich
- **🔴 C-Ware** - Defekt, zur Verschrottung

---

## ✨ Hauptfunktionen

| Feature | Beschreibung |
|---------|-------------|
| 📋 **RMA-Verwaltung** | Einfache Erstellung von Rückgabeanfragen direkt aus Verkaufsaufträgen |
| 🔀 **Intelligentes Splitting** | Automatische Aufteilung der Ware in A-, B-, C-Klassen |
| 📸 **Bildverwaltung** | Hochladen und Verwaltung von Inspektionsfotos |
| 🔐 **Seriennummern** | Optionale Verfolgung einzelner Geräte via Seriennummern |
| 📊 **Audit-Trail** | Vollständige Protokollierung aller RMA-Aktivitäten |
| ⚙️ **Flexible Konfiguration** | Anpassbare Lagerorte, Vorgangsarten und Rückgabegründe |
| 🔔 **Automatisierung** | Automatische Lagerbewegungen und Bestandsverwaltung |

---

## 🚀 Schnellstart

### 📦 Installation

```bash
# 1. Modul klonen
cd /path/to/odoo/addons
git clone https://github.com/LascheSz/rma_management.git

# 2. Odoo neu starten mit Update-Flag
odoo-bin -d database_name -u rma_management

# 3. Modul aktivieren
# Apps → Suchen: "RMA Management" → Installieren
```

### ⚙️ Erste Konfiguration

Nach der Installation müssen Sie folgende Einstellungen vornehmen:

```
RMA Management → Einstellungen
├── 📍 Lagerorte definieren
│   ├── RMA-Standardlager
│   ├── B-Ware Prüflager
│   ├── A-Ware Wiederverkaufslager
│   ├── C-Ware Schrottlager
│   └── Reparatur-Lager
├── 🔄 Vorgangsarten konfigurieren
│   ├── RMA-Eingang
│   ├── A-Ware Transfer
│   ├── B-Ware Transfer
│   └── Verschrottung
└── 🏷️ RMA-Gründe aktivieren
    ├── Defekt
    ├── Beschädigt
    ├── Falsch geliefert
    └── Nicht gewünscht
```

---

## 📚 Datenmodelle

### 🏷️ `rma.reason` - Rückgabegründe

Definiert die verfügbaren Rückgabegründe im System.

```
Beispiele:
├── 🔧 Defekt
├── 📦 Beschädigt
├── ❌ Falsch geliefert
├── 🚫 Nicht gewünscht
└── ❓ Sonstiges
```

---

### 📋 `rma.order` - RMA-Auftrag (Wizard)

Der Startpunkt für jede Rückgabe. Ein benutzerfreundlicher Wizard zur Erstellung von RMA-Eingängen.

**Workflow:**
```
Verkaufsauftrag öffnen
    ↓
"RMA erstellen" klicken
    ↓
Rückgabegrund wählen
    ↓
Mengen eingeben
    ↓
"Rückgabe erstellen" klicken
    ↓
RMA-Eingangsbeleg wird erstellt
```

---

### 🔀 `rma.splitting` - RMA-Splitting (Wizard)

Intelligente Aufteilung der eingegangenen Ware in Qualitätsklassen.

**Beispiel:**
```
5 Stück Laptop-Netzteil eingegangen
    ↓
Splitting durchführen
    ├── 2 Stück → 🟢 A-Ware (funktioniert einwandfrei)
    ├── 2 Stück → 🟡 B-Ware (leichte Kratzer)
    └── 1 Stück → 🔴 C-Ware (defekt)
    ↓
Automatische Lagerbewegungen erstellt
```

---

### 📦 `stock.picking` - Lagerbewegung (erweitert)

Alle RMA-Lagerbewegungen basieren auf dem Standard-Odoo Picking-Modell mit RMA-Erweiterungen:

- 📸 RMA-Bilder und Anhänge
- 🏷️ RMA-Grund
- 🔗 Verkaufsauftrag-Referenz
- 📝 RMA-Notizen

---

### 📊 `rma.audit.log` - Audit-Trail

Vollständige Protokollierung aller RMA-Aktivitäten für Compliance und Nachverfolgung.

**Protokollierte Ereignisse:**
```
✓ RMA-Eingang erstellt
✓ Splitting durchgeführt
✓ Ware klassifiziert
✓ Lagerbewegungen erstellt
✓ Benutzer und Zeitstempel
```

---

### ⚙️ `rma.stock.configuration` - Zentrale Konfiguration

Verwaltet alle RMA-relevanten Lagerorte und Vorgangsarten zentral.

---

## 🎬 Workflow: Schritt-für-Schritt

### 📌 Szenario: Kunde möchte 5 Laptop-Netzteile zurückgeben

#### Phase 1️⃣: RMA-Antrag erstellen

```
1. Öffnen Sie den Verkaufsauftrag des Kunden
   Verkauf → Aufträge → [Auftrag öffnen]

2. Klicken Sie auf "🔄 RMA erstellen"
   → Wizard öffnet sich

3. Wählen Sie den Rückgabegrund
   ├── 🔧 Defekt ← (in diesem Fall)
   ├── 📦 Beschädigt
   └── ...

4. Geben Sie die Rückgabemenge ein
   └── 5 Stück

5. Klicken Sie "✓ Rückgabe erstellen"
   → RMA-Eingangsbeleg wird erstellt
```

---

#### Phase 2️⃣: RMA-Eingang verarbeiten

```
1. RMA-Eingangsbeleg öffnen
   Status: 📋 Draft

2. Klicken Sie "✓ Bestätigen"
   Status: 🔄 Confirmed

3. Optional: Inspektionsfotos hochladen
   📸 Bilder → [Hochladen]

4. Klicken Sie "✓ Validieren"
   Status: ✅ Done
   → Ware ist jetzt im RMA-Lager
```

---

#### Phase 3️⃣: RMA-Splitting durchführen

```
1. RMA-Beleg öffnen
   Status: ✅ Done

2. Klicken Sie "🔀 RMA Splitting"
   → Splitting-Wizard öffnet sich

3. Verteilen Sie die Ware auf Klassen:

   📍 Artikel: Laptop-Netzteil (5 Stück)
   
   🟢 A-Ware:  2 Stück (funktionieren einwandfrei)
   🟡 B-Ware:  2 Stück (müssen geprüft werden)
   🔴 C-Ware:  1 Stück (defekt, nicht reparierbar)

4. Klicken Sie "✓ Splitting durchführen"
   → 3 separate Lagerbewegungen werden erstellt
```

---

#### Phase 4️⃣: Automatische Lagerbewegungen

```
Nach dem Splitting werden automatisch erstellt:

┌─────────────────────────────────────┐
│ 🟢 A-Ware Beleg                     │
│ 2 Stück → A-Lager (Wiederverkauf)   │
│ Status: Ready to validate           │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ 🟡 B-Ware Beleg                     │
│ 2 Stück → B-Lager (QS erforderlich) │
│ Status: Wartet auf Qualitätsprüfung │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ 🔴 C-Ware Beleg                     │
│ 1 Stück → Schrottlager              │
│ Status: Ready to validate           │
└─────────────────────────────────────┘
```

---

#### Phase 5️⃣: Abschluss

```
1. Validieren Sie alle Belege
   ├── 🟢 A-Ware: ✓ Validieren
   ├── 🟡 B-Ware: ✓ Validieren
   └── 🔴 C-Ware: ✓ Validieren

2. RMA-Prozess ist abgeschlossen ✅
   ├── Ware ist in den richtigen Lagern
   ├── Audit-Log ist aktualisiert
   └── Automatische Benachrichtigungen versendet
```

---

## 🎛️ Konfiguration im Detail

### 📍 Lagerorte einrichten

Gehen Sie zu: **RMA Management → Einstellungen**

| Lagerort | Zweck | Beispiel |
|----------|-------|---------|
| 🔵 RMA-Standardlager | Wo RMA-Eingänge landen | Rückgabe-Annahme |
| 🟡 B-Ware Prüflager | Zwischenlagerung für Prüfung | B-Ware Prüfzone |
| 🟢 A-Ware Lager | Wiederverkaufsreife Ware | Verkaufs-Lager |
| 🔴 Schrottlager | Defekte/unbrauchbare Ware | Verschrottung |
| 🔧 Reparatur-Lager | Zur Reparatur bestimmte Ware | Reparatur-Zone |

---

### 🔄 Vorgangsarten konfigurieren

| Vorgangsart | Typ | Verwendung |
|-------------|-----|-----------|
| RMA-Eingang | Incoming | Rückgaben empfangen |
| A-Ware Transfer | Internal | A-Ware ins Verkaufslager |
| B-Ware Transfer | Internal | B-Ware ins Prüflager |
| Verschrottung | Internal | Schrott ins Schrottlager |

---

### 🏷️ RMA-Gründe aktivieren

Wählen Sie, welche Rückgabegründe verfügbar sein sollen:

```
☑ 🔧 Defekt
☑ 📦 Beschädigt
☑ ❌ Falsch geliefert
☑ 🚫 Nicht gewünscht
☑ ❓ Sonstiges
```

---

## 👥 Berechtigungen & Benutzergruppen

### 👤 RMA User
```
✓ RMA-Aufträge erstellen
✓ RMA-Eingänge bestätigen
✓ RMA-Splitting durchführen
✓ Bilder hochladen
```

### 👨‍💼 RMA Manager
```
✓ Alle Rechte von RMA User
✓ Einstellungen ändern
✓ Audit-Log einsehen
✓ Benutzer verwalten
```

---

## 📊 Audit-Log & Nachverfolgung

Alle RMA-Aktivitäten werden automatisch protokolliert:

```
📅 Datum & Uhrzeit
👤 Benutzer
🎯 Aktion (z.B. "RMA erstellt", "Splitting durchgeführt")
📝 Details
🔗 Verknüpfte Belege
```

**Zugriff:** RMA Management → Audit-Log

---

## ❓ Häufig gestellte Fragen

### ❓ Was ist der Unterschied zwischen A-, B- und C-Ware?

| Klasse | Zustand | Status | Lagerort |
|--------|---------|--------|----------|
| 🟢 A-Ware | Neuwertig | Sofort verkaufsbereit | Verkaufslager |
| 🟡 B-Ware | Zu prüfen | Wartet auf QS-Entscheidung | Prüflager |
| 🔴 C-Ware | Defekt | Nicht verkaufsbereit | Schrottlager |

---

### ❓ Kann ich Seriennummern verwenden?

**Ja!** Aktivieren Sie in den Einstellungen:
```
☑ Seriennummern in RMA verwenden
```

Dann können Sie beim RMA-Erstellungswizard einzelne Seriennummern auswählen.

---

### ❓ Wie lange ist die Standard-Rückgabefrist?

**Standard: 14 Tage**

Sie können dies in den Einstellungen ändern:
```
RMA Management → Einstellungen
→ Standard-Rückgabefrist (Tage)
```

---

### ❓ Wo sehe ich alle RMA-Aktivitäten?

**Im Audit-Log:**
```
RMA Management → Audit-Log
```

Hier werden alle Ereignisse chronologisch aufgelistet mit Filter-Optionen.

---

### ❓ Kann ich die Lagerorte nachträglich ändern?

**Ja!** Gehen Sie zu:
```
RMA Management → Einstellungen
→ Lagerorte konfigurieren
```

---

## 🛠️ Technische Details

### 📋 Abhängigkeiten

```python
'depends': [
    'sale',        # Verkaufsmodul
    'stock',       # Lagerverwaltung
    'account',     # Buchhaltung
    'web',         # Web-Interface
],
```

### 🗄️ Datenbankmodelle

```
rma.reason              → Rückgabegründe
rma.order              → RMA-Aufträge (Wizard)
rma.splitting          → RMA-Splitting (Wizard)
rma.audit.log          → Audit-Trail
rma.stock.configuration → Stock-Konfiguration
```

### 🔐 Sicherheit

```
rma_security.xml       → Benutzergruppen & Zugriffskontrolle
```

---

## 📞 Support & Community

### 🐛 Probleme melden

Haben Sie ein Problem gefunden? Melden Sie es auf GitHub:

**GitHub Issues:** [LascheSz/rma_management/issues](https://github.com/LascheSz/rma_management/issues)

---

### 📖 Weitere Dokumentation

- **Code-Review:** `rma_management_code_review.md`
- **B-Ware Konzept:** `b_ware_ticket_kurz.md`
- **Erweiterungsideen:** `rma_erweiterungsideen.md`

---

## 📄 Lizenz

Dieses Modul ist unter der **LGPL-3.0 Lizenz** lizenziert.

```
Copyright (c) 2026 RMA Management Team

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License.
```

---

## 🎉 Danksagungen

Vielen Dank an alle Contributor und die Odoo-Community für ihre Unterstützung!

---

<div align="center">

**Made with ❤️ for Odoo**

[⭐ GitHub](https://github.com/LascheSz/rma_management) • [📧 Kontakt](mailto:support@example.com) • [🌐 Website](https://example.com)

</div>

---

**Version:** 1.0  
**Letzte Aktualisierung:** Juni 2026  
**Autor:** RMA Management Team  
**Status:** ✅ Production Ready
