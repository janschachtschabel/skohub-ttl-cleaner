#!/usr/bin/env python3
"""
TTL File Cleaner - Fixes common issues in TTL/SKOS files

This script analyzes TTL files for common issues and creates a cleaned version:
- Removes duplicate concepts (same URI)
- Fixes malformed URIs
- Removes concepts without prefLabel
- Fixes encoding issues
- Validates SKOS structure
- Generates detailed report

Usage: python ttl_cleaner.py input.ttl
"""

import re
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict, Counter
import urllib.parse
import urllib.parse

class TTLCleaner:
    """Clean and validate TTL files with SKOS integrity checks and performance optimizations."""
    
    def __init__(self, chunk_size=1000, enable_validation=True, memory_efficient=False, enable_skos_xl=False):
        self.stats = {
            'total_concepts': 0,
            'duplicates_removed': 0,
            'malformed_uris_fixed': 0,
            'encoding_issues_fixed': 0,
            'text_fields_cleaned': 0,
            'labels_processed': 0,
            'final_concepts': 0,
            'definitions_processed': 0,
            'notes_processed': 0,
            'empty_labels_removed': 0,
            'invalid_concepts_removed': 0,
            'comma_fixes': 0,
            'concepts_without_preflabel': 0
        }
        self.errors = []
        self.warnings = []
        self.change_log = []
        self.validation_violations = []
        self.validation_warnings = []
        self.base_declaration = None
        self.concept_scheme = None
        self.other_metadata = []
        
        # Performance settings
        self.chunk_size = chunk_size
        self.enable_validation = enable_validation
        self.memory_efficient = memory_efficient
        self.processed_chunks = 0
        
        # SKOS-XL support
        self.enable_skos_xl = enable_skos_xl

    def clean_ttl_file(self, input_path: str, output_path: Optional[str] = None, generate_reports: bool = True) -> bool:
        """Clean TTL file and save cleaned version."""
        try:
            # Generate default output path with _cleaned suffix if not provided
            if output_path is None:
                input_path_obj = Path(input_path)
                output_path = str(input_path_obj.parent / f"{input_path_obj.stem}_cleaned{input_path_obj.suffix}")
            
            # Read input file
            content = self._read_file_with_encoding(input_path)
            if not content:
                return False

            print(f"[INFO] Processing: {input_path}")
            print(f"[INFO] Original file size: {len(content)} characters")

            # Extract and clean concepts (with chunked processing for large files)
            concepts = self._extract_concepts(content)
            
            if self.memory_efficient and len(concepts) > self.chunk_size:
                cleaned_concepts = self._clean_concepts_chunked(concepts)
            else:
                cleaned_concepts = self._clean_concepts(concepts)

            # Perform SKOS validation (if enabled)
            all_violations = []
            all_warnings = []
            
            if self.enable_validation:
                if self.memory_efficient and len(cleaned_concepts) > self.chunk_size:
                    # Chunked validation for large datasets
                    violations, warnings = self._validate_concepts_chunked(cleaned_concepts)
                else:
                    # Standard validation with debug output
                    try:
                        print("[DEBUG] Starting SKOS integrity validation...")
                        violations, warnings = self._validate_skos_integrity(cleaned_concepts)
                        all_violations.extend(violations)
                        all_warnings.extend(warnings)
                        print(f"[DEBUG] SKOS integrity validation completed: {len(violations)} violations, {len(warnings)} warnings")
                    except Exception as e:
                        print(f"[DEBUG] Error in SKOS integrity validation: {e}")
                        raise
                    
                    try:
                        print("[DEBUG] Starting semantic relations validation...")
                        violations, warnings = self._validate_semantic_relations(cleaned_concepts)
                        all_violations.extend(violations)
                        all_warnings.extend(warnings)
                        print(f"[DEBUG] Semantic relations validation completed: {len(violations)} violations, {len(warnings)} warnings")
                    except Exception as e:
                        print(f"[DEBUG] Error in semantic relations validation: {e}")
                        raise
                    
                    try:
                        print("[DEBUG] Starting datatypes and URIs validation...")
                        violations, warnings = self._validate_datatypes_and_uris(cleaned_concepts)
                        all_violations.extend(violations)
                        all_warnings.extend(warnings)
                        print(f"[DEBUG] Datatypes and URIs validation completed: {len(violations)} violations, {len(warnings)} warnings")
                    except Exception as e:
                        print(f"[DEBUG] Error in datatypes and URIs validation: {e}")
                        raise
                    
                    # SKOS-XL validation if enabled
                    if self.enable_skos_xl:
                        try:
                            print("[DEBUG] Starting SKOS-XL validation...")
                            violations, warnings = self._validate_skos_xl_labels(cleaned_concepts)
                            all_violations.extend(violations)
                            all_warnings.extend(warnings)
                            print(f"[DEBUG] SKOS-XL validation completed: {len(violations)} violations, {len(warnings)} warnings")
                        except Exception as e:
                            print(f"[DEBUG] Error in SKOS-XL validation: {e}")
                            raise
                
                # Store validation results
                self.validation_violations = all_violations
                self.validation_warnings = all_warnings
            else:
                print("[INFO] SKOS validation disabled for performance")

            # Generate output path if not provided
            if not output_path:
                input_file = Path(input_path)
                output_path = input_file.parent / f"{input_file.stem}_cleaned{input_file.suffix}"

            # Write cleaned file
            self._write_cleaned_file(cleaned_concepts, content, output_path)

            # Generate report
            self._print_report(input_path, output_path)
            
            # Print validation report (only if validation was enabled)
            if self.enable_validation:
                print(self._generate_validation_report(all_violations, all_warnings))
            
            # Generate reports if requested
            if generate_reports:
                # Write change log if changes were made
                if self.change_log:
                    log_path = Path(output_path).parent / f"{Path(output_path).stem}_changes.log"
                    self._write_change_log(log_path)
                
                # Write validation report if validation was enabled
                if self.enable_validation and (all_violations or all_warnings):
                    validation_path = Path(output_path).parent / f"{Path(output_path).stem}_validation.log"
                    self._write_validation_report(validation_path, all_violations, all_warnings)

            return True

        except Exception as e:
            print(f"[ERROR] Error processing file: {e}")
            return False

    def clean_file(self, file_path: str) -> Tuple[str, Dict]:
        """Clean TTL file and return content and stats (for Streamlit integration)."""
        try:
            # Read input file
            content = self._read_file_with_encoding(file_path)
            if not content:
                return content, self.stats

            # Extract and clean concepts
            concepts = self._extract_concepts(content)
            cleaned_concepts = self._clean_concepts(concepts)

            # Generate cleaned content
            cleaned_content = self._generate_cleaned_content(cleaned_concepts, content)
            
            return cleaned_content, self.stats

        except Exception as e:
            print(f"[ERROR] Error processing file: {e}")
            return content, self.stats

    def _read_file_with_encoding(self, file_path: str) -> Optional[str]:
        """Read file with multiple encoding attempts."""
        encodings = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252', 'iso-8859-1']

        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                print(f"[OK] File read successfully with encoding: {encoding}")
                return content
            except UnicodeDecodeError:
                continue
            except Exception as e:
                self.errors.append(f"Error reading file with {encoding}: {e}")

        print("[ERROR] Could not read file with any encoding")
        return None

    def _extract_concepts(self, content: str) -> List[Dict]:
        """Extract SKOS concepts from TTL content."""
        concepts = []

        # Extract @base URI if present
        self.base_uri = self._extract_base_uri(content)
        
        # Extract metadata (ConceptScheme, etc.)
        self._extract_metadata(content)

        # Split content into concept blocks
        blocks = self._split_into_concept_blocks(content)
        self.stats['total_concepts'] = len(blocks)

        for block in blocks:
            concept = self._parse_concept_block(block)
            if concept:
                concepts.append(concept)

        
        return concepts
    
    def _extract_base_uri(self, content: str) -> Optional[str]:
        """Extract @base URI from TTL content."""
        base_match = re.search(r'(@base\s+<[^>]+>\s*\.)', content)
        if base_match:
            self.base_declaration = base_match.group(1)
            uri_match = re.search(r'@base\s+<([^>]+)>\s*\.', content)
            if uri_match:
                base_uri = uri_match.group(1)
                print(f"[INFO] Found @base URI: {base_uri}")
                return base_uri
        return None
    
    def _fix_comma_spacing(self, text: str) -> str:
        """Fix comma spacing in text - ensure space after comma."""
        if not text:
            return text
            
        original = text
        # Replace comma without space with comma + space
        # But avoid double spaces
        fixed = re.sub(r',(?!\s)', ', ', text)
        # Clean up multiple spaces
        fixed = re.sub(r'\s+', ' ', fixed)
        
        # Count fixes and log changes
        if fixed != original:
            self.stats['comma_fixes'] += 1
            self.change_log.append(f"Comma spacing fixed: '{original}' → '{fixed.strip()}'")
            
        return fixed.strip()
    
    def _extract_metadata(self, content: str) -> None:
        """Extract ConceptScheme and other metadata from TTL content."""
        lines = content.split('\n')
        current_block = []
        in_concept_scheme = False
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            # Check for ConceptScheme start
            if 'a skos:ConceptScheme' in line:
                in_concept_scheme = True
                current_block = [line]
            elif in_concept_scheme:
                current_block.append(line)
                # Check for end of ConceptScheme (line ending with .)
                if line.endswith(' .'):
                    self.concept_scheme = '\n    '.join(current_block)
                    in_concept_scheme = False
                    current_block = []
    
    def _split_into_concept_blocks(self, content: str) -> List[str]:
        """Split TTL content into individual concept blocks."""
        # Remove comments and empty lines
        lines = []
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                lines.append(line)
        
        # Find concept boundaries
        blocks = []
        current_block = []
        
        for line in lines:
            # Match various URI formats: <uuid>, prefix:id, or full URIs
            if re.match(r'^(<[^>]+>|[a-zA-Z0-9_:/-]+)\s+a\s+skos:Concept', line):
                # Start of new concept
                if current_block:
                    blocks.append('\n'.join(current_block))
                current_block = [line]
            elif line.strip() == '.' and current_block:
                # End of concept
                current_block.append(line)
                blocks.append('\n'.join(current_block))
                current_block = []
            elif current_block:
                # Part of current concept
                current_block.append(line)
        
        # Add last block if exists
        if current_block:
            blocks.append('\n'.join(current_block))
        
        return blocks
    
    def _parse_concept_block(self, block: str) -> Optional[Dict]:
        """Parse individual concept block."""
        concept = {
            'uri': None,
            'prefLabels': [],
            'altLabels': [],
            'definitions': [],
            'notes': [],
            'scopeNotes': [],
            'editorialNotes': [],
            'historyNotes': [],
            'changeNotes': [],
            'examples': [],
            'other_properties': [],  # Store all other SKOS properties
            'raw_block': block,
            'issues': []
        }
        
        # Extract URI - handle various formats
        uri_match = re.search(r'^(<[^>]+>|[a-zA-Z0-9_:/-]+)\s+a\s+skos:Concept', block, re.MULTILINE)
        if uri_match:
            raw_uri = uri_match.group(1).strip()
            concept['uri'] = self._clean_uri(raw_uri)
            if raw_uri != concept['uri']:
                concept['issues'].append('URI cleaned')
                self.stats['malformed_uris_fixed'] += 1
        else:
            concept['issues'].append('No URI found')
            return None
        
        # Extract prefLabels
        pref_labels = re.findall(r'skos:prefLabel\s+"([^"]+)"(?:@([a-z]{2}))?', block)
        for label, lang in pref_labels:
            cleaned_label = self._clean_label(label)
            if cleaned_label:
                concept['prefLabels'].append({'text': cleaned_label, 'lang': lang or 'en'})
        
        # Extract altLabels
        alt_labels = re.findall(r'skos:altLabel\s+"([^"]+)"(?:@([a-z]{2}))?', block)
        for label, lang in alt_labels:
            cleaned_label = self._clean_label(label)
            if cleaned_label:
                concept['altLabels'].append({'text': cleaned_label, 'lang': lang or 'en'})
        
        # Extract definitions
        definitions = re.findall(r'skos:definition\s+"([^"]+)"(?:@([a-z]{2}))?', block)
        for definition, lang in definitions:
            cleaned_definition = self._clean_text_field(definition)
            if cleaned_definition:
                concept['definitions'].append({'text': cleaned_definition, 'lang': lang or 'en'})
        
        # Extract notes
        notes = re.findall(r'skos:note\s+"([^"]+)"(?:@([a-z]{2}))?', block)
        for note, lang in notes:
            cleaned_note = self._clean_text_field(note)
            if cleaned_note:
                concept['notes'].append({'text': cleaned_note, 'lang': lang or 'en'})
        
        # Extract scopeNotes
        scope_notes = re.findall(r'skos:scopeNote\s+"([^"]+)"(?:@([a-z]{2}))?', block)
        for note, lang in scope_notes:
            cleaned_note = self._clean_text_field(note)
            if cleaned_note:
                concept['scopeNotes'].append({'text': cleaned_note, 'lang': lang or 'en'})
        
        # Extract editorialNotes
        editorial_notes = re.findall(r'skos:editorialNote\s+"([^"]+)"(?:@([a-z]{2}))?', block)
        for note, lang in editorial_notes:
            cleaned_note = self._clean_text_field(note)
            if cleaned_note:
                concept['editorialNotes'].append({'text': cleaned_note, 'lang': lang or 'en'})
        
        # Extract historyNotes
        history_notes = re.findall(r'skos:historyNote\s+"([^"]+)"(?:@([a-z]{2}))?', block)
        for note, lang in history_notes:
            cleaned_note = self._clean_text_field(note)
            if cleaned_note:
                concept['historyNotes'].append({'text': cleaned_note, 'lang': lang or 'en'})
        
        # Extract changeNotes
        change_notes = re.findall(r'skos:changeNote\s+"([^"]+)"(?:@([a-z]{2}))?', block)
        for note, lang in change_notes:
            cleaned_note = self._clean_text_field(note)
            if cleaned_note:
                concept['changeNotes'].append({'text': cleaned_note, 'lang': lang or 'en'})
        
        # Extract examples
        examples = re.findall(r'skos:example\s+"([^"]+)"(?:@([a-z]{2}))?', block)
        for example, lang in examples:
            cleaned_example = self._clean_text_field(example)
            if cleaned_example:
                concept['examples'].append({'text': cleaned_example, 'lang': lang or 'en'})
        
        # Extract all other SKOS properties (exactMatch, narrower, broader, etc.)
        # Parse multi-line properties correctly
        concept['other_properties'] = self._parse_multiline_properties(block)
        
        # Validate concept
        if not concept['prefLabels']:
            concept['issues'].append('No prefLabel found')
            self.stats['concepts_without_preflabel'] += 1
            return None
        
        return concept
    
    def _parse_multiline_properties(self, block: str) -> List[str]:
        """Parse multi-line SKOS properties correctly, preserving complete lists."""
        properties = []
        lines = block.split('\n')
        
        # Skip text fields that are already processed
        skip_patterns = [
            'skos:prefLabel', 'skos:altLabel', 'skos:definition', 'skos:note',
            'skos:scopeNote', 'skos:editorialNote', 'skos:historyNote', 
            'skos:changeNote', 'skos:example'
        ]
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines, comments, URI declaration, and end marker
            if (not line or line.startswith('#') or 
                line.endswith('a skos:Concept ;') or line == '.' or
                line.startswith('http://') or line.startswith('<')):
                i += 1
                continue
            
            # Skip already processed text fields
            if any(pattern in line for pattern in skip_patterns):
                i += 1
                continue
            
            # Check if this line starts a SKOS property
            if ':' in line and any(line.strip().startswith(prop) for prop in [
                'skos:exactMatch', 'skos:narrower', 'skos:broader', 'skos:broaderTransitive',
                'skos:related', 'skos:closeMatch', 'skos:exactMatch', 'skos:broadMatch',
                'skos:narrowMatch', 'skos:relatedMatch', 'skos:inScheme', 'skos:topConceptOf',
                'skos:hasTopConcept', 'skos:member', 'skos:memberList'
            ]):
                # Start collecting the complete property (may span multiple lines)
                property_lines = []
                current_line = line
                
                # Continue collecting until we find the end of this property
                while i < len(lines):
                    current_line = lines[i].strip()
                    if not current_line:
                        i += 1
                        continue
                        
                    property_lines.append(current_line)
                    
                    # Check if this line ends the property (ends with ; or .)
                    if current_line.endswith(';') or current_line.endswith('.'):
                        break
                    
                    i += 1
                
                # Join the property lines and clean up
                if property_lines:
                    complete_property = ' '.join(property_lines)
                    # Remove trailing punctuation for consistent formatting
                    complete_property = complete_property.rstrip(' ;.,').strip()
                    if complete_property and ':' in complete_property:
                        properties.append(complete_property)
            
            i += 1
        
        return properties
    
    def _validate_skos_integrity(self, concepts: List[Dict]) -> Tuple[List[str], List[str]]:
        """Validate SKOS integrity conditions (S14, S13, etc.) with enhanced error reporting."""
        violations = []
        warnings = []
        
        for concept in concepts:
            uri = concept.get('uri', 'unknown')
            
            # S14: At most one value of skos:prefLabel per language tag
            pref_labels = concept.get('prefLabels', [])
            if pref_labels:
                lang_counts = {}
                lang_labels = {}
                
                for label_obj in pref_labels:
                    text = label_obj.get('text', '')
                    lang = label_obj.get('lang', 'en')
                    lang_counts[lang] = lang_counts.get(lang, 0) + 1
                    if lang not in lang_labels:
                        lang_labels[lang] = []
                    lang_labels[lang].append(text)
                
                for lang, count in lang_counts.items():
                    if count > 1:
                        labels_list = ', '.join([f'"{label}"' for label in lang_labels[lang]])
                        violations.append(
                            f"S14 Violation: <{uri}> has {count} prefLabels for language '{lang}': {labels_list}. "
                            f"Suggestion: Keep only one prefLabel per language, move others to altLabel."
                        )
            
            # S13: Disjoint label properties with detailed reporting
            pref_set = set()
            alt_set = set()
            hidden_set = set()
            
            for label_obj in pref_labels:
                text = label_obj.get('text', '')
                lang = label_obj.get('lang', 'en')
                pref_set.add((text, lang))
            
            for label_obj in concept.get('altLabels', []):
                text = label_obj.get('text', '')
                lang = label_obj.get('lang', 'en')
                alt_set.add((text, lang))
            
            # Note: hiddenLabels not currently parsed in _parse_concept_block
            # This would need to be added if hiddenLabel support is required
            
            # Check overlaps with detailed suggestions
            pref_alt_overlap = pref_set & alt_set
            pref_hidden_overlap = pref_set & hidden_set
            alt_hidden_overlap = alt_set & hidden_set
            
            if pref_alt_overlap:
                overlap_details = ', '.join([f'"{text}"@{lang}' for text, lang in pref_alt_overlap])
                violations.append(
                    f"S13 Violation: <{uri}> has overlapping prefLabel/altLabel: {overlap_details}. "
                    f"Suggestion: Remove duplicate from altLabel or use different preferred term."
                )
            
            if pref_hidden_overlap:
                overlap_details = ', '.join([f'"{text}"@{lang}' for text, lang in pref_hidden_overlap])
                violations.append(
                    f"S13 Violation: <{uri}> has overlapping prefLabel/hiddenLabel: {overlap_details}. "
                    f"Suggestion: Remove from hiddenLabel if it's the preferred term."
                )
            
            if alt_hidden_overlap:
                overlap_details = ', '.join([f'"{text}"@{lang}' for text, lang in alt_hidden_overlap])
                violations.append(
                    f"S13 Violation: <{uri}> has overlapping altLabel/hiddenLabel: {overlap_details}. "
                    f"Suggestion: Decide whether term should be alternative or hidden."
                )
            
            # Enhanced label quality warnings
            all_label_objects = pref_labels + concept.get('altLabels', [])
            for label_obj in all_label_objects:
                label_text = label_obj.get('text', '')
                
                if len(label_text) > 500:
                    warnings.append(
                        f"Very long label ({len(label_text)} chars) in <{uri}>: '{label_text[:50]}...'. "
                        f"Suggestion: Consider shortening or using skos:definition for detailed descriptions."
                    )
                
                if label_text == '':
                    warnings.append(
                        f"Empty label in <{uri}>. Suggestion: Remove empty label or provide meaningful text."
                    )
                
                # Check for potential encoding issues
                if any(char in label_text for char in ['Ã¤', 'Ã¶', 'Ã¼', 'ÃŸ']):
                    warnings.append(
                        f"Potential encoding issue in <{uri}>: '{label_text}'. "
                        f"Suggestion: Check UTF-8 encoding of source data."
                    )
                
                # Check for suspicious patterns
                if label_text.lower().startswith(('http://', 'https://')):
                    warnings.append(
                        f"Label looks like URI in <{uri}>: '{label_text}'. "
                        f"Suggestion: Use skos:exactMatch for URI mappings instead."
                    )
        
        return violations, warnings
    
    def _validate_semantic_relations(self, concepts: List[Dict]) -> Tuple[List[str], List[str]]:
        """Validate semantic relations for SKOS compliance - simplified to avoid iteration errors."""
        violations = []
        warnings = []
        
        # Simplified validation to avoid dictionary iteration issues
        # Just check for basic semantic relation conflicts without complex transitive closure
        broader_relations = []
        related_relations = []
        
        for concept in concepts:
            uri = concept.get('uri', '')
            other_props = concept.get('other_properties', [])
            
            for prop in other_props:
                if 'skos:broader ' in prop:
                    target = self._extract_uri_from_property(prop)
                    if target:
                        broader_relations.append((uri, target))
                elif 'skos:related ' in prop:
                    target = self._extract_uri_from_property(prop)
                    if target:
                        related_relations.append((uri, target))
        
        # Simple check: if same concepts are both broader and related, that's a violation
        broader_set = set(broader_relations)
        related_set = set(related_relations)
        
        direct_conflicts = broader_set & related_set
        for conflict in direct_conflicts:
            violations.append(
                f"S27 Violation: <{conflict[0]}> has both skos:broader and skos:related to <{conflict[1]}>. "
                f"Suggestion: Use either broader or related, but not both for the same concept pair."
            )
        
        # Basic cycle detection without complex graph traversal
        for source, target in broader_relations:
            # Check if target also has source as broader (simple 2-node cycle)
            if (target, source) in broader_set:
                warnings.append(
                    f"Simple cycle detected: <{source}> and <{target}> are mutually broader. "
                    f"Suggestion: Remove one of the broader relations to create a proper hierarchy."
                )
        
        return violations, warnings
    
    def _validate_datatypes_and_uris(self, concepts: List[Dict]) -> Tuple[List[str], List[str]]:
        """Validate URIs and datatypes."""
        violations = []
        warnings = []
        
        for concept in concepts:
            # Check URI format
            if not self._is_valid_uri(concept['uri']):
                violations.append(f"Invalid URI format: {concept['uri']}")
            
            # Check language tags (basic BCP47 validation)
            for label in concept['prefLabels'] + concept['altLabels']:
                if label['lang'] and not self._is_valid_language_tag(label['lang']):
                    warnings.append(
                        f"Potentially invalid language tag '{label['lang']}' in {concept['uri']}"
                    )
        
        return violations, warnings
    
    def _extract_uri_from_property(self, prop: str) -> Optional[str]:
        """Extract URI from a property string like 'skos:broader <uri>'."""
        # Match URIs in angle brackets
        match = re.search(r'<([^>]+)>', prop)
        if match:
            return f"<{match.group(1)}>"
        return None
    
    def _compute_transitive_closure(self, relations: Set[Tuple[str, str]]) -> Set[Tuple[str, str]]:
        """Compute transitive closure of relations - fixed to prevent dictionary iteration errors."""
        closure = set(relations)
        changed = True
        
        while changed:
            changed = False
            new_relations = set()
            
            # Create a copy of closure to iterate over to avoid "dictionary changed size during iteration"
            closure_copy = set(closure)
            
            for (a, b) in closure_copy:
                for (c, d) in closure_copy:
                    if b == c and (a, d) not in closure:
                        new_relations.add((a, d))
                        changed = True
            
            closure.update(new_relations)
        
        return closure
    
    def _detect_cycles(self, relations: Set[Tuple[str, str]]) -> List[List[str]]:
        """Detect cycles in directed graph of relations."""
        # Build adjacency list
        graph = defaultdict(list)
        for source, target in relations:
            graph[source].append(target)
        
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(node, path):
            if node in rec_stack:
                # Found cycle
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:] + [node])
                return
            
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph[node]:
                dfs(neighbor, path + [neighbor])
            
            rec_stack.remove(node)
        
        for node in graph:
            if node not in visited:
                dfs(node, [node])
        
        return cycles
    
    def _is_valid_uri(self, uri: str) -> bool:
        """Basic URI validation."""
        try:
            # Remove angle brackets if present
            clean_uri = uri.strip('<>')
            result = urllib.parse.urlparse(clean_uri)
            return bool(result.scheme and result.netloc)
        except:
            return False
    
    def _is_valid_language_tag(self, tag: str) -> bool:
        """Basic BCP47 language tag validation."""
        if not tag:
            return False
        # Basic pattern: 2-3 letter language code, optionally followed by subtags
        pattern = r'^[a-z]{2,3}(-[A-Za-z0-9]{1,8})*$'
        return bool(re.match(pattern, tag))
    
    def _generate_validation_report(self, violations: List[str], warnings: List[str]) -> str:
        """Generate detailed validation report."""
        report = []
        report.append("\n" + "="*60)
        report.append("SKOS VALIDATION REPORT")
        report.append("="*60)
        
        if violations:
            report.append(f"\nINTEGRITY VIOLATIONS ({len(violations)}):")
            for i, violation in enumerate(violations, 1):
                report.append(f"  {i:3d}. {violation}")
        
        if warnings:
            report.append(f"\nWARNINGS ({len(warnings)}):")
            for i, warning in enumerate(warnings, 1):
                report.append(f"  {i:3d}. {warning}")
        
        if not violations and not warnings:
            report.append("\n✅ All SKOS integrity conditions satisfied!")
        
        report.append("\n" + "="*60)
        return "\n".join(report)
    
    def _clean_uri(self, uri: str) -> str:
        """Clean and normalize URI."""
        uri = uri.strip()
        
        # Remove angle brackets if present
        if uri.startswith('<') and uri.endswith('>'):
            uri = uri[1:-1]
        
        # If URI doesn't start with http, it might be relative to @base
        if not uri.startswith('http'):
            if self.base_uri and not ':' in uri:
                # Relative URI - combine with @base
                uri = f"{self.base_uri.rstrip('/')}/{uri}"
            elif ':' in uri:
                # Prefixed URI like esco:123
                prefix, local = uri.split(':', 1)
                if prefix == 'esco':
                    uri = f"http://data.europa.eu/esco/skill/{local}"
                else:
                    uri = f"http://example.org/{prefix}/{local}"
            else:
                # Plain ID, use @base if available, otherwise default ESCO prefix
                if self.base_uri:
                    uri = f"{self.base_uri.rstrip('/')}/{uri}"
                else:
                    uri = f"http://data.europa.eu/esco/skill/{uri}"
        
        return uri
    
    def _clean_label(self, label: str) -> Optional[str]:
        """Clean label text."""
        if not label:
            return None
        
        # Fix encoding issues
        original_label = label
        
        # Common encoding fixes
        replacements = {
            'Ã¤': 'ä', 'Ã¶': 'ö', 'Ã¼': 'ü',
            'Ã„': 'Ä', 'Ã–': 'Ö', 'Ãœ': 'Ü',
            'ÃŸ': 'ß', 'Ã©': 'é', 'Ã¨': 'è',
            'Ã¡': 'á', 'Ã ': 'à', 'Ã³': 'ó',
            'Ã²': 'ò', 'Ãº': 'ú', 'Ã¹': 'ù'
        }
        
        for wrong, correct in replacements.items():
            label = label.replace(wrong, correct)
        
        if label != original_label:
            self.stats['encoding_issues_fixed'] += 1
        
        # Remove extra whitespace
        label = ' '.join(label.split())
        
        # Remove empty labels
        if not label.strip():
            self.stats['empty_labels_removed'] += 1
            return None
        
        return label
    
    def _clean_text_field(self, text: str) -> Optional[str]:
        """Clean text fields like definition, note, etc."""
        if not text:
            return None
        
        original_text = text
        
        # Fix encoding issues (same as labels)
        replacements = {
            'Ã¤': 'ä', 'Ã¶': 'ö', 'Ã¼': 'ü',
            'Ã„': 'Ä', 'Ã–': 'Ö', 'Ãœ': 'Ü',
            'ÃŸ': 'ß', 'Ã©': 'é', 'Ã¨': 'è',
            'Ã¡': 'á', 'Ã ': 'à', 'Ã³': 'ó',
            'Ã²': 'ò', 'Ãº': 'ú', 'Ã¹': 'ù',
            '&nbsp;': ' ', '&amp;': '&', '&lt;': '<', '&gt;': '>',
            '&quot;': '"', '&#39;': "'", '&apos;': "'"
        }
        
        for wrong, correct in replacements.items():
            text = text.replace(wrong, correct)
        
        # Fix spacing after punctuation
        # Add space after commas if missing
        text = re.sub(r',(?!\s)', ', ', text)
        # Add space after periods if missing (but not in abbreviations)
        text = re.sub(r'\.(?!\s|$|\d)', '. ', text)
        # Add space after semicolons if missing
        text = re.sub(r';(?!\s)', '; ', text)
        # Add space after colons if missing
        text = re.sub(r':(?!\s|$)', ': ', text)
        # Add space after exclamation marks if missing
        text = re.sub(r'!(?!\s|$)', '! ', text)
        # Add space after question marks if missing
        text = re.sub(r'\?(?!\s|$)', '? ', text)
        
        # Remove multiple consecutive spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Track changes
        if text != original_text:
            self.stats['encoding_issues_fixed'] += 1
        
        # Remove empty text
        if not text.strip():
            self.stats['empty_labels_removed'] += 1
            return None
        
        return text
    
    def _fix_comma_spacing(self, text: str) -> str:
        """Fix spacing after commas and other punctuation in text."""
        if not text:
            return text
        
        original_text = text
        
        # Fix spacing after punctuation - only add space if none exists
        # Add space after commas if missing (negative lookahead for existing space)
        text = re.sub(r',(?!\s)', ', ', text)
        # Add space after periods if missing (but not in abbreviations or at end)
        text = re.sub(r'\.(?!\s|$|\d)', '. ', text)
        # Add space after semicolons if missing
        text = re.sub(r';(?!\s)', '; ', text)
        # Add space after colons if missing (but not at end)
        text = re.sub(r':(?!\s|$)', ': ', text)
        # Add space after exclamation marks if missing (but not at end)
        text = re.sub(r'!(?!\s|$)', '! ', text)
        # Add space after question marks if missing (but not at end)
        text = re.sub(r'\?(?!\s|$)', '? ', text)
        
        # Remove multiple consecutive spaces (but preserve single spaces)
        text = re.sub(r'\s{2,}', ' ', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Track comma fixes only if text actually changed
        if text != original_text:
            self.stats['comma_fixes'] += 1
        
        return text
    
    def _clean_concepts(self, concepts: List[Dict]) -> List[Dict]:
        """Clean and deduplicate concepts."""
        # Track URIs to find duplicates
        uri_counts = Counter(concept['uri'] for concept in concepts if concept['uri'])
        duplicates = {uri for uri, count in uri_counts.items() if count > 1}
        
        # Group concepts by URI
        uri_groups = defaultdict(list)
        for concept in concepts:
            if concept['uri']:
                uri_groups[concept['uri']].append(concept)
        
        cleaned_concepts = []
        
        seen_uris = set()
        unique_concepts = []
        
        for concept in concepts:
            uri = concept['uri']
            if uri not in seen_uris:
                seen_uris.add(uri)
                unique_concepts.append(concept)
            else:
                self.stats['duplicates_removed'] += 1
                self.change_log.append(f"Duplicate removed: {uri}")
        
        return unique_concepts
    
    def _merge_duplicate_concepts(self, concepts: List[Dict]) -> Dict:
        """Merge duplicate concepts into one."""
        if not concepts:
            return None
        
        # Use first concept as base
        merged = concepts[0].copy()
        merged['prefLabels'] = []
        merged['altLabels'] = []
        merged['issues'] = []
        
        # Collect all labels
        all_pref_labels = set()
        all_alt_labels = set()
        all_issues = set()
        
        for concept in concepts:
            for label in concept['prefLabels']:
                all_pref_labels.add((label['text'], label['lang']))
            for label in concept['altLabels']:
                all_alt_labels.add((label['text'], label['lang']))
            all_issues.update(concept['issues'])
        
        # Convert back to list format
        merged['prefLabels'] = [{'text': text, 'lang': lang} for text, lang in all_pref_labels]
        merged['altLabels'] = [{'text': text, 'lang': lang} for text, lang in all_alt_labels]
        merged['issues'] = list(all_issues)
        
        return merged
    
    def _generate_cleaned_content(self, concepts: List[Dict], original_content: str) -> str:
        """Generate cleaned TTL content as string."""
        # Extract prefixes from original file
        prefixes = []
        for line in original_content.split('\n'):
            if line.strip().startswith('@prefix'):
                prefixes.append(line.strip())
        
        # Generate cleaned TTL content
        lines = []
        
        # Add @base declaration if present
        if self.base_declaration:
            lines.append(self.base_declaration)
        
        # Add prefixes
        if prefixes:
            lines.extend(prefixes)
            lines.append('')
        else:
            # Add default prefixes
            lines.extend([
                '@prefix skos: <http://www.w3.org/2004/02/skos/core#> .',
                '@prefix esco: <http://data.europa.eu/esco/> .',
                ''
            ])
        
        # Add ConceptScheme if present
        if self.concept_scheme:
            lines.append(self.concept_scheme)
            lines.append('')
        
        # Add concepts
        for concept in concepts:
            lines.append(self._format_concept(concept))
            lines.append('')
        
        return '\n'.join(lines)
    
    def _write_cleaned_file(self, concepts: List[Dict], original_content: str, output_path: str):
        """Write cleaned concepts to new TTL file."""
        cleaned_content = self._generate_cleaned_content(concepts, original_content)
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
        
        print(f"[OK] Cleaned file saved: {output_path}")
    
    def _write_change_log(self, log_path: str) -> None:
        """Write detailed change log to file."""
        from datetime import datetime
        
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write(f"TTL CLEANER CHANGE LOG\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"="*60 + "\n\n")
            
            # Summary
            f.write(f"SUMMARY:\n")
            f.write(f"- Total concepts processed: {self.stats['total_concepts']}\n")
            f.write(f"- Duplicates removed: {self.stats['duplicates_removed']}\n")
            f.write(f"- Labels processed: {self.stats['labels_processed']}\n")
            f.write(f"- Comma spacing fixes: {self.stats['comma_fixes']}\n")
            f.write(f"\n")
            
            # Detailed changes
            f.write(f"DETAILED CHANGES:\n")
            f.write(f"-" * 40 + "\n")
            for i, change in enumerate(self.change_log, 1):
                f.write(f"{i:4d}. {change}\n")
                
        print(f"[OK] Change log written: {log_path}")
    
    def _write_validation_report(self, log_path: str, violations: List[str], warnings: List[str]) -> None:
        """Write detailed validation report to file."""
        from datetime import datetime
        
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write(f"SKOS VALIDATION REPORT\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"="*60 + "\n\n")
            
            # Summary
            f.write(f"SUMMARY:\n")
            f.write(f"- Integrity violations: {len(violations)}\n")
            f.write(f"- Warnings: {len(warnings)}\n")
            f.write(f"\n")
            
            # Violations
            if violations:
                f.write(f"INTEGRITY VIOLATIONS ({len(violations)}):\n")
                f.write(f"-" * 40 + "\n")
                for i, violation in enumerate(violations, 1):
                    f.write(f"{i:4d}. {violation}\n")
                f.write(f"\n")
            
            # Warnings
            if warnings:
                f.write(f"WARNINGS ({len(warnings)}):\n")
                f.write(f"-" * 40 + "\n")
                for i, warning in enumerate(warnings, 1):
                    f.write(f"{i:4d}. {warning}\n")
                f.write(f"\n")
            
            if not violations and not warnings:
                f.write("SUCCESS: All SKOS integrity conditions satisfied!\n")
                
        print(f"[OK] Validation report written: {log_path}")
    
    def _clean_concepts_chunked(self, concepts: List[Dict]) -> List[Dict]:
        """Clean concepts in chunks for memory efficiency."""
        cleaned_concepts = []
        total_chunks = (len(concepts) + self.chunk_size - 1) // self.chunk_size
        
        print(f"[INFO] Processing {len(concepts)} concepts in {total_chunks} chunks of {self.chunk_size}")
        
        for i in range(0, len(concepts), self.chunk_size):
            chunk = concepts[i:i + self.chunk_size]
            self.processed_chunks += 1
            
            print(f"[INFO] Processing chunk {self.processed_chunks}/{total_chunks}...")
            
            # Clean this chunk
            cleaned_chunk = self._clean_concepts(chunk)
            cleaned_concepts.extend(cleaned_chunk)
            
            # Memory cleanup for large datasets
            if self.memory_efficient:
                import gc
                gc.collect()
        
        return cleaned_concepts
    
    def _validate_concepts_chunked(self, concepts: List[Dict]) -> Tuple[List[str], List[str]]:
        """Validate concepts in chunks for memory efficiency."""
        all_violations = []
        all_warnings = []
        total_chunks = (len(concepts) + self.chunk_size - 1) // self.chunk_size
        
        print(f"[INFO] Validating {len(concepts)} concepts in {total_chunks} chunks")
        
        for i in range(0, len(concepts), self.chunk_size):
            chunk = concepts[i:i + self.chunk_size]
            chunk_num = (i // self.chunk_size) + 1
            
            print(f"[INFO] Validating chunk {chunk_num}/{total_chunks}...")
            
            # Validate this chunk
            violations, warnings = self._validate_skos_integrity(chunk)
            all_violations.extend(violations)
            all_warnings.extend(warnings)
            
            violations, warnings = self._validate_semantic_relations(chunk)
            all_violations.extend(violations)
            all_warnings.extend(warnings)
            
            violations, warnings = self._validate_datatypes_and_uris(chunk)
            all_violations.extend(violations)
            all_warnings.extend(warnings)
            
            # Memory cleanup
            if self.memory_efficient:
                import gc
                gc.collect()
        
        return all_violations, all_warnings
    
    def _validate_skos_xl_labels(self, concepts: List[Dict]) -> Tuple[List[str], List[str]]:
        """Validate SKOS-XL labels if enabled - simplified to prevent dictionary iteration errors."""
        violations = []
        warnings = []
        
        if not self.enable_skos_xl:
            return violations, warnings
        
        # Simplified SKOS-XL validation to avoid dictionary iteration issues
        # Check for SKOS-XL properties in other_properties
        xl_label_uris = set()
        
        for concept in concepts:
            uri = concept.get('uri', 'unknown')
            other_props = concept.get('other_properties', [])
            
            # Look for SKOS-XL properties in other_properties list
            for prop in other_props:
                if any(xl_prop in prop for xl_prop in ['skosxl:prefLabel', 'skosxl:altLabel', 'skosxl:hiddenLabel']):
                    # Extract URI from property if present
                    xl_uri = self._extract_uri_from_property(prop)
                    if xl_uri:
                        xl_label_uris.add(xl_uri)
                        
                        # Check for URI conflicts
                        concept_uris = [c.get('uri', '') for c in concepts]
                        if xl_uri in concept_uris:
                            warnings.append(
                                f"SKOS-XL label URI <{xl_uri}> conflicts with concept URI in <{uri}>. "
                                f"Suggestion: Use different namespace for XL labels."
                            )
                
                # Check for literal form properties
                elif 'skosxl:literalForm' in prop:
                    if uri not in xl_label_uris:
                        warnings.append(
                            f"Orphaned SKOS-XL label <{uri}> not referenced by any concept. "
                            f"Suggestion: Link to concept via skosxl:prefLabel/altLabel/hiddenLabel."
                        )
        
        return violations, warnings
    
    def _format_concept(self, concept: Dict) -> str:
        """Format concept as TTL."""
        lines = []
        
        # URI and type - use relative URI if @base is present
        uri = concept['uri']
        if self.base_uri and uri.startswith(self.base_uri):
            # Convert to relative URI
            relative_uri = f"<{uri[len(self.base_uri):]}>"
            lines.append(f"{relative_uri} a skos:Concept ;")
        else:
            lines.append(f"{uri} a skos:Concept ;")
        
        # Collect all properties to determine correct separators
        all_properties = []
        
        # Add prefLabels
        for label in concept['prefLabels']:
            lang_tag = f"@{label['lang']}" if label['lang'] else ""
            fixed_text = self._fix_comma_spacing(label['text'])
            all_properties.append(f'skos:prefLabel "{fixed_text}"{lang_tag}')
            self.stats['labels_processed'] += 1
        
        # Add altLabels
        for label in concept['altLabels']:
            lang_tag = f"@{label['lang']}" if label['lang'] else ""
            fixed_text = self._fix_comma_spacing(label['text'])
            all_properties.append(f'skos:altLabel "{fixed_text}"{lang_tag}')
            self.stats['labels_processed'] += 1
        
        # Add definitions
        for definition in concept['definitions']:
            lang_tag = f"@{definition['lang']}" if definition['lang'] else ""
            fixed_text = self._fix_comma_spacing(definition['text'])
            all_properties.append(f'skos:definition "{fixed_text}"{lang_tag}')
            self.stats['definitions_processed'] += 1
            self.stats['text_fields_cleaned'] += 1
        
        # Add notes
        for note in concept['notes']:
            lang_tag = f"@{note['lang']}" if note['lang'] else ""
            fixed_text = self._fix_comma_spacing(note['text'])
            all_properties.append(f'skos:note "{fixed_text}"{lang_tag}')
            self.stats['notes_processed'] += 1
            self.stats['text_fields_cleaned'] += 1
        
        # Add scopeNotes
        for note in concept['scopeNotes']:
            lang_tag = f"@{note['lang']}" if note['lang'] else ""
            fixed_text = self._fix_comma_spacing(note['text'])
            all_properties.append(f'skos:scopeNote "{fixed_text}"{lang_tag}')
            self.stats['notes_processed'] += 1
            self.stats['text_fields_cleaned'] += 1
        
        # Add editorialNotes
        for note in concept['editorialNotes']:
            lang_tag = f"@{note['lang']}" if note['lang'] else ""
            fixed_text = self._fix_comma_spacing(note['text'])
            all_properties.append(f'skos:editorialNote "{fixed_text}"{lang_tag}')
            self.stats['notes_processed'] += 1
            self.stats['text_fields_cleaned'] += 1
        
        # Add historyNotes
        for note in concept['historyNotes']:
            lang_tag = f"@{note['lang']}" if note['lang'] else ""
            fixed_text = self._fix_comma_spacing(note['text'])
            all_properties.append(f'skos:historyNote "{fixed_text}"{lang_tag}')
            self.stats['notes_processed'] += 1
            self.stats['text_fields_cleaned'] += 1
        
        # Add changeNotes
        for note in concept['changeNotes']:
            lang_tag = f"@{note['lang']}" if note['lang'] else ""
            fixed_text = self._fix_comma_spacing(note['text'])
            all_properties.append(f'skos:changeNote "{fixed_text}"{lang_tag}')
            self.stats['notes_processed'] += 1
            self.stats['text_fields_cleaned'] += 1
        
        # Add examples
        for example in concept['examples']:
            lang_tag = f"@{example['lang']}" if example['lang'] else ""
            fixed_text = self._fix_comma_spacing(example['text'])
            all_properties.append(f'skos:example "{fixed_text}"{lang_tag}')
            self.stats['text_fields_cleaned'] += 1
        
        # Add other SKOS properties
        for prop in concept['other_properties']:
            # Clean the property (remove any trailing punctuation)
            clean_prop = prop.rstrip(' ;.,').strip()
            if clean_prop:
                all_properties.append(clean_prop)
        
        # Format with correct separators
        for i, prop in enumerate(all_properties):
            separator = " ;" if i < len(all_properties) - 1 else " ."
            lines.append(f'    {prop}{separator}')
        
        return '\n'.join(lines)
    
    def _print_report(self, input_path: str, output_path: str):
        """Print cleaning report."""
        print("\n" + "="*60)
        print("TTL CLEANING REPORT")
        print("="*60)
        print(f"Input file:  {input_path}")
        print(f"Output file: {output_path}")
        print()
        print("STATISTICS:")
        print(f"   Total concepts processed: {self.stats['total_concepts']}")
        print(f"   Duplicates removed: {self.stats['duplicates_removed']}")
        print(f"   Malformed URIs fixed: {self.stats['malformed_uris_fixed']}")
        print(f"   Concepts without prefLabel: {self.stats['concepts_without_preflabel']}")
        print(f"   Encoding issues fixed: {self.stats['encoding_issues_fixed']}")
        print(f"   Empty labels removed: {self.stats['empty_labels_removed']}")
        print(f"   Text fields cleaned: {self.stats['text_fields_cleaned']}")
        print(f"   Comma spacing fixes: {self.stats['comma_fixes']}")
        print(f"   Labels processed: {self.stats['labels_processed']}")
        print(f"   Definitions processed: {self.stats['definitions_processed']}")
        print(f"   Notes processed: {self.stats['notes_processed']}")
        
        final_concepts = self.stats['total_concepts'] - self.stats['duplicates_removed'] - self.stats['concepts_without_preflabel']
        print(f"   Final concepts in output: {final_concepts}")
        
        if self.errors:
            print(f"\nERRORS ({len(self.errors)}):")
            for error in self.errors[:10]:  # Show first 10 errors
                print(f"   • {error}")
            if len(self.errors) > 10:
                print(f"   ... and {len(self.errors) - 10} more errors")
        
        if self.warnings:
            print(f"\nWARNINGS ({len(self.warnings)}):")
            for warning in self.warnings[:10]:  # Show first 10 warnings
                print(f"   • {warning}")
            if len(self.warnings) > 10:
                print(f"   ... and {len(self.warnings) - 10} more warnings")
        
        print("\n[SUCCESS] Cleaning completed!")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Clean and validate TTL files with SKOS integrity checks',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic cleaning (creates input_cleaned.ttl + reports)
  python ttl_cleaner.py input.ttl
  
  # High-performance mode for large files
  python ttl_cleaner.py large_file.ttl --memory-efficient --chunk-size 2000
  
  # Disable validation for speed
  python ttl_cleaner.py input.ttl --no-validation
  
  # Enable SKOS-XL support
  python ttl_cleaner.py input.ttl --enable-skos-xl
  
  # Custom output with verbose logging
  python ttl_cleaner.py input.ttl -o custom_name.ttl -v
  
  # Skip generating log files
  python ttl_cleaner.py input.ttl --no-reports

Default Output:
  input.ttl -> input_cleaned.ttl + input_cleaned_validation.log + input_cleaned_changes.log
"""
    )
    
    parser.add_argument('input_file', help='Input TTL file path')
    parser.add_argument('-o', '--output', help='Output file path (default: input_cleaned.ttl)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    # Performance options
    parser.add_argument('--chunk-size', type=int, default=1000,
                       help='Chunk size for processing large files (default: 1000)')
    parser.add_argument('--memory-efficient', action='store_true',
                       help='Enable memory-efficient mode for very large files')
    
    # Validation options
    parser.add_argument('--no-validation', action='store_true',
                       help='Disable SKOS validation for faster processing')
    parser.add_argument('--enable-skos-xl', action='store_true',
                       help='Enable SKOS-XL label validation')
    
    # Output options
    parser.add_argument('--no-reports', action='store_true',
                       help='Skip generating validation and change reports')
    
    args = parser.parse_args()
    
    # Initialize cleaner with options
    cleaner = TTLCleaner(
        chunk_size=args.chunk_size,
        enable_validation=not args.no_validation,
        memory_efficient=args.memory_efficient,
        enable_skos_xl=args.enable_skos_xl
    )
    
    # Print configuration if verbose
    if args.verbose:
        print(f"[CONFIG] Chunk size: {args.chunk_size}")
        print(f"[CONFIG] Memory efficient: {args.memory_efficient}")
        print(f"[CONFIG] Validation enabled: {not args.no_validation}")
        print(f"[CONFIG] SKOS-XL enabled: {args.enable_skos_xl}")
        print(f"[CONFIG] Reports enabled: {not args.no_reports}")
        print()
    
    # Process file
    success = cleaner.clean_ttl_file(args.input_file, args.output, generate_reports=not args.no_reports)
    
    if success:
        print("\n[SUCCESS] TTL file cleaned successfully!")
        
        # Print summary statistics
        stats = cleaner.stats
        print(f"\nSTATISTICS:")
        print(f"  Total concepts: {stats['total_concepts']}")
        print(f"  Final concepts: {stats['final_concepts']}")
        print(f"  Duplicates removed: {stats['duplicates_removed']}")
        print(f"  URIs fixed: {stats['malformed_uris_fixed']}")
        print(f"  Encoding issues fixed: {stats['encoding_issues_fixed']}")
        
        if cleaner.enable_validation:
            print(f"\nVALIDATION RESULTS:")
            print(f"  Violations: {len(cleaner.validation_violations)}")
            print(f"  Warnings: {len(cleaner.validation_warnings)}")
            
            if cleaner.validation_violations:
                print(f"  WARNING: Found {len(cleaner.validation_violations)} SKOS integrity violations!")
            else:
                print(f"  SUCCESS: All SKOS integrity conditions satisfied!")
        
    else:
        print("\n[ERROR] Failed to clean TTL file!")
        exit(1)
