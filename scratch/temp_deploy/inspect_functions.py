import re

with open("scratch/temp_deploy/Cu6plpcm.js", "r") as f:
    content = f.read()

# Let's find definition of s, a, n close to addPendingSignal or the enclosing function
# We can search for bulkDeleteNotifications:a
match = re.search(r"bulkDeleteNotifications:a", content)
if match:
    # Let's search backwards for definitions of s, a, n
    start = max(0, match.start() - 3500)
    end = min(len(content), match.end() + 2000)
    print("--- CONTEXT AROUND DEFINITIONS ---")
    print(content[start:end])
