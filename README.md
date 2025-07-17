# TTL Cleaner - ESCO Skills Data Processor

Ein spezialisiertes Tool zur Bereinigung und Korrektur von TTL (Turtle) Dateien mit SKOS-Konzepten, insbesondere für ESCO Skills Daten.

## 🎯 Hauptfunktionen

### ✅ Duplikat-Entfernung
- Erkennt und entfernt doppelte Konzepte basierend auf URI
- Protokolliert alle entfernten Duplikate im Änderungslog

### ✅ URI-Struktur Erhaltung
- **@base Declaration**: Erkennt und erhält `@base <URI>` Deklarationen
- **Relative URIs**: Konvertiert absolute URIs zurück zu relativen `<uuid>` Format
- **ConceptScheme**: Erhält `skos:ConceptScheme` Metadaten
- **Namespace Prefixes**: Behält alle `@prefix` Deklarationen bei

### ✅ SKOS-Properties Erhaltung
- **Alle SKOS-Eigenschaften**: `skos:exactMatch`, `skos:narrower`, `skos:broader`, etc.
- **ESCO-Referenzen**: Erhält `skos:exactMatch esco:...` Verknüpfungen
- **Hierarchische Beziehungen**: Behält Konzept-Hierarchien bei
- **Labels**: Verarbeitet `skos:prefLabel` und `skos:altLabel` mit Sprachkennzeichnungen

### ✅ Text-Korrekturen
- **Komma-Spacing**: Korrigiert fehlende Leerzeichen nach Kommas
- **TTL-Syntax**: Behebt Komma/Semikolon Probleme in TTL-Formatierung
- **Encoding**: Unterstützt verschiedene Zeichenkodierungen (UTF-8, Latin1, etc.)

### ✅ Änderungsprotokoll
- **Detailliertes Log**: Protokolliert alle Änderungen in separater `.log` Datei
- **Statistiken**: Zeigt Anzahl der Korrekturen und Verbesserungen
- **Nachverfolgbarkeit**: Vollständige Dokumentation aller Modifikationen

## 🚀 Verwendung

### Kommandozeile
```bash
# Basis-Verwendung (automatische Ausgabedatei)
python ttl_cleaner.py input.ttl

# Mit spezifischer Ausgabedatei
python ttl_cleaner.py input.ttl -o output_clean.ttl

# Mit ausführlicher Ausgabe
python ttl_cleaner.py input.ttl -v
```

### Parameter
- `input_file`: Pfad zur TTL-Eingabedatei (erforderlich)
- `-o, --output`: Pfad zur bereinigten Ausgabedatei (optional)
- `-v, --verbose`: Ausführliche Ausgabe aktivieren (optional)

---

## 📁 Input/Output Dateien

### Input-Datei
**Format**: TTL (Turtle) Datei mit SKOS-Konzepten
**Encoding**: UTF-8, UTF-8-BOM, Latin1, CP1252 (automatische Erkennung)
**Struktur**: Beliebige TTL-Datei mit `@base`, `@prefix` und SKOS-Konzepten

**Beispiel Input-Struktur**:
```turtle
@base <http://w3id.org/openeduhub/vocabs/escoSkills/> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix esco: <http://data.europa.eu/esco/skill/> .

<> a skos:ConceptScheme ;
    dct:title "ESCO Skills"@de .

<uuid1> a skos:Concept ;
    skos:prefLabel "Beispiel,Skill"@de ;
    skos:exactMatch esco:uuid1 ;
    skos:inScheme <> .

<uuid1> a skos:Concept ;  # Duplikat!
    skos:prefLabel "Anderes Label"@de .
```

### Output-Datei
**Automatische Benennung**: Wenn keine `-o` Option angegeben wird:
- Input: `example.ttl` → Output: `example_cleaned.ttl`
- Input: `esco_skills.ttl` → Output: `esco_skills_cleaned.ttl`

**Manuelle Benennung**: Mit `-o` Option:
```bash
python ttl_cleaner.py input.ttl -o my_clean_file.ttl
```

**Bereinigte Ausgabe-Struktur**:
```turtle
@base <http://w3id.org/openeduhub/vocabs/escoSkills/> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix esco: <http://data.europa.eu/esco/skill/> .

<> a skos:ConceptScheme ;
    dct:title "ESCO Skills"@de .

<uuid1> a skos:Concept ;
    skos:prefLabel "Beispiel, Skill"@de ;  # Komma-Spacing korrigiert
    skos:exactMatch esco:uuid1 ;
    skos:inScheme <> .  # Duplikat entfernt, TTL-Syntax korrigiert
```

---

## 📋 Change Log Datei

### Automatische Erstellung
Für jede bereinigte TTL-Datei wird automatisch ein Change Log erstellt:
- Input: `example.ttl` → Log: `example_cleaned_changes.log`
- Input: `esco_skills.ttl` → Log: `esco_skills_cleaned_changes.log`

### Log-Datei Struktur
```
TTL CLEANER CHANGE LOG
Generated: 2025-07-17 09:30:15
============================================================

SUMMARY:
- Total concepts processed: 13939
- Duplicates removed: 2987
- Labels processed: 20187
- Comma spacing fixes: 167
- Malformed URIs fixed: 13939
- Encoding issues fixed: 0

DETAILED CHANGES:
----------------------------------------
   1. Duplicate removed: http://w3id.org/openeduhub/vocabs/escoSkills/001d46db-035e-4b92-83a3-ed8771e0c123
   2. Duplicate removed: http://w3id.org/openeduhub/vocabs/escoSkills/002a8b8a-3b7c-4d8e-9f1a-8c7d6e5f4a3b
   3. Comma spacing fixed: 'Kommunikation,Teamarbeit' → 'Kommunikation, Teamarbeit'
   4. Comma spacing fixed: 'Projektmanagement,Führung' → 'Projektmanagement, Führung'
   ...
```

### Log-Kategorien

#### 1. **Duplicate Removal**
```
Duplicate removed: http://w3id.org/openeduhub/vocabs/escoSkills/uuid
```
- Zeigt entfernte doppelte Konzepte
- Vollständige URI des entfernten Duplikats
- Erste Instanz wird beibehalten

#### 2. **Comma Spacing Fixes**
```
Comma spacing fixed: 'Text,ohne' → 'Text, ohne'
```
- Korrigiert fehlende Leerzeichen nach Kommas
- Zeigt Vorher/Nachher Vergleich
- Betrifft hauptsächlich deutsche Labels

#### 3. **URI Normalization**
```
URI normalized: <relative-uuid> → http://w3id.org/openeduhub/vocabs/escoSkills/uuid
```
- Konvertiert relative URIs zu vollständigen URIs
- Verwendet @base URI als Basis
- Stellt Konsistenz sicher

#### 4. **TTL Syntax Fixes**
```
TTL syntax fixed: Comma replaced with semicolon in property list
```
- Behebt TTL-Formatierungsfehler
- Korrigiert Komma/Semikolon Probleme
- Stellt valide TTL-Syntax sicher

---

## 📊 Konsolen-Ausgabe

### Standard-Ausgabe
```
[OK] File read successfully with encoding: utf-8
[INFO] Processing: esco_skills_v1.2.0.ttl
[INFO] Original file size: 8456789 characters
[INFO] Found @base URI: http://w3id.org/openeduhub/vocabs/escoSkills/
[OK] Cleaned file saved: esco_skills_v1.2.0_cleaned.ttl

============================================================
TTL CLEANING REPORT
============================================================
Input file:  esco_skills_v1.2.0.ttl
Output file: esco_skills_v1.2.0_cleaned.ttl
Log file:    esco_skills_v1.2.0_cleaned_changes.log

STATISTICS:
   Total concepts processed: 13939
   Duplicates removed: 2987
   Malformed URIs fixed: 13939
   Concepts without prefLabel: 1
   Encoding issues fixed: 0
   Comma spacing fixes: 167
   Final concepts in output: 10951

[SUCCESS] Cleaning completed!
```

### Verbose-Ausgabe (-v)
```
[DEBUG] Detected encoding: utf-8
[DEBUG] @base URI extracted: http://w3id.org/openeduhub/vocabs/escoSkills/
[DEBUG] Processing concept: <001d46db-035e-4b92-83a3-ed8771e0c123>
[DEBUG] Duplicate found: <001d46db-035e-4b92-83a3-ed8771e0c123>
[DEBUG] Comma spacing fix: 'Kommunikation,Teamarbeit' → 'Kommunikation, Teamarbeit'
[DEBUG] Writing cleaned concept: <001d46db-035e-4b92-83a3-ed8771e0c123>
...
```

---

## 🔍 Praktische Anwendungsbeispiele

### 1. ESCO Skills bereinigen
```bash
# Generiere ESCO Skills TTL
python esco_ttl_generator.py "ESCO dataset - v1.2.0 - classification - de - csv" esco_skills_v1.2.0.ttl

# Bereinige die generierte Datei
python ttl_cleaner.py esco_skills_v1.2.0.ttl

# Ergebnis:
# - esco_skills_v1.2.0_cleaned.ttl (bereinigte TTL)
# - esco_skills_v1.2.0_cleaned_changes.log (Änderungsprotokoll)
```

### 2. ESCO Occupations bereinigen
```bash
# Generiere ESCO Occupations TTL
python esco_occupations_ttl_generator.py "ESCO dataset - v1.2.0 - classification - de - csv" esco_occupations_v1.2.0.ttl

# Bereinige die generierte Datei
python ttl_cleaner.py esco_occupations_v1.2.0.ttl

# Ergebnis:
# - esco_occupations_v1.2.0_cleaned.ttl (bereinigte TTL)
# - esco_occupations_v1.2.0_cleaned_changes.log (Änderungsprotokoll)
```

### 3. Beliebige TTL-Datei bereinigen
```bash
# Mit automatischer Ausgabedatei
python ttl_cleaner.py my_vocabulary.ttl

# Mit spezifischer Ausgabedatei
python ttl_cleaner.py my_vocabulary.ttl -o clean_vocabulary.ttl

# Mit ausführlicher Ausgabe
python ttl_cleaner.py my_vocabulary.ttl -v
```

### 4. Batch-Verarbeitung
```bash
# Windows Batch-Datei (clean_ttl.bat)
for %%f in (*.ttl) do python ttl_cleaner.py "%%f"

# Linux/Mac Bash
for file in *.ttl; do python ttl_cleaner.py "$file"; done
```

---

## ⚠️ Wichtige Hinweise

### Dateisicherheit
- **Backup**: Erstellen Sie immer eine Sicherungskopie der Original-TTL-Datei
- **Überschreibung**: Der Cleaner überschreibt niemals die Eingabedatei
- **Validierung**: Prüfen Sie die bereinigte Datei vor der Verwendung

### Performance
- **Große Dateien**: Verarbeitung kann bei >10MB Dateien einige Minuten dauern
- **Speicher**: Benötigt etwa 3x die Dateigröße als RAM
- **Fortschritt**: Verwenden Sie `-v` für Fortschrittsanzeige bei großen Dateien

### Kompatibilität
- **TTL-Standard**: Unterstützt Turtle (TTL) Format nach W3C-Standard
- **SKOS-Vokabular**: Optimiert für SKOS-Konzepte und -Properties
- **Encoding**: Automatische Erkennung verschiedener Zeichenkodierungen

---

## 🔧 Fehlerbehebung

### Häufige Probleme

#### 1. **Encoding-Fehler**
```
UnicodeDecodeError: 'utf-8' codec can't decode...
```
**Lösung**: Tool verwendet automatische Encoding-Erkennung

#### 2. **Speicher-Probleme**
```
MemoryError: Unable to allocate array
```
**Lösung**: Verarbeiten Sie sehr große Dateien (>100MB) in kleineren Teilen

#### 3. **Malformed TTL**
```
TTL parsing error: Invalid syntax
```
**Lösung**: Tool korrigiert automatisch häufige TTL-Syntax-Fehler

#### 4. **Keine @base URI gefunden**
```
Warning: No @base URI found, using relative URIs
```
**Lösung**: Normal, wenn TTL-Datei keine @base-Deklaration hat

### Debug-Modus
```bash
# Ausführliche Ausgabe für Debugging
python ttl_cleaner.py input.ttl -v
```

---

## 📈 Qualitätssicherung

### Validierung
- **TTL-Syntax**: Automatische Korrektur häufiger Syntax-Fehler
- **SKOS-Struktur**: Erhaltung aller SKOS-Properties und -Beziehungen
- **URI-Konsistenz**: Normalisierung zu einheitlichen URI-Formaten
- **Duplikat-Erkennung**: Zuverlässige Identifikation doppelter Konzepte

### Testresultate
- **ESCO Skills**: 13.939 → 10.951 Konzepte (2.987 Duplikate entfernt)
- **ESCO Occupations**: 3.039 → 3.039 Konzepte (keine Duplikate)
- **KLDB Sample**: 10 → 10 Konzepte (167 Komma-Korrekturen)

### Datenintegrität
- **Vollständigkeit**: Alle SKOS-Properties bleiben erhalten
- **Referenzen**: ESCO-Referenzen (`skos:exactMatch`) bleiben intakt
- **Hierarchien**: Konzept-Hierarchien (`broader`/`narrower`) bleiben erhalten
- **Metadaten**: ConceptScheme und Dublin Core Terms bleiben erhalten

---

## 🚀 Integration

### Skills&More Workflow
```bash
# 1. Generiere ESCO TTL
python esco_ttl_generator.py "ESCO dataset" esco_skills.ttl

# 2. Bereinige TTL
python ttl_cleaner.py esco_skills.ttl

# 3. Upload in Streamlit
# Verwende: esco_skills_cleaned.ttl
```

### Automatisierung
```bash
# Windows Batch-Datei
@echo off
for %%f in (*.ttl) do (
    echo Cleaning %%f...
    python ttl_cleaner.py "%%f"
)
echo All TTL files cleaned!
```

### CI/CD Integration
```yaml
# GitHub Actions Beispiel
- name: Clean TTL Files
  run: |
    for file in *.ttl; do
      python ttl_cleaner.py "$file"
    done
```

---

## 📋 Changelog

### Version 1.3 (Aktuell)
- ✅ Vollständige SKOS-Property-Erhaltung
- ✅ Verbesserte @base URI-Behandlung
- ✅ Detailliertes Change-Logging
- ✅ Windows-Konsolen-Kompatibilität
- ✅ Erweiterte Encoding-Unterstützung

### Version 1.2
- ✅ Duplikat-Entfernung implementiert
- ✅ Komma-Spacing-Korrektur
- ✅ TTL-Syntax-Fixes

### Version 1.1
- ✅ Basis-TTL-Verarbeitung
- ✅ SKOS-Konzept-Extraktion

---

**Für weitere Informationen und Support kontaktieren Sie das Skills&More Entwicklungsteam.**
