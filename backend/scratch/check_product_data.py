import json
from sqlalchemy import create_url, create_engine, text

# Database connection URL
db_url = "postgresql://postgres:postgres@localhost:5432/fast_platform"
engine = create_engine(db_url)

def check_product_details():
    with engine.connect() as conn:
        # Get the first viral product
        result = conn.execute(text("SELECT id, name, description, metadata, images FROM products LIMIT 1")).fetchone()
        if result:
            print(f"Product ID: {result[0]}")
            print(f"Product Name: {result[1]}")
            print("-" * 20)
            print("DESCRIPTION (first 500 chars):")
            print(result[2][:500] if result[2] else "N/A")
            print("-" * 20)
            print("METADATA:")
            print(json.dumps(result[3], indent=2, ensure_ascii=False) if result[3] else "N/A")
            print("-" * 20)
            print("IMAGES:")
            print(result[4])
        else:
            print("No products found.")

if __name__ == "__main__":
    check_product_details()
