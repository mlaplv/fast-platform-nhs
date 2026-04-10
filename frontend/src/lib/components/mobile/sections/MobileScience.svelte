<script lang="ts">
  import { ShieldCheck, Zap, Droplets } from 'lucide-svelte';
  import './MobileScience.css';
  
  let { product } = $props();
  const metadata = $derived(product?.metadata || {});
  
  const claims = $derived([
    metadata.science_claims?.[0] || { label: 'CƠ CHẾ DIỆT KHUẨN 72H', content: 'Vô hiệu hóa quá trình phân hủy axit béo của vi khuẩn, sát trùng triệt để và ngăn chặn mùi hôi ngay từ gốc.' },
    metadata.science_claims?.[1] || { label: 'AN TOÀN // LÀNH TÍNH', content: '100% thảo dược tự nhiên, cam kết không thâm nách, không ố vàng áo, an toàn cho cả mẹ bầu và trẻ nhỏ.' }
  ]);
  const stats = $derived(metadata.science_stats || { value: '72', unit: 'H', label: 'KHÔ THOÁNG TUYỆT ĐỐI' });

  const tech = $derived([
    {
      icon: ShieldCheck,
      title: typeof claims[0].label === 'string' ? claims[0].label : 'PHỨC HỢP DƯỢC LIỆU SINH HỌC',
      desc: typeof claims[0].content === 'string' ? claims[0].content : 'Vô hiệu hóa vi sinh vật gây mùi.'
    },
    {
      icon: Zap,
      title: `${stats.value}${stats.unit} ${stats.label}`,
      desc: typeof metadata.science_subheadline === 'string' ? metadata.science_subheadline : "Ức chế Acetylcholine để điều tiết tuyến mồ hôi chủ động."
    },
    {
      icon: Droplets,
      title: typeof claims[1].label === 'string' ? claims[1].label : 'THẢO DƯỢC QUÝ HIẾM',
      desc: typeof claims[1].content === 'string' ? claims[1].content : 'Phức hợp rễ cây dược liệu giúp se nhỏ lỗ chân lông.'
    }
  ]);
</script>

<div class="science-root">
  <div class="science-glow-1"></div>
  <div class="science-glow-2"></div>

  <div class="science-header">
    <h2 class="science-headline">
      {metadata.science_headline || 'TẠI SAO LẠI HIỆU QUẢ?'}
    </h2>
    <p class="science-subheadline">
      {metadata.science_subheadline || `Phác đồ thảo dược bí truyền Hồng Sơn.`}
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
        <span class="footer-top-label">TIÊU CHUẨN & AN TOÀN</span>
        <span class="footer-main-label">KIỂM CHỨNG LÂM SÀNG</span>
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
