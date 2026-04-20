from backend.schemas.category import CreateCategoryRequest, CategoryMetadata
try:
    data = {
        "name": "Test",
        "show_on_mobile": True,
        "show_on_desktop": True,
        "metadata": {"faqs": []}
    }
    req = CreateCategoryRequest(**data)
    print("MAPPING SUCCESS")
    print(f"showOnMobile: {req.showOnMobile}")
    print(f"showOnDesktop: {req.showOnDesktop}")
except Exception as e:
    print(f"MAPPING FAILED: {e}")
