# 🛡️ CẨM NANG THIẾT QUÂN LUẬT TRÊN GITHUB (DÀNH CHO SẾP)

Tài liệu này hướng dẫn Sếp cách khóa chặt cổng thành `main` trên giao diện trang chủ Github.com để Ép Buộc các Workflow CI/CD (R69, R70, R71) thực sự phát huy tác dụng.

> ⚠️ **LƯU Ý:** Nếu Sếp không cấu hình các bước này, đội Dev vẫn có thể bấm nút mầu xanh "Merge pull request" bất chấp việc code bị lỗi hoặc vi phạm luật từ GitHub Action.

---

### BƯỚC 0: Đẩy (Push) Code Lên GitHub
Trước khi làm gì khác, Sếp **BẮT BUỘC** phải lưu và đẩy các file cấu hình này lên nhánh `main` để GitHub nhận diện được sự tồn tại của các Job Tòa Án Binh.
1. Mở Terminal và gõ:
   ```bash
   git add .github/ docs/
   git commit -m "chore: setup github actions enforcer v61.0"
   git push origin main
   ```
*(Sau khi push xong, Sếp mới tiến hành cấu hình Bước 1 bên dưới)*

---

### BƯỚC 1: Truy cập Trình cấu hình Bảo vệ Nhánh
1. Mở trình duyệt và truy cập vào Repository của dự án trên GitHub: `[Tên-Tổ-chức]/fast-platform-core`.
2. Bấm vào tab **⚙️ Settings** ở góc phải trên cùng màn hình.
3. Ở menu bên trái, tìm và chọn cột **Branches**.
4. Bấm vào nút **Add branch protection rule** (Thêm luật bảo vệ nhánh).
5. Tại ô `Branch name pattern`, Sếp nhập chính xác tên nhánh: `main`

---

### BƯỚC 2: Thiết lập Kỷ luật Merging (Rất Quan Trọng)
Tại phần cấu hình bên dưới ô `Branch name pattern`, Sếp tích chọn các ô sau:

✅ **Require a pull request before merging** 
*(Bắt buộc mọi người phải tạo PR, cấm đẩy code thắng (Push) trực tiếp vào nhánh `main`)*
- Tích luôn ô con: **Require approvals**: Chỉnh số lượng cần duyệt là **1** hoặc **2**. 

✅ **Require status checks to pass before merging**
*(Đây là linh hồn của "Tòa Án Binh". Tích vào đây để bắt buộc các file Action `.yml` phải xanh lá mới cho Merge)*
- Sau khi tích, ở ô search bar nhỏ ngay bên dưới: Sếp gõ và chọn lần lượt **3 Job** của chúng ta:
  1. `R69: LOC Discipline Check`
  2. `R70: Anti-Latest Dependency Check`
  3. `R71: Backend Unit Test Mandate`
- Tích thêm ô: **Require branches to be up to date before merging**.

✅ **Require conversation resolution before merging**
*(Không cho Merge khi còn các đoạn comment soi lỗi chưa được Dev bấm "Resolve")*

---

### BƯỚC 3: Chặn phá hoại lịch sử (Force Push)
Kéo xuống cuối trang, Sếp hãy **BỎ TÍCH ĐI** (nếu đang tích) các quyền hạn nguy hiểm sau:

❌ **Allow force pushes** (Phải BỎ TÍCH)
*(Nếu tích, ai đó có thể dùng lệnh `git push -f` để ghi đè và làm mất sạch code của các tháng trước)*

❌ **Allow deletions** (Phải BỎ TÍCH)
*(Chặn việc ai đó xóa thẳng nhánh `main`)*

🎉 Đã thiết lập xong toàn bộ luật ngầm chặn bug từ xa. Sếp nhấn nút **Save changes** để Tòa Án Binh bắt đầu có hiệu lực!
