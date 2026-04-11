<script lang="ts">
  import { onMount, tick } from 'svelte';
  import { fade, fly, scale } from 'svelte/transition';
  import { cubicOut } from 'svelte/easing';
  import { Sparkles, ArrowRight, ShieldCheck, RefreshCw, Cpu, Database, Activity } from 'lucide-svelte';
  import { SHOP_CONFIG } from '$lib/constants/shop';
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import EditableWrapper from '../../admin/EditableWrapper.svelte';

  let { product } = $props();
  const shopStore = getShopStore();
  const metadata = $derived(product?.metadata || {});
  const questions = $derived(metadata?.quiz_questions || []);
  
  const labels = $derived({
    headline: metadata?.diagnostics_headline || 'CHẨN ĐOÁN CÁ NHÂN HÓA',
    subheadline: metadata?.diagnostics_subheadline || `Để hệ thống chẩn đoán của ${SHOP_CONFIG.pharmacy.name} thiết lập liệu trình liều lượng chính xác nhất.`,
    result_headline: metadata?.quiz_result_headline || 'LIỆU TRÌNH OPTIMAL.',
    result_subheadline: metadata?.quiz_result_subheadline || 'Hệ thống AI đề xuất: Bạn cần liệu trình {quantity} lọ để đạt hiệu quả tối ưu.',
    result_cta: metadata?.quiz_result_cta || 'KÍCH HOẠT LIỆU TRÌNH',
    restart_label: metadata?.quiz_restart_label || 'Thiết lập lại'
  });

  let currentStep = $state(0);
  let answers = $state<Array<{q: string, a: string}>>([]);
  let analysisStatus = $state("Đang phân tích tập dữ liệu lâm sàng...");
  let binaryData = $state("0 1 0 1 1 1 0 0 1");
  let activeSlide = $state(0);

  // Memory cleanup for async timers
  const timers = new Set<any>();
  function clearTimers() {
    timers.forEach(t => {
      clearTimeout(t);
      clearInterval(t);
    });
    timers.clear();
  }

  $effect(() => {
    return () => clearTimers();
  });

  // 🚀 Auto-autoplay diagnostic results (Elite V2.2)
  $effect(() => {
    if (shopStore.diagnosticResult && !shopStore.isAnalyzing) {
      const slideInterval = setInterval(() => {
        activeSlide = (activeSlide + 1) % 2;
      }, 5000);
      return () => clearInterval(slideInterval);
    }
  });


  function nextStep(value: string, label: string) {
    answers.push({ q: questions[currentStep].title, a: label });
    if (currentStep < questions.length - 1) {
      currentStep++;
    } else {
      // Binary data animation (visual only)
      const interval = setInterval(() => {
        binaryData = Array.from({ length: 16 }, () => Math.round(Math.random())).join(" ");
      }, 80);
      timers.add(interval);

      // Status messages synchronized with desktop
      timers.add(setTimeout(() => analysisStatus = "Đang xử lý cấu trúc sinh trắc học...", 1500));
      timers.add(setTimeout(() => analysisStatus = "Đang tối ưu hóa liệu trình cá nhân hóa...", 3500));
      timers.add(setTimeout(() => analysisStatus = "Hoàn tất cấu trúc Optimal. Đang chuẩn bị phác đồ...", 5000));

      shopStore.analyzeDiagnostics(answers).then(() => {
        clearInterval(interval);
        timers.delete(interval);
      });
    }
  }

  function restart() {
    currentStep = 0;
    answers = [];
    shopStore.diagnosticResult = null;
    shopStore.isAnalyzing = false;
    shopStore.setQuantity(1);
    activeSlide = 0;
  }
</script>

<div class="h-[100dvh] transition-all duration-700 flex flex-col px-4 pt-[var(--mobile-top-space)] pb-[var(--mobile-bottom-space)] bg-[#030303] relative overflow-hidden" id="diagnostics">
  <!-- HUD Flourish -->
  <div class="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-blue-500/50 to-transparent"></div>
  
  {#if !shopStore.diagnosticResult}
    <div class="mt-2 mb-2" transition:fade>
      <div class="inline-flex items-center gap-1.5 px-1.5 py-0.5 bg-blue-500/10 border border-blue-500/20 rounded-full mb-2 backdrop-blur-md">
        <div class="w-1 h-1 rounded-full bg-blue-500 animate-pulse"></div>
        <span class="text-[7px] uppercase tracking-[0.2em] text-blue-400 font-bold italic">System v2.6+</span>
      </div>
      <EditableWrapper path="metadata.diagnostics_headline" label="SỬA TIÊU ĐỀ" type="html" class="block w-full">
        <h2 class="text-xl font-bold text-white leading-tight uppercase tracking-tighter italic tiktok-shadow">
          {@html labels.headline}
        </h2>
      </EditableWrapper>
    </div>
  {/if}

  <div class="relative flex-1 flex flex-col">
    {#if questions.length > 0}
      {#if shopStore.isAnalyzing}
        <div class="absolute -inset-x-6 inset-y-0 z-modal flex flex-col items-center justify-center bg-[#030303] overflow-hidden" in:fade={{ duration: 400 }}>
          <!-- Sci-fi Technical Grid -->
          <div class="absolute inset-0 opacity-[0.07] tech-grid">
          </div>

          <!-- Biometric Pulses -->
          <div class="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div class="w-64 h-64 border border-blue-500/20 rounded-full animate-ping opacity-20"></div>
            <div class="w-96 h-96 border border-blue-500/10 rounded-full animate-ping opacity-10 biometric-pulse-delayed"></div>
          </div>

          <div class="relative z-surface text-center px-4 -mt-20">
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
            <div class="flex items-center gap-1"><Cpu size={8} /> HỆ THỐNG: ỔN ĐỊNH</div>
            <div class="flex items-center gap-1"><Activity size={8} /> ĐỘ TRỄ: 12ms</div>
            <div class="flex items-center gap-1"><Database size={8} /> MÃ HÓA: QUANTUM_V3</div>
          </div>

          <div class="absolute top-10 right-6 opacity-30 text-[7px] font-mono text-blue-500/80 text-right">
            <div>SIGNAL_STRENGTH: 98%</div>
            <div class="mt-1 flex gap-1 justify-end">
               {#each Array(4) as _, i}
                 <div class="w-1 h-1 rounded-full {i < Math.floor(Math.random()*4)+1 ? 'bg-blue-500' : 'bg-white/10'}"></div>
               {/each}
            </div>
          </div>

          <!-- Binary Streams -->
          <div class="absolute bottom-10 left-6 right-6 opacity-20 text-[6px] font-mono text-blue-400/80 flex justify-between">
            <div class="flex flex-col gap-1">
                <div>AI_LOG_STREAM // START_SYNC</div>
                <div class="tracking-widest">{binaryData}</div>
                <div class="tracking-widest">{binaryData.split(' ').reverse().join(' ')}</div>
            </div>
            <div class="text-right flex flex-col justify-end">
                <div>BIOMETRIC_ENCRYPTION_ACTIVE</div>
                <div>PARALLAX_SYNC_COMPLETE</div>
            </div>
          </div>
        </div>
      {:else if shopStore.diagnosticResult}
        <div class="flex-1 flex flex-col overflow-hidden" in:scale={{ duration: 500, start: 0.9 }}>
          <!-- Scrollable Content Area -->
          <div class="flex-1 overflow-y-auto hide-scrollbar pt-2 pb-4">
            <!-- Result Header HUD -->
            <div class="flex justify-between items-start mb-4 border-b border-white/10 pb-3 shrink-0">
              <div class="flex-1">
                <h3 class="text-xl font-black text-white tracking-tighter uppercase mb-1 drop-shadow-[0_0_15px_rgba(59,130,246,0.5)] italic">
                  PHÁC ĐỒ ĐIỀU TRỊ
                </h3>
                <p class="text-[7px] text-blue-400 font-bold uppercase tracking-[0.3em]">AI MICSMO 2026</p>
              </div>
              <div class="flex items-center gap-2 shrink-0">
               <div class="text-right">
                  <span class="block text-[6px] text-white/30 uppercase font-black">Hiệu lực</span>
                  <span class="block text-[7px] text-emerald-400 uppercase font-bold italic tracking-tighter">An toàn tuyệt đối</span>
               </div>
               <div class="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
                  <ShieldCheck class="w-5 h-5 text-emerald-400" />
               </div>
              </div>
            </div>

            <div class="space-y-6">
              <div class="relative overflow-visible group">
                <div class="flex items-center justify-between mb-2">
                  <h4 class="text-[9px] font-black text-blue-400 group-hover:text-blue-300 transition-colors uppercase tracking-[0.2em] border-l-2 border-blue-500/50 pl-2">
                    PHÂN TÍCH CHUYÊN SÂU
                  </h4>
                  <span class="text-[7px] font-mono text-white/20">LOG_ID: A126-DX</span>
                </div>
                <p class="text-white text-[15px] font-bold leading-relaxed italic px-1 drop-shadow-sm">
                  "{shopStore.diagnosticResult.analysis}"
                </p>
              </div>

              <!-- Info Slider: Tổng quan & Liệu trình -->
              <div class="relative overflow-hidden cursor-grab active:cursor-grabbing" 
                   role="region" 
                   aria-label="Diagnostic Carousel"
              >
                 <div class="flex items-start transition-transform duration-700 ease-[cubic-bezier(0.23,1,0.32,1)]" 
                      style:transform="translateX(-{activeSlide * 100}%)"
                 >
                    <!-- Slide 1: Tổng quan -->
                    <div class="w-full shrink-0 px-1">
                       <div class="flex flex-col gap-2 h-auto max-h-[32dvh] overflow-y-auto hide-scrollbar"
                            style="mask-image: linear-gradient(to bottom, black 80%, transparent 100%);">
                          <h4 class="text-[10px] font-black text-white/40 uppercase tracking-[0.2em] border-l-2 border-white/20 pl-2">01. TỔNG QUAN LÂM SÀNG</h4>
                          <p class="text-white/80 text-[13px] font-medium leading-normal italic">{shopStore.diagnosticResult.reasoning}</p>
                          <div class="h-6"></div> <!-- Spacer for mask -->
                       </div>
                    </div>
                    
                    <!-- Slide 2: Liệu trình -->
                    <div class="w-full shrink-0 px-1">
                       <div class="flex flex-col gap-2 h-auto max-h-[32dvh] overflow-y-auto hide-scrollbar"
                            style="mask-image: linear-gradient(to bottom, black 80%, transparent 100%);">
                          <div class="flex items-center justify-between border-l-2 border-emerald-500/30 pl-2">
                             <h4 class="text-[10px] font-black text-emerald-400/60 uppercase tracking-[0.2em]">02. LIỆU TRÌNH TỐI ƯU</h4>
                             {#if shopStore.diagnosticResult.promotion_label}
                                <span class="px-2 py-0.5 bg-red-500/20 text-red-500 text-[9px] font-black rounded-full animate-pulse">
                                   🎁 {shopStore.diagnosticResult.promotion_label}
                                </span>
                             {/if}
                          </div>
                          <p class="text-emerald-400 text-[14px] font-bold leading-normal italic">{shopStore.diagnosticResult.recommendation}</p>
                          <div class="h-6"></div> <!-- Spacer for mask -->
                       </div>
                    </div>
                 </div>

                 <!-- Paginated Indicators (Liquid Style) -->
                 <div class="flex justify-center gap-2 mt-2">
                    {#each Array(2) as _, i}
                       <button 
                         class="h-1 rounded-full transition-all duration-500 {activeSlide === i ? 'w-8 bg-blue-500 shadow-[0_0_15px_rgba(59,130,246,0.6)]' : 'w-2 bg-white/10'}"
                         onclick={() => activeSlide = i}
                         aria-label="Slide {i + 1}"
                       ></button>
                    {/each}
                 </div>
              </div>
            </div>
          </div>
          
          <!-- Sticky Action Footer (Naked Style) -->
          <div class="flex-none space-y-4 pb-4 mt-auto relative z-modal">
            <button 
              onclick={() => shopStore.openCheckout()}
              class="w-full py-4 bg-blue-600 rounded-2xl font-black text-white text-[13px] tracking-[0.2em] flex items-center justify-center gap-2 active:scale-95 transition-all uppercase italic"
            >
              XEM LIỆU TRÌNH <ArrowRight class="w-4 h-4" />
            </button>
            <button 
              onclick={restart}
              class="flex items-center gap-2 mx-auto py-1 text-[8px] font-bold text-white/30 uppercase tracking-[0.3em] hover:text-blue-400 transition-colors"
            >
              <RefreshCw class="w-2.5 h-2.5" /> Thiết lập lại
            </button>
          </div>
        </div>
      {:else}
        <EditableWrapper path="metadata.quiz_questions" label="QUẢN LÝ BỘ CÂU HỎI" type="quiz" class="flex-1 flex flex-col min-h-0">
          <div class="grid grid-cols-1 grid-rows-1 flex-1 overflow-hidden h-full">
            {#key currentStep}
              <div 
                class="col-start-1 row-start-1 flex flex-col w-full h-full" 
                in:fly={{ x: 20, duration: 600, easing: cubicOut }} 
                out:fade={{ duration: 300 }}
              >
                <div class="flex items-center justify-between mb-4 bg-white/[0.03] p-3 rounded-2xl border border-white/10 backdrop-blur-3xl shadow-lg relative overflow-hidden group">
                  <div class="absolute inset-0 bg-blue-500/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                  <div class="flex flex-col relative z-surface">
                    <span class="text-[6px] text-white/30 uppercase tracking-[0.2em] font-black">AI_PHASE_SEQUENCE</span>
                    <p class="text-[10px] text-blue-400 uppercase tracking-[0.2em] font-black italic mt-0.5">Step {currentStep + 1} <span class="text-white/10">//</span> {questions.length}</p>
                  </div>
                  <div class="relative w-20 h-1.5 bg-white/5 rounded-full overflow-hidden border border-white/5">
                    <div class="absolute inset-0 bg-blue-500/10 animate-pulse"></div>
                    <div class="absolute top-0 left-0 h-full bg-blue-500 transition-all duration-700 cubic-bezier(0.16, 1, 0.3, 1) progress-fill shadow-[0_0_10px_rgba(59,130,246,0.6)]" style:--progress="{((currentStep + 1) / questions.length) * 100}%"></div>
                  </div>
                </div>
                
                <h3 class="text-xl font-bold text-white mb-6 leading-tight uppercase italic tracking-tight drop-shadow-sm">
                  {typeof questions[currentStep].title === 'string' ? questions[currentStep].title : 'Đang tải phác đồ...'}
                </h3>
                
                <div class="grid gap-3 content-start overflow-y-auto pb-8 hide-scrollbar">
                  {#each questions[currentStep].options as opt, idx}
                    <button 
                      onclick={() => nextStep(opt.value, opt.label)}
                      class="w-full py-4 px-5 bg-white/[0.04] border border-white/10 rounded-2xl text-left flex items-center gap-4 group active:scale-[0.97] transition-all duration-300 hover:bg-white/[0.08] hover:border-blue-500/30"
                    >
                      <div class="w-10 h-10 bg-white/5 rounded-xl flex items-center justify-center text-xl group-hover:bg-blue-500/20 group-hover:text-blue-400 transition-all border border-white/5 shadow-inner">
                        {opt.icon || (idx + 1)}
                      </div>
                      <div class="flex flex-col overflow-hidden">
                        <span class="text-white/90 font-black text-xs uppercase tracking-tight truncate">
                          {typeof opt.label === 'string' ? opt.label : 'Lưu trữ...'}
                        </span>
                        <span class="text-[7px] text-white/20 uppercase tracking-[0.3em] font-black mt-0.5 group-hover:text-blue-400/50 transition-colors">SELECT_DATAPOINT</span>
                      </div>
                    </button>
                  {/each}
                </div>
              </div>
            {/key}
          </div>
        </EditableWrapper>
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

  .hide-scrollbar::-webkit-scrollbar {
    display: none;
  }
  .hide-scrollbar {
    -ms-overflow-style: none;
    scrollbar-width: none;
  }

  .z-surface {
    z-index: var(--z-surface, 10);
    position: relative;
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


