<script lang="ts">
  import { onMount, tick } from 'svelte';
  import { fade, fly, scale } from 'svelte/transition';
  import { Sparkles, ArrowRight, ShieldCheck, RefreshCw } from 'lucide-svelte';
  import { SHOP_CONFIG } from '$lib/constants/shop';
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';

  let { product } = $props();
  const shopStore = getShopStore();
  const metadata = $derived(product?.metadata || {});
  const questions = $derived(metadata?.quiz_questions || []);
  
  const labels = $derived({
    headline: metadata.diagnostics_headline || 'CHẨN ĐOÁN CÁ NHÂN HÓA',
    subheadline: metadata.diagnostics_subheadline || `Để hệ thống chẩn đoán của ${SHOP_CONFIG.pharmacy.name} thiết lập liệu trình liều lượng chính xác nhất.`,
    result_headline: (metadata.quiz_result_headline as string) || 'LIỆU TRÌNH OPTIMAL.',
    result_subheadline: (metadata.quiz_result_subheadline as string) || 'Hệ thống AI đề xuất: Bạn cần liệu trình {quantity} lọ để đạt hiệu quả tối ưu.',
    result_cta: (metadata.quiz_result_cta as string) || 'KÍCH HOẠT LIỆU TRÌNH',
    restart_label: (metadata.quiz_restart_label as string) || 'Thiết lập lại'
  });

  let currentStep = $state(0);
  let answers = $state<string[]>([]);
  let showResult = $state(false);
  let isAnalyzing = $state(false);
  let analysisStatus = $state("Đang phân tích tập dữ liệu lâm sàng...");
  let binaryData = $state("0 1 0 1 1 1 0 0 1");

  function nextStep(value: string) {
    answers.push(value);
    if (currentStep < questions.length - 1) {
      currentStep++;
    } else {
      isAnalyzing = true;
      
      // Binary data animation
      const interval = setInterval(() => {
        binaryData = Array.from({ length: 16 }, () => Math.round(Math.random())).join(" ");
      }, 80);

      // Status messages synchronized with desktop (+ richer mobile steps)
      setTimeout(() => analysisStatus = "Đang xử lý cấu trúc sinh trắc học...", 1500);
      setTimeout(() => analysisStatus = "Đang tối ưu hóa liệu trình cá nhân hóa...", 3500);
      setTimeout(() => analysisStatus = "Hoàn tất cấu trúc Optimal. Đang chuẩn bị phác đồ...", 5000);

      setTimeout(() => {
        clearInterval(interval);
        isAnalyzing = false;
        showResult = true;
        
        let recommendedQty = 1;
        if (answers.includes('heavy') || answers.includes('failed')) {
          recommendedQty = 2;
        }

        // Auto-apply promo if exists for the recommended quantity
        const deals = shopStore.product?.metadata?.active_deals;
        const matchingDeal = deals?.find((d: any) => d.buy_qty === recommendedQty);
        
        if (matchingDeal) {
          shopStore.setQuantity(matchingDeal.buy_qty + (matchingDeal.get_qty || 0));
        } else {
          shopStore.setQuantity(recommendedQty);
        }
      }, 6500);
    }
  }

  function restart() {
    currentStep = 0;
    answers = [];
    showResult = false;
    isAnalyzing = false;
    shopStore.setQuantity(1);
  }
</script>

<div class="h-full flex flex-col px-6 pt-[var(--mobile-top-space)] pb-[var(--mobile-bottom-space)] bg-[#030303] relative overflow-hidden" id="diagnostics">
  <!-- HUD Flourish -->
  <div class="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-blue-500/50 to-transparent"></div>
  
  <div class="mt-2 mb-2">
    <div class="inline-flex items-center gap-1.5 px-1.5 py-0.5 bg-blue-500/10 border border-blue-500/20 rounded-full mb-2 backdrop-blur-md">
      <div class="w-1 h-1 rounded-full bg-blue-500 animate-pulse"></div>
      <span class="text-[7px] uppercase tracking-[0.2em] text-blue-400 font-bold italic">System v2.6+</span>
    </div>
    <h2 class="text-xl font-bold text-white leading-tight uppercase tracking-tighter italic tiktok-shadow">
      {@html labels.headline}
    </h2>
  </div>

  <div class="relative flex-1 flex flex-col">
    {#if questions.length > 0}
      {#if isAnalyzing}
        <div class="absolute -inset-x-6 inset-y-0 z-50 flex flex-col items-center justify-center bg-[#030303] overflow-hidden" in:fade={{ duration: 400 }}>
          <!-- Sci-fi Technical Grid -->
          <div class="absolute inset-0 opacity-[0.07] tech-grid">
          </div>
          
          <!-- Biometric Pulses -->
          <div class="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div class="w-64 h-64 border border-blue-500/20 rounded-full animate-ping opacity-20"></div>
            <div class="w-96 h-96 border border-blue-500/10 rounded-full animate-ping opacity-10 biometric-pulse-delayed"></div>
          </div>
          
          <div class="relative z-10 text-center px-4 -mt-20">
            <div class="mb-10 relative">
              <div class="absolute inset-0 bg-blue-500/30 blur-[60px] rounded-full animate-pulse"></div>
              <div class="w-20 h-20 bg-blue-500/10 rounded-full border border-blue-500/40 flex items-center justify-center backdrop-blur-3xl shadow-[0_0_50px_rgba(59,130,246,0.3)] mx-auto relative group">
                <Sparkles class="w-10 h-10 text-blue-400 animate-spin-slow" />
                <div class="absolute -inset-1 border border-blue-500/20 rounded-full animate-[pulse_3s_infinite]"></div>
              </div>
            </div>

            <div class="text-3xl font-black text-white mb-2 tracking-[0.25em] italic uppercase drop-shadow-[0_0_15px_rgba(255,255,255,0.3)]">
              ĐANG PHÂN TÍCH...
            </div>
            
            <div class="text-[10px] text-blue-400 font-bold uppercase tracking-[0.2em] mb-12 h-4 animate-pulse">
              {analysisStatus}
            </div>

            <div class="relative w-64 h-[1px] bg-white/5 mx-auto overflow-hidden">
               <div class="absolute inset-0 bg-gradient-to-r from-transparent via-blue-400 to-transparent animate-[scan_2s_linear_infinite]"></div>
            </div>
          </div>

          <!-- HUD Data Overlays -->
          <div class="absolute top-10 left-6 opacity-30 text-[7px] font-mono text-blue-500/80 space-y-1 text-left">
            <div>HỆ THỐNG: ỔN ĐỊNH</div>
            <div>ĐỘ TRỄ: 12ms</div>
            <div>MÃ HÓA: QUANTUM_V3</div>
          </div>

          <div class="absolute top-10 right-6 opacity-30 text-[7px] font-mono text-blue-500/80 text-right">
            <div>TỌA ĐỘ: {Math.floor(Math.random()*100)}°N, {Math.floor(Math.random()*100)}°E</div>
            <div class="mt-1 flex gap-1 justify-end">
               {#each Array(4) as _, i}
                 <div class="w-1 h-1 rounded-full {i < currentStep + 1 ? 'bg-blue-500' : 'bg-white/10'}"></div>
               {/each}
            </div>
            <div class="mt-1">TRÍ TUỆ NHÂN TẠO: HOẠT ĐỘNG</div>
          </div>

          <!-- Binary Streams -->
          <div class="absolute bottom-10 left-6 opacity-40 text-[6px] font-mono text-blue-400/80 text-left">
            <div class="mb-1 text-white/40">ĐỒNG BỘ_DỮ LIỆU_THUÂN VIỆT</div>
            <div class="tracking-widest">{binaryData}</div>
          </div>

          <div class="absolute bottom-40 right-[-20px] opacity-20 text-[6px] font-mono text-blue-400 rotate-90 origin-left">
            FLOW_CONTROL: {binaryData.split(' ').reverse().join(' ')}
          </div>
        </div>
      {:else if showResult}
        <div class="flex-1 flex flex-col items-center justify-center py-10" in:scale={{ duration: 500, start: 0.9 }}>
          <div class="relative mb-10">
            <div class="absolute inset-0 bg-blue-500/20 blur-[40px] rounded-full animate-pulse"></div>
            <div class="w-24 h-24 bg-blue-500/10 rounded-3xl flex items-center justify-center relative border border-blue-500/30 shadow-[0_0_40px_rgba(59,130,246,0.2)] backdrop-blur-2xl">
              <ShieldCheck class="w-12 h-12 text-blue-400" />
            </div>
          </div>
          
          <h3 class="text-3xl font-bold text-white mb-3 uppercase tracking-tighter italic text-center tiktok-shadow">
            {@html labels.result_headline}
          </h3>
          <p class="text-white/50 text-[9px] mb-8 leading-relaxed font-bold uppercase tracking-[0.15em] text-center max-w-[260px]">
            {@html labels.result_subheadline.replace('{quantity}', shopStore.quantity.toString())}
          </p>
          
          <div class="w-full space-y-3">
            <button 
              onclick={() => shopStore.openCheckout()}
              class="w-full py-5 bg-blue-600 rounded-2xl font-bold text-white text-xs tracking-[0.2em] flex items-center justify-center gap-2 shadow-[0_10px_30px_rgba(37,99,235,0.3)] active:scale-95 transition-all uppercase italic"
            >
              {labels.result_cta} <ArrowRight class="w-4 h-4" />
            </button>
            <button 
              onclick={restart}
              class="flex items-center gap-2 mx-auto py-3 text-[8px] font-bold text-white/30 uppercase tracking-[0.3em] hover:text-blue-400 transition-colors"
            >
              <RefreshCw class="w-2.5 h-2.5" /> {labels.restart_label}
            </button>
          </div>
        </div>
      {:else}
        <div class="grid grid-cols-1 grid-rows-1 flex-1 overflow-hidden h-full">
          {#key currentStep}
            <div 
              class="col-start-1 row-start-1 flex flex-col w-full h-full" 
              in:fly={{ y: 20, duration: 300, delay: 100 }} 
              out:fade={{ duration: 200 }}
            >
              <div class="flex items-center justify-between mb-4 bg-white/5 p-3 rounded-lg border border-white/10 backdrop-blur-3xl shadow-lg">
                <div class="flex flex-col">
                  <span class="text-[6px] text-white/30 uppercase tracking-[0.1em] font-bold">Phase</span>
                  <p class="text-[9px] text-blue-400 uppercase tracking-widest font-bold">Step {currentStep + 1} <span class="text-white/20">/</span> {questions.length}</p>
                </div>
                <div class="relative w-16 h-1 bg-white/5 rounded-full overflow-hidden">
                  <div class="absolute inset-0 bg-blue-500/20 animate-pulse"></div>
                  <div class="absolute top-0 left-0 h-full bg-blue-500 transition-all duration-700 ease-out progress-fill" style:--progress="{((currentStep + 1) / questions.length) * 100}%"></div>
                </div>
              </div>
              
              <h3 class="text-lg font-bold text-white mb-4 leading-tight uppercase italic tracking-tight">
                {typeof questions[currentStep].title === 'string' ? questions[currentStep].title : 'Phân tích'}
              </h3>
              
              <div class="grid gap-2 content-start overflow-y-auto pb-4">
                {#each questions[currentStep].options as opt, idx}
                  <button 
                    onclick={() => nextStep(opt.value)}
                    class="w-full py-2.5 px-4 bg-white/[0.05] border border-white/10 rounded-xl text-left flex items-center gap-3 group active:scale-[0.98] transition-all duration-200"
                  >
                    <div class="w-8 h-8 bg-white/5 rounded-lg flex items-center justify-center text-lg group-hover:bg-blue-500/20 group-hover:text-blue-400 transition-all border border-white/5">
                      {opt.icon || (idx + 1)}
                    </div>
                    <div class="flex flex-col">
                      <span class="text-white/90 font-bold text-[11px] uppercase tracking-tight">
                        {typeof opt.label === 'string' ? opt.label : 'Lựa chọn'}
                      </span>
                      <span class="text-[6px] text-white/20 uppercase tracking-widest font-bold">Select</span>
                    </div>
                  </button>
                {/each}
              </div>
            </div>
          {/key}
        </div>
      {/if}
    {:else}
      <div class="flex-1 flex flex-col items-center justify-center gap-6" in:fade>
        <div class="relative">
          <div class="w-16 h-16 border-2 border-blue-500/10 border-t-blue-500 rounded-full animate-spin"></div>
          <div class="absolute inset-0 flex items-center justify-center">
             <div class="w-2 h-2 bg-blue-500 rounded-full animate-ping"></div>
          </div>
        </div>
        <div class="text-center">
          <p class="text-[10px] font-black text-white/30 uppercase tracking-[0.5em] animate-pulse">Syncing AI Core...</p>
          <p class="text-[8px] text-blue-500/40 uppercase tracking-widest mt-2 font-mono">Status: Secure_Protocol_Active</p>
        </div>
      </div>
    {/if}
  </div>

  <!-- Decorative HUD elements -->
  <div class="absolute bottom-10 left-0 w-32 h-32 bg-blue-500/5 blur-[80px] rounded-full pointer-events-none"></div>
  <div class="absolute top-40 right-0 w-48 h-48 bg-blue-500/5 blur-[100px] rounded-full pointer-events-none"></div>
</div>

<style>
  .tech-grid {
    background-image: linear-gradient(#3b82f6 1px, transparent 1px), linear-gradient(90deg, #3b82f6 1px, transparent 1px);
    background-size: 20px 20px;
  }

  .biometric-pulse-delayed {
    animation-delay: 1s;
  }

  .progress-fill {
    width: var(--progress, 0%);
  }

  .animate-spin-slow {
    animation: spin 3s linear infinite;
  }

  @keyframes scan {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
  }

  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
</style>


