import re

with open("scratch/temp_deploy/Cu6plpcm.js", "r") as f:
    content = f.read()

# Let's search for addPendingSignal
for match in re.finditer(r"addPendingSignal", content):
    start = max(0, match.start() - 300)
    end = min(len(content), match.end() + 1000)
    print(f"--- MATCH AT {match.start()} ---")
    print(content[start:end])
    print("\n" + "="*80 + "\n")
