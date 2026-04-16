import asyncio
import uuid
from decimal import Decimal
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

# Mocking environment
import os
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/fast_platform")

from backend.database.models.commerce import ProductBase, ProductVariant
from backend.services.commerce.checkout import CheckoutService
from backend.schemas.client.checkout import StealthCheckoutSchema, CheckoutItemSchema

async def test_security():
    engine = create_async_engine(DATABASE_URL)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as session:
        # 1. Find a product to test with
        res = await session.execute(select(ProductBase).limit(1))
        product = res.scalar_one_or_none()
        if not product:
            print("❌ No products found in DB to test.")
            return

        db_price = product.discount_price if product.discount_price is not None else product.price
        print(f"🔍 Testing with Product: {product.name} (ID: {product.id}), DB Price: {db_price}")

        # 2. Case: Tampered Price (User tries to buy at 10.0 instead of DB price)
        tampered_price = 10.0
        payload = StealthCheckoutSchema(
            items=[
                CheckoutItemSchema(product_id=product.id, quantity=1, price=tampered_price)
            ],
            customer_name="Test Hacker",
            customer_phone="0987654321",
            customer_address="123 Hacking Street, District 1, HCM",
            total_amount=tampered_price, # Matching the tampered price
            shipping_fee=0,
            payment_method="cod"
        )

        print(f"🛡️ Attempting tampered checkout with price {tampered_price}...")
        try:
            await CheckoutService.create_stealth_order(session, payload, "127.0.0.1", "TestBot")
            print("❌ SECURITY FAILURE: Tampered order was accepted!")
        except Exception as e:
            print(f"✅ SECURITY SUCCESS: Order rejected with error: {e}")

        # 3. Case: Valid Price, Tampered Total (User tries to buy at correct price but modified total)
        payload_valid_price = StealthCheckoutSchema(
            items=[
                CheckoutItemSchema(product_id=product.id, quantity=1, price=db_price)
            ],
            customer_name="Test Hacker 2",
            customer_phone="0987654322",
            customer_address="123 Hacking Street, District 1, HCM",
            total_amount=db_price - 5000, # User tries to shave off 5k from total
            shipping_fee=0,
            payment_method="cod"
        )
        
        print(f"🛡️ Attempting tampered total with price {db_price} but total {db_price - 5000}...")
        try:
            await CheckoutService.create_stealth_order(session, payload_valid_price, "127.0.0.1", "TestBot")
            print("❌ SECURITY FAILURE: Tampered total was accepted!")
        except Exception as e:
            print(f"✅ SECURITY SUCCESS: Order rejected with error: {e}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_security())
