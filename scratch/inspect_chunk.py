import os

filepath = "/home/lv/Desktop/fast-platform-core/frontend/dist/_app/immutable/nodes/9.DcL1N1GE.js"

if os.path.exists(filepath):
    with open(filepath, "r") as f:
        content = f.read()
    
    print("Content length:", len(content))
    # Let's extract around character 10979 (minified on line 4 usually, but let's look at the line or content itself)
    # The traceback has: at 9.DcL1N1GE.js:4:10979
    lines = content.split("\n")
    print("Number of lines:", len(lines))
    
    # Print around character 10979 of line 4 (which is index 3)
    if len(lines) >= 4:
        line4 = lines[3]
        print("Line 4 length:", len(line4))
        start = max(0, 10979 - 150)
        end = min(len(line4), 10979 + 150)
        print("Slice around 10979:")
        print(line4[start:end])
        
        print("\nSlice around 10929:")
        start2 = max(0, 10929 - 150)
        end2 = min(len(line4), 10929 + 150)
        print(line4[start2:end2])
    else:
        # Just slice the whole content around index 10979
        start = max(0, 10979 - 150)
        end = min(len(content), 10979 + 150)
        print("Slice around 10979:")
        print(content[start:end])
else:
    print("File does not exist!")
