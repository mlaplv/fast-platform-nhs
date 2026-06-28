# Kế hoạch Triển khai Chi tiết: Kiến trúc 7 Bản mẫu & Lựa chọn Ngẫu nhiên theo Nhóm Tiêu Đề (XOHI Dynamic Templates V4.0)

## 1. Mô tả thay đổi

### A. Frontend Layer (Quản trị giao diện - NewsForm.svelte)
- Thêm biến trạng thái `selectedTitleGroup` để ghi nhận nguồn gốc nhóm tiêu đề (`seo_sge`, `guide_advanced`, `related_keywords`, `custom`).
- Cập nhật hàm `selectSuggestedTitle` để lưu trữ thông tin nhóm tiêu đề khi quản trị viên click chọn.
- Lắng nghe sự kiện `oninput` trên trường nhập liệu Tiêu đề để tự động chuyển về trạng thái `custom` nếu người dùng chỉnh sửa.
- Tích hợp logic chọn ngẫu nhiên có định hướng (weighted dynamic choice) trong `handleAiSuggestContent` dựa trên `selectedTitleGroup`, đính kèm tham số `template` gửi lên Backend.

### B. Controller Layer (backend/controllers/article.py)
- Cập nhật hàm `suggest_content` để tiếp nhận tham số `template` từ request body và truyền tiếp vào tầng nghiệp vụ `ArticleService`.

### C. Backend Service Layer (backend/services/article_service.py)
- Khai báo 7 cấu trúc bản mẫu tương ứng với yêu cầu về định dạng của Google Search SGE/GEO 2026.
- Cập nhật phương thức `suggest_content` để nhận tham số `template`, lấy prompt bản mẫu tương ứng ghép vào `base_prompt` trước khi chạy Agent.

---

## 2. Chi tiết các thay đổi trong mã nguồn (Proposed Diff)

### 2.1. Thay đổi tại `frontend/src/lib/components/admin/management/NewsForm.svelte`

```diff
// Định nghĩa các biến trạng thái theo dõi nhóm tiêu đề
+  let selectedTitleGroup = $state<'seo_sge' | 'guide_advanced' | 'related_keywords' | 'custom' | null>(null);

// Cập nhật hàm chọn tiêu đề gợi ý để ghi nhận nhóm
-  function selectSuggestedTitle(title: string) {
+  function selectSuggestedTitle(title: string, group: 'seo_sge' | 'guide_advanced' | 'related_keywords' | 'custom' | null = null) {
     formTitle = title;
+    selectedTitleGroup = group;
     if (!editingId) formSlug = generateSlug(title);
     showTitleSuggestions = false;
     suggestedTitlesGrouped = { seo_sge: [], guide_advanced: [], related_keywords: [] };
     nanobot.showToast("Đã chọn tiêu đề.", "success");
   }

// Cập nhật sự kiện nhập liệu của ô nhập tiêu đề
             <input
               type="text"
               bind:value={formTitle}
               oninput={(e) => { 
                 const val = e.currentTarget.value;
+                selectedTitleGroup = 'custom';
                 if (!editingId && val) formSlug = generateSlug(val); 
               }}
               placeholder="Nhập tiêu đề Bài viết..."
               class="field-input text-xl font-bold"
             />

// Cập nhật sự kiện click của các nút tiêu đề gợi ý theo nhóm
                 <!-- Nhóm 1: SEO & SGE -->
                 {#each suggestedTitlesGrouped.seo_sge as title, i}
                   <button
-                    onclick={() => selectSuggestedTitle(title)}
+                    onclick={() => selectSuggestedTitle(title, 'seo_sge')}
                   >
                 {#each suggestedTitlesGrouped.guide_advanced as title, i}
                   <button
-                    onclick={() => selectSuggestedTitle(title)}
+                    onclick={() => selectSuggestedTitle(title, 'guide_advanced')}
                   >
                 {#each suggestedTitlesGrouped.related_keywords as title, i}
                   <button
-                    onclick={() => selectSuggestedTitle(title)}
+                    onclick={() => selectSuggestedTitle(title, 'related_keywords')}
                   >

// Cập nhật hàm gọi API sinh nội dung
   async function handleAiSuggestContent() {
     if (!formTitle) {
       nanobot.showToast("Vui lòng nhập tiêu đề bài viết trước.", "warning");
       return;
     }
     isSuggestingContent = true;
     try {
+      let chosenTemplate = 'sge_definition';
+      if (selectedTitleGroup === 'seo_sge') {
+        const templates = ['sge_definition', 'info_case_study', 'faq_hub'];
+        chosenTemplate = templates[Math.floor(Math.random() * templates.length)];
+      } else if (selectedTitleGroup === 'guide_advanced') {
+        const templates = ['step_by_step', 'versus_paradigm'];
+        chosenTemplate = templates[Math.floor(Math.random() * templates.length)];
+      } else if (selectedTitleGroup === 'related_keywords') {
+        const templates = ['consensus_list', 'expert_consensus'];
+        chosenTemplate = templates[Math.floor(Math.random() * templates.length)];
+      } else {
+        const templates = ['sge_definition', 'step_by_step', 'consensus_list', 'info_case_study', 'versus_paradigm', 'expert_consensus', 'faq_hub'];
+        chosenTemplate = templates[Math.floor(Math.random() * templates.length)];
+      }
+
+      const templateNames: Record<string, string> = {
+        'sge_definition': 'Khối Định nghĩa SGE',
+        'step_by_step': 'Quy trình RAG từng bước',
+        'consensus_list': 'Danh sách Đồng thuận',
+        'info_case_study': 'Case Study Tăng trưởng Thông tin',
+        'versus_paradigm': 'Đối chiếu Song song',
+        'expert_consensus': 'Ý kiến Chuyên gia Đồng thuận',
+        'faq_hub': 'Trung tâm FAQ Chuyên sâu'
+      };
+      nanobot.showToast(`XOHI đang dùng bản mẫu: ${templateNames[chosenTemplate] || chosenTemplate}`, "info");

       const res = await apiClient.post<{ data: string }>('/api/v1/articles/content-suggest', {
         title: formTitle,
         category: formCategory || '',
         excerpt: formExcerpt || '',
         product_id: formRelatedProductId || '',
+        template: chosenTemplate
       });
```

---

### 2.2. Thay đổi tại `backend/controllers/article.py`

```diff
     @post("/content-suggest", guards=[PermissionGuard(PermissionEnum.CONTENT_WRITE)], status_code=201)
     async def suggest_content(
         self,
         article_service: ArticleService,
         data: Dict[str, str],
     ) -> Dict[str, object]:
         """GEO 2026: XOHI Auto Content Generator — sinh HTML bài viết hoàn chỉnh."""
         title = data.get("title", "")
         category = data.get("category", "")
         excerpt = data.get("excerpt", "")
         product_id = data.get("product_id", "")
-        content = await article_service.suggest_content(None, title, category, excerpt, product_id)
+        template = data.get("template", "")
+        content = await article_service.suggest_content(None, title, category, excerpt, product_id, template)
         return {"data": content}
```

---

### 2.3. Thay đổi tại `backend/services/article_service.py`

```diff
-    async def suggest_content(self, db_session: Optional[AsyncSession], title: str, category: str, excerpt: str, product_id: str = "") -> str:
+    async def suggest_content(self, db_session: Optional[AsyncSession], title: str, category: str, excerpt: str, product_id: str = "", template: str = "") -> str:
         """GEO 2026: XOHI Auto Content Generator — sinh HTML bài viết hoàn chỉnh EEAT."""
         from pydantic_ai import Agent
         from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
 
         base_prompt = (
             "Bạn là nhà báo/chuyên gia nội dung EEAT tiêu chuẩn 2026.\n"
             "Nếu có thông tin sản phẩm liên kết dưới đây, bạn BẮT BUỘC phải lồng ghép sản phẩm liên quan này vào bài viết một cách tự nhiên, chuyên nghiệp và có sức thuyết phục cao. Giải thích rõ tại sao sản phẩm này là giải pháp tốt cho vấn đề được thảo luận trong bài viết.\n"
             "QUY TẮC TỐI CAO: Dù tiêu đề hoặc tóm tắt đầu vào là tiếng Anh, bạn BẮT BUỘC phải viết bài hoàn toàn bằng tiếng Việt thuần 100%.\n"
             "Viết bài viết HTML hoàn chỉnh bằng tiếng Việt dựa trên tiêu đề, chuyên mục, tóm tắt và sản phẩm liên kết được cung cấp.\n"
             "Yêu cầu cấu trúc:\n"
             "- Dùng <h2> cho các luận điểm chính (chứa từ khóa), <h3> cho luận điểm phụ.\n"
             "- Dùng <p>, <ul>, <li>, <strong> để làm phong phú nội dung.\n"
             "- Viết tối thiểu 600 từ, chia đều thành 3-5 phần logic.\n"
             "- TUYỆT ĐỐI không dùng Markdown. Không JSON. Chỉ HTML thuần.\n"
             "- Không có <!DOCTYPE>, <html>, <head>, <body> — chỉ nội dung bài viết.\n"
             "- TUYỆT ĐỐI không tự ý sinh hoặc chèn các thẻ liên kết <a>, đường dẫn (URL), hoặc bất kỳ liên kết ngoài/nội bộ nào trong nội dung bài viết. Tất cả nội dung văn bản phải ở dạng thuần túy không chứa thẻ liên kết."
         )
+
+        templates_prompts = {
+            "sge_definition": (
+                "Yêu cầu cấu trúc bổ sung (Bản mẫu 1: Khối Định nghĩa SGE):\n"
+                "- Mở đầu bài viết bằng một định nghĩa cực kỳ súc tích, trực diện về thuật ngữ/khái niệm chủ chốt.\n"
+                "- Ngay sau tiêu đề H2 đầu tiên, bạn BẮT BUỘC phải chèn một khối trích dẫn <blockquote> chứa định nghĩa in đậm (sử dụng <strong>) dài 1-2 câu làm khối định nghĩa chính để AI Overviews có thể trích xuất.\n"
+                "- Các phần tiếp theo đi vào phân tích chi tiết cơ chế tác dụng ở cấp độ tế bào và ứng dụng thực tế."
+            ),
+            "step_by_step": (
+                "Yêu cầu cấu trúc bổ sung (Bản mẫu 2: Quy trình RAG từng bước):\n"
+                "- Trình bày nội dung dưới dạng một hướng dẫn/quy trình từng bước (Step-by-step tutorial/workflow) có hệ thống.\n"
+                "- Mỗi bước hành động phải được đánh số thứ tự rõ ràng (ví dụ: Bước 1, Bước 2...) kết hợp với tiêu đề phụ H3 và phần giải thích ngắn gọn, đi thẳng vào cách thực hiện."
+            ),
+            "consensus_list": (
+                "Yêu cầu cấu trúc bổ sung (Bản mẫu 3: Danh sách Đồng thuận):\n"
+                "- Trình bày bài viết theo dạng danh sách tổng hợp, đánh giá hoặc tuyển chọn các sản phẩm/thành phần hàng đầu.\n"
+                "- Sử dụng bảng HTML (<table>, <tr>, <th>, <td>) để so sánh các thuộc tính một cách rõ ràng giữa các sự lựa chọn.\n"
+                "- Nêu bật ưu điểm và nhược điểm thực tế của từng giải pháp."
+            ),
+            "info_case_study": (
+                "Yêu cầu cấu trúc bổ sung (Bản mẫu 4: Case Study Tăng trưởng Thông tin):\n"
+                "- Cấu trúc bài viết xoay quanh một câu chuyện trải nghiệm thực tế (storytelling) của khách hàng hoặc nghiên cứu tình huống cụ thể.\n"
+                "- Mô tả chi tiết vấn đề ban đầu, quá trình áp dụng giải pháp và kết quả định lượng cụ thể bằng các con số thực tế.\n"
+                "- Đưa vào các thông tin độc nhất mang tính thực tiễn cao (Information Gain) nhằm tăng độ tin cậy."
+            ),
+            "versus_paradigm": (
+                "Yêu cầu cấu trúc bổ sung (Bản mẫu 5: Đối chiếu Song song):\n"
+                "- Viết bài dưới dạng so sánh đối chiếu trực tiếp giữa hai sản phẩm, hai hoạt chất hoặc hai phương pháp phổ biến (A vs B).\n"
+                "- Xây dựng bảng so sánh HTML chi tiết về công dụng, tính an toàn và giá cả.\n"
+                "- Đưa ra kết luận cụ thể đối tượng người dùng nào nên ưu tiên chọn phương án nào."
+            ),
+            "expert_consensus": (
+                "Yêu cầu cấu trúc bổ sung (Bản mẫu 6: Ý kiến Chuyên gia Đồng thuận):\n"
+                "- Phân tích xu hướng thị trường và tổng hợp nhận định, đánh giá của các chuyên gia hoặc bác sĩ uy tín trong ngành.\n"
+                "- Sử dụng các trích dẫn ngắn (nằm trong thẻ <blockquote> hoặc định dạng nổi bật) để minh họa cho ý kiến đồng thuận.\n"
+                "- Đưa ra dự báo hoặc khuyến nghị đáng tin cậy về tương lai."
+            ),
+            "faq_hub": (
+                "Yêu cầu cấu trúc bổ sung (Bản mẫu 7: Trung tâm FAQ Chuyên sâu):\n"
+                "- Cấu trúc bài viết hoàn toàn dưới dạng các câu hỏi thường gặp và câu trả lời chi tiết.\n"
+                "- Mỗi tiêu đề phụ H3 bắt buộc phải viết ở dạng câu hỏi tự nhiên thường được người dùng tìm kiếm.\n"
+                "- Câu trả lời tương ứng phải súc tích, đầy đủ và đi thẳng vào trọng tâm câu hỏi."
+            )
+        }
+
+        template_prompt = templates_prompts.get(template, "")
+        if template_prompt:
+            base_prompt = f"{base_prompt}\n\n{template_prompt}"
+
         sge_cfg = await _get_sge_config_async()
         system_prompt = build_entropy_system_prompt(
             base_prompt,
```

---

## 4. Kế hoạch xác minh (Verification Plan)

- **Xác minh giao diện & Payload gửi lên:**
  - Bấm sinh gợi ý tiêu đề, chọn tiêu đề từ Nhóm 1. Xác thực tham số `template` thuộc Nhóm 1 được đính kèm chính xác trong cuộc gọi API sinh bài viết.
  - Sửa tiêu đề thủ công, bấm sinh bài viết. Xác thực tham số `template` được chọn ngẫu nhiên trong toàn bộ 7 mẫu.
- **Xác minh chất lượng AI Output:**
  - Kiểm tra nội dung bài viết HTML sinh ra trên giao diện để đảm bảo tuân thủ đúng định dạng thẻ của bản mẫu được chỉ định (ví dụ: có bảng HTML đối với bản mẫu So sánh/Danh sách, hoặc có khối blockquote đối với bản mẫu Định nghĩa).
