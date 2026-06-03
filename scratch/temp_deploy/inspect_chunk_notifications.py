import re

with open("/home/lv/Desktop/fast-platform-core/frontend/dist/_app/immutable/chunks/Cu6plpcm.js", "r") as f:
    content = f.read()

# Let's search for "new Set"
for match in re.finditer(r"new Set", content):
    start = max(0, match.start() - 500)
    end = min(len(content), match.end() + 1000)
    print(f"--- MATCH AT {match.start()} ---")
    print(content[start:end])
    print("\n" + "="*80 + "\n")
