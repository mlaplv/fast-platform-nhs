import re

file_path = "frontend/src/lib/components/storefront/product-detail/shared/VerificationCenter.svelte"
with open(file_path, "r") as f:
    content = f.read()

# 1. Replace all the rounded classes
content = content.replace("rounded-2xl", "rounded-none")
content = content.replace("!rounded-2xl", "!rounded-none")
content = content.replace("rounded-[32px]", "rounded-none")
content = content.replace("rounded-[24px]", "rounded-none")
content = content.replace("rounded-[20px]", "rounded-none")
content = content.replace("rounded-xl", "rounded-none")

# 2. Replace border-radius 32px to 0px
content = content.replace("border-radius: 32px;", "border-radius: 0px;")

# 3. Replace gaps
content = content.replace("gap-6", "gap-2")
content = content.replace("gap-8", "gap-4")

# 4. Replace margins
content = content.replace("mb-8", "mb-4")
content = content.replace("mb-6", "mb-2")
content = content.replace("mb-10", "mb-4")

# 5. Replace paddings for specific elements
content = content.replace("p-6 sm:p-8", "p-4 sm:p-5")
content = content.replace("p-6 sm:p-10", "p-5 sm:p-8")

with open(file_path, "w") as f:
    f.write(content)

print("Done replacing.")
