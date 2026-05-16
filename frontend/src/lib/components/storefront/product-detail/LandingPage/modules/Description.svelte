<script lang="ts">
  import type { Product } from '$lib/types';
  import ChevronDown from "@lucide/svelte/icons/chevron-down";
  import HelpCircle from "@lucide/svelte/icons/help-circle";

  interface Props {
    product: Product;
  }

  let { product }: Props = $props();

  let activeFaqIndex = $state<number | null>(0);

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
      {@html product.description || '<p>Thông tin sản phẩm đang được cập nhật...</p>'}
    </article>
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
    background: #d0011b;
  }

  .prose-wrapper {
    max-width: 800px;
    margin: 0 auto;
  }

  /* Standardized Prose for Elite V2.2 */
  :global(.prose-osmo) {
    color: #374151;
    line-height: 1.8;
    font-size: 15px;
  }

  :global(.prose-osmo h2) {
    font-size: 1.5rem;
    font-weight: 800;
    color: #111827;
    margin-top: 2.5rem;
    margin-bottom: 1.25rem;
    letter-spacing: -0.025em;
  }

  :global(.prose-osmo p) {
    margin-bottom: 1.5rem;
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
    background: #f9fafb;
    border-radius: 8px;
  }

  .section-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 2rem;
  }

  .header-icon {
    color: #d0011b;
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
    border-color: #d0011b;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
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
    font-size: 14px;
    font-weight: 700;
    color: #1f2937;
  }

  .chevron-icon {
    color: #9ca3af;
    transition: transform 0.3s;
  }

  .open .chevron-icon {
    transform: rotate(180deg);
    color: #d0011b;
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
