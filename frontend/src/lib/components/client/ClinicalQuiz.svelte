<script lang="ts">
  import { fade, fly, scale } from 'svelte/transition';
  import { quintOut } from 'svelte/easing';
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import type { QuizQuestion, ProductMetadata } from '$lib/types';
  import QuizIcon from './QuizIcon.svelte';
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
  let answers = $state<string[]>([]);
  let progress = $derived(questions.length > 0 ? (currentStep / questions.length) * 100 : 0);

  let quizContainer = $state<HTMLElement | null>(null);

  function nextStep(value: string) {
    answers.push(value);
    if (currentStep < questions.length - 1) {
      currentStep++;
    } else {
      currentStep++;
      // Logic for quantity recommendation
      if (answers.includes('heavy') || answers.includes('failed')) {
        shopStore.setQuantity(2);
      }
    }
  }

  function restart() {
    currentStep = 0;
    answers = [];
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

<div bind:this={quizContainer} class="clinical-quiz glass-liquid p-8 md:p-12 rounded-[3.5rem] relative overflow-hidden max-w-4xl mx-auto border-white/5 shadow-2xl">
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
              onclick={() => nextStep(option.value)}
              onkeydown={(e) => e.key === 'Enter' && nextStep(option.value)}
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
      <div class="result-container text-center py-12 relative" style:z-index="var(--z-surface)" in:fade={{ duration: 1000 }}>
        <div class="relative inline-block mb-12">
          <div class="absolute inset-0 bg-blue-500 blur-[50px] opacity-10 animate-pulse"></div>
          <div class="relative w-32 h-32 glass-liquid rounded-[2.5rem] flex items-center justify-center shadow-2xl border-white/10" in:scale={{ duration: 800, delay: 100 }}>
            <svg class="w-16 h-16 text-blue-400/80" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>
        </div>
        
        <h3 class="text-5xl md:text-6xl font-black text-white mb-6 tracking-[-0.05em] leading-[0.9] uppercase">
          {@html labels.result_headline}
        </h3>
        <p class="text-xl text-blue-100/40 mb-12 max-w-lg mx-auto leading-relaxed font-medium">
          {@html labels.result_subheadline.replace('{quantity}', shopStore.quantity.toString())}
        </p>

        <div class="flex flex-col gap-6 max-w-sm mx-auto">
          <button
            onclick={() => shopStore.openCheckout()}
            class="group relative w-full py-6 bg-blue-600/90 text-white rounded-[2rem] font-black text-2xl shadow-xl overflow-hidden active:scale-[0.98] transition-all duration-500"
          >
            <span class="relative" style:z-index="var(--z-surface)">{labels.result_cta}</span>
            <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700"></div>
          </button>
          <button
            onclick={restart}
            class="text-xs font-black text-white/10 hover:text-blue-400/50 transition-colors uppercase tracking-[0.3em] py-2"
          >
            {labels.restart_label}
          </button>
        </div>
      </div>
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

