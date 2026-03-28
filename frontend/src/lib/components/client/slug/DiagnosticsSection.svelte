<script lang="ts">
  import ClinicalQuiz from '$lib/components/client/ClinicalQuiz.svelte';
  import "./DiagnosticsSection.css";
  import "./LiquidEffects.css";
</script>

<section id="diagnostics" class="diagnostics-container snap-session relative overflow-hidden bg-[#020617] flex-1">
  <div class="container mx-auto px-6 max-w-5xl text-center relative my-auto" style:z-index="var(--z-surface)">
    <h3 id="personalized-care" class="section-title text-neural font-black tracking-tight leading-none uppercase mb-6 text-4xl md:text-6xl">
      CHẨN ĐOÁN CÁ NHÂN HÓA
    </h3>
    
    <p class="section-description text-white/20 text-base md:text-lg max-w-lg mx-auto leading-relaxed mb-20">
      Phân tích sinh trắc học chuẩn xác bởi <span class="text-white/40">AI Engine</span>.
    </p>

    <div class="quiz-wrapper relative">
      <ClinicalQuiz />
    </div>
  </div>
</section>
