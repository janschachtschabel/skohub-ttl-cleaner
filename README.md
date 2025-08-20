# TTL Cleaner (SKOS) – README (DE)

Dieses Dokument beschreibt ein Kommandozeilen-Tool zur Bereinigung und Validierung von SKOS-Vokabularen im Turtle-Format (TTL). Der Fokus liegt auf robuster Verarbeitung, klaren Berichten und prüfbarer Hierarchiekonsistenz.

## Überblick

- Liest eine TTL-Datei, bereinigt Inhalte und schreibt eine neue, bereinigte Datei.
- Führt optional Validierungen durch (SKOS-Labels, Beziehungen, Schemes, Hierarchie).
- Schreibt Berichte über Änderungen und Validierungsergebnisse.
- Unterstützt Mehrfachwerte in SKOS-Properties (z. B. `skos:narrower` mit mehreren URIs).

## Installation

Voraussetzungen: Python 3.x

```bash
python -m pip install -r requirements.txt
```

`requirements.txt` enthält u. a.:
- rdflib>=6.3.2

## Verwendung (CLI)

Grundaufrufe:

```bash
# Standard: bereinigt und erstellt Reports
python ttl_cleaner.py input.ttl

# Mit benutzerdefiniertem Output-Pfad
python ttl_cleaner.py input.ttl -o output_cleaned.ttl

# Ausführliche Ausgabe
python ttl_cleaner.py input.ttl -v

# Nur bereinigen, keine Reports
python ttl_cleaner.py input.ttl --no-reports
```

Leistungs- und Validierungsoptionen:

```bash
# Große Dateien: speicherschonend und größere Chunks
python ttl_cleaner.py input.ttl --memory-efficient --chunk-size 2000

# Validierung deaktivieren (nur Cleaning)
python ttl_cleaner.py input.ttl --no-validation

# SKOS-XL-Labelvalidierung aktivieren
python ttl_cleaner.py input.ttl --enable-skos-xl

# Hierarchie-Autofix (fehlende skos:broader ergänzen)
python ttl_cleaner.py input.ttl --autofix-broader -v

# Optionale Hinweise: Eltern ohne explizites skos:narrower zurück auf das Kind
python ttl_cleaner.py input.ttl --warn-missing-narrower -v
```

## CLI-Referenz

- `input_file` (positional): Pfad zur Eingabedatei (TTL)
- `-o, --output`: Pfad zur Ausgabedatei (Default: `input_cleaned.ttl`)
- `-v, --verbose`: Ausführliche Konsolenausgabe
- `--chunk-size <int>`: Größe der Verarbeitungschunks (Default: 1000)
- `--memory-efficient`: Speicherschonender Modus für sehr große Dateien
- `--no-validation`: SKOS-Validierung überspringen
- `--enable-skos-xl`: SKOS-XL-Labelvalidierung aktivieren
- `--autofix-broader`: Fehlende `skos:broader` zum nächstliegenden Präfix-Elternkonzept ergänzen
- `--warn-missing-narrower`: Info-Hinweise ausgeben, wenn Elternkonzept kein explizites `skos:narrower` zurück auf das Kind hat
- `--no-reports`: Keine Report-Dateien schreiben

## Modi und Wirkung (Prüfen vs. Ändern)

| Modus/Flag | Prüft (Validierung) | Ändert TTL | Berichte/Konsole |
|---|---|---|---|
| Standard (ohne Flags) | SKOS-Validierung aktiv (Labels, Relationen, Schemes, Hierarchie) | Bereinigt und schreibt `*_cleaned.ttl` | `*_validation.log`, `*_changes.log` (falls Änderungen), `*_full.log`, Konsolenübersicht |
| `--no-validation` | Keine Validierung | Nur Bereinigung/Schreiben | Keine Validierungssektion; `*_changes.log` (falls Änderungen), `*_full.log` |
| `--enable-skos-xl` | Zusätzlich SKOS-XL-Labelprüfungen | Nein | Validierungsberichte enthalten SKOS-XL-Prüfungen |
| `--autofix-broader` | Wie Standard | Ja: ergänzt fehlende `skos:broader` zum nächstliegenden existierenden Präfix-Elternkonzept (am Kind) | `*_changes.log` mit „Autofix“-Einträgen; weniger Hierarchie-Warnungen erwartet |
| `--warn-missing-narrower` | Info-Level-Hinweise, wenn Eltern kein explizites `skos:narrower` zurück zum Kind haben | Nein | Infos im Validation-/Full-Report (optional) |
| `--memory-efficient` | Unverändert (nur Verarbeitungsmodus) | Nein | Keine inhaltliche Änderung der Berichte |
| `--chunk-size <n>` | Unverändert (nur Verarbeitungsmodus) | Nein | Keine inhaltliche Änderung der Berichte |
| `--no-reports` | Wie konfiguriert | Wie konfiguriert | Keine Logdateien, nur `*_cleaned.ttl` |
| `-v/--verbose` | Unverändert | Unverändert | Mehr Konsolenausgaben |

## Ausgabedateien

Standardmäßig werden (ohne `--no-reports`) erzeugt:

```
input.ttl -> input_cleaned.ttl
             input_cleaned_validation.log
             input_cleaned_changes.log
             input_cleaned_full.log
```

- `*_cleaned.ttl`: Bereinigte TTL-Datei.
- `*_validation.log`: Detaillierter Validierungsbericht (auch bei 0 Befunden, inkl. Zusammenfassung nach Prüftypen).
- `*_changes.log`: Änderungen, die beim Cleaning/Autofix erfolgt sind (nur wenn Änderungen anfielen).
- `*_full.log`: Kombinierter Gesamtbericht (Statistik, Validierung – inkl. optionaler Infos – und Änderungen).

## Validierung (Überblick)

Die Validierung umfasst u. a.:

- Label-Konsistenz (z. B. maximal ein bevorzugtes Label pro Sprache, disjunkte Label-Typen).
- Konsistenz semantischer Relationen (`skos:broader`, `skos:narrower`, `skos:related`).
- Scheme-Konsistenz (`skos:inScheme`, `skos:topConceptOf`, `skos:hasTopConcept`).
- Hierarchieprüfungen (siehe unten).

Hinweis: SKOS-XL-Labelvalidierung ist optional und nur aktiv mit `--enable-skos-xl`.

## Hierarchieprüfungen und Autofix

- Präfixbasierte Hierarchie: Aus numerischen/segmentierten Codes eines Konzepts werden mögliche Elternpräfixe abgeleitet. Fehlende `skos:broader`-Beziehungen zum nächsten bestehenden Präfix-Elternkonzept werden als Warnungen gemeldet.
- Optionaler Autofix (`--autofix-broader`): Ergänzt am Kind fehlende `skos:broader` zum nächstliegenden existierenden Präfix-Elternkonzept vor der Validierung. Dadurch reduzieren sich entsprechende Warnungen.
- Optionale Hinweise (`--warn-missing-narrower`): Info-Level-Hinweise, wenn ein Elternkonzept kein explizites `skos:narrower` zurück auf sein Kind hat (nur Hinweis, keine Verletzung).

Grenzen:
- Der Autofix ergänzt nur `skos:broader` am Kind; ein spiegelndes `skos:narrower` am Elternkonzept wird nicht automatisch erzeugt.

## Mehrfachwerte (Multi-URI) in Properties

Mehrfachwerte in Zeilen wie `skos:narrower`, `skos:broader`, `skos:related`, `skos:inScheme`, `skos:topConceptOf` werden vollständig berücksichtigt. Alle URIs innerhalb spitzer Klammern werden extrahiert – auch in komma-separierten Listen, ggf. mehrzeilig.

Beispiel:

```turtle
# Mehrzeilige Liste
skos:narrower <http://example.org/c1>,
              <http://example.org/c2>,
              <http://example.org/c3> ;
```

## Beispiele

- Schneller Lauf mit Reports:
  ```bash
  python ttl_cleaner.py vocab.ttl
  ```
- Performance für große Dateien:
  ```bash
  python ttl_cleaner.py vocab.ttl --memory-efficient --chunk-size 2000
  ```
- Hierarchie-Autofix und ausführliche Ausgabe:
  ```bash
  python ttl_cleaner.py vocab.ttl --autofix-broader -v
  ```
- Optionale Info-Hinweise aktivieren:
  ```bash
  python ttl_cleaner.py vocab.ttl --warn-missing-narrower -v
  ```

## Hinweise

- Die Originaldatei wird nicht überschrieben; die Ausgabe erfolgt in eine neue Datei.
- Validierungsberichte werden auch bei 0 Befunden erzeugt (Zusammenfassungen mit Zählwerten). `--no-reports` unterdrückt alle Logdateien.
- Stellen Sie sicher, dass URIs in spitzen Klammern notiert sind, damit Mehrfachwerte korrekt erkannt werden.

---

Dieses Dokument beschreibt ausschließlich die Nutzung des TTL Cleaners. Für projektspezifische Aspekte siehe ggf. die Datei `README.md` im Repository-Wurzelverzeichnis.
