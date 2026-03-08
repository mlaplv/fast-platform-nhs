from typing import List, Dict

class CapabilityRegistry:
    """
    R70: Agent Skills Matrix — Centralized Registry for AI Cognitive Capabilities.

    Các toggle này kiểm soát IntentAction — KHÔNG phải Tier routing.
    Tier routing (1/2/3) là kiến trúc xử lý nội tại, độc lập với cấu hình này.

    Mapping:
      READ           → chặn IntentAction.READ + COUNT  (truy vấn Dữ liệu / đếm)
      MUTATE         → chặn IntentAction.MUTATE        (tạo/sửa/xoá qua Final Glance R11)
      ANALYZE        → chặn IntentAction.ANALYZE       (phân tích sâu, chủ yếu Tier 3)
      CONTENT_CREATE → chặn IntentAction.CONTENT_CREATE (V62.1: Sáng tạo nội dung SEO)
    """
    
    @staticmethod
    def get_spectrum() -> List[Dict]:
        return [
            {
                "id": "READ",
                "name": "Data Extraction",
                "desc": "Chặn action READ + COUNT: truy vấn, xem và đếm dữ liệu. Được xử lý ở Tier 1/2/3.",
                "color": "text-blue-400",
                "icon": "Database"
            },
            {
                "id": "MUTATE",
                "name": "System Mutation",
                "desc": "Chặn action MUTATE: tạo, cập nhật, xoá dữ liệu qua Final Glance (R11).",
                "color": "text-amber-400",
                "icon": "Zap"
            },
            {
                "id": "ANALYZE",
                "name": "Deep Analysis",
                "desc": "Chặn action ANALYZE: phân tích sâu, báo cáo liên module, insight chiến lược (Tier 3).",
                "color": "text-purple-400",
                "icon": "Brain"
            },
            {
                "id": "CONTENT_CREATE",
                "name": "Content Factory",
                "desc": "V62.1: Sáng tạo nội dung SEO. Bao gồm viết bài, lập dàn ý, check đạo văn qua 6 cổng kiểm duyệt.",
                "color": "text-emerald-400",
                "icon": "Pencil"
            }
        ]

capability_registry = CapabilityRegistry()
