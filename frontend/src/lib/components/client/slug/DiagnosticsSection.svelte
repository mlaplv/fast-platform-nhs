<script lang="ts">
  import ClinicalQuiz from '$lib/components/client/ClinicalQuiz.svelte';
  import type { QuizQuestion, ProductMetadata } from '$lib/types';
  import { SHOP_CONFIG } from '$lib/constants/shop';
  import "./DiagnosticsSection.css";
  import "./LiquidEffects.css";

  let {
    questions = [],
    metadata = {}
  }: {
    questions: QuizQuestion[];
    metadata: ProductMetadata;
  } = $props();

  const labels = $derived({
    headline: metadata.diagnostics_headline || 'CHẨN ĐOÁN CÁ NHÂN HÓA',
    subheadline: metadata.diagnostics_subheadline || `Để hệ thống chẩn đoán của <span class="text-white/60">${SHOP_CONFIG.pharmacy.name}</span> thiết lập phác đồ liều lượng chính xác nhất, vui lòng chọn mức độ biểu hiện hiện tại của bạn.`,
    disclaimer: metadata.diagnostics_disclaimer || `Mọi thông tin được bảo mật tuyệt đối bởi ${SHOP_CONFIG.pharmacy.name}`
  });
</script>

<section id="diagnostics" aria-labelledby="personalized-care" class="diagnostics-container snap-session relative overflow-x-hidden bg-[#020617]">
  <div class="container mx-auto px-6 max-w-5xl text-center relative pt-[var(--section-pt)] pb-20" style:z-index="var(--z-surface)">
    <h3 id="personalized-care" class="section-title text-neural font-black tracking-tight leading-none uppercase mb-4 text-4xl md:text-6xl">
      {@html labels.headline}
    </h3>

    <p class="section-description text-white/40 text-base md:text-lg max-w-2xl mx-auto leading-relaxed mb-8">
      {@html labels.subheadline}
    </p>

    <div class="quiz-wrapper relative">
      <ClinicalQuiz {questions} {metadata} />
    </div>

    <!-- Security & Privacy Disclaimer thưa Sếp! -->
    <div class="mt-16 flex items-center justify-center gap-3 text-[10px] font-black tracking-[0.2em] text-white/20 uppercase bg-white/5 py-4 px-8 rounded-full border border-white/5 w-fit mx-auto backdrop-blur-md">
      <svg class="w-4 h-4 text-emerald-500/40" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
      </svg>
      {labels.disclaimer}
    </div>
  </div>
  <!-- Dynamic Line Wave Divider - Refined Analytical Diag thưa Sếp! -->
  <div class="wave-container">
    <svg viewBox="0 0 1440 320" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="none">
      <defs>
        <linearGradient id="wave-gradient-diag" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="#10b981" stop-opacity="0" />
          <stop offset="50%" stop-color="#06b6d4" stop-opacity="0.8" />
          <stop offset="100%" stop-color="#10b981" stop-opacity="0" />
        </linearGradient>
      </defs>
      <!-- Premium Digital Flow: Shifted higher for visibility thưa Sếp! -->
      <path class="wave-line opacity-30" d="M0,180 Q180,160 360,180 T720,180 T1080,180 T1440,180" />
      <path class="wave-line" d="M0,200 C150,190 200,100 300,200 C450,210 500,120 600,200 C750,190 800,100 900,200 C1050,210 1100,120 1200,200 C1350,190 1400,100 1440,200" />
      <path class="wave-line secondary" d="M0,210 C200,200 300,180 400,210 C500,220 600,190 700,210 C800,230 900,180 1000,210 C1100,240 1200,190 1440,210" />
    </svg>
  </div>
</section>
