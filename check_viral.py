import sys
from sqlalchemy import create_engine, text

engine = create_engine("postgresql://postgres:postgres@localhost:5432/fast_platform")
with engine.connect() as conn:
    res = conn.execute(text("SELECT id, name, metadata FROM products LIMIT 5;"))
    for row in res:
        metadata = row[2]
        viral = metadata.get('viral_suite', {})
        share = viral.get('share_promotion', {})
        if share:
            print(f"Product: {row[1]}")
            print(f"Voucher ID: {share.get('voucher_id')}")
            print(f"Reward Label: {viral.get('share_reward_label')}")
            print("---")
