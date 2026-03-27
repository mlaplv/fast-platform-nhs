<script lang="ts">
  import { shopStore } from '$lib/state/commerce/shop.svelte.ts';
  import { fade, fly } from 'svelte/transition';

  let currentStep = $state(0);
  let answers = $state<string[]>([]);
  let progress = $derived((currentStep / 2) * 100);

  const questions = [
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
      title: "Lịch sử sử dụng sản phẩm?",
      subtitle: "Thông tin này giúp tối ưu hóa nồng độ Nano hoạt tính",
      options: [
        { label: "Chưa từng dùng thuốc", desc: "Cơ địa mới bắt đầu", value: "none", icon: "🌱" },
        { label: "Đã dùng nhưng không hiệu quả", desc: "Cần công thức mạnh hơn", value: "failed", icon: "🛡️" },
        { label: "Sợ bị ố vàng áo & kích ứng", desc: "Cần độ tinh khiết 100%", value: "fear", icon: "👔" }
      ]
    }
  ];

  function nextStep(value: string) {
    answers.push(value);
    if (currentStep < questions.length - 1) {
      currentStep++;
    } else {
      currentStep++; // Show result
      // Logic: If heavy or failed, upsell 2-3 bottles
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

<div class="clinical-quiz glass-premium p-8 md:p-12 rounded-[3.5rem] relative overflow-hidden bg-white/80 backdrop-blur-2xl border border-blue-100/50 shadow-[0_40px_100px_-20px_rgba(37,99,235,0.1)]">
  <!-- Neural Background Element -->
  <div class="absolute -top-24 -right-24 w-64 h-64 bg-blue-500/5 rounded-full blur-[80px] pointer-events-none"></div>
  
  <!-- Progress Bar -->
  <div class="absolute top-0 left-0 right-0 h-1.5 bg-slate-100/50">
    <div 
      class="h-full bg-gradient-to-r from-blue-500 to-indigo-600 transition-all duration-1000 ease-out shadow-[0_0_20px_rgba(37,99,235,0.4)]" 
      style="width: {progress}%"
    ></div>
  </div>

  {#if currentStep < questions.length}
    <div class="step-container" in:fly={{ y: 30, duration: 800, delay: 100 }}>
      <div class="mb-12">
        <div class="inline-flex items-center gap-2 px-3 py-1 bg-blue-50 rounded-full mb-4">
          <span class="flex h-1.5 w-1.5 rounded-full bg-blue-600 animate-pulse"></span>
          <span class="text-blue-600 font-black text-[9px] uppercase tracking-[0.2em]">Neural Diagnostic Mode</span>
        </div>
        <h3 class="text-3xl md:text-4xl font-black text-slate-900 mb-3 tracking-tighter leading-tight">
          {questions[currentStep].title}
        </h3>
        <p class="text-slate-500 font-medium text-lg italic">{questions[currentStep].subtitle}</p>
      </div>

      <div class="grid grid-cols-1 gap-5">
        {#each questions[currentStep].options as option, idx}
          <button
            onclick={() => nextStep(option.value)}
            class="group p-8 text-left bg-white border border-slate-100 rounded-[2rem] hover:border-blue-500 hover:shadow-[0_25px_60px_-15px_rgba(37,99,235,0.15)] transition-all duration-500 flex items-center gap-8 relative overflow-hidden"
          >
            <div class="absolute inset-0 bg-gradient-to-br from-blue-50/0 via-transparent to-blue-50/0 group-hover:from-blue-50/50 transition-all"></div>
            
            <div class="w-20 h-20 bg-slate-50 rounded-[1.5rem] flex items-center justify-center text-4xl group-hover:scale-110 transition-transform duration-500 shadow-inner relative z-10">
              {option.icon}
            </div>
            <div class="flex-1 relative z-10">
              <span class="block text-xl font-black text-slate-900 group-hover:text-blue-600 transition-colors uppercase tracking-tight mb-1">{option.label}</span>
              <span class="text-sm text-slate-400 font-bold uppercase tracking-widest">{option.desc}</span>
            </div>
            <div class="w-10 h-10 rounded-full border-2 border-slate-100 group-hover:border-blue-600 group-hover:bg-blue-600 flex items-center justify-center transition-all duration-500 relative z-10">
              <svg class="w-5 h-5 text-white scale-0 group-hover:scale-100 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="4" d="M5 13l4 4L19 7" />
              </svg>
            </div>
          </button>
        {/each}
      </div>
    </div>
  {:else}
    <div class="result-container text-center py-10" in:fade={{ duration: 1000 }}>
      <div class="relative inline-block mb-12">
        <div class="absolute inset-0 bg-blue-600 blur-[40px] opacity-20 animate-pulse"></div>
        <div class="relative w-32 h-32 bg-slate-950 rounded-[2.5rem] flex items-center justify-center shadow-2xl">
          <svg class="w-16 h-16 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.673.337a4 4 0 01-2.506.326l-1.623-.324a10 10 0 00-5.422.158l-1.315.438a2 2 0 01-2.583-1.98V8.14a2 2 0 011.666-1.97l3.351-.558a10 10 0 015.423.157l1.623.324a4 4 0 002.506-.326l.673-.337A6 6 0 0115.01 5l2.387.477a2 2 0 011.022.547l.951.951a2 2 0 01.559 1.968l-1.012 3.86a2 2 0 01-1.127 1.348l-1.294.518a2 2 0 00-1.127 1.348l-1.012 3.86a2 2 0 01-.559 1.968l-.951-.951z" />
          </svg>
        </div>
      </div>
      
      <h3 class="text-4xl md:text-5xl font-black text-slate-900 mb-6 tracking-tighter leading-none">PHÁC ĐỒ ĐIỀU TRỊ <br/><span class="text-blue-600">RIÊNG BIỆT.</span></h3>
      <p class="text-xl text-slate-600 mb-12 max-w-lg mx-auto leading-relaxed font-medium">
        Dựa trên phân tích sinh trắc học, hệ thống khuyến nghị: Bạn cần liệu trình <span class="text-blue-600 font-black underline decoration-blue-200 decoration-4 underline-offset-4">{shopStore.quantity} lọ</span> để đạt hiệu quả triệt để nhất.
      </p>

      <div class="flex flex-col gap-5 max-w-sm mx-auto">
        <button
          onclick={() => shopStore.openCheckout()}
          class="group relative w-full py-6 bg-blue-600 text-white rounded-[2rem] font-black text-2xl shadow-[0_25px_60px_-10px_rgba(37,99,235,0.4)] overflow-hidden active:scale-95 transition-all"
        >
          <span class="relative z-10 flex items-center justify-center gap-3">
            ÁP DỤNG PHÁC ĐỒ
            <svg class="w-6 h-6 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M14 5l7 7m0 0l-7 7m7-7H3" /></svg>
          </span>
          <div class="absolute inset-0 animate-shimmer"></div>
        </button>
        <button
          onclick={restart}
          class="text-xs font-black text-slate-300 hover:text-blue-500 transition-colors uppercase tracking-[0.2em] py-2"
        >
          Làm mới chuẩn đoán
        </button>
      </div>
    </div>
  {/if}
</div>

<style>
  .clinical-quiz {
    box-shadow: 0 50px 120px -30px rgba(15, 23, 42, 0.08);
  }
  
  .animate-shimmer {
    background: linear-gradient(
      90deg,
      rgba(255, 255, 255, 0) 0%,
      rgba(255, 255, 255, 0.1) 50%,
      rgba(255, 255, 255, 0) 100%
    );
    background-size: 200% 100%;
    animation: shimmer 2s infinite linear;
  }

  @keyframes shimmer {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
  }

  .animate-float {
    animation: float 6s ease-in-out infinite;
  }

  @keyframes float {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-10px); }
  }
</style>

