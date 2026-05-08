#!/usr/bin/env python3
"""
Fix corrupted import lines in Svelte files.
Corruption pattern: migration script mangled imports by concatenating them
with kebab-case icon paths from module names.

Example corrupted line:
  import supportAgent } from '$lib/state/supportAgent.svelte.ts'; import { Sparkles from "@lucide/svelte/icons/support-agent } from '...'; import { -sparkles";

Fixed to:
  import { supportAgent } from '$lib/state/supportAgent.svelte.ts';
  import Sparkles from "@lucide/svelte/icons/sparkles";
"""

import re
import os
import sys

def to_pascal_case(kebab: str) -> str:
    return ''.join(w.capitalize() for w in kebab.lstrip('-').split('-') if w)

def is_corrupted_line(line: str) -> bool:
    """Detect if a line is corrupted."""
    if 'from "@lucide/svelte/icons/' not in line and "from '@lucide/svelte/icons/" not in line:
        return False
    # Corruption markers
    if re.search(r'import \{ -[a-z]', line):
        return True
    if re.search(r'from "@lucide/svelte/icons/[a-z-]+ \}', line):
        return True
    if re.search(r"from '@lucide/svelte/icons/[a-z-]+ \}", line):
        return True
    if re.search(r'from "@lucide/svelte/icons/[a-z-]+}', line):
        return True
    # Line has multiple `from "@lucide/svelte/icons/` occurrences
    count = line.count('from "@lucide/svelte/icons/') + line.count("from '@lucide/svelte/icons/")
    if count > 1:
        return True
    return False

def extract_icon_name(line: str):
    """Extract icon name from end of corrupted line."""
    # Pattern: `import { -icon-name";` at end
    m = re.search(r'import \{ -([a-z0-9-]+)["\']', line)
    if m:
        return m.group(1), to_pascal_case(m.group(1))
    # Pattern: `import { -icon-name` with no quotes
    m = re.search(r'import \{ -([a-z0-9-]+)\s*$', line)
    if m:
        return m.group(1), to_pascal_case(m.group(1))
    # Pattern: icon2 already present as last `from "@lucide/svelte/icons/VALID_ICON"`
    # Find all valid icon paths (only letters, digits, hyphens, no space/} after)
    for m in re.finditer(r'from "@lucide/svelte/icons/([a-z][a-z0-9-]*)"', line):
        return m.group(1), to_pascal_case(m.group(1))
    for m in re.finditer(r"from '@lucide/svelte/icons/([a-z][a-z0-9-]*)'", line):
        return m.group(1), to_pascal_case(m.group(1))
    return None, None

def extract_icon_component_name(line: str):
    """Extract icon component name (PascalCase) from the line."""
    # Before the corrupted `from "@lucide/svelte/icons/[kebab-of-module]`:
    # There's `import { ComponentName from "@lucide/svelte/icons/kebab-of-module`
    # Find the LAST `import { [PascalCase] from "@lucide/svelte/icons/` that is corrupted
    for m in re.finditer(r'import \{ ([A-Z][a-zA-Z0-9]*) from "@lucide/svelte/icons/', line):
        name = m.group(1)
        # Check the path after icons/ - if it looks like a module path (has content from module), it's corrupted
        rest = line[m.end():]
        path_end = rest.find('"')
        if path_end == -1:
            path_end = rest.find("'")
        if path_end > 0:
            path = rest[:path_end]
            if not re.match(r'^[a-z][a-z0-9-]*$', path) or '}' in path:
                return name
        else:
            return name
    return None

def find_corruption_start(line: str) -> int:
    """Find the index where corruption starts in the line."""
    # Look for: ` import { [PascalOrCamel] from "@lucide/svelte/icons/[something-with-module-chars]`
    for m in re.finditer(r' import \{ [A-Z][a-zA-Z0-9]* from "@lucide/svelte/icons/', line):
        rest = line[m.end():]
        path_end = rest.find('"')
        if path_end > 0:
            path = rest[:path_end]
            if not re.match(r'^[a-z][a-z0-9-]*$', path):
                return m.start()
    # Alternative: ` import { [camelCase] from "@lucide/svelte/icons/[kebab]`
    for m in re.finditer(r' import \{ [a-z][a-zA-Z0-9]* from "@lucide/svelte/icons/', line):
        rest = line[m.end():]
        path_end = rest.find('"')
        if path_end > 0:
            path = rest[:path_end]
            if not re.match(r'^[a-z][a-z0-9-]*$', path):
                return m.start()
    return -1

def fix_corrupted_line(line: str, indent: str = '  ') -> list:
    """Fix a single corrupted import line into multiple clean lines."""
    stripped = line.strip()

    icon_kebab, icon_pascal = extract_icon_name(stripped)
    # Try to get component name override
    component_name = extract_icon_component_name(stripped)
    if component_name:
        icon_pascal = component_name

    # Find where corruption starts
    corrupt_start = find_corruption_start(stripped)
    if corrupt_start > 0:
        valid_part = stripped[:corrupt_start].strip()
    else:
        # Fallback: take everything and remove the icon suffix
        valid_part = stripped
        # Remove trailing `; import { -...");`
        valid_part = re.sub(r';\s*import \{ -[a-z0-9-]+"[;\s]*$', '', valid_part)
        valid_part = re.sub(r';\s*import \{ -[a-z0-9-]+[;\s]*$', '', valid_part)

    # Fix the valid part: add missing opening { to the first import if needed
    # Pattern: `import identifier } from` → `import { identifier } from`
    def fix_missing_brace(s):
        return re.sub(
            r'^(import\s+)(?!\{|type\s+\{|type\s+\w|\*|"|\')([a-zA-Z_$][a-zA-Z0-9_$]*(?:\s*,\s*[a-zA-Z_$][a-zA-Z0-9_$]*)*)\s+\}',
            lambda m: m.group(1) + '{ ' + m.group(2) + ' }',
            s
        )

    valid_part = fix_missing_brace(valid_part)

    # Split into individual import statements
    # Split on "; import " boundary
    import_stmts = re.split(r';\s*(?=import\s)', valid_part)
    
    result_lines = []
    for stmt in import_stmts:
        stmt = stmt.strip().rstrip(';')
        if stmt:
            # Apply fix_missing_brace on each part too
            stmt = fix_missing_brace(stmt)
            result_lines.append(indent + stmt + ';')

    # Add the icon import at the end
    if icon_kebab and icon_pascal:
        result_lines.append(f'{indent}import {icon_pascal} from "@lucide/svelte/icons/{icon_kebab}";')

    return result_lines

def fix_file(filepath: str) -> bool:
    """Fix all corrupted import lines in a file."""
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    lines = content.splitlines(keepends=True)
    new_lines = []
    changed = False
    in_script = False

    for i, line in enumerate(lines):
        stripped = line.rstrip('\n').rstrip('\r')
        
        if re.search(r'<script', stripped):
            in_script = True
        if re.search(r'</script>', stripped):
            in_script = False

        if in_script and is_corrupted_line(stripped):
            # Determine indent
            indent = '  ' if stripped.startswith('  ') or not stripped.startswith('import') else ''
            fixed = fix_corrupted_line(stripped, indent)
            for fl in fixed:
                new_lines.append(fl + '\n')
            changed = True
            print(f"  [FIXED] {filepath}:{i+1}")
            for fl in fixed:
                print(f"    → {fl}")
        else:
            new_lines.append(line)

    if changed:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
    
    return changed

def main():
    base = '/home/lv/Desktop/fast-platform-core/frontend/src'
    
    # Find all svelte files with corruption
    corrupted_files = []
    for root, dirs, files in os.walk(base):
        # Skip node_modules and .svelte-kit
        dirs[:] = [d for d in dirs if d not in ('node_modules', '.svelte-kit', '__pycache__')]
        for fname in files:
            if fname.endswith('.svelte'):
                fp = os.path.join(root, fname)
                try:
                    with open(fp, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read()
                    if is_corrupted_line_in_content(content):
                        corrupted_files.append(fp)
                except Exception as e:
                    print(f"  [ERROR] Cannot read {fp}: {e}")

    print(f"\nFound {len(corrupted_files)} files with corrupted imports.\n")
    
    fixed_count = 0
    for fp in corrupted_files:
        print(f"\nProcessing: {fp}")
        try:
            if fix_file(fp):
                fixed_count += 1
        except Exception as e:
            print(f"  [ERROR] {e}")
    
    print(f"\n✅ Done. Fixed {fixed_count}/{len(corrupted_files)} files.")

def is_corrupted_line_in_content(content: str) -> bool:
    for line in content.splitlines():
        if is_corrupted_line(line):
            return True
    return False

if __name__ == '__main__':
    main()
