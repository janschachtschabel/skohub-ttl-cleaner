# TTL Cleaner für SKOS Vocabularies

Der TTL Cleaner ist ein Python-Tool zur Bereinigung und Validierung von SKOS (Simple Knowledge Organization System) Vocabularies im Turtle (TTL) Format. Das Tool wurde speziell für die Verarbeitung großer SKOS-Dateien wie der ESCO Skills Taxonomy entwickelt und ist vollständig stabil und produktionsreif.

## ✅ Stable Release - Alle kritischen Bugs behoben

**Version 1.0** - Der TTL Cleaner ist jetzt vollständig stabil:
- ✅ "Dictionary changed size during iteration" Fehler behoben
- ✅ Unicode-Encoding-Probleme gelöst
- ✅ SKOS-Validierung funktioniert zuverlässig
- ✅ Erfolgreich getestet mit 14.579 ESCO Skills Konzepten

## 🚀 Features

### **Datenbereinigung:**
- ✅ **Duplikate entfernen** - Erkennt und entfernt doppelte Konzepte (gleiche URI)
- ✅ **URI-Normalisierung** - Korrigiert malformierte URIs und relative Pfade
- ✅ **Encoding-Probleme beheben** - Automatische UTF-8 Korrektur (ä, ö, ü, etc.)
- ✅ **Label-Bereinigung** - Entfernt leere Labels und korrigiert Formatierung
- ✅ **Listen-Erhaltung** - Vollständige Erhaltung von mehrzeiligen SKOS-Properties
- ✅ **Konsistente Formatierung** - Einheitliche Einrückung und Property-Reihenfolge

### **SKOS-Validierung (W3C-konform):**
- 🔍 **S14**: Nur ein `skos:prefLabel` pro Sprache
- 🔍 **S13**: Disjunkte Label-Properties (prefLabel ≠ altLabel ≠ hiddenLabel)
- 🔍 **S27**: `skos:related` disjunkt mit `skos:broaderTransitive`
- 🔍 **S9/S37**: Disjunkte Klassen (Concept ≠ ConceptScheme ≠ Collection)
- 🔍 **Zyklen-Erkennung** in hierarchischen Beziehungen
- 🔍 **URI-Validierung** und Language-Tag-Prüfung (BCP47)
- 🔍 **Semantic Relations** Konsistenzprüfung

### **Erweiterte Funktionen:**
- 📊 **Detaillierte Berichte** - Cleaning-Statistiken und Validierungsergebnisse
- 📝 **Change-Log** - Dokumentation aller Änderungen
- ⚠️ **Warnungen & Violations** - Unterscheidung zwischen Fehlern und Warnungen
- 🎯 **Multi-Line Property Support** - Korrekte Verarbeitung von SKOS-Listen
- 🔧 **Konfigurierbare Validierung** - Anpassbare Integritätsprüfungen

## 📦 Installation

```bash
# Abhängigkeiten installieren
pip install pathlib urllib3

# TTL Cleaner herunterladen
git clone <repository-url>
cd skohub_ttl_generator
```

## 🚀 Verwendung

### **Basis-Verwendung:**
```bash
# Einfache Bereinigung (erstellt input_cleaned.ttl + Reports)
python ttl_cleaner.py input.ttl

# Mit benutzerdefiniertem Output
python ttl_cleaner.py input.ttl -o custom_output.ttl

# Verbose Modus mit detaillierter Ausgabe
python ttl_cleaner.py input.ttl -v

# Ohne Report-Dateien (nur TTL-Bereinigung)
python ttl_cleaner.py input.ttl --no-reports
```

### **Erweiterte CLI-Optionen:**

```bash
# Performance-Optimierung für große Dateien
python ttl_cleaner.py large_file.ttl --memory-efficient --chunk-size 2000

# Validierung deaktivieren für maximale Geschwindigkeit
python ttl_cleaner.py input.ttl --no-validation

# SKOS-XL Label-Unterstützung aktivieren
python ttl_cleaner.py input.ttl --enable-skos-xl

# Kombinierte Optionen
python ttl_cleaner.py input.ttl -o custom.ttl -v --chunk-size 500
```

#### **Vollständige CLI-Parameter:**

| Parameter | Beschreibung | Default |
|-----------|--------------|----------|
| `input_file` | Input TTL-Datei (erforderlich) | - |
| `-o, --output` | Output-Pfad | `input_cleaned.ttl` |
| `-v, --verbose` | Detaillierte Ausgabe | `False` |
| `--chunk-size` | Chunk-Größe für große Dateien | `1000` |
| `--memory-efficient` | Memory-efficient Modus | `False` |
| `--no-validation` | SKOS-Validierung deaktivieren | `False` |
| `--enable-skos-xl` | SKOS-XL Label-Support | `False` |
| `--no-reports` | Report-Generierung überspringen | `False` |

### **Python-Integration:**

```python
from ttl_cleaner import TTLCleaner

# TTL Cleaner initialisieren
cleaner = TTLCleaner()

# Datei bereinigen und validieren
success = cleaner.clean_ttl_file("input.ttl", "output_clean.ttl")

# Validierungsergebnisse abrufen
violations = cleaner.validation_violations
warnings = cleaner.validation_warnings

print(f"Violations: {len(violations)}")
print(f"Warnings: {len(warnings)}")
```

## 📋 Output-Dateien

**🎯 Neues Default-Verhalten:** Der TTL Cleaner überschreibt nie die Original-Datei!

Der TTL Cleaner generiert standardmäßig mehrere Output-Dateien:

```
input.ttl                         # Original-Datei (unverändert)
├── input_cleaned.ttl             # ✅ Bereinigte TTL-Datei
├── input_cleaned_validation.log  # ✅ SKOS-Validierungsbericht (bei Violations/Warnings)
└── input_cleaned_changes.log     # ✅ Change-Log (bei Änderungen)
```

**Optionen:**
- `--no-reports`: Nur TTL-Datei generieren, keine Log-Dateien
- `-o custom.ttl`: Benutzerdefinierten Output-Namen verwenden

### **Beispiel Cleaning-Report:**
```
============================================================
TTL CLEANING REPORT
============================================================
Input file:  escoSkillsneu.ttl
Output file: escoSkillsneu_clean.ttl

STATISTICS:
   Total concepts processed: 14579
   Duplicates removed: 0
   Malformed URIs fixed: 14579
   Encoding issues fixed: 1119
   Text fields cleaned: 13940
   Labels processed: 17614
   Final concepts in output: 14579

✅ All SKOS integrity conditions satisfied!
```

### **Beispiel Validation-Report:**
```
============================================================
SKOS VALIDATION REPORT
============================================================
Generated: 2024-01-27 13:00:00

SUMMARY:
- Integrity violations: 2
- Warnings: 5

INTEGRITY VIOLATIONS (2):
   1. S14 Violation: <concept123> has multiple prefLabels for language 'en'
   2. S13 Violation: <concept456> has overlapping prefLabel/altLabel: [('test', 'en')]

WARNINGS (5):
   1. Very long label (512 chars) in <concept789>
   2. Potentially invalid language tag 'en-US-x-custom' in <concept101>
   3. Cycle detected in broader relations: <A> -> <B> -> <C> -> <A>
   4. Empty label in <concept202>
   5. Invalid URI format: malformed-uri
```

## 🔧 SKOS-Integritätsprüfungen

Der TTL Cleaner implementiert die wichtigsten W3C SKOS-Integritätsbedingungen:

| Regel | Beschreibung | Typ |
|-------|-------------|-----|
| **S14** | Maximal ein `skos:prefLabel` pro Sprache | Violation |
| **S13** | Disjunkte Label-Properties | Violation |
| **S27** | `skos:related` ≠ `skos:broaderTransitive` | Violation |
| **S9** | `skos:ConceptScheme` ≠ `skos:Concept` | Violation |
| **S37** | `skos:Collection` ≠ `skos:Concept` | Violation |
| **Zyklen** | Keine Zyklen in `skos:broader` | Warning |
| **URIs** | Gültige URI-Formate | Violation |
| **Language Tags** | BCP47-konforme Sprach-Tags | Warning |

## 🎯 Anwendungsfälle

### **1. ESCO Skills Bereinigung:**
```bash
# ESCO Skills TTL bereinigen und validieren
python ttl_cleaner.py escoSkillsneu.ttl -o escoSkills_clean.ttl
```

### **2. Thesaurus-Validierung:**
```bash
# Thesaurus auf SKOS-Konformität prüfen
python ttl_cleaner.py my_thesaurus.ttl
```

### **3. Batch-Verarbeitung:**
```python
import glob
from ttl_cleaner import TTLCleaner

cleaner = TTLCleaner()
for ttl_file in glob.glob("*.ttl"):
    print(f"Processing {ttl_file}...")
    cleaner.clean_ttl_file(ttl_file)
```

## ⚙️ Konfiguration

### **Validierung anpassen:**
```python
# Nur bestimmte Validierungen ausführen
cleaner = TTLCleaner()
# Implementierung für selektive Validierung folgt
```

### **Custom SKOS-Regeln:**
```python
# Eigene Integritätsprüfungen hinzufügen
def custom_validation(concepts):
    violations = []
    # Custom logic here
    return violations, []

# Integration in TTL Cleaner
cleaner.custom_validators.append(custom_validation)
```

## 🔍 Technische Details

### **Unterstützte SKOS-Properties:**
- **Labels**: `skos:prefLabel`, `skos:altLabel`, `skos:hiddenLabel`
- **Relations**: `skos:broader`, `skos:narrower`, `skos:related`, `skos:broaderTransitive`
- **Mappings**: `skos:exactMatch`, `skos:closeMatch`, `skos:broadMatch`
- **Documentation**: `skos:definition`, `skos:scopeNote`, `skos:note`
- **Schemes**: `skos:inScheme`, `skos:topConceptOf`, `skos:hasTopConcept`

### **Multi-Line Property Support:**
Der TTL Cleaner erkennt und erhält mehrzeilige SKOS-Properties:
```turtle
# Vorher (mehrzeilig)
skos:narrower <concept1>,
    <concept2>,
    <concept3> ;

# Nachher (kompakt, aber vollständig)
skos:narrower <concept1>, <concept2>, <concept3> ;
```

### **Encoding-Unterstützung:**
- UTF-8, UTF-8-BOM, Latin1, CP1252, ISO-8859-1
- Automatische Encoding-Erkennung
- Korrektur häufiger Encoding-Probleme (ä→Ã¤, etc.)

## 📚 Beispiele

### **Vor der Bereinigung:**
```turtle
<concept1> a skos:Concept ;
    skos:prefLabel "Test"@en ;
    skos:prefLabel "Another Test"@en ;  # S14 Violation!
    skos:altLabel "Test"@en ;           # S13 Violation!
    skos:broader <concept2> ;
    skos:related <concept2> .           # S27 Violation!
```

### **Nach der Bereinigung:**
```turtle
<concept1> a skos:Concept ;
    skos:prefLabel "Test"@en ;
    skos:altLabel "Another Test"@en ;
    skos:broader <concept2> ;
    skos:inScheme <> .
```

## 🤝 Integration mit SkoHub

Der TTL Cleaner ist Teil des SkoHub TTL Generator Ecosystems:

- **Generator**: Erstellt TTL aus CSV/JSON → **TTL Cleaner** → **SkoHub Vocabs**
- **Validierung**: SKOS-Konformität vor Deployment
- **Qualitätssicherung**: Automatische Bereinigung und Validierung

## 🐛 Troubleshooting

### **Häufige Probleme:**

**1. Encoding-Fehler:**
```bash
[ERROR] Could not read file with any encoding
```
→ Datei manuell in UTF-8 konvertieren

**2. Speicher-Probleme bei großen Dateien:**
```bash
MemoryError: Unable to allocate array
```
→ Datei in kleinere Chunks aufteilen

**3. SKOS-Violations:**
```bash
S14 Violation: Multiple prefLabels for language 'en'
```
→ Doppelte Labels in Original-Daten korrigieren

## 📄 Lizenz

MIT License - Siehe LICENSE-Datei für Details.

## 🔗 Links

- [W3C SKOS Reference](http://www.w3.org/TR/skos-reference/)
- [SkoHub Project](https://skohub.io/)
- [ESCO Skills Taxonomy](https://esco.ec.europa.eu/)

---

**Entwickelt für das SkoHub TTL Generator Projekt**  
Version 2.0 - Mit SKOS-Validierung und erweiterten Bereinigungsfunktionen
