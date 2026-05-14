from sqlalchemy import event
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import json
import uuid
from datetime import datetime, UTC
from backend.database.models.system import AuditLog

logger = logging.getLogger("audit-trail")

def get_model_changes(obj):
    """Trích xuất các thay đổi từ một object SQLAlchemy."""
    state = obj.__mapper__.class_manager.get_history(obj, 'state')
    changes = {}
    for attr in obj.__mapper__.all_orm_descriptors:
        if hasattr(attr, 'key'):
            history = obj.__mapper__.class_manager.get_history(obj, attr.key)
            if history.has_changes():
                changes[attr.key] = {
                    "old": history.deleted[0] if history.deleted else None,
                    "new": history.added[0] if history.added else None
                }
    return changes

async def capture_audit_events(session: AsyncSession):
    """
    Elite V2.2: Lắng nghe và ghi lại các thay đổi trong Session.
    Cơ chế: Duyệt qua session.new, session.dirty, session.deleted.
    """
    audit_entries = []
    
    # 1. New records
    for obj in session.new:
        if isinstance(obj, AuditLog): continue
        table_name = getattr(obj, "__tablename__", "unknown")
        data = {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
        audit_entries.append({
            "action": "INSERT",
            "table": table_name,
            "id": str(getattr(obj, "id", "new")),
            "changes": data
        })

    # 2. Updated records
    for obj in session.dirty:
        if isinstance(obj, AuditLog): continue
        table_name = getattr(obj, "__tablename__", "unknown")
        changes = {}
        for attr in obj.__mapper__.column_attrs:
            history = getattr(obj.__mapper__.class_manager.get_history(obj, attr.key), "deleted", None)
            if history:
                changes[attr.key] = {
                    "old": history[0],
                    "new": getattr(obj, attr.key)
                }
        if changes:
            audit_entries.append({
                "action": "UPDATE",
                "table": table_name,
                "id": str(getattr(obj, "id", "unknown")),
                "changes": changes
            })

    # 3. Deleted records
    for obj in session.deleted:
        if isinstance(obj, AuditLog): continue
        table_name = getattr(obj, "__tablename__", "unknown")
        audit_entries.append({
            "action": "DELETE",
            "table": table_name,
            "id": str(getattr(obj, "id", "unknown")),
            "changes": {"deleted": True}
        })

    return audit_entries

# Note: Trong môi trường Async, việc sử dụng sync listeners (event.listen) 
# để ghi ngược vào DB rất phức tạp. Chúng ta sẽ log ra stdout trước.
