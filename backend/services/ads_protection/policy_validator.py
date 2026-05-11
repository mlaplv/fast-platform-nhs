"""
Policy Validator — Google AdWords Policy Compliance Engine
Kiểm tra 15 quy tắc chính sách Google Ads trước khi submit.
Zero-dependency: chỉ dùng stdlib + regex, không gọi API ngoài.
"""
from __future__ import annotations

import re
import logging
from urllib.parse import urlparse

from backend.services.ads_protection.schemas import (
    PolicyViolation,
    PolicyCheckResult,
    ResponsiveSearchAdCreate,
    CampaignCreateRequest,
)

logger = logging.getLogger("ads_protection.policy_validator")

# ─────────────────────────────────────────────────────────────────────────────
# Danh sách từ cấm theo Google Ads Policy
# ─────────────────────────────────────────────────────────────────────────────
_FORBIDDEN_TERMS: list[str] = [
    "guaranteed", "bảo đảm 100%", "miễn phí hoàn toàn",
    "số 1 thế giới", "tốt nhất thế giới", "hàng giả", "replica",
    "thuốc tăng cân", "thuốc giảm cân nhanh", "giảm cân không cần tập",
    "cược", "cờ bạc", "casino",
]

# Trademarked terms không được bid nếu không có authorization
_TRADEMARKED_TERMS: list[str] = [
    "apple", "iphone", "samsung", "google", "nike", "adidas", "gucci",
    "louis vuitton", "chanel", "dior", "rolex", "sony", "xiaomi",
]

# Google Ads 2026: Call-only ads are deprecated
_CALL_ONLY_DEPRECATION_WARNING = "Google Ads 2026: Quảng cáo 'Chỉ gọi' (Call-only) đã bị loại bỏ. Hãy dùng Responsive Search Ads với Call Assets."

# Ký tự đặc biệt không được phép
_DISALLOWED_SPECIAL_CHARS = re.compile(r"[!@#$%^&*]{2,}|\.{3,}|\?{2,}")

# ALL CAPS (3 từ viết hoa liên tiếp)
_ALL_CAPS_PATTERN = re.compile(r"\b[A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚĂĐĨŨƠƯẠ-Ử]{3,}\b\s+\b[A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚĂĐĨŨƠƯẠ-Ử]{3,}\b")

# URL phải HTTPS
_HTTPS_PATTERN = re.compile(r"^https://")

# Date format YYYY-MM-DD
_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class PolicyValidator:
    """
    Engine kiểm tra 15 quy tắc chính sách Google Ads.
    Mỗi rule trả về list[PolicyViolation] — danh sách rỗng = pass.
    """

    TOTAL_RULES = 15

    def check_ad(self, ad: ResponsiveSearchAdCreate) -> PolicyCheckResult:
        """Kiểm tra toàn bộ policy cho một Responsive Search Ad."""
        violations: list[PolicyViolation] = []

        violations += self._check_headline_count(ad.headlines)
        violations += self._check_headline_length(ad.headlines)
        violations += self._check_headline_caps(ad.headlines)
        violations += self._check_headline_special_chars(ad.headlines)
        violations += self._check_headline_forbidden(ad.headlines)
        violations += self._check_headline_trademark(ad.headlines)
        violations += self._check_ai_max_readiness(ad)

        violations += self._check_description_count(ad.descriptions)
        violations += self._check_description_length(ad.descriptions)
        violations += self._check_description_caps(ad.descriptions)
        violations += self._check_description_forbidden(ad.descriptions)

        violations += self._check_url_https(ad.final_url)
        violations += self._check_url_format(ad.final_url)
        violations += self._check_display_path(ad.display_path1, ad.display_path2)
        violations += self._check_duplicate_headlines(ad.headlines)
        violations += self._check_headline_variety(ad.headlines)

        errors   = [v for v in violations if v.severity == "ERROR"]
        warnings = [v for v in violations if v.severity == "WARNING"]
        score = max(0.0, 100.0 - len(errors) * 15.0 - len(warnings) * 5.0)

        logger.info(
            "policy_check_ad errors=%d warnings=%d score=%.1f",
            len(errors), len(warnings), score,
        )
        return PolicyCheckResult(
            is_compliant=len(errors) == 0,
            violations=violations,
            score=round(score, 1),
            checked_rules=self.TOTAL_RULES,
        )

    def check_campaign(self, req: CampaignCreateRequest) -> PolicyCheckResult:
        """Kiểm tra policy ở cấp Campaign (ngân sách, ngày, từ khoá)."""
        violations: list[PolicyViolation] = []
        violations += self._check_budget_minimum(req.budget.daily_budget_vnd)
        violations += self._check_campaign_name(req.name)
        violations += self._check_dates(req.start_date, req.end_date)
        violations += self._check_bidding_consistency(req)

        errors = [v for v in violations if v.severity == "ERROR"]
        warnings = [v for v in violations if v.severity == "WARNING"]
        score = max(0.0, 100.0 - len(errors) * 20.0 - len(warnings) * 5.0)

        return PolicyCheckResult(
            is_compliant=len(errors) == 0,
            violations=violations,
            score=round(score, 1),
            checked_rules=4,
        )

    # ─── Rule implementations ─────────────────────────────────────────────────

    def _check_headline_count(self, headlines: list[str]) -> list[PolicyViolation]:
        if len(headlines) < 3:
            return [PolicyViolation(
                field="headlines",
                rule="HEADLINE_MIN_COUNT",
                severity="ERROR",
                message=f"Cần tối thiểu 3 headline, hiện có {len(headlines)}.",
                suggestion="Thêm ít nhất 3 headline để quảng cáo hoạt động.",
            )]
        if len(headlines) > 15:
            return [PolicyViolation(
                field="headlines",
                rule="HEADLINE_MAX_COUNT",
                severity="ERROR",
                message=f"Tối đa 15 headline, hiện có {len(headlines)}.",
                suggestion="Giữ lại 15 headline quan trọng nhất.",
            )]
        return []

    def _check_headline_length(self, headlines: list[str]) -> list[PolicyViolation]:
        violations = []
        for i, h in enumerate(headlines):
            if len(h) > 30:
                violations.append(PolicyViolation(
                    field=f"headline[{i}]",
                    rule="HEADLINE_TOO_LONG",
                    severity="ERROR",
                    message=f"'{h[:20]}...' có {len(h)} ký tự. Giới hạn: 30.",
                    suggestion=f"Rút ngắn còn tối đa 30 ký tự: '{h[:30]}'",
                ))
        return violations

    def _check_headline_caps(self, headlines: list[str]) -> list[PolicyViolation]:
        violations = []
        for i, h in enumerate(headlines):
            if _ALL_CAPS_PATTERN.search(h):
                violations.append(PolicyViolation(
                    field=f"headline[{i}]",
                    rule="EXCESSIVE_CAPITALIZATION",
                    severity="ERROR",
                    message=f"Headline '{h}' dùng quá nhiều chữ hoa liên tiếp.",
                    suggestion="Chỉ viết hoa chữ cái đầu mỗi từ quan trọng.",
                ))
        return violations

    def _check_headline_special_chars(self, headlines: list[str]) -> list[PolicyViolation]:
        violations = []
        for i, h in enumerate(headlines):
            if _DISALLOWED_SPECIAL_CHARS.search(h):
                violations.append(PolicyViolation(
                    field=f"headline[{i}]",
                    rule="DISALLOWED_SPECIAL_CHARS",
                    severity="ERROR",
                    message=f"Headline chứa ký tự đặc biệt lặp lại: '{h}'",
                    suggestion="Loại bỏ các ký tự '!!!', '...', '???' liên tiếp.",
                ))
        return violations

    def _check_headline_forbidden(self, headlines: list[str]) -> list[PolicyViolation]:
        violations = []
        for i, h in enumerate(headlines):
            for term in _FORBIDDEN_TERMS:
                if term.lower() in h.lower():
                    violations.append(PolicyViolation(
                        field=f"headline[{i}]",
                        rule="FORBIDDEN_TERM",
                        severity="ERROR",
                        message=f"Headline chứa từ bị cấm: '{term}'",
                        suggestion=f"Loại bỏ hoặc thay thế từ '{term}' bằng từ ngữ tuân thủ chính sách.",
                    ))
        return violations

    def _check_headline_trademark(self, headlines: list[str]) -> list[PolicyViolation]:
        violations = []
        for i, h in enumerate(headlines):
            for tm in _TRADEMARKED_TERMS:
                if re.search(rf"\b{re.escape(tm)}\b", h.lower()):
                    violations.append(PolicyViolation(
                        field=f"headline[{i}]",
                        rule="TRADEMARKED_TERM",
                        severity="WARNING",
                        message=f"Headline chứa thương hiệu đã đăng ký: '{tm}'",
                        suggestion=f"Cần có authorization từ thương hiệu '{tm}' để sử dụng trong quảng cáo.",
                    ))
        return violations

    def _check_description_count(self, descs: list[str]) -> list[PolicyViolation]:
        if len(descs) < 2:
            return [PolicyViolation(
                field="descriptions",
                rule="DESCRIPTION_MIN_COUNT",
                severity="ERROR",
                message=f"Cần tối thiểu 2 description, hiện có {len(descs)}.",
                suggestion="Thêm ít nhất 2 description.",
            )]
        return []

    def _check_description_length(self, descs: list[str]) -> list[PolicyViolation]:
        violations = []
        for i, d in enumerate(descs):
            if len(d) > 90:
                violations.append(PolicyViolation(
                    field=f"description[{i}]",
                    rule="DESCRIPTION_TOO_LONG",
                    severity="ERROR",
                    message=f"Description có {len(d)} ký tự. Giới hạn: 90.",
                    suggestion=f"Rút ngắn còn tối đa 90 ký tự: '{d[:90]}'",
                ))
        return violations

    def _check_description_caps(self, descs: list[str]) -> list[PolicyViolation]:
        violations = []
        for i, d in enumerate(descs):
            if _ALL_CAPS_PATTERN.search(d):
                violations.append(PolicyViolation(
                    field=f"description[{i}]",
                    rule="EXCESSIVE_CAPITALIZATION",
                    severity="ERROR",
                    message=f"Description dùng quá nhiều chữ hoa.",
                    suggestion="Sử dụng viết hoa chữ cái đầu câu thay vì toàn bộ chữ hoa.",
                ))
        return violations

    def _check_description_forbidden(self, descs: list[str]) -> list[PolicyViolation]:
        violations = []
        for i, d in enumerate(descs):
            for term in _FORBIDDEN_TERMS:
                if term.lower() in d.lower():
                    violations.append(PolicyViolation(
                        field=f"description[{i}]",
                        rule="FORBIDDEN_TERM",
                        severity="ERROR",
                        message=f"Description chứa từ bị cấm: '{term}'",
                        suggestion=f"Thay thế '{term}' bằng từ ngữ tuân thủ chính sách Google.",
                    ))
        return violations

    def _check_url_https(self, url: str) -> list[PolicyViolation]:
        if not _HTTPS_PATTERN.match(url):
            return [PolicyViolation(
                field="final_url",
                rule="URL_NOT_HTTPS",
                severity="ERROR",
                message="Final URL phải dùng HTTPS.",
                suggestion=f"Đổi thành: {url.replace('http://', 'https://')}",
            )]
        return []

    def _check_url_format(self, url: str) -> list[PolicyViolation]:
        try:
            parsed = urlparse(url)
            if not parsed.netloc:
                raise ValueError("invalid domain")
        except Exception:
            return [PolicyViolation(
                field="final_url",
                rule="URL_INVALID_FORMAT",
                severity="ERROR",
                message=f"URL không hợp lệ: '{url}'",
                suggestion="Nhập URL đầy đủ, ví dụ: https://osmo.vn/san-pham",
            )]
        return []

    def _check_display_path(
        self, path1: str | None, path2: str | None
    ) -> list[PolicyViolation]:
        violations = []
        for i, p in enumerate([path1, path2], 1):
            if p and len(p) > 15:
                violations.append(PolicyViolation(
                    field=f"display_path{i}",
                    rule="DISPLAY_PATH_TOO_LONG",
                    severity="ERROR",
                    message=f"Display path {i} có {len(p)} ký tự. Giới hạn: 15.",
                    suggestion=f"Rút ngắn: '{p[:15]}'",
                ))
        return violations

    def _check_duplicate_headlines(self, headlines: list[str]) -> list[PolicyViolation]:
        seen: set[str] = set()
        duplicates: list[str] = []
        for h in headlines:
            h_lower = h.lower().strip()
            if h_lower in seen:
                duplicates.append(h)
            seen.add(h_lower)
        if duplicates:
            return [PolicyViolation(
                field="headlines",
                rule="DUPLICATE_HEADLINES",
                severity="WARNING",
                message=f"Có {len(duplicates)} headline bị trùng lặp.",
                suggestion="Mỗi headline phải có nội dung duy nhất để tối đa hiệu quả.",
            )]
        return []

    def _check_headline_variety(self, headlines: list[str]) -> list[PolicyViolation]:
        """Khuyến cáo nếu ít hơn 5 headline (Google recommend 8-15)."""
        if len(headlines) < 5:
            return [PolicyViolation(
                field="headlines",
                rule="LOW_HEADLINE_COUNT",
                severity="WARNING",
                message=f"Chỉ có {len(headlines)} headline. Google khuyến nghị 8-15.",
                suggestion="Thêm nhiều headline để hệ thống máy học tối ưu hiệu quả hiển thị.",
            )]
        return []

    def _check_budget_minimum(self, daily_vnd: float) -> list[PolicyViolation]:
        if daily_vnd < 50_000:
            return [PolicyViolation(
                field="budget.daily_budget_vnd",
                rule="BUDGET_TOO_LOW",
                severity="WARNING",
                message=f"Ngân sách ngày {daily_vnd:,.0f}₫ quá thấp có thể không có impression.",
                suggestion="Khuyến nghị tối thiểu 50,000₫/ngày để đảm bảo tiếp cận.",
            )]
        return []

    def _check_campaign_name(self, name: str) -> list[PolicyViolation]:
        if len(name) < 3:
            return [PolicyViolation(
                field="name",
                rule="CAMPAIGN_NAME_TOO_SHORT",
                severity="ERROR",
                message="Tên campaign quá ngắn (tối thiểu 3 ký tự).",
                suggestion="Đặt tên mô tả rõ ràng, ví dụ: 'Serum Trắng Da - Brand Search'",
            )]
        return []

    def _check_dates(self, start: str, end: str | None) -> list[PolicyViolation]:
        violations = []
        if not _DATE_PATTERN.match(start):
            violations.append(PolicyViolation(
                field="start_date",
                rule="INVALID_DATE_FORMAT",
                severity="ERROR",
                message=f"Ngày bắt đầu '{start}' không đúng định dạng YYYY-MM-DD.",
                suggestion="Sử dụng định dạng: 2026-01-15",
            ))
        if end and not _DATE_PATTERN.match(end):
            violations.append(PolicyViolation(
                field="end_date",
                rule="INVALID_DATE_FORMAT",
                severity="ERROR",
                message=f"Ngày kết thúc '{end}' không đúng định dạng YYYY-MM-DD.",
                suggestion="Sử dụng định dạng: 2026-12-31",
            ))
        return violations

    def _check_bidding_consistency(self, req: CampaignCreateRequest) -> list[PolicyViolation]:
        violations = []
        if req.bidding_strategy == "TARGET_CPA" and not req.target_cpa_vnd:
            violations.append(PolicyViolation(
                field="target_cpa_vnd",
                rule="MISSING_TARGET_CPA",
                severity="ERROR",
                message="Chiến lược TARGET_CPA yêu cầu nhập giá trị target_cpa_vnd.",
                suggestion="Nhập CPA mục tiêu (VNĐ), ví dụ: 50000",
            ))
        if req.bidding_strategy == "TARGET_ROAS" and not req.target_roas:
            violations.append(PolicyViolation(
                field="target_roas",
                rule="MISSING_TARGET_ROAS",
                severity="ERROR",
                message="Chiến lược TARGET_ROAS yêu cầu nhập giá trị target_roas.",
                suggestion="Nhập ROAS mục tiêu, ví dụ: 3.5 (350%)",
            ))
        return violations

    def _check_ai_max_readiness(self, ad: ResponsiveSearchAdCreate) -> list[PolicyViolation]:
        """Google Ads 2026: AI Max yêu cầu mật độ tài sản cao."""
        violations = []
        if len(ad.headlines) < 8:
            violations.append(PolicyViolation(
                field="headlines",
                rule="AI_MAX_LOW_ASSETS",
                severity="WARNING",
                message="Chế độ AI Max 2026 yêu cầu tối thiểu 8 headlines để tối ưu hóa AI Overviews.",
                suggestion="Thêm ít nhất 8 headlines để Xohi AI có đủ dữ liệu học máy.",
            ))
        if len(ad.descriptions) < 4:
            violations.append(PolicyViolation(
                field="descriptions",
                rule="AI_MAX_LOW_ASSETS",
                severity="WARNING",
                message="AI Max yêu cầu tối thiểu 4 descriptions.",
                suggestion="Bổ sung đủ 4 descriptions để đạt điểm tối ưu 'Excellent'.",
            ))
        return violations
