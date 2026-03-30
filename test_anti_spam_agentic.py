import asyncio
import logging
import os
import sys
from typing import Dict, List, Any

# Mocking modules if necessary, but we try to run in the container context
sys.path.append("/home/lv/Desktop/fast-platform-core")

from backend.services.anti_spam import anti_spam_service, OrderSpamData

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test-anti-spam")

async def run_test():
    logger.info("Starting Anti-Spam Agentic AI 2026 Test Suite...")
    
    # 🧪 Test case 1: Normal Order (Low Score)
    logger.info("--- Test Case 1: Normal Order ---")
    order1: OrderSpamData = {
        "name": "Nguyễn Văn A",
        "phone": "0912345678",
        "address": "123 Đường Lê Lợi, Quận 1, TP.HCM",
        "total": 500000.0,
        "items": [{"id": "prod_1", "quantity": 1}]
    }
    is_spam, reason, score, _ = await anti_spam_service.check_order_spam(
        ip="127.0.0.1",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) test",
        tenant_id="test_tenant",
        order_data=order1
    )
    logger.info(f"Result: is_spam={is_spam}, score={score}, reason='{reason}'")

    # 🧪 Test case 2: Troll/Spam Address (Agentic AI Review)
    logger.info("--- Test Case 2: Troll Address (AI Audit) ---")
    order2: OrderSpamData = {
        "name": "asdfgh",
        "phone": "0988888888",
        "address": "qwertyuiop 123456789", # Rác để AI phân tích
        "total": 1000000.0,
        "items": [{"id": "prod_2", "quantity": 1}]
    }
    is_spam, reason, score, _ = await anti_spam_service.check_order_spam(
        ip="1.1.1.1", # Different IP
        user_agent="Bot/1.0",
        tenant_id="test_tenant",
        order_data=order2
    )
    logger.info(f"Result: is_spam={is_spam}, score={score}, reason='{reason}'")

    # 🧪 Test case 3: VIP Bypass
    logger.info("--- Test Case 3: VIP Bypass ---")
    # Simulate VIP in Redis
    if anti_spam_service.redis:
        await anti_spam_service.redis.sadd("spam:vip:phones", "0900000000")
        order3: OrderSpamData = {
            "name": "Sếp Tổng",
            "phone": "0900000000",
            "address": "123 Smart Shop HQ",
            "total": 10000000.0,
            "items": [{"id": "vip_prod", "quantity": 1}]
        }
        is_spam, reason, score, _ = await anti_spam_service.check_order_spam(
            ip="1.2.3.4",
            user_agent="Elite Mobile",
            tenant_id="test_tenant",
            order_data=order3
        )
        logger.info(f"Result: is_spam={is_spam}, score={score}, reason='{reason}'")
        await anti_spam_service.redis.srem("spam:vip:phones", "0900000000")

    # 🧪 Test case 4: Agentic AI Review (Rapid Fire Case)
    logger.info("--- Test Case 4: Agentic AI Audit (Rapid Fire) ---")
    phone_ai = "0355666777"
    # First call to establish baseline
    await anti_spam_service.check_order_spam(
        ip="9.9.9.9",
        user_agent="Google Chrome Mobile",
        tenant_id="test_tenant",
        order_data={"phone": phone_ai, "name": "Nam", "address": "123 Lê Lợi", "items": []}
    )
    
    # Rapid Fire call (different IP, same phone) -> adds only 50 score -> triggers AI
    order4: OrderSpamData = {
        "name": "Nguyên Hoàng Nam",
        "phone": phone_ai,
        "address": "Địa chỉ rác asdfghjk 123 lừa đảo", # Troll keywords but let's see if AI handles it
        "total": 300000.0,
        "items": [{"id": "prod_4", "quantity": 1}]
    }
    is_spam, reason, score, _ = await anti_spam_service.check_order_spam(
        ip="10.10.10.10", # Different IP to avoid IP Rapid Fire
        user_agent="Google Chrome Mobile",
        tenant_id="test_tenant",
        order_data=order4
    )
    logger.info(f"Result: is_spam={is_spam}, score={score}, reason='{reason}'")

    # 🧪 Test case 5: Direct Agentic AI Review
    logger.info("--- Test Case 5: Direct AI Review (Semantic Analysis) ---")
    bad_addr = "Số nhà x sẹc y thành phố hồ chí minh lừa đảo" # Suspect
    good_addr = "123 Đường Lê Lợi, Phường Bến Thành, Quận 1, TP.HCM"
    
    score_bad = await anti_spam_service.agentic_address_review("Kẻ Phá Hoại", bad_addr)
    logger.info(f"AI Score (Bad Addr): {score_bad}")
    
    score_good = await anti_spam_service.agentic_address_review("Nguyễn Văn Trung", good_addr)
    logger.info(f"AI Score (Good Addr): {score_good}")

    logger.info("All tests completed.")

async def clear_redis():
    if anti_spam_service.redis:
        keys = await anti_spam_service.redis.keys("spam:vector:*")
        if keys:
            await anti_spam_service.redis.delete(*keys)
        logger.info(f"Cleared {len(keys)} test keys from Redis.")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(clear_redis())
    loop.run_until_complete(run_test())
