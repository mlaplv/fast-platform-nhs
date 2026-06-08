import re
import logging
from typing import List, Dict, Any
from backend.services.ads_protection.ai_strategist import ai_strategist

logger = logging.getLogger("policy-shield")

# Regulated Vietnamese keywords categorized by risk
SENSITIVE_CATEGORIES = {
    "body_parts": {
        "label": "Bộ phận cơ thể nhạy cảm / Nhãn quan hạn chế",
        "patterns": [
            r"\bnhũ\s+hoa\b", r"\bngực\b", r"\bvú\b", r"\bbẹn\b", r"\bmông\b", 
            r"\bbikini\b", r"\bnách\b", r"\bâm\s+đạo\b", r"\bdương\s+vật\b", 
            r"\bsinh\s+dục\b", r"\bbao\s+quy\s+đầu\b"
        ],
        "suggestion": "Tránh dùng trực tiếp tên các bộ phận cơ thể nhạy cảm. Nên dùng cách diễn đạt giảm nhẹ hoặc tập trung vào công dụng chăm sóc da/làm sáng da toàn thân."
    },
    "medical_claims": {
        "label": "Tuyên bố y tế / Cam kết chữa trị",
        "patterns": [
            r"\bthuốc\b", r"\bđiều\s+trị\b", r"\bđặc\s+trị\b", r"\btrị\s+dứt\s+điểm\b", 
            r"\bchữa\s+khỏi\b", r"\bchữa\s+trị\b", r"\bkhỏi\s+hẳn\b"
        ],
        "suggestion": "Google Ads cấm quảng cáo mỹ phẩm/thực phẩm chức năng dưới dạng thuốc chữa bệnh. Thay thế các từ 'thuốc', 'điều trị', 'đặc trị' bằng các từ 'kem dưỡng', 'cải thiện', 'chăm sóc'."
    },
    "overpromising": {
        "label": "Cam kết hiệu quả thái quá",
        "patterns": [
            r"\bhiệu\s+quả\s+100%\b", r"\bhoàn\s+tiền\s+100%\b", r"\bcam\s+kết\s+hiệu\s+quả\b", 
            r"\bcam\s+kết\s+100%\b", r"\btốt\s+nhất\b", r"\bsố\s+1\b", r"\btuyệt\s+đối\b"
        ],
        "suggestion": "AI kiểm duyệt của Google thường gắn cờ các tuyên bố cam kết tuyệt đối. Hãy dùng 'hiệu quả nhanh', 'được kiểm nghiệm', hoặc tập trung vào trải nghiệm khách hàng."
    },
    "medical_ingredients": {
        "label": "Hoạt chất y tế / Dược phẩm hạn chế",
        "patterns": [
            r"\bhydroquinone\b", r"\btretinoin\b", r"\bcorticoid\b", r"\bclindamycin\b", 
            r"\bminoxidil\b", r"\bsalicylic\s+acid\b", r"\btranexamic\s+acid\b", 
            r"\bthuốc\s+rượu\b", r"\bthuốc\s+bắc\s+tái\s+tạo\b", r"\bkem\s+trộn\b"
        ],
        "suggestion": "Google Ads cấm hoặc hạn chế nghiêm ngặt các hoạt chất y tế kê đơn và sản phẩm lột tẩy da tự chế. Nên thay thế bằng các thành phần lành tính hơn như Niacinamide, Vitamin C, Arbutin."
    }
}

def normalize_text_for_policy(text: str) -> str:
    # Clean inner-word punctuation like "tr.ị" -> "trị"
    cleaned = re.sub(r'(?<=[\w])[\.\-_;\*\/]+(?=[\w])', '', text)
    return cleaned.lower()

class AIPolicyShield:
    async def validate(self, headlines: List[str], descriptions: List[str], keywords: List[str], landing_page_url: str) -> Dict[str, Any]:
        """
        Runs real-time policy checks:
        1. Sensitive Term Detection (headlines, descriptions, keywords)
        2. Cross-matching (checking if keywords/ads align with landing page content)
        3. Low Search Volume Risk Check
        """
        logger.info("Running AI Policy Shield validation for url=%s", landing_page_url)
        
        # Initialize results structure
        results = {
            "success": True,
            "sensitive_warnings": [],
            "landing_page_warnings": [],
            "low_volume_warnings": [],
            "status": "SAFE"
        }

        # 1. Fetch Landing Page content for cross-matching
        landing_text = ""
        if landing_page_url:
            try:
                raw_report = await ai_strategist._fetch_page(landing_page_url)
                # Extract text between preview markers if present
                if "=== LANDING PAGE CONTENT PREVIEW ===" in raw_report:
                    parts = raw_report.split("=== LANDING PAGE CONTENT PREVIEW ===")
                    if len(parts) > 1:
                        landing_text = parts[1].split("=====================================")[0].strip().lower()
                else:
                    landing_text = raw_report.lower()
            except Exception as e:
                logger.error("Failed to fetch landing page in policy shield: %s", e)

        # Helper to check terms
        def scan_text(text: str, source: str):
            text_normalized = normalize_text_for_policy(text)
            for cat_key, cat_info in SENSITIVE_CATEGORIES.items():
                for pattern in cat_info["patterns"]:
                    if re.search(pattern, text_normalized):
                        match_word = re.search(pattern, text_normalized).group(0)
                        results["sensitive_warnings"].append({
                            "category": cat_info["label"],
                            "matched_term": match_word,
                            "source": source,
                            "context": text,
                            "suggestion": cat_info["suggestion"]
                        })

        # Scan all ad copy & keywords for sensitive terms
        for h in headlines:
            scan_text(h, "Tiêu đề (Headline)")
        for d in descriptions:
            scan_text(d, "Mô tả (Description)")
        for kw in keywords:
            scan_text(kw, "Từ khóa (Keyword)")

        # 2. Cross-matching with landing page content
        # Check if landing page claims to be a cosmetic/cream, but ad claims it is a medical "treatment" or "drug"
        is_cosmetic_landing = any(x in landing_text for x in ["mỹ phẩm", "kem dưỡng", "lành tính", "serum", "gel"])
        
        for kw in keywords:
            kw_lower = kw.lower().strip()
            # If landing page is resolved and doesn't contain the keyword at all
            if landing_text and len(landing_text) > 200:
                # Basic exact/partial text match check
                if kw_lower not in landing_text:
                    # Clean punctuation
                    kw_clean = re.sub(r'[^\w\s]', '', kw_lower)
                    # If clean keyword still not in text, raise caution
                    if kw_clean not in landing_text:
                        results["landing_page_warnings"].append({
                            "type": "MISMATCH_MISSING",
                            "keyword": kw,
                            "message": f"Từ khóa '{kw}' không xuất hiện trên nội dung trang đích. AI của Google Ads có thể đánh giá quảng cáo không khớp nội dung.",
                            "suggestion": "Hãy bổ sung từ khóa này vào thẻ H1/H2 hoặc nội dung bài viết chính của Landing Page để tối ưu điểm chất lượng."
                        })

            # Specific "Drug vs Cosmetic" concept mismatch
            if is_cosmetic_landing:
                if any(x in kw_lower for x in ["thuốc", "đặc trị", "điều trị"]):
                    results["landing_page_warnings"].append({
                        "type": "MISMATCH_CONCEPT",
                        "keyword": kw,
                        "message": f"Trang đích hướng tới 'mỹ phẩm dưỡng da' nhưng từ khóa chứa từ trị liệu y tế '{kw}'. Nguy cơ AI đánh giá đánh tráo khái niệm.",
                        "suggestion": "Chuyển từ khóa từ '{kw}' sang dạng cụm từ nhẹ nhàng hơn như chăm sóc, phục hồi dưỡng sáng."
                    })

        # 3. Low Search Volume Risk
        # Keywords with very long length (e.g. > 5 words) or excessive exact matching brackets that restrict searches too much
        for kw in keywords:
            kw_clean = re.sub(r'[^\w\s]', '', kw.lower().strip())
            words_count = len(kw_clean.split())
            if words_count > 6:
                results["low_volume_warnings"].append({
                    "keyword": kw,
                    "message": f"Từ khóa quá dài ({words_count} từ). Có nguy cơ cao bị xếp vào nhóm 'Lượng tìm kiếm thấp' của Google Ads.",
                    "suggestion": "Hãy cân nhắc rút ngắn từ khóa hoặc chuyển sang loại đối sánh cụm từ (Phrase Match) để tăng lượng hiển thị."
                })

        # Update final state status
        if results["sensitive_warnings"]:
            results["status"] = "RISKY"
        elif results["landing_page_warnings"]:
            results["status"] = "WARNING"
        else:
            results["status"] = "SAFE"

        return results

policy_shield: AIPolicyShield = AIPolicyShield()
