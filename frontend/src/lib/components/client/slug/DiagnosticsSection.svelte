<script lang="ts">
  import ClinicalQuiz from '$lib/components/client/ClinicalQuiz.svelte';
  import type { QuizQuestion, ProductMetadata, Product } from '$lib/types';
  import { SHOP_CONFIG } from '$lib/constants/shop';
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import EditableWrapper from '$lib/components/admin/EditableWrapper.svelte';
  import "./DiagnosticsSection.css";
  import "./LiquidEffects.css";

  import { liveEditStore } from '$lib/state/commerce/liveEdit.svelte';

  let { product: propProduct = $bindable() } = $props<{ product?: Product }>();
  const shopStore = getShopStore();
  
  const product = $derived(liveEditStore.isEditMode && liveEditStore.dirtyProduct ? liveEditStore.dirtyProduct : (propProduct || shopStore.product));
  const metadata = $derived(product?.metadata || {});
  const questions = $derived(metadata?.quiz_questions || []);

  const labels = $derived({
    headline: metadata.diagnostics_headline || 'DỰ ĐOÁN PHỤC HỒI CHUYÊN SÂU',
    subheadline: metadata.diagnostics_subheadline || `Để hệ thống Trí tuệ Nhân tạo của <span class="text-white/60">${SHOP_CONFIG.pharmacy.name}</span> thiết lập phác đồ liều lượng tối ưu nhất, vui lòng phản hồi chính xác tình trạng hiện tại của Sếp.`,
    disclaimer: metadata.diagnostics_disclaimer || `MICSMO - Gemini là AI và có thể mắc sai sót.`
  });
</script>

<section id="diagnostics-section" aria-labelledby="personalized-care" class="snap-session snap-session-standard diagnostics-container diagnostic-premium-flow relative overflow-x-hidden" style:padding-top="var(--standard-pt)">
  <div class="container mx-auto px-4 md:px-6 max-w-7xl text-center relative z-surface">
    <EditableWrapper path="metadata.diagnostics_headline" label="SỬA TIÊU ĐỀ CHẨN ĐOÁN">
      <h3 id="personalized-care" class="elite-session-headline mb-8">
        {@html labels.headline}
      </h3>
    </EditableWrapper>

    <EditableWrapper path="metadata.diagnostics_subheadline" label="SỬA MÔ TẢ CHẨN ĐOÁN">
      <p class="section-description text-white/40 text-base md:text-lg max-w-2xl mx-auto leading-relaxed mb-8">
        {@html labels.subheadline}
      </p>
    </EditableWrapper>

    <div class="quiz-wrapper relative">
      <ClinicalQuiz {product} {questions} {metadata} />
    </div>

    <!-- Security & Privacy Disclaimer! -->
    <div class="mt-4 md:mt-6 flex items-center justify-center gap-3 text-[10px] font-black tracking-[0.2em] text-white/20 uppercase bg-white/5 py-4 px-8 rounded-full border border-white/5 w-fit mx-auto backdrop-blur-md">
      <svg class="w-4 h-4 text-emerald-500/40" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
      </svg>
      <EditableWrapper path="metadata.diagnostics_disclaimer" label="SỬA LỜI NHẮC">
        {labels.disclaimer}
      </EditableWrapper>
    </div>
  </div>
  <!-- Dynamic Line Wave Divider - Refined Analytical Diag! -->
  <div class="wave-container">
    <svg viewBox="0 0 1440 320" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="none">
      <defs>
        <linearGradient id="wave-gradient-diag" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="#10b981" stop-opacity="0" />
          <stop offset="50%" stop-color="#06b6d4" stop-opacity="0.8" />
          <stop offset="100%" stop-color="#10b981" stop-opacity="0" />
        </linearGradient>
      </defs>
      <!-- Premium Digital Flow: Shifted higher for visibility! -->
      <path class="wave-line opacity-30" d="M0,180 Q180,160 360,180 T720,180 T1080,180 T1440,180" />
      <path class="wave-line" d="M0,200 C150,190 200,100 300,200 C450,210 500,120 600,200 C750,190 800,100 900,200 C1050,210 1100,120 1200,200 C1350,190 1400,100 1440,200" />
      <path class="wave-line secondary" d="M0,210 C200,200 300,180 400,210 C500,220 600,190 700,210 C800,230 900,180 1000,210 C1100,240 1200,190 1440,210" />
    </svg>
  </div>
</section>

<style>
  .z-surface { z-index: var(--z-surface); }
</style>
