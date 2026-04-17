import asyncio
import os
import sys

# Ensure backend is in path
sys.path.append(os.getcwd())

from backend.services.commerce.product_vector import ProductVectorService
from backend.services.commerce.product import ProductService
from backend.schemas.product import CreateProductRequest, ProductVariantSchema, VariantAttributes, ProductMetadata
from backend.database.alchemy_config import alchemy_config
from unittest.mock import MagicMock

async def verify():
    # Setup service
    vector_service = MagicMock(spec=ProductVectorService)
    
    # Dummy async function for embedding upsert
    async def dummy_upsert(*args, **kwargs):
        return None
    
    vector_service.upsert_product_embedding = dummy_upsert
    
    product_service = ProductService(vector_service)
    
    # Create request
    try:
        req = CreateProductRequest(
            name="Test Product attributes",
            slug="test-product-attrs-" + os.urandom(4).hex(),
            price=100000,
            sku="TEST-ATTR-" + os.urandom(4).hex(),
            variants=[
                ProductVariantSchema(
                    sku="TEST-ATTR-V1-" + os.urandom(4).hex(),
                    price=100000,
                    stock=10,
                    tier_index=[0],
                    attributes=VariantAttributes(
                        combo_qty=5,
                        gifts=[{"name": "Mask", "qty": 1}]
                    )
                )
            ],
            metadata=ProductMetadata(landing_type='standard')
        )
        
        session_maker = alchemy_config.create_session_maker()
        async with session_maker() as session:
            # Create
            res = await product_service.create_product(session, req)
            pid = res.id
            print(f"Created product: {pid}")
            
            # Get back
            p = await product_service.get_product(session, pid)
            variant = p.variants[0]
            print(f"Variant Attributes type: {type(variant.attributes)}")
            print(f"Variant Attributes content: {variant.attributes}")
            
            success = True
            # Checking attributes - in ProductVariantSchema it's a VariantAttributes object
            if variant.attributes and variant.attributes.combo_qty == 5:
                print("✅ SUCCESS: combo_qty saved correctly.")
            else:
                print(f"❌ FAILURE: combo_qty NOT saved. Value: {variant.attributes.combo_qty if variant.attributes else 'None'}")
                success = False
                
            if variant.attributes and len(variant.attributes.gifts) > 0:
                print("✅ SUCCESS: gifts saved correctly.")
                if variant.attributes.gifts[0].get('name') == "Mask":
                     print("✅ SUCCESS: gift name saved correctly.")
                else:
                     print(f"❌ FAILURE: gift name mismatch: {variant.attributes.gifts[0].get('name')}")
                     success = False
            else:
                print("❌ FAILURE: gifts NOT saved.")
                success = False
            
            if success:
                print("\n🎉 ALL TESTS PASSED!")
            else:
                print("\n⚠️ SOME TESTS FAILED!")
                
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ Error during verification: {e}")

if __name__ == "__main__":
    asyncio.run(verify())
