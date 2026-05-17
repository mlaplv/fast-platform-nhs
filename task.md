# Viral Share-To-Unlock UI Stabilization

- [x] Analyze `ShareToUnlock.svelte` để tìm lý do box share biến mất sau khi chia sẻ.
- [x] Lần đầu: Xóa `&& step !== 'revealed'` khỏi wrapper ngoài (fix sai — tạo revealed card dead code).
- [x] Lần 2: Fix lại sang dạng sibling `{#if} {:else if}` — wrapper ngoài giữ `&& step !== 'revealed'`, revealed card là một nhánh riêng biệt ở ngoài `{:else if isEnabled && step === 'revealed' && voucherCode}`.
- [x] Apply cùng fix cho `ShareToUnlockPromoMobile.svelte`.
- [x] Wrap `{#key product.id}` tại tất cả các điểm mount: `LandingPage/Info`, `MainDetail/Info`, `ProductMobileMedia`, `MobileOffer`.
- [x] **Root Cause cuối cùng được xác nhận:** Template cũ có `{#if isEnabled && step !== 'revealed'}` bao ngoài `{:else if step === 'revealed'}` bên trong → dead code, hai điều kiện triệt tiêu nhau. Box share không hiện do inner revealed branch không thể đạt được. Fix: Tách revealed card ra thành nhánh `{:else if}` độc lập ở cấp wrapper.

# Storefront Hydration Error Stabilization for Admin Accounts
- [x] Phân tích Root Cause lỗi hydration (`root.svelte:44:41`) khi tài khoản có role ADMIN truy cập storefront.
- [x] Nhận diện nguyên nhân: Sự chênh lệch trạng thái phân quyền giữa Server-Side (khách vãng lai, `liveEditStore.isAdmin = false`) và Client-Side (đã giải mã token trước lúc hydrate, `liveEditStore.isAdmin = true`) kích hoạt nỗ lực mount Admin JIT components không đồng nhất.
- [x] Khai báo trạng thái `$state` rune `isMounted = false` trong `[slug]-funnel/+page.svelte`.
- [x] Phát hiện hiện tượng chạy đồng bộ của `isMounted = true` trong `onMount` vẫn có thể bị cuốn vào chu kỳ hydration gốc của Svelte 5.
- [x] Refactor sang cơ chế **Deferred Gate Guard (Trì hoãn bằng setTimeout 150ms)** để đẩy tác vụ render Admin HUD sang luồng event loop tiếp theo, khi Svelte đã hoàn thành 100% root hydration, đặt cờ `hydrating = false` và ổn định hoàn toàn cấu trúc DOM storefront.
- [x] Đăng ký hàm hủy `clearTimeout` tại sự kiện hủy component trong `onMount` (Resource Discipline).
- [x] Kiểm tra cú pháp và hoàn thành kiểm định.

# Viral Progress Bar Visual Upgrade & Optimization
- [x] Phân tích và nâng cấp hiệu ứng thẩm mỹ cho thanh tiến trình chia sẻ trong `ViralShareBarDesktop.svelte` (vệt sao chổi mờ dần + neon beacon).
- [x] Phân tích và nâng cấp hiệu ứng thẩm mỹ cho thanh tiến trình chia sẻ trong `ViralShareBarMobile.svelte` (vệt sao chổi mờ dần + neon beacon).
- [x] Phân tích và nâng cấp hiệu ứng thẩm mỹ cho thanh tiến trình chia sẻ trong `ViralFunnelLanding.svelte` (vệt sao chổi mờ dần + neon beacon).
- [x] Tự kiểm thức và chạy kiểm tra cú pháp biên dịch dự án.
