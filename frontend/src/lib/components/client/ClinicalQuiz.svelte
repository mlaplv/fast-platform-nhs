<script lang="ts">
  import { shopStore } from '$lib/state/commerce/shop.svelte.ts';
  import { fade, fly, scale } from 'svelte/transition';
  import { quintOut } from 'svelte/easing';
  import "./slug/LiquidEffects.css";

  let currentStep = $state(0);
  let answers = $state<string[]>([]);
  let progress = $derived((currentStep / 2) * 100);

  interface QuizOption {
    label: string;
    desc: string;
    value: string;
    icon: string;
  }

  interface Question {
    id: number;
    title: string;
    subtitle: string;
    options: QuizOption[];
  }

  const questions: Question[] = [
    {
      id: 1,
      title: "Tình trạng mồ hôi & mùi cơ thể?",
      subtitle: "Để chúng tôi hiểu rõ mức độ cần can thiệp y khoa của bạn",
      options: [
        { label: "Mùi nhẹ khi vận động", desc: "Cần bảo vệ hằng ngày", value: "light", icon: "💧" },
        { label: "Mùi nồng, ra mồ hôi nhiều", desc: "Cần liệu trình chuyên sâu", value: "heavy", icon: "🌊" },
        { label: "Thâm nách, lỗ chân lông to", desc: "Cần phục hồi tế bào", value: "dark", icon: "✨" }
      ]
    },
    {
      id: 2,
      subtitle: "Thông tin này giúp tối ưu hóa nồng độ Nano hoạt tính",
      title: "Lịch sử sử dụng sản phẩm?",
      options: [
        { label: "Chưa từng dùng thuốc", desc: "Cơ địa mới bắt đầu", value: "none", icon: "🌱" },
        { label: "Đã dùng nhưng không hiệu quả", desc: "Cần công thức mạnh hơn", value: "failed", icon: "🛡️" },
        { label: "Sợ bị ố vàng áo & kích ứng", desc: "Cần độ tinh khiết 100%", value: "fear", icon: "👔" }
      ]
    }
  ];

  let quizContainer = $state<HTMLElement | null>(null);

  function nextStep(value: string) {
    answers.push(value);
    if (currentStep < questions.length - 1) {
      currentStep++;
    } else {
      currentStep++; 
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
            class="group p-6 text-left glass-liquid border-white/5 rounded-[2rem] hover:border-blue-500/30 transition-all duration-500 flex items-center gap-6 relative overflow-hidden liquid-bubble"
            in:fly={{ x: 15, duration: 800, delay: idx * 50, easing: quintOut }}
          >
            <div class="w-16 h-16 bg-white/5 rounded-[1.5rem] flex items-center justify-center text-3xl group-hover:scale-105 transition-all duration-500 border border-white/5 relative" style:z-index="var(--z-surface)">
              {option.icon}
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
        PHÁC ĐỒ <br/><span class="text-blue-500/80">OPTIMAL.</span>
      </h3>
      <p class="text-xl text-blue-100/40 mb-12 max-w-lg mx-auto leading-relaxed font-medium">
        Hệ thống AI đề xuất: Bạn cần liệu trình <span class="text-blue-400 font-black">{shopStore.quantity} lọ</span> để đạt hiệu quả tối ưu.
      </p>

      <div class="flex flex-col gap-6 max-w-sm mx-auto">
        <button
          onclick={() => shopStore.openCheckout()}
          class="group relative w-full py-6 bg-blue-600/90 text-white rounded-[2rem] font-black text-2xl shadow-xl overflow-hidden active:scale-[0.98] transition-all duration-500"
        >
          <span class="relative" style:z-index="var(--z-surface)">KÍCH HOẠT PHÁC ĐỒ</span>
          <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700"></div>
        </button>
        <button
          onclick={restart}
          class="text-xs font-black text-white/10 hover:text-blue-400/50 transition-colors uppercase tracking-[0.3em] py-2"
        >
          Thiết lập lại
        </button>
      </div>
    </div>
  {/if}
</div>

<style>
  :global(.clinical-quiz) {
    transition: all 0.8s cubic-bezier(0.23, 1, 0.32, 1);
  }
</style>

