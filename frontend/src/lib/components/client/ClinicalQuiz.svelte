<script lang="ts">
  import { fade, fly, scale } from 'svelte/transition';
  import { quintOut } from 'svelte/easing';
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import type { QuizQuestion, ProductMetadata } from '$lib/types';
  import QuizIcon from './QuizIcon.svelte';
  import DiagnosticScanner from './slug/DiagnosticScanner.svelte';
  import "./slug/LiquidEffects.css";

  const shopStore = getShopStore();

  const product = $derived(shopStore.product);
  const metadata = $derived(product?.metadata || {});
  const questions = $derived(metadata.quiz_questions || []);

  const labels = $derived({
    result_headline: (metadata.quiz_result_headline as string) || 'PHÁC ĐỒ <br/><span class="text-blue-500/80">OPTIMAL.</span>',
    result_subheadline: (metadata.quiz_result_subheadline as string) || 'Hệ thống AI đề xuất: Bạn cần liệu trình <span class="text-blue-400 font-black">{quantity} lọ</span> để đạt hiệu quả tối ưu.',
    result_cta: (metadata.quiz_result_cta as string) || 'KÍCH HOẠT PHÁC ĐỒ',
    restart_label: (metadata.quiz_restart_label as string) || 'Thiết lập lại',
    loading_label: (metadata.quiz_loading_label as string) || 'Đang xử lý dữ liệu...'
  });

  let currentStep = $state(0);
  let answers = $state<Array<{q: string, a: string}>>([]);
  let progress = $derived(questions.length > 0 ? (currentStep / questions.length) * 100 : 0);

  let quizContainer = $state<HTMLElement | null>(null);

  function nextStep(value: string, label: string) {
    answers.push({ q: questions[currentStep].title, a: label });
    if (currentStep < questions.length - 1) {
      currentStep++;
    } else {
      currentStep++;
      // Trigger AI Agentic Analysis
      shopStore.analyzeDiagnostics(answers);
    }
  }

  function restart() {
    currentStep = 0;
    answers = [];
    shopStore.diagnosticResult = null;
    shopStore.setQuantity(1);
  }
</script>

<!-- SVG Filter for Liquid/Gooey Effect -->
<svg style="visibility: hidden; position: absolute;" width="0" height="0" xmlns="http://www.w3.org/2000/svg" version="1.1">
  <defs>
    <filter id="liquid-goo">
      <feGaussianBlur in="SourceGraphic" stdDeviation="10" result="blur" />
      <feColorMatrix in="blur" mode="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 19 -9" result="goo" />
      <feComposite in="SourceGraphic" in2="goo" operator="atop"/>
    </filter>
  </defs>
</svg>

<div bind:this={quizContainer} class="clinical-quiz glass-liquid p-8 md:p-12 rounded-[3.5rem] relative overflow-hidden max-w-4xl mx-auto border-white/5 shadow-2xl min-h-[550px]">
  <!-- Subdued Neural Orbs -->
  <div class="neural-orb -top-20 -right-20 opacity-20" style="background: radial-gradient(circle, #3b82f6 0%, transparent 70%); transform: scale(1.5);"></div>
  <div class="neural-orb -bottom-40 -left-20 opacity-10" style="background: radial-gradient(circle, #818cf8 0%, transparent 70%);"></div>
  
  <!-- Neural Progress Track -->
  <div class="absolute top-0 left-0 right-0 h-1 bg-white/5">
    <div 
      class="h-full bg-blue-500 transition-all duration-1000 ease-[cubic-bezier(0.23,1,0.32,1)] shadow-[0_0_15px_rgba(59,130,246,0.3)]" 
      style="width: {progress}%"
    ></div>
  </div>

  {#if questions.length > 0}
    {#if currentStep < questions.length}
      <div id="s{currentStep + 1}" class="step-container relative" style:z-index="var(--z-surface)" in:fly={{ y: 30, duration: 800, easing: quintOut }}>
        <div class="mb-12 text-left">
          <h3 class="text-4xl md:text-5xl font-black text-white mb-3 tracking-[-0.04em] leading-tight">
            {questions[currentStep].title}
          </h3>
          <p class="text-blue-100/40 font-medium text-lg leading-relaxed">{questions[currentStep].subtitle}</p>
        </div>

        <div class="grid grid-cols-1 gap-4">
          {#each questions[currentStep].options as option, idx}
            <button
              onclick={() => nextStep(option.value, option.label)}
              onkeydown={(e) => e.key === 'Enter' && nextStep(option.value, option.label)}
              aria-label="Select {option.label}"
              class="group p-6 text-left glass-liquid border-white/5 rounded-[2rem] hover:border-blue-500/30 transition-all duration-500 flex items-center gap-6 relative overflow-hidden liquid-bubble"
              in:fly={{ x: 15, duration: 800, delay: idx * 50, easing: quintOut }}
            >
              <div class="w-16 h-16 bg-white/5 rounded-[1.5rem] flex items-center justify-center group-hover:scale-105 transition-all duration-500 border border-white/5 relative" style:z-index="var(--z-surface)">
                <QuizIcon icon={option.icon} />
              </div>
              <div class="flex-1 relative" style:z-index="var(--z-surface)">
                <span class="block text-xl font-bold text-white/90 group-hover:text-blue-400 transition-colors uppercase tracking-tight">{option.label}</span>
              </div>
              
              <div class="w-10 h-10 rounded-full border border-white/5 group-hover:border-blue-500/50 group-hover:bg-blue-500/20 flex items-center justify-center transition-all duration-500 relative" style:z-index="var(--z-surface)">
                <svg class="w-5 h-5 text-white scale-0 group-hover:scale-100 transition-all duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="4" d="M5 13l4 4L19 7" />
                </svg>
              </div>
            </button>
          {/each}
        </div>
      </div>
    {:else}
      {#if shopStore.isAnalyzing}
        <DiagnosticScanner status="Hệ thống AI đang phân tích và thiết kế liệu trình..." />
      {:else if shopStore.diagnosticResult}
        <div class="result-container text-center py-12 relative" style:z-index="var(--z-surface)" in:fade={{ duration: 1000 }}>
          <div class="mb-10 text-left glass-liquid p-8 md:p-12 rounded-[3.5rem] border-white/10 backdrop-blur-3xl relative overflow-hidden shadow-[0_0_80px_rgba(30,58,138,0.3)]">
            <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 mb-10 border-b border-white/10 pb-8">
              <div>
                <h3 class="text-3xl md:text-5xl font-black text-white tracking-tighter uppercase mb-2">KẾT QUẢ PHÂN TÍCH</h3>
                <p class="text-blue-400/60 font-black text-[10px] tracking-[0.4em] uppercase">Phác đồ cá nhân hóa bởi AI Agent 2026</p>
              </div>
              <div class="flex items-center gap-4">
                <div class="text-right hidden md:block">
                  <div class="text-[10px] font-black text-white/30 uppercase tracking-widest">Hiệu lực</div>
                  <div class="text-emerald-400 font-bold text-sm tracking-tighter uppercase">Chứng thực an toàn</div>
                </div>
                <div class="w-16 h-16 rounded-3xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
                  <svg class="w-8 h-8 text-emerald-400" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z" />
                  </svg>
                </div>
              </div>
            </div>
            
            <div class="space-y-8">
              <div>
                <h4 class="text-xs font-black text-blue-400/60 mb-2 uppercase tracking-[0.3em]">Hệ thống phân tích</h4>
                <p class="text-white text-2xl font-bold leading-tight tracking-tight">"{shopStore.diagnosticResult.analysis}"</p>
              </div>
              
              <div class="grid grid-cols-1 md:grid-cols-2 gap-8 pt-8 border-t border-white/5">
                <div>
                  <h4 class="text-[10px] font-black text-white/30 mb-3 uppercase tracking-[0.3em]">Lập luận y khoa</h4>
                  <p class="text-white/50 text-sm leading-relaxed">{shopStore.diagnosticResult.reasoning}</p>
                </div>
                <div>
                  <div class="flex items-center gap-3 mb-3">
                    <h4 class="text-[10px] font-black text-emerald-400/60 uppercase tracking-[0.3em]">Phác đồ tối ưu</h4>
                    {#if shopStore.diagnosticResult.promotion_label}
                      <span class="px-3 py-1 bg-red-500/10 border border-red-500/20 text-red-500 text-[9px] font-black rounded-full animate-pulse shadow-[0_0_15px_rgba(239,68,68,0.2)]">
                        🎁 {shopStore.diagnosticResult.promotion_label}
                      </span>
                    {/if}
                  </div>
                  <p class="text-emerald-500/80 text-sm font-bold leading-relaxed">{shopStore.diagnosticResult.recommendation}</p>
                </div>
              </div>
            </div>
          </div>

          <div class="flex flex-col gap-6 max-w-sm mx-auto">
            <button
              onclick={() => shopStore.openCheckout()}
              class="group relative w-full py-8 bg-blue-600 text-white rounded-[2.5rem] font-black text-3xl shadow-[0_30px_70px_rgba(59,130,246,0.5)] overflow-hidden active:scale-[0.98] transition-all duration-500"
            >
              <span class="relative" style:z-index="var(--z-surface)">XEM LIỆU TRÌNH</span>
              <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000"></div>
            </button>
            <button
              onclick={restart}
              class="text-[10px] font-black text-white/10 hover:text-blue-400/50 transition-colors uppercase tracking-[0.4em] py-2"
            >
              Làm lại chẩn đoán
            </button>
          </div>
        </div>
      {/if}
    {/if}
  {:else}
    <div class="py-20 text-center" in:fade>
      <div class="inline-block w-12 h-12 border-4 border-blue-500/20 border-t-blue-500 rounded-full animate-spin mb-4"></div>
      <p class="text-blue-100/20 font-black uppercase tracking-[0.3em] text-xs">Phân tích dữ liệu lâm sàng...</p>
    </div>
  {/if}
</div>

<style>
  :global(.clinical-quiz) {
    transition: all 0.8s cubic-bezier(0.23, 1, 0.32, 1);
  }
</style>

