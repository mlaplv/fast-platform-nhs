#!/usr/bin/env bash
set -e
# Update repository
git pull --rebase
# Convert Pydantic imports and add ConfigDict
find backend -type f -name "*.py" | while read f; do
  if grep -q "from pydantic import BaseModel" "$f"; then
    # Add ConfigDict import if not present
    if ! grep -q "ConfigDict" "$f"; then
      sed -i "s/from pydantic import BaseModel/from pydantic import BaseModel, ConfigDict/" "$f"
    fi
    # Insert model_config after each class inheriting BaseModel
    perl -0777 -i -pe "s/(class \w+\(BaseModel\):)/$1\n    model_config = ConfigDict(extra='allow')/g" "$f"
  fi
  # Convert @validator to @field_validator
  if grep -q "@validator" "$f"; then
    sed -i "s/@validator/@field_validator/g" "$f"
  fi
  # Remove legacy Config inner class if exists
  if grep -q "class Config:" "$f"; then
    perl -0777 -i -pe "s/class Config:\n(?:\s+.*\n)+//g" "$f"
  fi
done
# Remove legacy warning filters from main.py
sed -i '12,16d' /home/lv/Desktop/fast-platform-core/backend/main.py
echo "Pydantic V2 migration completed"
