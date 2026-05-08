import os
import re

def comprehensive_fix_transitions():
    src_dir = "/home/lv/Desktop/fast-platform-core/frontend/src"
    transition_names = ["fade", "fly", "scale", "slide"]
    
    for root, _, files in os.walk(src_dir):
        for file in files:
            if file.endswith(".svelte"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Find all transitions actually used in the template
                used = []
                for t in transition_names:
                    if re.search(fr"\b(in|out|transition):{t}\b", content):
                        used.append(t)
                
                if not used:
                    continue

                # Check current imports
                import_match = re.search(r"import\s+\{(.*?)\}\s+from\s+['\"]svelte/transition['\"];?", content)
                
                if import_match:
                    current_imports = [i.strip() for i in import_match.group(1).split(",")]
                    missing = [t for t in used if t not in current_imports]
                    
                    if missing:
                        print(f"Updating {path}: adding {missing}")
                        new_imports = sorted(list(set(current_imports + missing)))
                        new_line = f"import {{ {', '.join(new_imports)} }} from 'svelte/transition';"
                        new_content = content.replace(import_match.group(0), new_line)
                        with open(path, "w", encoding="utf-8") as f:
                            f.write(new_content)
                else:
                    # No svelte/transition import at all
                    print(f"Fixing {path}: adding fresh import {used}")
                    import_line = f"  import {{ {', '.join(sorted(used))} }} from 'svelte/transition';\n"
                    # Insert after <script>
                    new_content = re.sub(r'(<script[^>]*>)', r'\1\n' + import_line, content, count=1)
                    if new_content != content:
                        with open(path, "w", encoding="utf-8") as f:
                            f.write(new_content)

if __name__ == "__main__":
    comprehensive_fix_transitions()
