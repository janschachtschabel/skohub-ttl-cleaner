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


class TTLCleaner:
    def __init__(self):
        self.stats = {
            'total_concepts': 0,
            'duplicates_removed': 0,
            'malformed_uris_fixed': 0,
            'concepts_without_preflabel': 0,
            'encoding_issues_fixed': 0,
            'empty_labels_removed': 0,
            'invalid_concepts_removed': 0,
            'comma_fixes': 0,
            'labels_processed': 0
        }
        self.errors = []
        self.warnings = []
        self.base_uri = None
        self.base_declaration = None
        self.concept_scheme = None
        self.other_metadata = []
        self.change_log = []

    def clean_ttl_file(self, input_path: str, output_path: Optional[str] = None) -> bool:
        """Clean TTL file and save cleaned version."""
        try:
            # Read input file
            content = self._read_file_with_encoding(input_path)
            if not content:
                return False

            print(f"[INFO] Processing: {input_path}")
            print(f"[INFO] Original file size: {len(content)} characters")

            # Extract and clean concepts
            concepts = self._extract_concepts(content)
            cleaned_concepts = self._clean_concepts(concepts)

            # Generate output path if not provided
            if not output_path:
                input_file = Path(input_path)
                output_path = input_file.parent / f"{input_file.stem}_cleaned{input_file.suffix}"

            # Write cleaned file
            self._write_cleaned_file(cleaned_concepts, content, output_path)

            # Generate report
            self._print_report(input_path, output_path)
            
            # Write change log if changes were made
            if self.change_log:
                log_path = Path(output_path).parent / f"{Path(output_path).stem}_changes.log"
                self._write_change_log(log_path)

            return True

        except Exception as e:
            print(f"[ERROR] Error processing file: {e}")
            return False

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
        
        # Extract all other SKOS properties (exactMatch, narrower, broader, etc.)
        lines = block.split('\n')
        for line in lines:
            line = line.strip()
            # Skip URI declaration line, labels (already processed), and structural elements
            if (line.startswith('http://') or line.startswith('<') or 
                'skos:prefLabel' in line or 'skos:altLabel' in line or
                line.endswith('a skos:Concept ;') or line == '.' or not line or
                line.startswith('#')):
                continue
            
            # Clean up the property line (remove trailing punctuation)
            cleaned_line = line.rstrip(' ;.,').strip()
            if cleaned_line and ':' in cleaned_line:
                concept['other_properties'].append(cleaned_line)
        
        # Validate concept
        if not concept['prefLabels']:
            concept['issues'].append('No prefLabel found')
            self.stats['concepts_without_preflabel'] += 1
            return None
        
        return concept
    
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
    
    def _write_cleaned_file(self, concepts: List[Dict], original_content: str, output_path: str):
        """Write cleaned concepts to new TTL file."""
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
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        print(f"[OK] Cleaned file saved: {output_path}")
    
    def _print_report(self, input_path: str, output_path: str) -> None:
        """Print cleaning report with statistics."""
        print("\n" + "="*60)
        print("TTL CLEANER REPORT")
        print("="*60)
        print(f"Input file:  {input_path}")
        print(f"Output file: {output_path}")
        print("\nSTATISTICS:")
        print("-"*30)
        print(f"Total concepts processed: {self.stats['total_concepts']}")
        print(f"Duplicates removed:      {self.stats['duplicates_removed']}")
        print(f"URIs cleaned:            {self.stats['uris_cleaned']}")
        print(f"Labels processed:        {self.stats['labels_processed']}")
        print(f"Comma spacing fixes:     {self.stats['comma_fixes']}")
        
        if self.base_uri:
            print(f"\nURI STRUCTURE:")
            print("-"*30)
            print(f"Base URI: {self.base_uri}")
            print(f"Using relative URIs: YES")
        else:
            print(f"\nURI STRUCTURE:")
            print("-"*30)
            print(f"Using relative URIs: NO")
            
        if self.concept_scheme:
            print(f"\nMETADATA PRESERVED:")
            print("-"*30)
            print(f"ConceptScheme: YES")
        
        final_count = self.stats['total_concepts'] - self.stats['duplicates_removed']
        print(f"\nFINAL RESULT:")
        print("-"*30)
        print(f"Unique concepts in output: {final_count}")
        
        if self.stats['comma_fixes'] > 0:
            print(f"Text improvements: {self.stats['comma_fixes']} comma spacing fixes")
            
        print("="*60)
    
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


def main():
    parser = argparse.ArgumentParser(description='Clean TTL/SKOS files')
    parser.add_argument('input_file', help='Input TTL file path')
    parser.add_argument('-o', '--output', help='Output file path (optional)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if not Path(args.input_file).exists():
        print(f"❌ Input file not found: {args.input_file}")
        sys.exit(1)
    
    cleaner = TTLCleaner()
    success = cleaner.clean_ttl_file(args.input_file, args.output)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
