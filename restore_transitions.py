import os
import re

def fix_missing_transitions():
    src_dir = "/home/lv/Desktop/fast-platform-core/frontend/src"
    transition_names = ["fade", "fly", "scale", "slide"]
    
    for root, _, files in os.walk(src_dir):
        for file in files:
            if file.endswith(".svelte"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Check if file uses any transitions
                used = [t for t in transition_names if re.search(fr"\b(in|out|transition):{t}\b", content)]
                
                if used:
                    # Check if svelte/transition import exists
                    if "from 'svelte/transition'" not in content and 'from "svelte/transition"' not in content:
                        print(f"Fixing {path} - adding {', '.join(used)}")
                        
                        import_line = f"  import {{ {', '.join(used)} }} from 'svelte/transition';\n"
                        
                        # Try to insert after <script>
                        new_content = re.sub(r'(<script[^>]*>)', r'\1\n' + import_line, content, count=1)
                        
                        if new_content != content:
                            with open(path, "w", encoding="utf-8") as f:
                                f.write(new_content)

if __name__ == "__main__":
    fix_missing_transitions()
