import asyncio
import json
import os
import sys

# Ensure backend can be imported
sys.path.append("/app")

from backend.database.alchemy_config import alchemy_config
from backend.services.commerce.product import ProductService
from backend.services.commerce.product_vector import ProductVectorService
from backend.services.commerce.seo_service import SeoService

async def main():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as session:
        slug = "miccosmo-hurry-harry-premium-neck-cream-rich-40gr-kem-duong-sang-co"
        # In the container environment, we should resolve dependencies
        vector_service = ProductVectorService()
        product_service = ProductService(vector_service=vector_service)
        try:
            product = await product_service.get_product_by_slug(session, slug, is_public=True)
            seo_meta = await SeoService.generate_seo_meta(product, db=session)
            print("=== TITLE ===")
            print(seo_meta.title)
            print("\n=== DESCRIPTION ===")
            print(seo_meta.description)
            print("\n=== CANONICAL URL ===")
            print(seo_meta.canonical_url)
            print("\n=== JSON-LD STRING ===")
            try:
                parsed_ld = json.loads(seo_meta.json_ld_string)
                print(json.dumps(parsed_ld, indent=2, ensure_ascii=False))
            except Exception as e:
                print("Failed to parse JSON-LD:", e)
                print(seo_meta.json_ld_string)
            print("\n=== BREADCRUMB LD STRING ===")
            try:
                parsed_breadcrumb = json.loads(seo_meta.breadcrumb_ld_string)
                print(json.dumps(parsed_breadcrumb, indent=2, ensure_ascii=False))
            except Exception as e:
                print("Failed to parse Breadcrumb JSON-LD:", e)
                print(seo_meta.breadcrumb_ld_string)
            print("\n=== FAQ LD STRING ===")
            try:
                parsed_faq = json.loads(seo_meta.faq_ld_string)
                print(json.dumps(parsed_faq, indent=2, ensure_ascii=False))
            except Exception as e:
                print("Failed to parse FAQ JSON-LD:", e)
                print(seo_meta.faq_ld_string)
        except Exception as e:
            print("Error retrieving product or generating SEO meta:", e)

if __name__ == "__main__":
    asyncio.run(main())
