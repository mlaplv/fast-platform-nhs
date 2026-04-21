import asyncio
from backend.schemas.order import OrderDraft
from backend.services.commerce.logic.lead_extractor import ExtractedLead, LeadOrderItem
import datetime

lead = ExtractedLead(
    customer_name=None,
    customer_phone=None,
    customer_address=None,
    items=[LeadOrderItem(name="Miccosmo", quantity=1, price=0.0, id=None)],
    is_definite_purchase=True
)

try:
    draft = OrderDraft(
        session_id="test_session",
        items=[it.model_dump() for it in lead.items]
    )
    print("✅ OrderDraft success:", draft.model_dump())
except Exception as e:
    print("❌ OrderDraft failed:", e)

