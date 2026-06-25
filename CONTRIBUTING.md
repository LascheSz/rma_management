# 🤝 Beitragsleitfaden für RMA Management

Danke, dass Sie daran interessiert sind, zu RMA Management beizutragen! Dieses Dokument enthält Richtlinien und Anweisungen für die Zusammenarbeit.

---

## 📋 Inhaltsverzeichnis

1. [Code of Conduct](#code-of-conduct)
2. [Wie kann ich beitragen?](#wie-kann-ich-beitragen)
3. [Entwicklungsrichtlinien](#entwicklungsrichtlinien)
4. [Git Workflow](#git-workflow)
5. [Code-Stil](#code-stil)
6. [Testing](#testing)
7. [Pull Request Prozess](#pull-request-prozess)

---

## 📜 Code of Conduct

Alle Beiträger müssen sich an unseren [Code of Conduct](CODE_OF_CONDUCT.md) halten.

**Zusammenfassung:**
- ✅ Respekt und Höflichkeit
- ✅ Konstruktives Feedback
- ✅ Fokus auf das Beste für die Community
- ❌ Keine Belästigung oder Diskriminierung
- ❌ Keine Spam oder Werbung

---

## 🎯 Wie kann ich beitragen?

### 🐛 Fehler melden

Fehler können über [GitHub Issues](https://github.com/LascheSz/rma_management/issues) gemeldet werden.

**Bitte verwenden Sie die Bug Report Template:**
```
1. Gehen Sie zu Issues
2. Klicken Sie "New Issue"
3. Wählen Sie "🐛 Bug Report"
4. Füllen Sie alle Felder aus
```

### ✨ Feature Requests

Feature-Anfragen können auch über Issues eingereicht werden.

**Bitte verwenden Sie die Feature Request Template:**
```
1. Gehen Sie zu Issues
2. Klicken Sie "New Issue"
3. Wählen Sie "✨ Feature Request"
4. Beschreiben Sie Ihre Idee
```

### 🔒 Sicherheitsprobleme

**WICHTIG:** Sicherheitsprobleme sollten NICHT öffentlich gemeldet werden!

Senden Sie stattdessen eine E-Mail an: **security@msv-systemhaus.de**

### 📚 Dokumentation verbessern

Dokumentation ist genauso wichtig wie Code. Sie können:
- README verbessern
- Typos korrigieren
- Beispiele hinzufügen
- Dokumentation übersetzen

---

## 💻 Entwicklungsrichtlinien

### Voraussetzungen

- Python 3.8+
- Odoo 16.0+
- Git
- PostgreSQL (für Tests)

### Umgebung einrichten

```bash
# 1. Fork das Repository
git clone https://github.com/YOUR_USERNAME/rma_management.git
cd rma_management

# 2. Erstellen Sie einen Feature Branch
git checkout -b feature/your-feature-name

# 3. Installieren Sie Abhängigkeiten
pip install -r requirements.txt

# 4. Starten Sie die Entwicklung
# ... Ihre Änderungen ...
```

---

## 🔄 Git Workflow

### Branch-Naming Konvention

```
feature/feature-name          # Neue Features
bugfix/bug-name              # Fehlerbehebungen
docs/documentation-update    # Dokumentation
refactor/refactoring-name    # Code-Refactoring
test/test-name               # Tests
```

### Commit-Nachricht Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Typen:**
- `feat`: Neue Funktion
- `fix`: Fehlerbehebung
- `docs`: Dokumentation
- `style`: Code-Stil (keine Logik-Änderungen)
- `refactor`: Code-Refactoring
- `test`: Tests hinzufügen/ändern
- `chore`: Build, Dependencies, etc.

**Beispiele:**
```
feat(rma-order): Add serial number support
fix(splitting): Correct quantity calculation
docs(readme): Update installation instructions
```

---

## 🎨 Code-Stil

### Python Code-Stil

Wir folgen [PEP 8](https://www.python.org/dev/peps/pep-0008/):

```python
# ✅ Gut
def calculate_total_quantity(items):
    """Calculate total quantity from items."""
    return sum(item.quantity for item in items)

# ❌ Schlecht
def calc_qty(i):
    return sum(x.qty for x in i)
```

### Tools

```bash
# Code formatieren
black models/

# Imports sortieren
isort models/

# Linting
flake8 models/
pylint models/
```

### Docstrings

```python
def create_rma_order(sale_order, reason_id, quantities):
    """
    Create RMA order from sale order.
    
    Args:
        sale_order (sale.order): The sale order to create RMA from
        reason_id (int): RMA reason ID
        quantities (dict): Mapping of product_id to quantity
    
    Returns:
        stock.picking: Created RMA picking
    
    Raises:
        ValueError: If quantities are invalid
    """
```

---

## 🧪 Testing

### Tests schreiben

```bash
# Tests ausführen
python -m pytest tests/ -v

# Mit Coverage
python -m pytest tests/ --cov=models --cov-report=html
```

### Test-Struktur

```python
from odoo.tests import TransactionCase, Command

class TestRMAOrder(TransactionCase):
    """Test RMA Order functionality."""
    
    def setUp(self):
        super().setUp()
        self.sale_order = self.env['sale.order'].create({
            'partner_id': self.env.ref('base.partner_admin').id,
        })
    
    def test_create_rma_order(self):
        """Test RMA order creation."""
        wizard = self.env['rma.order'].create({
            'sale_order_id': self.sale_order.id,
        })
        self.assertEqual(wizard.sale_order_id, self.sale_order)
```

### Mindestens 80% Code Coverage

Neue Features sollten mindestens 80% Code Coverage haben.

---

## 📤 Pull Request Prozess

### Vor dem Pull Request

1. **Aktualisieren Sie Ihren Branch:**
   ```bash
   git fetch origin
   git rebase origin/main
   ```

2. **Tests ausführen:**
   ```bash
   python -m pytest tests/ -v
   ```

3. **Code-Qualität prüfen:**
   ```bash
   black models/
   isort models/
   flake8 models/
   ```

4. **Commits squashen (optional):**
   ```bash
   git rebase -i origin/main
   ```

### Pull Request erstellen

1. Gehen Sie zu [Pull Requests](https://github.com/LascheSz/rma_management/pulls)
2. Klicken Sie "New Pull Request"
3. Wählen Sie Ihren Branch
4. Füllen Sie die PR-Beschreibung aus

### PR-Beschreibung Template

```markdown
## 📝 Beschreibung
Kurze Beschreibung der Änderungen.

## 🎯 Typ der Änderung
- [ ] 🐛 Fehlerbehebung
- [ ] ✨ Neue Funktion
- [ ] 📚 Dokumentation
- [ ] ♻️ Refactoring

## 🔗 Verknüpfte Issues
Schließt #123

## ✅ Checkliste
- [ ] Mein Code folgt den Code-Richtlinien
- [ ] Ich habe die Dokumentation aktualisiert
- [ ] Ich habe Tests hinzugefügt
- [ ] Alle Tests bestanden
- [ ] Keine neuen Warnungen
```

### Review Prozess

1. **Mindestens 1 Reviewer** muss den PR genehmigen
2. **Alle Checks** müssen bestanden sein
3. **Keine Konflikte** mit main branch
4. **Code Coverage** muss mindestens 80% sein

---

## 📞 Fragen?

Haben Sie Fragen? Kontaktieren Sie uns:

- 📧 Email: support@msv-systemhaus.de
- 💬 Discussions: [GitHub Discussions](https://github.com/LascheSz/rma_management/discussions)
- 📖 Dokumentation: [README](README.md)

---

## 🙏 Danke!

Danke, dass Sie zu RMA Management beitragen! Ihre Hilfe ist wertvoll für uns. 💙

---

**Viel Spaß beim Coden! 🚀**
