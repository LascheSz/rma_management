# RMA Management — Betriebshandbuch

**MSV Systemhaus Martin Schlaak GmbH**
Stand: Juni 2026 · Odoo 19 · Version 1.0

Dieses Dokument beschreibt jeden Schritt im RMA-Prozess so, dass eine neue Person den Ablauf ohne Vorkenntnisse nachvollziehen und selbstständig durchführen kann.

---

## Inhaltsverzeichnis

1. [Systemzugang und Voraussetzungen](#1-systemzugang-und-voraussetzungen)
2. [Überblick — wie hängt alles zusammen?](#2-überblick--wie-hängt-alles-zusammen)
3. [Weg A — Kunde meldet sich über das Portal](#3-weg-a--kunde-meldet-sich-über-das-portal)
4. [Weg B — Mitarbeiter erstellt RMA direkt](#4-weg-b--mitarbeiter-erstellt-rma-direkt)
5. [RMA-Eingang bearbeiten (Lager)](#5-rma-eingang-bearbeiten-lager)
6. [Mengenprüfung durchführen](#6-mengenprüfung-durchführen)
7. [Seriennummern prüfen](#7-seriennummern-prüfen-nur-bei-serialisierten-artikeln)
8. [KI-Klassifizierung nutzen](#8-ki-klassifizierung-nutzen-optional)
9. [Folgebelege verarbeiten](#9-folgebelege-verarbeiten)
10. [Reparaturaufträge (B-Ware)](#10-reparaturaufträge-b-ware)
11. [Portal-Anfragen verwalten](#11-portal-anfragen-verwalten)
12. [Auswertung und Statistik](#12-auswertung-und-statistik)
13. [Einstellungen und Konfiguration](#13-einstellungen-und-konfiguration)
14. [Häufige Fehler und Lösungen](#14-häufige-fehler-und-lösungen)
15. [Benutzer und Rechte](#15-benutzer-und-rechte)

---

## 1. Systemzugang und Voraussetzungen

### Odoo-Login

- URL: wird vom Administrator bereitgestellt (z. B. `https://odoo.firma.de`)
- Benutzername und Passwort: vom Administrator erhalten
- Benötigte Berechtigung: **RMA Benutzer** oder **RMA Manager**

### Wer darf was?

| Aktion | RMA Benutzer | RMA Manager |
|--------|:---:|:---:|
| RMA erstellen | ja | ja |
| Mengenprüfung durchführen | ja | ja |
| Portal-Anfragen genehmigen | ja | ja |
| KI-Klassifizierung nutzen | ja | ja |
| Rückgabegründe anlegen | nein | ja |
| RMA-Einstellungen ändern | nein | ja |

Wenn eine Funktion nicht sichtbar ist oder ein Fehler "Zugriff verweigert" erscheint, fehlt die Berechtigung. Dann beim Administrator melden.

---

## 2. Überblick — wie hängt alles zusammen?

Der RMA-Prozess hat zwei mögliche Einstiegspunkte und läuft dann in gemeinsamen Schritten weiter:

```
EINSTIEG A                          EINSTIEG B
Kunde besucht                       Mitarbeiter öffnet
/rma/anfrage                        RMA Management → Erstellung
        │                                   │
        ▼                                   │
Kunde gibt E-Mail +                         │
Rechnungsnummer ein                         │
        │                                   │
        ▼                                   │
System prüft Verifizierung                  │
        │                                   │
        ▼                                   │
Kunde wählt Artikel                         │
und Mengen aus                              │
        │                                   │
        ▼                                   │
Portal-Anfrage landet                       │
im Backend                                  │
        │                                   │
        ▼                                   │
Mitarbeiter prüft                           │
und genehmigt                               │
Kunde erhält E-Mail                         │
        │                                   │
        └──────────────┬────────────────────┘
                       ▼
            RMA-Erstellung
            (Referenz auswählen)
                       │
                       ▼
            RMA-Eingangsbeleg wird
            automatisch angelegt
                       │
                       ▼
            Ware kommt im Lager an
            → Beleg validieren
                       │
                       ▼
            Mengenprüfung
            A-Ware / B-Ware / C-Ware
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
      Hauptlager   Prüflager    Schrottlager
                   + Reparatur-
                     auftrag
```

---

## 3. Weg A — Kunde meldet sich über das Portal

### 3.1 Was der Kunde tut

Der Kunde öffnet in seinem Browser die Adresse:

```
https://[eure-odoo-domain]/rma/anfrage
```

Er sieht ein Formular mit zwei Feldern:

- **E-Mail-Adresse** — die E-Mail-Adresse, die beim Kunden in Odoo hinterlegt ist
- **Rechnungsnummer** — die Nummer seiner Rechnung (z. B. `INV/2026/00042`)

Nach dem Klick auf "Weiter" prüft das System, ob die E-Mail-Adresse zur angegebenen Rechnung gehört. Stimmt beides überein, sieht der Kunde eine Liste aller Artikel aus dieser Rechnung.

Der Kunde:
1. Trägt bei jedem Artikel die Menge ein, die er zurückgeben möchte
2. Wählt einen Rückgabegrund aus der Liste
3. Kann optional eine Beschreibung des Problems eingeben
4. Klickt auf "Anfrage absenden"

Danach sieht der Kunde eine Bestätigungsseite mit seiner Anfragenummer (z. B. `RMA/P/00001`).

### 3.2 Was der Mitarbeiter im Backend tut

**Navigation:** Linke Seitenleiste → **RMA Management** → **Portal-Anfragen**

Hier erscheint die neue Anfrage des Kunden mit Status **"Eingereicht"**.

**Schritt 1: Anfrage öffnen**

Auf die Anfrage in der Liste klicken. Die Detailansicht zeigt:
- Kundendaten (Name, E-Mail)
- Rechnung
- Welche Artikel in welcher Menge zurückgegeben werden sollen
- Den Rückgabegrund
- Ggf. die Beschreibung des Kunden

**Schritt 2: Prüfen**

Überlegen, ob die Anfrage genehmigt werden kann:
- Stimmen die Mengen?
- Ist der Rückgabegrund plausibel?
- Ist der Artikel noch innerhalb der Rückgabefrist?

**Schritt 3a: Genehmigen**

Oben auf **"Genehmigen & E-Mail senden"** klicken.

Das System:
- Setzt den Status auf "Genehmigt"
- Schickt dem Kunden automatisch eine E-Mail mit der Rücksendeadresse und einem Hinweis, die Anfragenummer auf das Paket zu schreiben

Der grüne Hinweis oben in der Maske erklärt: Sobald die Ware eingetroffen ist, in der **RMA-Erstellung** diese Anfrage auswählen.

**Schritt 3b: Ablehnen**

Auf **"Ablehnen"** klicken. Es kann ein Ablehnungsgrund eingetragen werden (optional). Der Kunde wird nicht automatisch informiert — das muss manuell per E-Mail oder Telefon geschehen.

---

## 4. Weg B — Mitarbeiter erstellt RMA direkt

Wenn kein Portal-Anfrage vorliegt (z. B. der Kunde ruft an), kann der RMA-Eingang direkt erstellt werden.

**Möglichkeit 1: Über das RMA-Modul**

Navigation: **RMA Management** → **Erstellung**

**Möglichkeit 2: Direkt aus dem Verkaufsauftrag**

Navigation: **Verkauf** → **Aufträge** → Auftrag des Kunden öffnen → oben auf **"RMA erstellen"** klicken

### 4.1 Formular ausfüllen

**Feld "Referenz":**

Das ist das erste und wichtigste Feld. Hier wird entweder eine Portal-Anfrage oder ein Verkaufsauftrag ausgewählt — beides erscheint in einer kombinierten Suchliste.

- Tippe den Kundennamen, die Auftragsnummer oder die Anfragenummer ein
- In der Liste erscheinen:
  - `[Anfrage] RMA/P/00001` — genehmigte Portal-Anfragen
  - `[Auftrag] S00042` — Verkaufsaufträge

**Bei Auswahl einer Portal-Anfrage:**
- Verkaufsauftrag, Rückgabegrund und Rückgabemengen werden automatisch vorbelegt
- Alle Felder können danach noch angepasst werden

**Bei Auswahl eines Verkaufsauftrags:**
- Nur der Auftrag wird gesetzt, der Rest muss manuell ausgefüllt werden

**Feld "RMA-Grund":**

Aus der Dropdown-Liste wählen (z. B. "Defekt", "Falsch geliefert", "Nicht gewünscht"). Pflichtfeld.

**Kundeninformationen:**

Werden automatisch aus dem Verkaufsauftrag geladen — Adresse, E-Mail, Telefon, Rückgabefrist. Keine manuelle Eingabe nötig.

**Positionen:**

Die Tabelle zeigt alle Artikel aus dem Verkaufsauftrag. Für jeden Artikel:

| Spalte | Bedeutung |
|--------|-----------|
| Artikel | Name des Produkts (nicht änderbar) |
| Bestellt | Ursprünglich bestellte Menge |
| Bereits retourniert | Mengen aus früheren RMAs zu diesem Auftrag |
| Noch möglich | Maximale Rückgabemenge (automatisch berechnet) |
| Rückgabemenge | Hier die tatsächliche Rückgabemenge eintragen |

Bei serialisierten Artikeln erscheint zusätzlich ein Barcode-Icon. Darauf klicken, um konkrete Seriennummern auszuwählen (→ siehe Abschnitt 7).

**Rückgabefrist:**

Unten im Kundenblock wird die Frist angezeigt. Ist sie abgelaufen, erscheint ein roter Hinweis. Das System lässt trotzdem fortfahren, zeigt aber einen Bestätigungsdialog.

### 4.2 Lieferschein erstellen

Wenn alles ausgefüllt ist, oben auf **"Lieferschein erstellen"** klicken.

Das System:
- Legt einen RMA-Eingangsbeleg im Lager an
- Verknüpft ihn mit dem Verkaufsauftrag
- Setzt die Portal-Anfrage (falls vorhanden) auf "In Bearbeitung"
- Schreibt einen Eintrag ins Audit-Log und in den Chatter des Verkaufsauftrags

---

## 5. RMA-Eingang bearbeiten (Lager)

Der RMA-Eingangsbeleg ist ein normaler Odoo-Lagerbeleg. Er wird automatisch angelegt und muss nicht manuell bearbeitet werden — bis die Ware tatsächlich eintrifft.

**Navigation zum Beleg:**

Entweder über: **Lager** → **Vorgänge** → **Transfers** → Typ "RMA-Eingang" filtern

Oder über den Smart-Button "RMA" direkt im Verkaufsauftrag.

### 5.1 Ware einbuchen

Wenn die Ware vom Kunden eingetroffen ist:

1. Beleg öffnen
2. Tatsächliche Mengen kontrollieren (ggf. anpassen)
3. Auf **"Validieren"** klicken

Der Beleg ist nun abgeschlossen. Jetzt kann die Mengenprüfung gestartet werden.

### 5.2 Fotos und Anhänge

Im Beleg gibt es die Registerkarte **"RMA Prüfung"**. Hier können Prüffotos und andere Dokumente hochgeladen werden, bevor die Mengenprüfung gestartet wird. Die Fotos werden automatisch an alle Folgebelege weitergegeben.

---

## 6. Mengenprüfung durchführen

Die Mengenprüfung ist der Kernprozess: Hier wird entschieden, in welchen Zustand die zurückgegebene Ware eingestuft wird.

**Navigation:** **RMA Management** → **Mengenprüfung**

### 6.1 RMA-Eingang auswählen

In der Suchleiste oben den Beleg suchen (nach Kundennamen oder Belegnummer). Nur validierte RMA-Eingänge erscheinen in der Liste.

Auf den Beleg klicken.

### 6.2 Prüfpositionen befüllen

Die Tabelle zeigt alle Artikel des RMA-Eingangs. Für jede Position müssen die Mengen auf A-, B- und C-Ware aufgeteilt werden:

| Spalte | Bedeutung |
|--------|-----------|
| Artikel | Produktname |
| Retourenmenge | Menge laut Eingangsbeleg (Vorgabe) |
| A-Ware | Neuwertige, direkt wiederverkaufbare Ware |
| B-Ware | Prüfbedürftig, leichte Mängel, reparierbar |
| C-Ware | Defekt, nicht mehr verkaufsfähig |
| Umtausch | Vorgemerkt für Tauschlieferung (nur Dokumentation) |
| Rückerstattung | Vorgemerkt für Gutschrift (nur Dokumentation) |

**Wichtige Regel:** Die Summe aus A-Ware + B-Ware + C-Ware muss gleich der Retourenmenge sein. Das System prüft das beim Klick auf "Durchführen".

**Beispiel:**

```
Artikel: Laptop-Netzteil   Retourenmenge: 5
→ A-Ware: 2  (neuwertig, Originalverpackung)
→ B-Ware: 2  (funktioniert, aber Gehäuse verkratzt)
→ C-Ware: 1  (defekt, Kabel abgebrochen)
Summe: 5 ✓
```

### 6.3 Optional: KI-Klassifizierung nutzen

Bei jeder Position gibt es ein Kamera-Icon. Darauf klicken öffnet den KI-Inspektor (→ siehe Abschnitt 8).

### 6.4 Optional: Seriennummern prüfen

Bei serialisierten Artikeln erscheint ein Barcode-Icon. Darauf klicken öffnet die Seriennummern-Qualitätsprüfung (→ siehe Abschnitt 7).

### 6.5 Durchführen

Wenn alle Positionen ausgefüllt sind, auf **"Durchführen"** klicken.

Das System:
- Prüft, ob alle Summen stimmen
- Validiert den RMA-Eingang
- Erzeugt automatisch Folgebelege für A-, B- und C-Ware
- Legt für B-Ware automatisch Reparaturaufträge an
- Überträgt Prüffotos auf alle Folgebelege
- Schreibt einen Eintrag ins Audit-Log

Danach erscheint ein Dialog mit Links zu den erzeugten Folgebelegen.

---

## 7. Seriennummern prüfen (nur bei serialisierten Artikeln)

Wenn Artikel mit Seriennummernpflicht zurückgegeben werden und die RMA mit konkreten Seriennummern erstellt wurde, muss jeder Seriennummer eine Qualitätsklasse zugewiesen werden.

**Wann erscheint das Barcode-Icon?**

- Der Artikel hat Seriennummern-Tracking in Odoo
- In der RMA-Erstellung wurden konkrete Seriennummern ausgewählt
- Die Option "RMA Seriennummern" ist in den Einstellungen aktiv

### 7.1 Dialog öffnen

In der Mengenprüfungs-Tabelle das Barcode-Icon in der entsprechenden Zeile anklicken.

### 7.2 Qualitätsklassen vergeben

Es erscheint eine Liste aller Seriennummern dieser Position. Für jede Seriennummer eine Klasse wählen:

| Auswahl | Bedeutung |
|---------|-----------|
| A-Ware | Neuwertig |
| B-Ware | Prüfbedürftig |
| C-Ware | Defekt |

Alternativ: Barcode-Scanner verwenden. Im Feld "Seriennummer scannen" die Seriennummer einscannen — sie wird automatisch zur richtigen Position zugeordnet.

### 7.3 Übernehmen

Auf **"Übernehmen"** klicken. Das System:
- Überträgt die Mengen automatisch in die A/B/C-Felder der Prüfposition
- Speichert welche konkrete Seriennummer welche Klasse bekommen hat
- Die Klasse ist später auf dem Folgebeleg und im Lagerbeleg sichtbar

---

## 8. KI-Klassifizierung nutzen (optional)

Die KI kann anhand eines Fotos vorschlagen, ob ein Artikel A-, B- oder C-Ware ist.

**Voraussetzung:** In den Odoo-Einstellungen muss ein API-Key für OpenAI oder Google hinterlegt sein.

### 8.1 Inspektor öffnen

In der Mengenprüfungs-Tabelle das Kamera-Icon in der entsprechenden Zeile anklicken.

### 8.2 Foto hochladen

Auf das Upload-Feld klicken und ein Foto des Artikels auswählen. Das Foto sollte den Zustand des Artikels klar zeigen — z. B. Beschädigungen, Verpackungszustand, sichtbare Defekte.

### 8.3 Hinweise eingeben (optional)

Im Textfeld können zusätzliche Informationen für die KI eingetragen werden:

```
Beispiel: "Verpackung beschädigt, Gerät selbst optisch einwandfrei"
Beispiel: "Kabel abgebrochen, starke Gebrauchsspuren"
```

Je mehr Kontext, desto genauer die Einschätzung.

### 8.4 Klassifizieren

Auf **"Klassifizieren"** klicken. Die KI analysiert das Foto und gibt eine Empfehlung aus:
- Vorgeschlagene Klasse (A/B/C)
- Kurze Begründung auf Deutsch

### 8.5 Vorschlag übernehmen oder verwerfen

- **"Vorschlag übernehmen"**: Die Q-Klasse wird auf die Prüfposition übertragen
- Dialog schließen ohne zu übernehmen: Die Position bleibt unverändert, der Mitarbeiter entscheidet selbst

Die KI-Empfehlung ist immer nur ein Vorschlag — die finale Entscheidung trifft der Mitarbeiter.

---

## 9. Folgebelege verarbeiten

Nach der Mengenprüfung entstehen automatisch Folgebelege — je nach eingetragenen Mengen bis zu drei Stück.

**Navigation:** Der Dialog nach "Durchführen" zeigt direkte Links. Alternativ: **Lager** → **Vorgänge** → **Transfers**

### A-Ware — Wareneingang ins Hauptlager

Dieser Beleg bucht die neuwertige Ware direkt zurück in den normalen Lagerbestand.

1. Beleg öffnen
2. Mengen kontrollieren (bereits korrekt vorbelegt)
3. Falls Seriennummern: diese sind bereits eingetragen
4. Auf **"Validieren"** klicken
5. Die Ware ist jetzt wieder im Bestand und kann verkauft werden

### B-Ware — Transfer ins Prüflager

Dieser Beleg bucht die prüfbedürftige Ware ins Prüflager.

1. Beleg öffnen
2. Auf **"Validieren"** klicken
3. Die Ware ist jetzt im Prüflager
4. Zusätzlich wurde automatisch ein Reparaturauftrag angelegt (→ Abschnitt 10)

### C-Ware — Transfer ins Schrottlager

Dieser Beleg bucht die defekte Ware ins Schrottlager.

1. Beleg öffnen
2. Auf **"Validieren"** klicken
3. Die Ware ist jetzt im Schrottlager und aus dem normalen Bestand entfernt

---

## 10. Reparaturaufträge (B-Ware)

Für jede B-Ware-Position wird nach der Mengenprüfung automatisch ein Reparaturauftrag im Odoo-Reparaturmodul angelegt.

**Bei serialisierten Artikeln:** Ein Reparaturauftrag pro Seriennummer

**Bei Mengenware:** Ein Reparaturauftrag mit der gesamten B-Ware-Menge

### 10.1 Reparaturaufträge finden

**Weg 1:** Auf dem RMA-Eingangsbeleg oben den Smart-Button **"Reparaturen"** klicken (erscheint nach der Mengenprüfung).

**Weg 2:** **Reparatur** → **Reparaturaufträge**

### 10.2 Reparaturauftrag bearbeiten

Im Reparaturauftrag kann der weitere Prozess gesteuert werden:
- Reparatur starten
- Ersatzteile hinzufügen
- Reparatur abschließen
- Artikel als nicht reparierbar markieren

Die Reparaturaufträge sind vollständige Odoo-`repair.order`-Belege — alle normalen Odoo-Reparaturfunktionen stehen zur Verfügung.

---

## 11. Portal-Anfragen verwalten

**Navigation:** **RMA Management** → **Portal-Anfragen**

### Status-Übersicht

| Status | Bedeutung | Nächste Aktion |
|--------|-----------|----------------|
| Eingereicht | Neu vom Kunden | Prüfen und genehmigen oder ablehnen |
| Genehmigt | Genehmigt, Kunde informiert | Warten auf Wareneingang, dann RMA erstellen |
| In Bearbeitung | RMA-Eingang wurde angelegt | Mengenprüfung durchführen |
| Erledigt | Prozess abgeschlossen | Keine |
| Abgelehnt | Anfrage abgelehnt | Keine |

### Anfrage als erledigt markieren

Wenn die Mengenprüfung abgeschlossen ist, die Portal-Anfrage öffnen und oben **"Als erledigt markieren"** klicken. Das schließt die Anfrage ab.

### Suchen und Filtern

Oben in der Listenansicht gibt es eine Suchleiste mit vordefinierten Filtern:

- **Offen** — alle Anfragen die noch Aktion erfordern (Eingereicht oder Genehmigt)
- **Eingereicht** — nur neue, unbearbeitete Anfragen
- **Genehmigt** — genehmigt, aber noch kein RMA-Eingang

---

## 12. Auswertung und Statistik

**Navigation:** **RMA Management** → **Auswertung**

Die Auswertung zeigt alle abgeschlossenen RMAs mit ihren Qualitätsklassen-Anteilen.

### Filtern

In der Suchleiste oben können Filter kombiniert werden:

**Nach Kunde:**
Auf das Suchfeld klicken → "Kunde" auswählen → Kundennamen eintippen

**Nach Artikel:**
Auf das Suchfeld klicken → "Artikel" auswählen → Artikelname eintippen

**Nach Q-Klasse:**
Auf das Dropdown "Filter" klicken:
- "Nur A-Ware" — zeigt nur Einträge wo A-Ware die dominante Klasse ist
- "Nur B-Ware" — zeigt nur B-Ware-dominante Einträge
- "Nur C-Ware" — zeigt nur C-Ware-dominante Einträge

### Spalten

| Spalte | Bedeutung |
|--------|-----------|
| Beleg | RMA-Eingangsbeleg |
| Kunde | Kundenname |
| Artikel | Produktname |
| A-Ware / B-Ware / C-Ware | absolute Mengen |
| A % / B % / C % | prozentuale Anteile |
| Dominant | Welche Klasse überwiegt |
| Datum | Wann die Mengenprüfung abgeschlossen wurde |

### Gruppieren

Über das Dropdown "Gruppieren nach" können die Einträge zusammengefasst werden:
- Nach Kunde
- Nach Artikel
- Nach Q-Klasse
- Nach Monat

---

## 13. Einstellungen und Konfiguration

**Navigation:** **Lager** → **Konfiguration** → **Einstellungen** → Abschnitt "RMA Management"

> Nur für RMA Manager sichtbar.

### Lagerorte

Hier werden die drei RMA-Lagerorte konfiguriert. Felder leer lassen = automatisch erstellte Standardlagerorte werden verwendet. Eigene Lagerorte können aus dem Dropdown gewählt werden (alle in Odoo vorhandenen Lagerorte stehen zur Auswahl).

### Vorgangsarten

Hier werden die drei RMA-Vorgangsarten konfiguriert. Analog zu den Lagerorten — leer = Standard.

### Rückgabegründe

**Navigation:** **RMA Management** → **Rückgabegründe** (nur für RMA Manager sichtbar)

Hier können neue Gründe angelegt, vorhandene bearbeitet oder deaktiviert werden. Deaktivierte Gründe erscheinen nicht mehr in der Auswahl bei der RMA-Erstellung.

### Rückgabefrist (Standard)

In den Einstellungen kann die Standard-Rückgabefrist in Tagen definiert werden. Diese gilt für alle Kunden, bei denen keine individuelle Frist hinterlegt ist.

**Individuelle Frist pro Kunde:**
**Verkauf** → **Kunden** → Kunde öffnen → Feld **"Rückgabefrist (Tage)"**

### KI-API-Schlüssel

Die KI-Schlüssel werden nicht im RMA-Modul selbst eingestellt, sondern in den globalen Odoo-Systemparametern:

**Navigation:** **Einstellungen** → **Technisch** → **Parameter** → **Systemparameter**

| Schlüssel | Wert |
|-----------|------|
| `ai.openai_key` | OpenAI API-Key (bevorzugt) |
| `ai.google_key` | Google API-Key (Fallback) |

Ist keiner hinterlegt, erscheint beim Öffnen des KI-Inspektors eine Fehlermeldung.

### Ausgehender Mailserver (für Portal-E-Mails)

**Navigation:** **Einstellungen** → **Technisch** → **Ausgehende Mailserver**

Hier muss ein SMTP-Server konfiguriert sein, damit Kunden die Genehmigungs-E-Mail erhalten. Ohne Mailserver schlägt der E-Mail-Versand fehl.

Typische Konfiguration:
- Host: `mail.firmen-domain.de`
- Port: `465` (SSL/TLS) oder `587` (STARTTLS)
- Authentifizierung: Benutzername
- Benutzername + Passwort: E-Mail-Konto der Firma

---

## 14. Häufige Fehler und Lösungen

### "Zugriff verweigert" oder Funktion nicht sichtbar

**Ursache:** Fehlende Berechtigung.
**Lösung:** Administrator bitten, die Rolle "RMA Benutzer" oder "RMA Manager" zuzuweisen. Pfad für den Administrator: Einstellungen → Benutzer → Benutzer öffnen → Abschnitt "RMA Management".

---

### Artikel erscheinen nicht in der Rückgabeliste

**Ursache:** Nur Artikel, die tatsächlich aus dem Verkaufsauftrag geliefert wurden, erscheinen in der RMA-Erstellung.
**Lösung:** Prüfen, ob der Lieferbeleg des Verkaufsauftrags validiert ist. Nicht gelieferte Artikel können nicht retourniert werden.

---

### Summe stimmt nicht bei Mengenprüfung

**Ursache:** A + B + C ≠ Retourenmenge.
**Lösung:** Die Summe aller Qualitätsklassen muss exakt der erwarteten Retourenmenge entsprechen. Werte nochmal prüfen und korrigieren.

---

### E-Mail-Versand schlägt fehl ("Zustellungsfehler")

**Ursache:** Kein Mailserver konfiguriert, oder SMTP-Zugangsdaten falsch.
**Lösung:** Einstellungen → Technisch → Ausgehende Mailserver → Verbindung testen. Bei Fehler: SMTP-Daten prüfen oder IT-Administrator kontaktieren.

---

### KI-Klassifizierung gibt keinen Vorschlag

**Ursache 1:** Kein API-Key hinterlegt.
**Lösung:** Administrator in Systemparametern `ai.openai_key` oder `ai.google_key` eintragen lassen.

**Ursache 2:** API-Guthaben erschöpft.
**Lösung:** Im jeweiligen API-Dashboard (OpenAI oder Google) prüfen und ggf. aufladen.

---

### Portal-Anfrage erscheint nicht bei der RMA-Erstellung

**Ursache:** Nur Anfragen mit Status "Genehmigt" erscheinen in der kombinierten Referenzliste.
**Lösung:** Zuerst die Anfrage in "Portal-Anfragen" öffnen und auf "Genehmigen & E-Mail senden" klicken.

---

### Reparaturauftrag wurde nicht erstellt

**Ursache:** Kein B-Ware-Eintrag bei der Mengenprüfung.
**Lösung:** Reparaturaufträge entstehen nur, wenn mindestens eine Einheit als B-Ware eingetragen wurde. Bei C-Ware oder A-Ware entstehen keine Reparaturaufträge.

---

### "Artikel nicht in der Rechnung gefunden" im Portal

**Ursache:** Die eingegebene Rechnungsnummer existiert nicht, ist nicht gebucht oder die E-Mail-Adresse stimmt nicht überein.
**Lösung:** Kunden bitten, die Rechnungsnummer genau so einzugeben wie sie auf der Rechnung steht (z. B. `INV/2026/00042`). Außerdem prüfen ob die verwendete E-Mail mit dem Kundendatensatz in Odoo übereinstimmt.

---

## 15. Benutzer und Rechte

**Navigation (nur für Administratoren):** **Einstellungen** → **Benutzer und Unternehmen** → **Benutzer**

### Berechtigung zuweisen

1. Benutzer in der Liste öffnen
2. Im Abschnitt **"RMA Management"** eine Rolle auswählen:
   - leer = kein Zugriff
   - **RMA Benutzer** = normaler Zugriff
   - **RMA Manager** = voller Zugriff inkl. Konfiguration
3. Speichern

### Kundenzugang für das Portal

Kunden brauchen **keinen** Odoo-Account. Das Portal `/rma/anfrage` ist öffentlich erreichbar — die Verifizierung erfolgt per E-Mail und Rechnungsnummer.

---

## Anhang — Schnellübersicht Navigations-Pfade

| Aufgabe | Navigationspfad |
|---------|----------------|
| Portal-Anfragen bearbeiten | RMA Management → Portal-Anfragen |
| RMA erstellen | RMA Management → Erstellung |
| RMA aus Verkaufsauftrag | Verkauf → Aufträge → Auftrag → "RMA erstellen" |
| Mengenprüfung | RMA Management → Mengenprüfung |
| Reparaturaufträge | Reparatur → Reparaturaufträge |
| Auswertung | RMA Management → Auswertung |
| Audit-Log | RMA Management → Übersicht → Audit-Log |
| Rückgabegründe | RMA Management → Rückgabegründe |
| RMA-Einstellungen | Lager → Konfiguration → Einstellungen → RMA Management |
| Mailserver | Einstellungen → Technisch → Ausgehende Mailserver |
| API-Keys (KI) | Einstellungen → Technisch → Parameter → Systemparameter |
| Individuelle Rückgabefrist | Verkauf → Kunden → Kunde → "Rückgabefrist (Tage)" |
| Benutzerrechte | Einstellungen → Benutzer → Benutzer → "RMA Management" |
| Portal-URL für Kunden | /rma/anfrage |

---

**© 2026 MSV Systemhaus Martin Schlaak GmbH — Alle Rechte vorbehalten**
