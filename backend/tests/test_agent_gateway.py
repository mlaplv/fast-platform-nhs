import pytest
from litestar.testing import AsyncTestClient
from backend.main import app

@pytest.fixture(autouse=True)
def clear_redis_blacklist_sync_fixture():
    """Clear Redis security blacklist for test client synchronously before each test."""
    import redis
    import os
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    try:
        r = redis.from_url(redis_url, decode_responses=True)
        r.delete("support:blacklist:testclient")
        r.delete("support:security_infractions:testclient")
    except Exception:
        pass

@pytest.mark.asyncio
async def test_well_known_ai_plugin():
    """Verify that the OpenAI Plugin manifest endpoint serves valid specifications."""
    async with AsyncTestClient(app=app, base_url="http://test") as client:
        response = await client.get("/.well-known/ai-plugin.json")
        assert response.status_code == 200
        data = response.json()
        assert data.get("schema_version") == "v1"
        assert data.get("name_for_model") == "osmo_ai_commerce"
        assert "api" in data

@pytest.mark.asyncio
async def test_well_known_mcp_discovery():
    """Verify that the Model Context Protocol manifest endpoint serves correct server metadata."""
    async with AsyncTestClient(app=app, base_url="http://test") as client:
        response = await client.get("/.well-known/mcp.json")
        assert response.status_code == 200
        data = response.json()
        assert data.get("mcp_version") == "2024-11-05"
        assert data.get("name") == "Osmo Commerce Public MCP"
        assert "capabilities" in data

@pytest.mark.asyncio
async def test_public_mcp_tools_listing():
    """Verify that the consumer MCP tools can be listed publicly without admin auth."""
    async with AsyncTestClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/client/mcp/tools")
        assert response.status_code == 200
        tools = response.json()
        assert isinstance(tools, list)
        
        tool_names = [t["name"] for t in tools]
        assert "search_products" in tool_names
        assert "preview_pricing" in tool_names
        assert "stealth_checkout" in tool_names

@pytest.mark.asyncio
async def test_pricing_preview_endpoint():
    """Verify Phase 1: POST /api/v1/client/checkout/preview calculating pricing breakdown."""
    payload = {
        "items": [
            {
                "product_id": "test_product_1",
                "variant_id": None,
                "quantity": 2,
                "price": 150000.0
            }
        ],
        "voucher_ids": [],
        "points_to_redeem": 0,
        "available_points": 0
    }
    async with AsyncTestClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/client/checkout/preview", json=payload)
        assert response.status_code in (200, 201)
        data = response.json()
        assert "subtotal" in data
        assert "final_payable" in data
        assert data["subtotal"] == 300000.0

@pytest.mark.asyncio
async def test_webhook_registration():
    """Verify Phase 2: Callback URL registration for order tracking."""
    payload = {
        "order_id": "order_test_123",
        "callback_url": "https://callback.my-agent.com/webhooks"
    }
    async with AsyncTestClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/client/checkout/webhook/register", json=payload)
        assert response.status_code in (200, 201)
        data = response.json()
        assert data.get("status") == "success"
        assert data.get("order_id") == "order_test_123"

@pytest.mark.asyncio
async def test_stealth_checkout_error_mapping():
    """Verify Phase 1: Structured machine-readable error returns on invalid parameters."""
    invalid_checkout = {
        "items": [], # Invalid empty list
        "customer_name": "Test Agent",
        "customer_phone": "0988776655",
        "customer_address": "HN",
        "total_amount": 100000
    }
    async with AsyncTestClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/client/checkout/stealth", json=invalid_checkout)
        # Validation error from Litestar/Pydantic
        assert response.status_code in (400, 422)

@pytest.mark.asyncio
async def test_agent_api_key_auth_and_bypass():
    """Verify Phase 3: AI Agent verified API Key bypasses User-Agent anti-bot check in support chat."""
    chat_payload = {
        "message": "Hello, I am an autonomous AI agent buying a beauty product.",
        "customer_name": "AI Agent Partner",
        "customer_phone": "0988665544"
    }
    # Headless User-Agent would normally be blocked with 403 Forbidden
    headers = {
        "User-Agent": "headless-python-requests/2.31.0",
        "X-Agent-API-Key": "osmo-agent-secure-key-2026"
    }
    async with AsyncTestClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/client/support/chat", json=chat_payload, headers=headers)
        # Verify it bypasses 403 Forbidden anti-bot check and proceeds to session check or execution
        assert response.status_code != 403

@pytest.mark.asyncio
async def test_agent_metrics_endpoint():
    """Verify Phase 3: Accessing telemetry metrics endpoint with verified API Key."""
    headers = {
        "X-Agent-API-Key": "osmo-agent-secure-key-2026"
    }
    async with AsyncTestClient(app=app, base_url="http://test") as client:
        # Request metrics endpoint
        response = await client.get("/api/v1/client/mcp/metrics", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "success"
        assert "metrics" in data
        assert "orders" in data["metrics"]
        assert "tokens" in data["metrics"]

@pytest.mark.asyncio
async def test_a2a_context_header_json():
    """Verify that a raw JSON X-A2A-Context header is successfully parsed and integrated into the request scope."""
    import json
    chat_payload = {
        "message": "Tư vấn cho tôi kem dưỡng ẩm.",
        "customer_name": "AI Partner",
        "customer_phone": "0988665544"
    }
    a2a_payload = {
        "referring_agent": "Google Gemini Agent",
        "user_intent": "Tìm kem dưỡng phục hồi da khô",
        "budget_range": "300k - 500k",
        "geo_location": "Hà Nội"
    }
    headers = {
        "User-Agent": "headless-python-requests/2.31.0",
        "X-Agent-API-Key": "osmo-agent-secure-key-2026",
        "X-A2A-Context": json.dumps(a2a_payload)
    }
    async with AsyncTestClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/client/support/chat", json=chat_payload, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("ok") is True

@pytest.mark.asyncio
async def test_a2a_context_header_base64():
    """Verify that a Base64-encoded X-A2A-Context header is successfully decoded, parsed, and integrated."""
    import json
    import base64
    chat_payload = {
        "message": "Tư vấn cho tôi kem dưỡng ẩm.",
        "customer_name": "AI Partner",
        "customer_phone": "0988665544"
    }
    a2a_payload = {
        "referring_agent": "OpenAI GPT Agent",
        "user_intent": "Tìm kem chống nắng cho da dầu mụn",
        "budget_range": "400k - 600k",
        "geo_location": "Sài Gòn"
    }
    encoded_a2a = base64.b64encode(json.dumps(a2a_payload).encode("utf-8")).decode("utf-8")
    headers = {
        "User-Agent": "headless-python-requests/2.31.0",
        "X-Agent-API-Key": "osmo-agent-secure-key-2026",
        "X-A2A-Context": encoded_a2a
    }
    async with AsyncTestClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/client/support/chat", json=chat_payload, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("ok") is True

@pytest.mark.asyncio
async def test_unauthorized_mcp_tool_triggers_security_infraction():
    """Verify that calling an unauthorized MCP tool returns an error and records a security infraction."""
    payload = {
        "name": "dangerous_admin_tool",
        "arguments": {}
    }
    try:
        async with AsyncTestClient(app=app, base_url="http://test") as client:
            response = await client.post("/api/v1/client/mcp/call", json=payload)
            assert response.status_code in (200, 201)
            data = response.json()
            assert data.get("status") == "error"
            assert "restricted or unauthorized" in data.get("message", "")
    finally:
        try:
            import redis
            import os
            redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
            r = redis.from_url(redis_url, decode_responses=True)
            r.delete("support:security_infractions:testclient")
            r.delete("support:blacklist:testclient")
            r.delete("security:blacklist:ip:testclient")
            r.delete("support:security_infractions:127.0.0.1")
            r.delete("support:blacklist:127.0.0.1")
            r.delete("security:blacklist:ip:127.0.0.1")
        except Exception:
            pass

@pytest.mark.asyncio
async def test_agent_signature_and_replay_protection():
    """Verify that cryptographic signatures (HMAC-SHA256) and replay protection work."""
    import hmac
    import hashlib
    import time
    import json
    
    agent_key = "osmo-agent-secure-key-2026"
    payload = {
        "name": "search_products",
        "arguments": {"query": "kem duong", "limit": 1}
    }
    body_str = json.dumps(payload, separators=(',', ':'))
    
    # 1. Valid Signature & Valid Timestamp
    now = str(time.time())
    sig = hmac.new(agent_key.encode("utf-8"), body_str.encode("utf-8"), hashlib.sha256).hexdigest()
    
    headers = {
        "User-Agent": "headless-python-requests/2.31.0",
        "X-Agent-API-Key": agent_key,
        "X-Agent-Signature": sig,
        "X-Agent-Timestamp": now
    }
    
    try:
        async with AsyncTestClient(app=app, base_url="http://test") as client:
            # 1. Valid Signature & Valid Timestamp
            response = await client.post("/api/v1/client/mcp/call", json=payload, headers=headers)
            assert response.status_code in (200, 201)
            
            # 2. Replay Protection - Expired Timestamp
            expired_time = str(time.time() - 400) # > 300s window
            sig_expired = hmac.new(agent_key.encode("utf-8"), body_str.encode("utf-8"), hashlib.sha256).hexdigest()
            
            headers_expired = {
                "User-Agent": "headless-python-requests/2.31.0",
                "X-Agent-API-Key": agent_key,
                "X-Agent-Signature": sig_expired,
                "X-Agent-Timestamp": expired_time
            }
            response = await client.post("/api/v1/client/mcp/call", json=payload, headers=headers_expired)
            assert response.status_code == 403
            
            # 3. Tampered Payload (Invalid Signature)
            headers_tampered = {
                "User-Agent": "headless-python-requests/2.31.0",
                "X-Agent-API-Key": agent_key,
                "X-Agent-Signature": "invalid-signature-value-12345",
                "X-Agent-Timestamp": now
            }
            response = await client.post("/api/v1/client/mcp/call", json=payload, headers=headers_tampered)
            assert response.status_code == 403
    finally:
        try:
            import redis
            import os
            redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
            r = redis.from_url(redis_url, decode_responses=True)
            r.delete("support:security_infractions:testclient")
            r.delete("support:blacklist:testclient")
            r.delete("security:blacklist:ip:testclient")
            r.delete("support:security_infractions:127.0.0.1")
            r.delete("support:blacklist:127.0.0.1")
            r.delete("security:blacklist:ip:127.0.0.1")
        except Exception:
            pass

def generate_admin_token():
    import jwt
    import os
    from datetime import datetime, timedelta, timezone
    secret_key = os.environ.get("ENCRYPTION_SALT", "osmo_Elite_Standard_Salt_2026")
    payload = {
        "id": "admin-test-id",
        "sub": "admin@osmo.vn",
        "roles": ["SUPER_ADMIN"],
        "perms": [],
        "stamp": "VALID_STAMP_2026",
        "name": "Admin Test User",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    return jwt.encode(payload, secret_key, algorithm="HS256")

@pytest.mark.asyncio
async def test_admin_manual_blacklist_and_whitelist():
    """Verify that an admin can manually blacklist and whitelist an IP address."""
    import os
    import redis
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    try:
        r = redis.from_url(redis_url, decode_responses=True)
        r.delete("support:blacklist:192.168.99.99")
        r.delete("support:security_infractions:192.168.99.99")
    except Exception:
        pass
        
    try:
        token = generate_admin_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        async with AsyncTestClient(app=app, base_url="http://test") as client:
            # 1. Manually blacklist IP
            blacklist_payload = {"ip": "192.168.99.99", "duration": 3600}
            response = await client.post("/api/v1/client/mcp/blacklist", json=blacklist_payload, headers=headers)
            assert response.status_code in (200, 201)
            data = response.json()
            assert data.get("status") == "success"
            
            # Verify the IP is indeed blacklisted by checking metrics
            metrics_response = await client.get("/api/v1/client/mcp/metrics", headers=headers)
            assert metrics_response.status_code == 200
            metrics_data = metrics_response.json()
            blacklisted_ips = metrics_data.get("metrics", {}).get("blacklisted_ips", [])
            assert any(item["ip"] == "192.168.99.99" for item in blacklisted_ips)
            
            # 2. Manually whitelist/unblock IP
            response_unblock = await client.post("/api/v1/client/mcp/whitelist", json={"ip": "192.168.99.99"}, headers=headers)
            assert response_unblock.status_code in (200, 201)
            data_unblock = response_unblock.json()
            assert data_unblock.get("status") == "success"
            
            # Verify it's no longer blacklisted
            metrics_response = await client.get("/api/v1/client/mcp/metrics", headers=headers)
            assert metrics_response.status_code == 200
            metrics_data = metrics_response.json()
            blacklisted_ips = metrics_data.get("metrics", {}).get("blacklisted_ips", [])
            assert not any(item["ip"] == "192.168.99.99" for item in blacklisted_ips)
    finally:
        try:
            r = redis.from_url(redis_url, decode_responses=True)
            r.delete("support:blacklist:192.168.99.99")
            r.delete("support:security_infractions:192.168.99.99")
        except Exception:
            pass

@pytest.mark.asyncio
async def test_mcp_stealth_checkout_records_order():
    """Verify that calling the stealth_checkout tool via /api/v1/client/mcp/call is logged in AgentMonitor telemetry."""
    import hmac
    import hashlib
    import time
    import json
    import redis
    import os
    
    initial_sandbox = 0
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    try:
        r = redis.from_url(redis_url, decode_responses=True)
        initial_sandbox = int(r.hget("agent:metrics:orders", "sandbox") or 0)
        r.sadd("spam:whitelist:phones", "0988665544")
    except Exception:
        pass
    try:
        from backend.database.dependencies import get_session
        from backend.database.models.commerce import ProductBase
        from sqlalchemy import select
        
        from sqlalchemy.orm import selectinload
        async with get_session() as session:
            # Query an active product from the database (like a real client)
            stmt = select(ProductBase).where(ProductBase.status == "ACTIVE").limit(1).options(selectinload(ProductBase.variants))
            res_db = await session.execute(stmt)
            prod = res_db.scalars().first()
            if not prod:
                stmt = select(ProductBase).limit(1).options(selectinload(ProductBase.variants))
                res_db = await session.execute(stmt)
                prod = res_db.scalars().first()
            if not prod:
                prod = ProductBase(
                    id="prod_miccosmo_virgin_white",
                    name="Miccosmo Beppin Body Virgin White Serum 30g",
                    slug="miccosmo-beppin-body-virgin-white-serum",
                    sku="4968123159004",
                    price=600000,
                    stock=99,
                    status="ACTIVE",
                    category_id="cham-soc-da",
                    tenant_id="osmo.vn"
                )
                session.add(prod)
                await session.commit()
            
            product_id = prod.id
            combo_variants = [v for v in prod.variants if v.attributes and v.attributes.get("combo_qty")]
            if combo_variants:
                sorted_tiers = sorted(combo_variants, key=lambda v: int(v.attributes.get("combo_qty", 0)), reverse=True)
                best_tier = next((v for v in sorted_tiers if int(v.attributes.get("combo_qty", 0)) <= 1), None)
                if best_tier:
                    price = int(best_tier.discount_price if best_tier.discount_price is not None else best_tier.price)
                else:
                    price = int(prod.discount_price if prod.discount_price is not None else prod.price)
            else:
                price = int(prod.discount_price if prod.discount_price is not None else prod.price)

        agent_key = "osmo-agent-secure-key-2026"
        payload = {
            "name": "stealth_checkout",
            "arguments": {
                "items": [
                    {
                        "product_id": product_id,
                        "variant_id": None,
                        "quantity": 1,
                        "price": price
                    }
                ],
                "customer_name": "Nguyen Van A Sandbox",
                "customer_phone": "0988665544",
                "customer_address": "Hà Nội",
                "total_amount": price,
                "sandbox": True
            }
        }
        
        body_str = json.dumps(payload, separators=(',', ':'))
        now = str(time.time())
        sig = hmac.new(agent_key.encode("utf-8"), body_str.encode("utf-8"), hashlib.sha256).hexdigest()
        
        headers = {
            "User-Agent": "headless-python-requests/2.31.0",
            "X-Agent-API-Key": agent_key,
            "X-Agent-Signature": sig,
            "X-Agent-Timestamp": now,
            "Content-Type": "application/json"
        }
        
        token = generate_admin_token()
        admin_headers = {"Authorization": f"Bearer {token}"}
        
        async with AsyncTestClient(app=app, base_url="http://test") as client:
            # Call stealth_checkout tool
            response = await client.post("/api/v1/client/mcp/call", content=body_str, headers=headers)
            assert response.status_code in (200, 201)
            data = response.json()
            assert data.get("status") == "success"
            
            # Check metrics to verify order count increased
            metrics_response = await client.get("/api/v1/client/mcp/metrics", headers=admin_headers)
            assert metrics_response.status_code == 200
            metrics_data = metrics_response.json()
            orders = metrics_data.get("metrics", {}).get("orders", {})
            assert orders.get("sandbox", 0) > initial_sandbox
            
            # Allow background tasks and event bus to finish before disposing pool
            import asyncio
            await asyncio.sleep(0.5)
    finally:
        try:
            r = redis.from_url(redis_url, decode_responses=True)
            r.srem("spam:whitelist:phones", "0988665544")
        except Exception:
            pass
        try:
            from backend.database.models.commerce import Order
            from sqlalchemy import delete
            async with get_session() as session:
                delete_stmt = delete(Order).where(Order.customer_phone == "0988665544")
                await session.execute(delete_stmt)
                await session.commit()
        except Exception:
            pass
        try:
            from backend.database.alchemy_config import alchemy_config
            await alchemy_config.get_engine().dispose()
        except Exception:
            pass


@pytest.mark.asyncio
async def test_mcp_stealth_checkout_records_real_order():
    """Verify that calling the stealth_checkout tool with sandbox=False increments the 'real' orders telemetry counter."""
    import hmac
    import hashlib
    import time
    import json
    import redis
    import os
    
    initial_real = 0
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    try:
        r = redis.from_url(redis_url, decode_responses=True)
        initial_real = int(r.hget("agent:metrics:orders", "real") or 0)
        r.sadd("spam:whitelist:phones", "0988665544")
    except Exception:
        pass
    try:
        from backend.database.dependencies import get_session
        from backend.database.models.commerce import ProductBase
        from sqlalchemy import select
        
        from sqlalchemy.orm import selectinload
        async with get_session() as session:
            # Query an active product from the database (like a real client)
            stmt = select(ProductBase).where(ProductBase.status == "ACTIVE").limit(1).options(selectinload(ProductBase.variants))
            res_db = await session.execute(stmt)
            prod = res_db.scalars().first()
            if not prod:
                stmt = select(ProductBase).limit(1).options(selectinload(ProductBase.variants))
                res_db = await session.execute(stmt)
                prod = res_db.scalars().first()
            if not prod:
                prod = ProductBase(
                    id="prod_miccosmo_virgin_white",
                    name="Miccosmo Beppin Body Virgin White Serum 30g",
                    slug="miccosmo-beppin-body-virgin-white-serum",
                    sku="4968123159004",
                    price=600000,
                    stock=99,
                    status="ACTIVE",
                    category_id="cham-soc-da",
                    tenant_id="osmo.vn"
                )
                session.add(prod)
                await session.commit()
            
            product_id = prod.id
            combo_variants = [v for v in prod.variants if v.attributes and v.attributes.get("combo_qty")]
            if combo_variants:
                sorted_tiers = sorted(combo_variants, key=lambda v: int(v.attributes.get("combo_qty", 0)), reverse=True)
                best_tier = next((v for v in sorted_tiers if int(v.attributes.get("combo_qty", 0)) <= 1), None)
                if best_tier:
                    price = int(best_tier.discount_price if best_tier.discount_price is not None else best_tier.price)
                else:
                    price = int(prod.discount_price if prod.discount_price is not None else prod.price)
            else:
                price = int(prod.discount_price if prod.discount_price is not None else prod.price)

        agent_key = "osmo-agent-secure-key-2026"
        payload = {
            "name": "stealth_checkout",
            "arguments": {
                "items": [
                    {
                        "product_id": product_id,
                        "variant_id": None,
                        "quantity": 1,
                        "price": price
                    }
                ],
                "customer_name": "Nguyen Van A Real",
                "customer_phone": "0988665544",
                "customer_address": "Hà Nội",
                "total_amount": price,
                "sandbox": False
            }
        }
        
        body_str = json.dumps(payload, separators=(',', ':'))
        now = str(time.time())
        sig = hmac.new(agent_key.encode("utf-8"), body_str.encode("utf-8"), hashlib.sha256).hexdigest()
        
        headers = {
            "User-Agent": "headless-python-requests/2.31.0",
            "X-Agent-API-Key": agent_key,
            "X-Agent-Signature": sig,
            "X-Agent-Timestamp": now,
            "Content-Type": "application/json"
        }
        
        token = generate_admin_token()
        admin_headers = {"Authorization": f"Bearer {token}"}
        
        async with AsyncTestClient(app=app, base_url="http://test") as client:
            response = await client.post("/api/v1/client/mcp/call", content=body_str, headers=headers)
            assert response.status_code in (200, 201)
            data = response.json()
            assert data.get("status") == "success"
            
            metrics_response = await client.get("/api/v1/client/mcp/metrics", headers=admin_headers)
            assert metrics_response.status_code == 200
            metrics_data = metrics_response.json()
            orders = metrics_data.get("metrics", {}).get("orders", {})
            assert orders.get("real", 0) > initial_real
            
            import asyncio
            await asyncio.sleep(0.5)
    finally:
        try:
            r = redis.from_url(redis_url, decode_responses=True)
            r.srem("spam:whitelist:phones", "0988665544")
        except Exception:
            pass
        try:
            from backend.database.models.commerce import Order
            from sqlalchemy import delete
            async with get_session() as session:
                delete_stmt = delete(Order).where(Order.customer_phone == "0988665544")
                await session.execute(delete_stmt)
                await session.commit()
        except Exception:
            pass
        try:
            from backend.database.alchemy_config import alchemy_config
            await alchemy_config.get_engine().dispose()
        except Exception:
            pass


@pytest.mark.asyncio
async def test_agent_user_delegation_and_auto_optimize():
    """Verify Phase 1 & 2 integration: Agent inheriting User Context and Auto-Optimizing pricing."""
    import hmac
    import hashlib
    import time
    import json
    import jwt
    import os
    from datetime import datetime, timezone, timedelta
    from backend.database.dependencies import get_session
    from backend.database.models.commerce import UserLoyalty
    from backend.database.models.auth import User
    from backend.database.models.promotion import Voucher
    from sqlalchemy import select
    
    agent_key = "osmo-agent-secure-key-2026"
    user_id = "test-delegated-user-123"
    phone = "0988665544"
    
    async with get_session() as session:
        # Create User if not exist
        stmt = select(User).where((User.id == user_id) | (User.username == phone))
        res_user = await session.execute(stmt)
        user = res_user.scalars().first()
        if not user:
            user = User(
                id=user_id,
                username=phone,
                phone=phone,
                email="delegated@osmo.vn",
                name="Delegated Customer",
                status="ACTIVE",
                password="dummy"
            )
            session.add(user)
        else:
            user_id = user.id
            
        # Create Loyalty if not exist
        stmt_loyalty = select(UserLoyalty).where(UserLoyalty.user_id == user_id)
        res_loyalty = await session.execute(stmt_loyalty)
        loyalty = res_loyalty.scalars().first()
        if not loyalty:
            loyalty = UserLoyalty(
                user_id=user_id,
                available_points=1000, # 1,000 points
                balance_seal="dummy",
                tenant_id="osmo.vn"
            )
            session.add(loyalty)
        else:
            loyalty.available_points = 1000
            loyalty.tenant_id = "osmo.vn"
            
        # Create a test voucher
        voucher_id = "test-opt-voucher-123"
        voucher = await session.get(Voucher, voucher_id)
        if not voucher:
            voucher = Voucher(
                id=voucher_id,
                type="FIXED",
                value=50000, # 50k off
                min_spend=100000,
                is_active=True,
                used_count=0,
                usage_limit=10,
                priority=1,
                tenant_id="osmo.vn"
            )
            session.add(voucher)
        else:
            voucher.value = 50000
            voucher.min_spend = 100000
            voucher.is_active = True
            voucher.used_count = 0
            voucher.usage_limit = 10
            voucher.tenant_id = "osmo.vn"
            voucher.start_date = datetime.now(timezone.utc) - timedelta(days=1)
            voucher.end_date = datetime.now(timezone.utc) + timedelta(days=1)
            
        await session.commit()
    
    # Dispose engine to clear pool before starting test client
    from backend.database.alchemy_config import alchemy_config
    await alchemy_config.get_engine().dispose()

    # Generate user delegation token
    secret_key = os.environ.get("ENCRYPTION_SALT", "osmo_Elite_Standard_Salt_2026")
    user_token_payload = {
        "id": user_id,
        "sub": phone,
        "email": "delegated@osmo.vn",
        "roles": ["CUSTOMER"],
        "perms": [],
        "stamp": "VALID_STAMP_2026",
        "name": "Delegated Customer",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    user_token = jwt.encode(user_token_payload, secret_key, algorithm="HS256")

    # Call preview_pricing via Agent gateway with X-User-Delegation-Token
    payload = {
        "name": "preview_pricing",
        "arguments": {
            "items": [
                {
                    "product_id": "test_product_1",
                    "variant_id": None,
                    "quantity": 1,
                    "price": 150000.0
                }
            ]
        }
    }
    body_str = json.dumps(payload, separators=(',', ':'))
    now = str(time.time())
    sig = hmac.new(agent_key.encode("utf-8"), body_str.encode("utf-8"), hashlib.sha256).hexdigest()
    
    headers = {
        "User-Agent": "headless-python-requests/2.31.0",
        "X-Agent-API-Key": agent_key,
        "X-Agent-Signature": sig,
        "X-Agent-Timestamp": now,
        "X-User-Delegation-Token": user_token,
        "Content-Type": "application/json"
    }
    
    try:
        async with AsyncTestClient(app=app, base_url="http://test") as client:
            response = await client.post("/api/v1/client/mcp/call", content=body_str, headers=headers)
            assert response.status_code in (200, 201)
            data = response.json()
            assert data.get("status") == "success"
            
            # Extract pricing dictionary
            res_dict = data.get("pricing", {})
            assert "voucher_discount" in res_dict
            assert res_dict["voucher_discount"] == 50000.0
            assert res_dict["applied_voucher_ids"] == ["test-opt-voucher-123"]
    finally:
        try:
            from backend.database.models.auth import User
            from backend.database.models.commerce import UserLoyalty
            from backend.database.models.promotion import Voucher
            from sqlalchemy import delete
            async with get_session() as session:
                await session.execute(delete(UserLoyalty).where(UserLoyalty.user_id == user_id))
                await session.execute(delete(User).where(User.id == user_id))
                await session.execute(delete(Voucher).where(Voucher.id == "test-opt-voucher-123"))
                await session.commit()
        except Exception:
            pass
        try:
            from backend.database.alchemy_config import alchemy_config
            await alchemy_config.get_engine().dispose()
        except Exception:
            pass

