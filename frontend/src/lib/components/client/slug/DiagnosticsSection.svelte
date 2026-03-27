<script lang="ts">
  import ClinicalQuiz from '$lib/components/client/ClinicalQuiz.svelte';
</script>

<section id="diagnostics" class="diagnostics-container py-32 bg-canvas">
  <div class="container mx-auto px-6 max-w-4xl text-center">
    <span class="badge-accent inline-block px-4 py-1.5 rounded-full font-bold text-[10px] uppercase tracking-[0.3em] mb-8">Personalized Care</span>
    <h3 class="section-title text-5xl font-black tracking-tighter leading-none uppercase mb-10">CHẨN ĐOÁN <br/> CÁ NHÂN HÓA</h3>
    <p class="section-description text-xl max-w-2xl mx-auto leading-relaxed mb-24">Hệ thống AI phân tích tình trạng để đề xuất nồng độ Nano Silver phù hợp.</p>
    <ClinicalQuiz />
  </div>
</section>

<style lang="postcss">
  .diagnostics-container {
    container-type: inline-size;
    --accent-glow: color-mix(in srgb, #60a5fa, transparent 90%);
    --accent-text: var(--color-primary);
  }

  .badge-accent {
    background-color: var(--accent-glow);
    color: var(--accent-text);
  }

  .section-title {
    color: var(--text-base);
  }

  .section-description {
    color: var(--color-secondary);
  }

  @container (min-width: 768px) {
    .section-title {
      font-size: 4.5rem; /* Equivalent to text-7xl */
      line-height: 1;
    }
  }

  @container (max-width: 640px) {
    .section-title {
      font-size: 2.25rem; /* Equivalent to text-4xl */
      line-height: 2.5rem;
    }
  }
</style>
