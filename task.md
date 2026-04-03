# TASK: SECURITY & SEEDING UNIFICATION (ELITE 2026)

- [/] **Giai đoạn 1: Refactor Security Standard** <!-- id: 400 -->
    - [ ] Backend: Cập nhật  sang chuẩn JSON + AES-GCM duy nhất. <!-- id: 401 -->
    - [ ] Cleanup: Xóa toàn bộ code fallback và các hàm cũ (KISS Principle). <!-- id: 402 -->
- [ ] **Giai đoạn 2: Hiện đại hóa Seeding** <!-- id: 410 -->
    - [ ] Config: Thêm  vào .env. <!-- id: 411 -->
    - [ ] Data: Xóa Key cứng trong . <!-- id: 412 -->
    - [ ] Script: Cập nhật  nạp Key từ môi trường. <!-- id: 413 -->
- [ ] **Giai đoạn 3: Đồng bộ hệ thống (Callers)** <!-- id: 420 -->
    - [ ] Operative: Cập nhật . <!-- id: 421 -->
    - [ ] Controller: Cập nhật . <!-- id: 422 -->
    - [ ] Loader: Cập nhật . <!-- id: 423 -->
    - [ ] AI Service: Cập nhật . <!-- id: 424 -->
- [ ] **Giai đoạn 4: Nghiệm thu (Re-seed & Verify)** <!-- id: 430 -->
    - [ ] Execute: Chạy . <!-- id: 431 -->
    - [ ] Verify: Test Chat với dấu phẩy và kiểm tra log Gemini. <!-- id: 432 -->
