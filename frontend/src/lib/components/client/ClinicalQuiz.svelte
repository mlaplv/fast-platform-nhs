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

  const QUIZ_FALLBACKS = {
    result_headline: 'LIỆU TRÌNH <br/><span class="text-blue-500/80">OPTIMAL.</span>',
    result_subheadline: 'Hệ thống AI đề xuất: Bạn cần liệu trình <span class="text-blue-400 font-black">{quantity} lọ</span> để đạt hiệu quả tối ưu.',
    result_cta: 'KÍCH HOẠT LIỆU TRÌNH',
    restart_label: 'Thiết lập lại',
    loading_label: 'Đang xử lý dữ liệu...'
  };

  const labels = $derived({
    result_headline: metadata.quiz_result_headline || QUIZ_FALLBACKS.result_headline,
    result_subheadline: metadata.quiz_result_subheadline || QUIZ_FALLBACKS.result_subheadline,
    result_cta: metadata.quiz_result_cta || QUIZ_FALLBACKS.result_cta,
    restart_label: metadata.quiz_restart_label || QUIZ_FALLBACKS.restart_label,
    loading_label: metadata.quiz_loading_label || QUIZ_FALLBACKS.loading_label
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
<svg class="invisible absolute" width="0" height="0" xmlns="http://www.w3.org/2000/svg" version="1.1">
  <defs>
    <filter id="liquid-goo">
      <feGaussianBlur in="SourceGraphic" stdDeviation="10" result="blur" />
      <feColorMatrix in="blur" mode="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 19 -9" result="goo" />
      <feComposite in="SourceGraphic" in2="goo" operator="atop"/>
    </filter>
  </defs>
</svg>

<div 
  bind:this={quizContainer} 
  class="clinical-quiz {!shopStore.diagnosticResult ? 'glass-liquid border-white/5' : ''} {shopStore.diagnosticResult ? 'p-0 md:p-0 lg:p-12' : 'p-6 md:p-8 lg:p-12'} rounded-[3.5rem] relative overflow-hidden max-w-4xl mx-auto shadow-2xl min-h-[500px]"
>
  <!-- Subdued Neural Orbs -->
  <div class="neural-orb -top-20 -right-20 opacity-20" style:background="radial-gradient(circle, #3b82f6 0%, transparent 70%)" style:transform="scale(1.5)"></div>
  <div class="neural-orb -bottom-40 -left-20 opacity-10" style:background="radial-gradient(circle, #818cf8 0%, transparent 70%)"></div>
  
  <!-- Neural Progress Track -->
  <div class="absolute top-0 left-0 right-0 h-1 bg-white/5">
    <div 
      class="h-full bg-blue-500 transition-all duration-1000 ease-[cubic-bezier(0.23,1,0.32,1)] shadow-[0_0_15px_rgba(59,130,246,0.3)]" 
      style:width="{progress}%"
    ></div>
  </div>

  {#if questions.length > 0}
    {#if currentStep < questions.length}
      <div id="s{currentStep + 1}" class="step-container relative z-surface" in:fly={{ y: 30, duration: 800, easing: quintOut }}>
        <div class="mb-8 md:mb-10 text-left">
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
              <div class="w-16 h-16 bg-white/5 rounded-[1.5rem] flex items-center justify-center group-hover:scale-105 transition-all duration-500 border border-white/5 relative z-surface">
                <QuizIcon icon={option.icon} />
              </div>
              <div class="flex-1 relative z-surface">
                <span class="block text-xl font-bold text-white/90 group-hover:text-blue-400 transition-colors uppercase tracking-tight">{option.label}</span>
              </div>
              
              <div class="w-10 h-10 rounded-full border border-white/5 group-hover:border-blue-500/50 group-hover:bg-blue-500/20 flex items-center justify-center transition-all duration-500 relative z-surface">
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
        <div class="result-container text-center py-0 md:py-0 lg:py-10 relative z-surface" in:fade={{ duration: 1000 }}>
          <div class="mb-0 md:mb-0 lg:mb-12 text-left glass-liquid p-6 md:p-8 lg:p-12 rounded-[2.5rem] border-white/10 backdrop-blur-3xl relative overflow-hidden shadow-[0_0_80px_rgba(30,58,138,0.3)]">
            <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6 border-b border-white/10 pb-6">
              <div>
                <h3 class="text-3xl md:text-[2.25rem] lg:text-5xl font-black text-white tracking-tighter uppercase mb-2 whitespace-nowrap">KẾT QUẢ PHÂN TÍCH</h3>
                <p class="text-blue-400/60 font-black text-[10px] tracking-[0.4em] uppercase">Liệu trình cá nhân hóa bởi AI Agent 2026</p>
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
            
            <div class="space-y-6">
              <div>
                <h4 class="text-xs font-black text-blue-400/60 mb-2 uppercase tracking-[0.3em]">Hệ thống phân tích</h4>
                <p class="text-white text-2xl font-bold leading-tight tracking-tight">"{shopStore.diagnosticResult.analysis}"</p>
              </div>
              
              <div class="grid grid-cols-1 md:grid-cols-2 gap-6 pt-6 border-t border-white/5">
                <div>
                  <h4 class="text-[10px] font-black text-white/30 mb-3 uppercase tracking-[0.3em]">Tổng quan</h4>
                  <p class="text-white/50 text-sm leading-relaxed">{shopStore.diagnosticResult.reasoning}</p>
                </div>
                <div>
                  <div class="flex items-center gap-3 mb-3">
                    <h4 class="text-[10px] font-black text-emerald-400/60 uppercase tracking-[0.3em]">Liệu trình tối ưu</h4>
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

          <div class="flex flex-col gap-4 max-w-sm mx-auto mt-8 md:mt-10 lg:mt-12">
            <button
              onclick={() => shopStore.openCheckout()}
              class="group relative w-full py-5 md:py-6 bg-blue-600 text-white rounded-[2rem] font-black text-2xl md:text-2xl lg:text-3xl shadow-[0_20px_50px_rgba(59,130,246,0.4)] overflow-hidden active:scale-[0.98] transition-all duration-500"
            >
              <span class="relative z-surface">XEM LIỆU TRÌNH</span>
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
  .z-surface {
    z-index: var(--z-surface);
  }
</style>

