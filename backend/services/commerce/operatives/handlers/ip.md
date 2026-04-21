# HELEN INTELLIGENT PIPELINE (IP) - ARCHITECT'S BLUEPRINT (MICSMO ELITE V2.6)

> **CHỈ THỊ TỐI CAO:** Helen là một **Autonomous Sales Engine** — chuyên gia tư vấn mỹ phẩm cao cấp và chăm sóc da chuyên sâu cho toàn sàn **Micsmo.com**. Hệ thống được thiết kế để chốt đơn thần tốc, tối ưu hóa RAM (2-4GB) và duy trì tỷ lệ chuyển đổi (CR) cao nhất thông qua Specialist Pipeline + 6 DB Tools.

---

## 🏗️ SƠ ĐỒ KIẾN TRÚC TỔNG THỂ (SYSTEM ARCHITECTURE)

```mermaid
graph TD
    User([User Message]) --> Frontend[Svelte 5 Runes / SSE Listener]
    Frontend --> L0_Fast[L0: Fast Intent - Classifier < 200ms]
    
    L0_Fast -- Greeting/Quick Response --> Done([DONE])
    L0_Fast -- Complex Query --> L05_Sync[L0.5: Heuristic Sync - < 100ms]
    
    L05_Sync -- Price/Ship/Address/Hotline/Quick Ack --> Done
    L05_Sync -- Deep Analysis Needed --> L1_Brain[L1: Deep Brain - Background Task]
    
    subgraph Specialist_Pipeline [L1: Specialist Pipeline]
        Router[SupportRouter - Orchestrator] --> Guard[Zone 0: Guardrail]
        Guard --> Order[Zone 3: Order Closer - SALE FIRST]
        Order --> Greet[Zone 1: Greeting - Smart Hook]
        Greet --> Cons[Zone 2: Consultant - RAG + 6 DB Tools]
    end
    
    L1_Brain --> Router
    Order -- "Missing Info" --> AskInfo[Hỏi SĐT/Địa chỉ/Số lượng]
    Order -- "Full Data" --> DB[(SQLAlchemy 2.0 / Order Creation)]
    
    Cons -- "search_products_tool" --> ProductDB[(ProductBase)]
    Cons -- "get_active_promotions_tool" --> VoucherDB[(Voucher + ComboDeal)]
    Cons -- "search_articles_tool" --> ArticleDB[(Article / News)]
    
    Trinity[TrinityBridge - AI Orchestrator] <--> L0_Fast
    Trinity <--> Specialist_Pipeline
    
    AskInfo --> Pulse[Neural Pulse - SSE Update]
    DB --> Pulse
    Pulse --> Frontend
```

---

## ⚡ 3-LAYER EXECUTION MODEL

### 🔹 Layer 0: Neural Reflex (Classifier)
- **Cơ chế:** Fast-Path LLM (Gemini Flash).
- **Nhiệm vụ:** Phân loại ý định ngay lập tức. Nếu là chào hỏi xã giao, phản hồi ngay.
- **Latency:** < 200ms.

### 🔹 Layer 0.5: Heuristic Sync (Phản xạ tức thì)
- **Cơ chế:** Synchronous Keyword Matching + Context Awareness (Bypass LLM).
- **Nhiệm vụ:** Trả lời: **Giá**, **Phí ship**, **Địa chỉ**, **Hotline**, **Thành phần**.
- **Điểm đặc biệt:** Lấy giá thực tế từ `ProductBase` trong DB.
- **Latency:** < 100ms.

### 🔹 Layer 1: Deep Brain (Specialist Pipeline)
- **Cơ chế:** Background Task + `SupportRouter` điều phối Specialist Handlers.
- **Nhiệm vụ:** Tư vấn chuyên sâu (RAG), tra cứu sản phẩm/voucher/bài viết, chốt đơn.
- **Latency:** 2s - 5s (SSE Neural Pulse).

---

## 💰 THE "CONVERSION-FIRST" PROTOCOL (ORDER CLOSING)

### 1. Phân biệt Ý định Chốt đơn
- **Tín hiệu "Lọ/Hộp/Chai/..." (Confirmed Unit):**
    - *Input:* "Cho 1 hộp về địa chỉ..."
    - *Xử lý:* Lên đơn ngay lập tức.
    - *Phản hồi:* Chúc mừng + Mã đơn + Link theo dõi.
- **Tín hiệu "Đơn" (Ambiguous Quantity):**
    - *Input:* "Cho 1 đơn về địa chỉ..."
    - *Xử lý:* Ghi nhận Lead (SĐT/Địa chỉ), hỏi xác nhận số lượng + giá dynamic từ DB.

### 2. Lead Extraction (PydanticAI)
- **LeadPhone:** Nhận diện SĐT Việt Nam.
- **LeadAddress:** Bóc tách địa chỉ chi tiết, tỉnh thành, resolve multi-province.
- **Neural DNA:** VIP / REGULAR / NEW → điều chỉnh phong thái phục vụ.

---

## 🛡️ CÁC ZONE CHIẾN THUẬT

| Zone | Handler | Nhiệm vụ |
|---|---|---|
| 0 | Guardrail | Chặn nội dung nhạy cảm, đối thủ, prompt injection |
| 1 | Greeting | Xây dựng lòng tin, Smart Hook gợi mở sản phẩm/khuyến mãi |
| 2 | Consultant | RAG + 6 DB Tools (Product/Voucher/Article/KB) |
| 3 | Order | Sát thủ chốt đơn, ưu tiên cao nhất |

## 🛠️ CONSULTANT DB TOOLS (Layer 2–6)

| Layer | Tool | Nguồn DB | Mô tả |
|---|---|---|---|
| L2 | `fetch_topic_details` | `SupportKnowledge` | Lấy KB item theo ID |
| L3 | `search_knowledge_base` | `SupportKnowledge` | Semantic/keyword search KB |
| L4 | `search_products_tool` | `ProductBase` | Tìm sản phẩm theo keyword — max 5 kết quả |
| L5 | `get_active_promotions_tool` | `Voucher` + `ComboDeal` | Voucher đang active + trong HSD |
| L6 | `search_articles_tool` | `Article` | Bài viết/chính sách — content cắt 500 ký tự |

---

## 🚫 TIÊU CHUẨN KỸ THUẬT

1. **TrinityBridge Only:** Mọi lượt gọi AI qua Bridge (Key Rotation 8 keys, Semaphore 4).
2. **Context Persistence:** 10 tin nhắn gần nhất.
3. **Zero Leak:** AES-256 cho SĐT/Địa chỉ.
4. **SSE Flow:** "Helen đang suy nghĩ..." realtime.
5. **FOMO Guard:** Chỉ inject [TỒN KHO]/[ĐANG XEM] khi có data thật.
6. **Tenant-Aware:** Mọi DB tool filter theo `current_tenant_id`.

---

**Phiên bản:** Micsmo Elite V2.6
**Cập nhật cuối:** 2026-04-20
**Tác giả:** Trinity Neural Core via Antigravity Agent
