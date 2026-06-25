# RMA Management Modul für Odoo

Ein umfassendes Rückgabemanagementsystem (RMA) für Odoo, das den kompletten Prozess von der Rückgabeanfrage über die Qualitätsprüfung bis zur Lagerklassifizierung (A-Ware, B-Ware, C-Ware) abbildet.

---

## 1. Installation

### Voraussetzungen
- Odoo 16.0 oder höher
- Module: `sale`, `stock`, `account`
- Datenbankzugriff mit Admin-Rechten

### Installationsschritte

**Schritt 1: Modul herunterladen**
```bash
cd /path/to/odoo/addons
git clone https://github.com/LascheSz/rma_management.git
```

**Schritt 2: Odoo neu starten**
```bash
# Starten Sie Odoo mit dem Update-Flag
odoo-bin -d database_name -u rma_management
```

**Schritt 3: Modul aktivieren**
- Gehen Sie zu Apps → Suchen Sie nach "RMA Management"
- Klicken Sie auf "Installieren"

**Schritt 4: Konfiguration durchführen**
- Gehen Sie zu RMA Management → Einstellungen
- Konfigurieren Sie die erforderlichen Lagerorte und Vorgangsarten (siehe Konfiguration)

---

## 2. Datenmodelle (Übersicht)

Das RMA-Modul definiert folgende Hauptmodelle:

### 2.1 `rma.reason` - RMA-Gründe
**Zweck:** Definiert die möglichen Rückgabegründe (z.B. "Defekt", "Beschädigt", "Falsch geliefert")

**Wichtige Felder:**
- `name` (Char): Name des Grundes (z.B. "Defekt")
- `description` (Text): Ausführliche Beschreibung
- `active` (Boolean): Ist dieser Grund aktiv?

**Verwendung:** Wird beim RMA-Erstellungswizard ausgewählt

---

### 2.2 `rma.order` - RMA-Auftrag (Wizard)
**Zweck:** Temporärer Wizard zur Erstellung von RMA-Eingangsbelegen

**Wichtige Felder:**
- `sale_order_id` (Many2one): Referenz zum Original-Verkaufsauftrag
- `rma_reason_id` (Many2one): Ausgewählter Rückgabegrund
- `partner_id` (Many2one): Kunde
- `line_ids` (One2many): Zeilen mit Produkten und Rückgabemengen

**Workflow:**
1. Benutzer öffnet einen Verkaufsauftrag
2. Klickt auf "RMA erstellen"
3. Wählt Rückgabegrund und Mengen
4. Klickt "Rückgabe erstellen"
5. RMA-Eingangsbeleg wird erstellt

---

### 2.3 `rma.splitting` - RMA-Splitting (Wizard)
**Zweck:** Teilt einen RMA-Eingangsbeleg in A-, B- und C-Ware auf

**Wichtige Felder:**
- `rma_order_id` (Many2one): Referenz zum RMA-Eingangsbeleg
- `line_ids` (One2many): Zeilen mit Aufteilung pro Artikel
  - `rma_qty_a` (Float): Menge für A-Ware
  - `rma_qty_b` (Float): Menge für B-Ware
  - `rma_qty_c` (Float): Menge für C-Ware

**Workflow:**
1. Benutzer öffnet einen RMA-Eingangsbeleg
2. Klickt auf "RMA Splitting"
3. Verteilt die Mengen auf A-, B-, C-Ware
4. Klickt "Splitting durchführen"
5. Drei separate Lagerbewegungen werden erstellt

---

### 2.4 `stock.picking` - Lagerbewegung (erweitert)
**Zweck:** Standard-Odoo Lagerbewegung mit RMA-Erweiterungen

**Neue RMA-Felder:**
- `rma_reason_id` (Many2one): RMA-Grund
- `rma_sale_order_id` (Many2one): Referenz zum Verkaufsauftrag
- `rma_attachment_ids` (Many2many): Hochgeladene Bilder/Dokumente
- `rma_receipt_created` (Boolean): Wurde ein RMA-Eingang erstellt?
- `picking_type_code` (Char): Art der Lagerbewegung (incoming, outgoing, internal)

**Verwendung:** Alle Lagerbewegungen im RMA-Prozess (RMA-Eingang, A-Ware, B-Ware, C-Ware)

---

### 2.5 `rma.audit.log` - Audit-Log
**Zweck:** Protokolliert alle wichtigen RMA-Ereignisse

**Wichtige Felder:**
- `action` (Selection): Art des Ereignisses (z.B. 'receipt_created', 'split_executed')
- `name` (Char): Beschreibung des Ereignisses
- `sale_order_id` (Many2one): Zugehöriger Verkaufsauftrag
- `picking_id` (Many2one): Zugehöriger Beleg
- `user_id` (Many2one): Benutzer, der die Aktion durchgeführt hat
- `create_date` (Datetime): Zeitstempel

**Verwendung:** Nachverfolgung aller RMA-Aktivitäten

---

### 2.6 `rma.stock.configuration` - Stock-Konfiguration
**Zweck:** Zentrale Verwaltung der RMA-Lagerorte und Vorgangsarten

**Wichtige Methoden:**
- `_get_location(location_key)`: Gibt den Lagerort für einen Schlüssel zurück
  - `'rma'`: RMA-Standardlager
  - `'b_goods'`: B-Ware Prüflager
  - `'scrap'`: C-Ware Schrottlager
  - `'a_goods'`: A-Ware Wiederverkaufslager
  - `'repair'`: Reparatur-Lager
- `_get_picking_type(type_key)`: Gibt die Vorgangsart zurück
  - `'incoming'`: RMA-Eingang
  - `'b_goods'`: B-Ware Vorgangsart
  - `'scrap'`: C-Ware Vorgangsart

---

### 2.7 `rma.order.service` - Service-Schicht
**Zweck:** Geschäftslogik für RMA-Operationen

**Wichtige Methoden:**
- `create_return_picking(wizard)`: Erstellt RMA-Eingangsbeleg
- `execute_split(wizard)`: Führt RMA-Splitting durch
- `_create_selected_serial_move_lines(moves_by_line)`: Verarbeitet Seriennummern

---

## 3. Konfiguration

### Einstellungen aufrufen
Gehen Sie zu: **RMA Management → Einstellungen**

### Erforderliche Konfigurationen

**1. Standard-Rückgabefrist (Tage)**
- Standard: 14 Tage
- Zeitraum, innerhalb dessen Rückgaben akzeptiert werden

**2. Lagerorte konfigurieren**
- **RMA-Standardlager**: Wo RMA-Eingänge landen
- **B-Ware Prüflager**: Wo B-Ware zwischengelagert wird
- **C-Ware Schrottlager**: Wo Schrott landet
- **A-Ware Wiederverkaufslager**: Wo verkaufsreife Ware landet
- **Reparatur-Lager**: Wo Ware zur Reparatur liegt

**3. Vorgangsarten konfigurieren**
- **RMA-Eingang Vorgangsart**: Für RMA-Eingänge
- **A-Ware Vorgangsart**: Für A-Ware Umlagern
- **B-Ware Vorgangsart**: Für B-Ware Umlagern
- **C-Ware Vorgangsart**: Für Verschrottung

**4. Seriennummern verwenden**
- Toggle: "Seriennummern in RMA verwenden"
- Wenn aktiviert: Seriennummern können pro Artikel ausgewählt werden
- Wenn deaktiviert: Rein mengenbasiert

**5. RMA-Gründe aktivieren**
- Wählen Sie, welche Rückgabegründe verfügbar sein sollen
- Standard: Defekt, Beschädigt, Falsch geliefert, Nicht gewünscht

---

## 4. Workflow: Schritt für Schritt

### Szenario: Kunde möchte 5 Stück Laptop-Netzteil zurückgeben (defekt)

#### Phase 1: RMA-Antrag erstellen

**Schritt 1:** Öffnen Sie den Verkaufsauftrag des Kunden
- Gehen Sie zu Verkauf → Aufträge
- Öffnen Sie den Auftrag

**Schritt 2:** Klicken Sie auf "RMA erstellen"
- Ein Wizard öffnet sich
- Wählen Sie "Defekt" als Rückgabegrund
- Geben Sie 5 als Rückgabemenge ein
- Klicken Sie "Rückgabe erstellen"

**Ergebnis:**
- RMA-Eingangsbeleg wird erstellt
- Status: "Draft" (Entwurf)
- 5 Stück Laptop-Netzteil sind im RMA-Beleg

#### Phase 2: RMA-Eingang bestätigen

**Schritt 3:** Bestätigen Sie den RMA-Eingangsbeleg
- Klicken Sie "Bestätigen"
- Status wechselt zu "Confirmed"
- Lagerbewegung wird vorbereitet

**Schritt 4:** Markieren Sie als erhalten
- Klicken Sie "Validieren"
- Status wechselt zu "Done"
- Ware ist jetzt im RMA-Lager

**Optional: Bilder hochladen**
- Im Beleg können Inspektionsfotos hochgeladen werden
- Diese werden später im QS-Prozess verwendet

#### Phase 3: RMA-Splitting durchführen

**Schritt 5:** Öffnen Sie den RMA-Eingangsbeleg
- Klicken Sie auf "RMA Splitting"
- Ein Wizard öffnet sich

**Schritt 6:** Verteilen Sie die Ware
- Für die 5 Stück Laptop-Netzteil:
  - A-Ware: 2 Stück (funktionieren einwandfrei)
  - B-Ware: 2 Stück (haben leichte Mängel)
  - C-Ware: 1 Stück (defekt, nicht reparierbar)
- Klicken Sie "Splitting durchführen"

**Ergebnis:**
- 3 separate Lagerbewegungen werden erstellt:
  1. **A-Ware Beleg**: 2 Stück → A-Lager (Wiederverkauf)
  2. **B-Ware Beleg**: 2 Stück → B-Lager (Prüfung erforderlich)
  3. **C-Ware Beleg**: 1 Stück → Schrottlager (Verschrottung)

#### Phase 4: B-Ware Qualitätsprüfung (optional)

**Hinweis:** B-Ware Tickets sind derzeit deaktiviert. Sie können aber manuell:

**Schritt 7:** B-Ware Beleg öffnen
- Suchen Sie den B-Ware Beleg
- Dokumentieren Sie die Qualitätsprüfung
- Entscheiden Sie: Wiederverkauf oder Verschrottung

#### Phase 5: Abschluss

**Schritt 8:** Alle Belege validieren
- A-Ware Beleg: Validieren → Ware ist verkaufsbereit
- B-Ware Beleg: Validieren → Ware wird als B-Ware verkauft
- C-Ware Beleg: Validieren → Ware wird verschrottet

**Ergebnis:**
- RMA-Prozess ist abgeschlossen
- Ware ist in den richtigen Lagern
- Audit-Log hat alle Schritte protokolliert

---

## 5. Benutzeroberfläche

### Menü-Navigation
```
RMA Management
├── RMA Aufträge (Verkaufsaufträge mit RMA-Option)
├── RMA Splitting (Splitting-Wizard)
├── RMA Gründe (Verwaltung der Rückgabegründe)
├── Audit-Log (Protokoll aller Aktivitäten)
└── Einstellungen (Konfiguration)
```

### Wichtige Views

**RMA-Eingangsbeleg (Stock Picking)**
- Header mit Beleg-Nummer, Status, Datum
- Reiter: Allgemein, Zusätzliche Informationen, Notizen
- Buttons: Bestätigen, Validieren, RMA Splitting
- Chatter für Kommentare

**RMA Splitting Wizard**
- Zeigt alle Positionen aus dem RMA-Eingang
- Felder zum Verteilen auf A-, B-, C-Ware
- Validierung: Summe muss gleich Eingangsmenge sein
- Button: "Splitting durchführen"

**Audit-Log**
- Chronologische Liste aller RMA-Ereignisse
- Filter nach Verkaufsauftrag, Beleg, Aktion, Datum
- Detaillierte Informationen zu jeder Aktion

---

## 6. Berechtigungen

Das Modul definiert folgende Benutzergruppen:

**Gruppe: RMA User**
- Darf RMA-Aufträge erstellen
- Darf RMA-Eingänge bestätigen
- Darf RMA-Splitting durchführen

**Gruppe: RMA Manager**
- Alle Rechte von RMA User
- Darf Einstellungen ändern
- Darf Audit-Log einsehen

---

## 7. Häufig gestellte Fragen

**F: Was ist der Unterschied zwischen A-, B- und C-Ware?**

A: 
- **A-Ware**: Funktioniert einwandfrei, kann direkt wiederverkauft werden
- **B-Ware**: Hat leichte Mängel, funktioniert aber, wird mit Rabatt verkauft
- **C-Ware**: Ist defekt oder stark beschädigt, wird verschrottet

**F: Kann ich Seriennummern verwenden?**

A: Ja! Wenn Sie "Seriennummern verwenden" in den Einstellungen aktivieren, können Sie beim RMA-Erstellungswizard einzelne Seriennummern auswählen.

**F: Wie kann ich die Rückgabefrist ändern?**

A: Gehen Sie zu RMA Management → Einstellungen → "Standard-Rückgabefrist (Tage)" und ändern Sie den Wert.

**F: Wo sehe ich alle RMA-Aktivitäten?**

A: Gehen Sie zu RMA Management → Audit-Log. Hier werden alle Ereignisse chronologisch aufgelistet.

**F: Kann ich die Lagerorte ändern?**

A: Ja! Gehen Sie zu RMA Management → Einstellungen und konfigurieren Sie die Lagerorte nach Ihren Anforderungen.

---

## 8. Technische Details

### Abhängigkeiten
```python
'depends': [
    'sale',
    'stock',
    'account',
    'web',
],
```

### Datenbankmodelle
- `rma.reason`: Rückgabegründe
- `rma.order`: RMA-Aufträge (Wizard)
- `rma.splitting`: RMA-Splitting (Wizard)
- `rma.audit.log`: Audit-Log
- `rma.stock.configuration`: Stock-Konfiguration

### Erweiterte Modelle
- `stock.picking`: Lagerbewegung (RMA-Felder hinzugefügt)
- `sale.order`: Verkaufsauftrag (RMA-Buttons hinzugefügt)

### Sicherheit
- `rma_security.xml`: Benutzergruppen und Zugriffskontrolle

---

## 9. Support und Dokumentation

**Probleme melden:**
- GitHub Issues: https://github.com/LascheSz/rma_management/issues

**Code-Review:**
- Siehe `rma_management_code_review.md` für detaillierte Code-Analyse

**Konzept und Design:**
- Siehe `b_ware_ticket_kurz.md` für B-Ware Ticket-Konzept

---

## 10. Lizenz

Dieses Modul ist unter der LGPL-3.0 Lizenz lizenziert.

---

**Version:** 1.0  
**Letzte Aktualisierung:** Juni 2026  
**Autor:** RMA Management Team
