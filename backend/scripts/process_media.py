import os
import uuid
import asyncio
from PIL import Image
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configuration
BASE_PATH = "/app/frontend/static/uploads/img"
SOURCE_FILE = "logo.webp"
OUTPUT_FILE = "logo_transparent.webp"
TENANT_ID = "micsmo.com"
DB_URL = "postgresql://postgres:postgres@db:5432/fast_platform"

def remove_background(input_path, output_path):
    print(f"🎨 Processing {input_path} for background removal...")
    img = Image.open(input_path).convert("RGBA")
    datas = img.getdata()

    new_data = []
    # Using a threshold for "whitish" colors
    # Our target was (241, 241, 239)
    threshold = 220 
    
    for item in datas:
        # If all R, G, B are above the threshold, make it transparent
        if item[0] >= threshold and item[1] >= threshold and item[2] >= threshold:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append(item)

    img.putdata(new_data)
    img.save(output_path, "WEBP")
    print(f"✅ Saved transparent logo to {output_path}")

async def register_to_db(filename, relative_path):
    print(f"💾 Registering {filename} to database...")
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    asset_id = str(uuid.uuid4())
    file_size = os.path.getsize(f"/app/frontend/static{relative_path}")
    
    with Image.open(f"/app/frontend/static{relative_path}") as img:
        dims = f"{img.width}x{img.height}"

    try:
        # Check if already exists
        result = session.execute(text("SELECT id FROM media_registry WHERE file_path = :path"), {"path": relative_path}).fetchone()
        if result:
            print(f"⚠️  File already registered in DB (ID: {result[0]}). Skipping insertion.")
            return

        session.execute(
            text("""
                INSERT INTO media_registry (id, filename, file_path, file_size, mime_type, dimensions, provider, is_linked, tenant_id, media_metadata, created_at, updated_at)
                VALUES (:id, :filename, :file_path, :file_size, :mime_type, :dimensions, :provider, :is_linked, :tenant, :meta, NOW(), NOW())
            """),
            {
                "id": asset_id,
                "filename": filename,
                "file_path": relative_path,
                "file_size": file_size,
                "mime_type": "image/webp",
                "dimensions": dims,
                "provider": "local",
                "is_linked": False,
                "tenant": TENANT_ID,
                "meta": "{}"
            }
        )
        session.commit()
        print(f"🚀 Successfully registered in DB (ID: {asset_id})")
    except Exception as e:
        session.rollback()
        print(f"❌ Error during DB registration: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    input_p = os.path.join(BASE_PATH, SOURCE_FILE)
    output_p = os.path.join(BASE_PATH, OUTPUT_FILE)
    
    # Do work
    remove_background(input_p, output_p)
    
    # Register (relative to static root)
    asyncio.run(register_to_db(OUTPUT_FILE, f"/uploads/img/{OUTPUT_FILE}"))
