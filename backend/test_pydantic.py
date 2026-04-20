from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List

class FaqItem(BaseModel):
    model_config = ConfigDict(strict=True)
    question: str
    answer: str

class CategoryMetadata(BaseModel):
    model_config = ConfigDict(extra='allow', populate_by_name=True)
    faqs: List[FaqItem] = Field(default_factory=list, alias="faqs")

class UpdateCategoryRequest(BaseModel):
    model_config = ConfigDict(strict=True, populate_by_name=True)
    name: Optional[str] = None
    metadata: Optional[CategoryMetadata] = None

# Case 1: Client sends camelCase
try:
    data1 = {"name": "Test", "metadata": {"faqs": [{"question": "Q", "answer": "A"}]}}
    req1 = UpdateCategoryRequest(**data1)
    print("MAPPING 1 SUCCESS (camelCase metadata field, snake_case faqs inside)")
except Exception as e:
    print(f"MAPPING 1 FAILED: {e}")

# Case 2: Client sends snake_case metadata
try:
    data2 = {"name": "Test", "category_metadata": {"faqs": [{"question": "Q", "answer": "A"}]}}
    req2 = UpdateCategoryRequest(**data2)
    print("MAPPING 2 SUCCESS (snake_case)")
except Exception as e:
    print(f"MAPPING 2 FAILED: {e}")

# Case 3: Metadata with camelCase faqs inside
try:
    data3 = {"metadata": {"faqs": [{"question": "Q", "answer": "A"}]}}
    req3 = UpdateCategoryRequest(**data3)
    print("MAPPING 3 SUCCESS")
except Exception as e:
    print(f"MAPPING 3 FAILED: {e}")
