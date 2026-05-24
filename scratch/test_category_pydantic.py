import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.schemas.category import UpdateCategoryRequest
from pydantic import ValidationError

payload = {
    "name": "Kem mắt",
    "slug": "kem-mat",
    "parentId": "cat_cham_soc_mat",
    "description": "Mô tả kem mắt",
    "seoTitle": "SEO Title Kem mắt",
    "seoDescription": "SEO Description Kem mắt",
    "image": "",
    "icon": "",
    "show_on_mobile": True,
    "show_on_desktop": True,
    "metadata": {
        "faqs": [
            {"question": "Kem mắt dùng khi nào?", "answer": "Dùng vào buổi tối."}
        ],
        "seo_keywords": "kem mat, duong mat"
    }
}

try:
    data = UpdateCategoryRequest.model_validate(payload)
    print("SUCCESS!")
    print("Validated data:", data)
    print("Dump by alias:", data.metadata.model_dump(by_alias=True) if data.metadata else None)
except ValidationError as e:
    print("VALIDATION ERROR:")
    print(e)
