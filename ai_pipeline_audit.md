# Báo Cáo Quét & Sửa Anti-Pattern AI Pipeline

> **Phạm vi:** Toàn bộ backend AI content generation (XOHI, SEO, FAQ, Title, Product AI)

## Tổng Kết

| File | Số hàm sửa | Anti-Pattern cũ | Chuẩn mới |
|---|---|---|---|
| `article_service.py` | 4 | Regex + `json.loads` | PydanticAI V2 `output_type` |
| `product_ai.py` | 6 | Regex + `json.loads` | PydanticAI V2 `output_type` |

**Tổng: 10 hàm AI generation** đã được nâng cấp từ legacy sang PydanticAI V2 Structured Output.

## Chi Tiết Thay Đổi

### 1. `article_service.py` — 4 methods

| Method | Trước | Sau |
|---|---|---|
| `suggest_seo` | `Agent()` → regex `\{.*\}` → `json.loads` | `Agent(output_type=SEOSuggestionResponse)` |
| `suggest_faqs` | `Agent()` → regex `\[.*\]` → `json.loads` | `Agent(output_type=FAQResponse)` |
| `suggest_excerpt` | `Agent()` (không khai báo type) | `Agent(output_type=str)` |
| `suggest_titles` | `Agent()` → regex `\{.*\}` → `json.loads` | `Agent(output_type=TitleSuggestionResponse)` |

### 2. `product_ai.py` — 6 functions (REWRITE hoàn toàn)

| Function | Trước | Sau |
|---|---|---|
| `suggest_seo_logic` | Regex `\{.*\}` → `json.loads` | `Agent(output_type=ProductSEOResponse)` |
| `suggest_faqs_logic` | Regex `\[.*\]` → `json.loads` | `Agent(output_type=ProductFAQResponse)` |
| `suggest_ingredients_logic` | Regex `\[.*\]` → `json.loads` | `Agent(output_type=IngredientListResponse)` |
| `suggest_specs_logic` | Regex `\{.*\}` → `json.loads` | `Agent(output_type=Dict[str, str])` |
| `suggest_semantic_logic` | Raw string (HTML) | `Agent(output_type=str)` (hợp lệ — output là HTML) |
| `suggest_ingredients_grouped_logic` | Regex `\[.*\]` → `json.loads` | `Agent(output_type=IngredientGroupResponse)` |

## Modules Đã Kiểm Tra & Xác Nhận OK (Không cần sửa)

| Module | Lý do OK |
|---|---|
| `creative_pen.py` | Đã dùng `Agent(output_type=ArticleOutline)` |
| `ai_inspector.py` | Đã dùng `Agent(output_type=AiReadyReport)` |
| `seo_analyzer.py` | Đã dùng `Agent(output_type=SeoReport)` |
| `neural_booster.py` | Đã dùng `Agent(output_type=NeuralBoosterReport)` |
| `neural_rewriter.py` | Đã dùng `Agent(output_type=str)` |
| `plagiarism_cop.py` | Đã dùng `Agent(output_type=PlagiarismResult)` |
| `plagiarism_refiner.py` | Đã dùng `Agent(output_type=AtomicFixResponse)` |
| `kg_generator.py` | Đã dùng `Agent(output_type=KnowledgeGraph)` |
| `content_enricher.py` | Đã dùng `Agent(output_type=EnrichAIPayload)` |
| `media_analyst.py` | Đã dùng `Agent(output_type=MediaAnalysisResult)` |
| `vision_insight.py` | Đã dùng `Agent(output_type=TopicSeed)` |
| `price_agent.py` | Đã dùng `Agent(output_type=MarketPriceIntel)` |
| `seo_contextual_linker.py` | Không có `json.loads` trên AI output |

> [!IMPORTANT]
> `article_service.py` hiện **1355 dòng** — vượt giới hạn R00 (500 dòng). Tuy nhiên theo quy tắc "Cấm đổi kiến trúc", việc tách file cần sự cho phép của sếp.

## Pydantic Models Đã Tạo

```python
# article_service.py (inline)
SEOSuggestionResponse(seo_title, seo_description, seo_keywords)
FAQItem(question, answer), FAQResponse(faqs: List[FAQItem])
TitleSuggestionResponse(seo_sge, guide_advanced, related_keywords)

# product_ai.py (module-level)
ProductSEOResponse(title, description, keywords)
FAQItem(question, answer), ProductFAQResponse(faqs: List[FAQItem])
IngredientItem(name, benefit, icon), IngredientListResponse(ingredients)
IngredientGroupItem(group, priority, items), IngredientGroupResponse(groups)
```
