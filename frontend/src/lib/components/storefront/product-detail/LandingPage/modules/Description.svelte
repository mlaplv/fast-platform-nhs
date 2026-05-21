<script lang="ts">
  import type { Product } from '$lib/types';
  import ChevronDown from "@lucide/svelte/icons/chevron-down";
  import HelpCircle from "@lucide/svelte/icons/help-circle";
  import { parseDescriptionAndCommitments } from '$lib/utils/product';

  interface Props {
    product: Product;
  }

  let { product }: Props = $props();

  let activeFaqIndex = $state<number | null>(0);

  const parsedDescription = $derived(parseDescriptionAndCommitments(product.description));

  // Elite V2.2 Fix: Normalize FAQ schema — DB uses {question,answer}, hardcode uses {q,a}
  const faqItems = $derived.by(() => {
    const raw = product.metadata?.faqs;
    if (raw && raw.length > 0) {
      return raw.map((f: Record<string, string>) => ({
        q: f.question ?? f.q ?? '',
        a: f.answer ?? f.a ?? '',
      }));
    }
    return [
      { q: "Sản phẩm có gây kích ứng da không?", a: "Sản phẩm đã được kiểm nghiệm da liễu, an toàn cho mọi loại da, kể cả da nhạy cảm." },
      { q: "Bao lâu thì thấy hiệu quả rõ rệt?", a: "Hiệu quả tùy thuộc vào cơ địa, thông thường khách hàng sẽ thấy cải thiện sau 2-4 tuần sử dụng đều đặn." },
      { q: "Cách bảo quản sản phẩm tốt nhất?", a: "Bảo quản nơi khô ráo, thoáng mát, tránh ánh nắng trực tiếp và đóng nắp kín sau khi sử dụng." }
    ];
  });

  function toggleFaq(index: number) {
    activeFaqIndex = activeFaqIndex === index ? null : index;
  }
</script>

<div class="description-container">
  <!-- Description Header -->
  <div class="tabs-header">
    <button class="tab-btn active">MÔ TẢ SẢN PHẨM</button>
  </div>

  <!-- HTML Content -->
  <div class="prose-wrapper">
    <article class="prose-osmo">
      {@html parsedDescription.cleanDescription || '<p>Thông tin sản phẩm đang được cập nhật...</p>'}
    </article>

    {#if parsedDescription.commitments}
      {@const commitments = parsedDescription.commitments}
      <div class="commitment-card-luxury mt-8 p-5 rounded-2xl border border-emerald-500/10 bg-white/40 relative overflow-hidden shadow-[0_15px_30px_rgba(4,120,87,0.02)] backdrop-blur-md transition-all duration-300">
        <!-- Subtle backlights -->
        <div class="absolute -top-12 -right-12 w-32 h-32 rounded-full bg-emerald-100/20 blur-2xl pointer-events-none"></div>
        <div class="absolute -bottom-12 -left-12 w-32 h-32 rounded-full bg-teal-100/20 blur-2xl pointer-events-none"></div>
        
        <div class="relative z-10 flex flex-col gap-3">
          <!-- Compact Row 1: Header (title | subtitle) - Prevent title compression -->
          <div class="flex flex-col sm:flex-row sm:items-center gap-2 pb-3 border-b border-emerald-500/10">
            <div class="flex items-center gap-2 shrink-0">
              <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
              <span class="text-[12px] font-black text-slate-800 uppercase tracking-widest shrink-0 whitespace-nowrap">{commitments.title}</span>
            </div>
            {#if commitments.subtitle}
              <span class="text-gray-300 hidden sm:inline shrink-0">|</span>
              <span class="text-[11.5px] font-black text-[#ee4d2d] tracking-tight leading-normal">{commitments.subtitle}</span>
            {/if}
          </div>

          <!-- Compact Row 2: Grid of 3 items -->
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {#each commitments.items as item}
              {@const parts = item.split(':')}
              {@const boldPart = parts[0]}
              {@const normalPart = parts.slice(1).join(':')}
              <div class="flex items-center gap-2.5 p-2 bg-white/70 border border-emerald-500/5 hover:border-emerald-500/20 hover:bg-white rounded-xl transition-all duration-300 group min-w-0">
                <div class="w-6 h-6 rounded-full bg-emerald-500/10 flex items-center justify-center text-emerald-600 shrink-0">
                  <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <div class="flex flex-col min-w-0 leading-tight py-0.5">
                  <span class="text-[11.5px] font-black text-slate-800 leading-normal">{boldPart.trim()}</span>
                  {#if normalPart}
                    <span class="text-[10px] text-gray-500 leading-normal mt-0.5">{normalPart.trim()}</span>
                  {/if}
                </div>
              </div>
            {/each}
          </div>

          <!-- Compact Row 3: Simple Minimalist Viral Ribbon (No bg, no border) -->
          <a href="/chinh-sach-doi-tra-hoan-tien.html" class="flex items-center justify-between gap-4 pt-3 border-t border-emerald-500/10 mt-1 group no-underline text-slate-700 hover:text-emerald-600 transition-all duration-300">
            <div class="flex items-center gap-2 min-w-0">
              <svg class="w-4 h-4 text-emerald-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              <span class="text-[10px] font-black text-slate-800 uppercase tracking-widest shrink-0">FREESHIP & ĐỔI TRẢ:</span>
              <span class="text-[11px] font-medium text-gray-500 truncate">{commitments.fomo}</span>
            </div>
            
            <div class="flex items-center gap-0.5 shrink-0 text-emerald-600 text-[11px] font-bold group-hover:translate-x-1 transition-transform duration-300">
              <span>Xem thêm</span>
              <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
              </svg>
            </div>
          </a>
        </div>
      </div>
    {/if}
  </div>

  <!-- FAQ Section -->
  <div class="faq-section">
    <div class="section-header">
      <HelpCircle size={20} class="header-icon" />
      <h2 class="section-title">HỎI ĐÁP VỀ {product.name.toUpperCase()}</h2>
    </div>
    
    <div class="faq-list">
      {#each faqItems as faq, i}
        <div class="faq-item" class:open={activeFaqIndex === i}>
          <button class="faq-question" onclick={() => toggleFaq(i)}>
            <span class="q-text">{faq.q}</span>
            <ChevronDown size={18} class="chevron-icon" />
          </button>
          {#if activeFaqIndex === i}
            <div class="faq-answer">
              <p>{faq.a}</p>
            </div>
          {/if}
        </div>
      {/each}
    </div>
  </div>
</div>

<style>
  .description-container {
    margin-top: 3rem;
    background: white;
    padding: 2rem 1.25rem;
    border-top: 1px solid #f3f4f6;
  }

  .tabs-header {
    border-bottom: 1px solid #f3f4f6;
    margin-bottom: 2rem;
    display: flex;
  }

  .tab-btn {
    padding: 1rem 2rem;
    font-size: 16px;
    font-weight: 700;
    color: #111827;
    background: none;
    border: none;
    position: relative;
    cursor: pointer;
  }

  .tab-btn.active::after {
    content: '';
    position: absolute;
    bottom: -1px;
    left: 0;
    right: 0;
    height: 3px;
    background: #0d9488 !important;
  }

  .prose-wrapper {
    max-width: 800px;
    margin: 0 auto;
  }

  :global(.prose-osmo) {
    color: #374151;
    line-height: 1.6;
    font-size: 15px; /* Sleek e-commerce standard (Lazada/Shopee) */
  }

  :global(.prose-osmo h2) {
    font-size: 1.5rem;
    font-weight: 800;
    color: #6b7280 !important;
    margin-top: 2.5rem;
    margin-bottom: 1.25rem;
    letter-spacing: -0.025em;
    text-transform: lowercase !important;
  }

  :global(.prose-osmo h2::first-letter) {
    text-transform: uppercase !important;
  }

  :global(.prose-osmo p) {
    margin-bottom: 1.5rem;
    font-weight: 400;
    letter-spacing: -0.011em;
  }

  :global(.prose-osmo strong) {
    color: #111827;
    font-weight: 700;
  }

  .faq-section {
    margin-top: 4rem;
    max-width: 800px;
    margin-left: auto;
    margin-right: auto;
    padding: 2.5rem;
    background: linear-gradient(135deg, #f0fdf4 0%, #fff7ed 100%) !important;
    border: 1px solid rgba(13, 148, 136, 0.1) !important;
    border-radius: 8px !important;
  }

  .section-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 2rem;
  }

  .header-icon {
    color: #0d9488 !important;
  }

  .section-title {
    font-size: 16px;
    font-weight: 900;
    letter-spacing: 0.05em;
    color: #111827;
    margin: 0;
  }

  .faq-list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .faq-item {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    overflow: hidden;
    transition: all 0.2s;
  }

  .faq-item.open {
    border-color: #0d9488 !important;
    box-shadow: 0 4px 15px rgba(13, 148, 136, 0.08) !important;
  }

  .faq-question {
    width: 100%;
    padding: 1.25rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: none;
    border: none;
    cursor: pointer;
    text-align: left;
  }

  .q-text {
    font-size: 15px;
    font-weight: 700;
    color: #1f2937;
  }

  .chevron-icon {
    color: #9ca3af;
    transition: transform 0.3s;
  }

  .open .chevron-icon {
    transform: rotate(180deg);
    color: #0d9488 !important;
  }

  .faq-answer {
    padding: 0 1.25rem 1.25rem 1.25rem;
    font-size: 14px;
    color: #4b5563;
    line-height: 1.6;
    border-top: 1px solid #f3f4f6;
  }

  .faq-answer p {
    margin: 0;
  }
</style>
