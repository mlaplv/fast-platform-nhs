import asyncio
from sqlalchemy import select
from backend.database import async_session_maker
from backend.database.models.commerce import ProductBase

async def clean_metadata():
    async with async_session_maker() as session:
        # Fetch all active products
        stmt = select(ProductBase)
        res = await session.execute(stmt)
        products = res.scalars().all()
        
        print(f"[*] Found {len(products)} products in the database.")
        
        def clean_str(s):
            if not s:
                return s
            import re
            cleaned = re.sub(r'^(\[OFF\]|\*|\s)+', '', str(s), flags=re.IGNORECASE)
            return cleaned.strip()

        updated_count = 0
        for p in products:
            meta = p.product_metadata
            if not meta:
                continue
            
            print(f"[*] Inspecting Product: {p.name} (ID: {p.id})")
            changed = False
            
            # Fields we want to aggressively clean of [OFF] inside product_metadata
            keys_to_clean = [
                "science_headline",
                "science_headline_1",
                "science_headline_2",
                "science_subheadline",
                "science_card1_title",
                "science_card1_desc",
                "science_card2_title",
                "science_card2_desc",
                "science_faq_title",
                "science_faq_subtitle"
            ]
            
            for key in keys_to_clean:
                if key in meta and meta[key]:
                    val = meta[key]
                    if isinstance(val, str) and ("[OFF]" in val or val.startswith("*")):
                        cleaned_val = clean_str(val)
                        print(f"    - Key '{key}': '{val}' -> '{cleaned_val}'")
                        meta[key] = cleaned_val
                        changed = True
            
            # Check other general metadata string keys for any [OFF] leaks
            for key, val in list(meta.items()):
                if isinstance(val, str) and ("[OFF]" in val or val.startswith("*")):
                    # For non-science subheadline fields, if it is just a string, we strip the [OFF] prefix
                    cleaned_val = clean_str(val)
                    print(f"    - Key '{key}': '{val}' -> '{cleaned_val}'")
                    meta[key] = cleaned_val
                    changed = True
            
            if changed:
                # Assign back to trigger SQL Alchemy JSONB mutation detection
                p.product_metadata = dict(meta)
                session.add(p)
                updated_count += 1
                
        if updated_count > 0:
            await session.commit()
            print(f"[✓] Successfully cleaned up product_metadata for {updated_count} products.")
        else:
            print("[*] No legacy [OFF] prefixes found in any product metadata.")

if __name__ == "__main__":
    asyncio.run(clean_metadata())
