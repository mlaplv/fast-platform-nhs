#!/usr/bin/env python3
"""
Fix 2 remaining issues:
1. Incorrect icon names (loader2 → loader-2, trash2 → trash-2, etc.)
2. Remaining orphan corrupted lines (on-mount, fade, slide, scale used as icon names)
"""
import re, os

BASE = '/home/lv/Desktop/fast-platform-core/frontend/src'

# Icons that existed with suffix without hyphen in older versions
# but need a hyphen in current @lucide/svelte
ICON_RENAMES = {
    'loader2':         'loader-2',
    'trash2':          'trash-2',
    'check-circle2':   'check-circle-2',
    'bar-chart2':      'bar-chart-2',
    'bar-chart3':      'bar-chart-3',
    'edit3':           'edit-3',
    'maximize2':       'maximize-2',
    'minimize2':       'minimize-2',
    'mouse-pointer2':  'mouse-pointer-2',
    'settings2':       'settings-2',
    'share2':          'share-2',
    'volume2':         'volume-2',
    'wand2':           'wand-2',
    'wand2-sparkles':  'wand-sparkles',
}

# These paths are NOT valid lucide icon names — they snuck in as corruption remnants
BAD_LUCIDE_PATHS = {
    'fade', 'fly', 'slide', 'scale', 'on-mount', 'format-bytes',
    'product-metadata', 'z_index_admin', 'z_index_client',
    'on-mount } from ',
    "scale } from 'svelte/transition';",
    "z_index_admin } from '$lib/core/constants/z_index_admin'; import { fade",
    "z_index_client } from '$lib/core/constants/z-index'; import { x",
}

def fix_icon_renames(content: str) -> str:
    """Replace deprecated icon paths with correct names."""
    for old, new in ICON_RENAMES.items():
        # Match in import paths: "@lucide/svelte/icons/OLD"
        content = content.replace(
            f'@lucide/svelte/icons/{old}"',
            f'@lucide/svelte/icons/{new}"'
        )
        content = content.replace(
            f"@lucide/svelte/icons/{old}'",
            f"@lucide/svelte/icons/{new}'"
        )
    return content

def is_bad_lucide_import(line: str) -> bool:
    """Detect lines with bad lucide icon paths."""
    for bad in BAD_LUCIDE_PATHS:
        if f'@lucide/svelte/icons/{bad}' in line:
            return True
    return False

def fix_bad_lucide_line(line: str) -> str | None:
    """
    Try to salvage line or return None to delete it.
    These are remnant corrupted lines that the main script missed.
    """
    stripped = line.strip()

    # Pattern: import Xxx from "@lucide/svelte/icons/on-mount"  → belongs elsewhere
    # Pattern: import Xxx from "@lucide/svelte/icons/fade"       → belongs elsewhere
    # These are completely bogus - remove them
    if re.match(r'^import \w+ from "@lucide/svelte/icons/(fade|fly|slide|scale|on-mount|format-bytes|product-metadata)";?$', stripped):
        return None  # Delete line

    # Pattern still has the full corruption tail
    # e.g: `import { Z_INDEX_ADMIN } from '...'; import { fade from "@lucide/svelte/icons/z_index_admin..."`
    # Split at the corrupted icon import and keep just the first part
    split_match = re.search(r' import \{ \w+ from "@lucide/svelte/icons/(?:z_index|on-mount|scale \}|fade \})', line)
    if split_match:
        valid = line[:split_match.start()].rstrip('; ').strip()
        if valid and not valid.endswith(';'):
            valid += ';'
        return valid if valid else None

    return line  # Keep as-is if we can't parse

def process_file(filepath: str) -> bool:
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        original = f.read()

    # Step 1: Fix icon name renames
    content = fix_icon_renames(original)

    # Step 2: Fix bad lucide paths line by line
    lines = content.splitlines(keepends=True)
    new_lines = []
    changed = False
    in_script = False

    for i, line in enumerate(lines):
        if '<script' in line:
            in_script = True
        if '</script>' in line:
            in_script = False

        if in_script and is_bad_lucide_import(line.rstrip()):
            fixed = fix_bad_lucide_line(line.rstrip())
            if fixed is None:
                print(f"  [DELETED] {filepath}:{i+1}: {line.rstrip()[:80]}")
                changed = True
                # Don't append — effectively delete
            elif fixed != line.rstrip():
                print(f"  [FIXED]   {filepath}:{i+1}")
                print(f"    from: {line.rstrip()[:80]}")
                print(f"    to:   {fixed[:80]}")
                new_lines.append(fixed + '\n')
                changed = True
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    if content != original:
        changed = True

    if changed:
        final = ''.join(new_lines) if new_lines else content
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(final)
    return changed

def main():
    fixed = 0
    total = 0
    for root, dirs, files in os.walk(BASE):
        dirs[:] = [d for d in dirs if d not in ('node_modules', '.svelte-kit', '__pycache__')]
        for fname in files:
            if not fname.endswith('.svelte'):
                continue
            fp = os.path.join(root, fname)
            try:
                with open(fp, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                needs_fix = any(old in content for old in ICON_RENAMES) or \
                            any(f'@lucide/svelte/icons/{b}' in content for b in BAD_LUCIDE_PATHS)
                if needs_fix:
                    total += 1
                    print(f"\nProcessing: {fp}")
                    if process_file(fp):
                        fixed += 1
            except Exception as e:
                print(f"  [ERROR] {fp}: {e}")

    print(f"\n✅ Done. Fixed {fixed}/{total} files.")

if __name__ == '__main__':
    main()
