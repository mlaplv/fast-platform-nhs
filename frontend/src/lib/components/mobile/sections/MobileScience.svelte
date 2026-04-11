<script lang="ts">
  import { ShieldCheck, Zap, Droplets } from 'lucide-svelte';
  import './MobileScience.css';
  
  let { product } = $props();
  const metadata = $derived(product?.metadata || {});
  
  const claims = $derived([
    metadata.science_claims?.[0] || { label: 'CƠ CHẾ PHÁ VỠ HẮC SẮC TỐ', content: 'Ức chế mạnh mẽ quá trình sản sinh Melanin tối màu nhờ tinh chất Hoa Anh Đào (Sakura) và Vitamin C. Đánh bật các gốc thâm sạm từ sâu bên trong, nâng tone rạng rỡ vùng da xỉn màu.' },
    metadata.science_claims?.[1] || { label: 'AN TOÀN // LÀNH TÍNH CHUẨN NHẬT', content: 'Chiết xuất dược liệu sinh học thân thiện với những vùng da mỏng manh nhất. Cam kết "3 KHÔNG": Không cồn, không Paraben, không hóa chất lột tẩy.' }
  ]);
  const stats = $derived(metadata.science_stats || { value: '3', unit: 'S', label: 'THẨM THẤU TÀNG HÌNH' });

  const tech = $derived([
    {
      icon: ShieldCheck,
      title: typeof claims[0].label === 'string' ? claims[0].label : 'CƠ CHẾ PHÁ VỠ HẮC SẮC TỐ',
      desc: typeof claims[0].content === 'string' ? claims[0].content : 'Ức chế Melanin từ tinh chất Sakura.'
    },
    {
      icon: Zap,
      title: `KHÔNG BẾT DÍNH - CHỈ ${stats.value}${stats.unit} CHẠM DA`,
      desc: "Kết cấu serum siêu vi hạt mỏng nhẹ, tan ngay lập tức. Bơm đầy độ ẩm phục hồi sự láng mịn nhưng vẫn đảm bảo bề mặt khô ráo."
    },
    {
      icon: Droplets,
      title: typeof claims[1].label === 'string' ? claims[1].label : 'AN TOÀN CHUẨN NHẬT',
      desc: typeof claims[1].content === 'string' ? claims[1].content : 'Cam kết 3 KHÔNG: Không cồn, không Paraben, không hóa chất lột tẩy.'
    }
  ]);
</script>

<div class="science-root">
  <div class="science-glow-1"></div>
  <div class="science-glow-2"></div>

  <div class="science-header">
    <h2 class="science-headline">
      {metadata.science_headline || 'TẠI SAO LẠI HIỆU QUẢ VƯỢT TRỘI?'}
    </h2>
    <p class="science-subheadline">
      {metadata.science_subheadline || `Đột phá công thức "Bodycare" hàng đầu từ Nhật Bản.`}
    </p>
  </div>

  <div class="science-claims-stack">
    {#each tech as item}
      {@const Icon = item.icon}
      <div class="claim-card group">
        <div class="claim-icon-box">
          <div class="claim-icon-glow"></div>
          <Icon class="w-6 h-6 text-blue-400 relative z-surface" />
        </div>
        <div>
          <h4 class="claim-title">{item.title}</h4>
          <p class="claim-desc">{@html item.desc}</p>
        </div>
      </div>
    {/each}
  </div>

  <div class="science-footer">
    <div class="footer-inner">
      <div class="footer-text">
        <span class="footer-top-label">BẢO CHỨNG AN TOÀN</span>
        <span class="footer-main-label">& CHẤT LƯỢNG QUỐC TẾ</span>
      </div>
      <div class="footer-badges">
        <div class="footer-badge badge-emerald">
          <ShieldCheck class="w-4 h-4 text-emerald-400" />
        </div>
        <div class="footer-badge badge-blue">
          <Zap class="w-4 h-4 text-blue-400" />
        </div>
      </div>
    </div>
  </div>
</div>
