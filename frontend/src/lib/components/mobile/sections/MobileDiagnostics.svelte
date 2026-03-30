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
    subheadline: metadata.diagnostics_subheadline || `Để hệ thống chẩn đoán của ${SHOP_CONFIG.pharmacy.name} thiết lập phác đồ liều lượng chính xác nhất.`,
    result_headline: (metadata.quiz_result_headline as string) || 'PHÁC ĐỒ OPTIMAL.',
    result_subheadline: (metadata.quiz_result_subheadline as string) || 'Hệ thống AI đề xuất: Bạn cần liệu trình {quantity} lọ để đạt hiệu quả tối ưu.',
    result_cta: (metadata.quiz_result_cta as string) || 'KÍCH HOẠT PHÁC ĐỒ',
    restart_label: (metadata.quiz_restart_label as string) || 'Thiết lập lại'
  });

  let currentStep = $state(0);
  let answers = $state<string[]>([]);
  let showResult = $state(false);

  function nextStep(value: string) {
    answers.push(value);
    if (currentStep < questions.length - 1) {
      currentStep++;
    } else {
      showResult = true;
      if (answers.includes('heavy') || answers.includes('failed')) {
        shopStore.setQuantity(2);
      }
    }
  }

  function restart() {
    currentStep = 0;
    answers = [];
    showResult = false;
    shopStore.setQuantity(1);
  }
</script>

<div class="h-full flex flex-col justify-center px-6 py-20 bg-[#050505]" id="diagnostics">
  <div class="mb-10">
    <div class="inline-flex items-center gap-2 px-3 py-1 bg-blue-500/10 border border-blue-500/20 rounded-full mb-4">
      <Sparkles class="w-3 h-3 text-blue-400" />
      <span class="text-[10px] uppercase tracking-widest text-blue-400 font-bold italic">AI Diagnostics</span>
    </div>
    <h2 class="text-3xl font-black text-white leading-tight uppercase tracking-tighter italic">
      {@html labels.headline}
    </h2>
    <p class="mt-4 text-white/40 text-[10px] uppercase tracking-[0.3em] font-medium leading-relaxed">
      {@html labels.subheadline}
    </p>
  </div>

  <div class="relative min-h-[400px]">
    {#if questions.length > 0}
      {#if !showResult}
        {#key currentStep}
          <div in:fly={{ y: 20, duration: 400 }} out:fade>
            <div class="flex items-center justify-between mb-8">
              <p class="text-[10px] text-blue-400/60 uppercase tracking-widest font-black">Step {currentStep + 1} / {questions.length}</p>
              <div class="h-1 w-24 bg-white/5 rounded-full overflow-hidden">
                <div class="h-full bg-blue-500 transition-all duration-500" style="width: {((currentStep + 1) / questions.length) * 100}%"></div>
              </div>
            </div>
            
            <h3 class="text-xl font-bold text-white mb-8 leading-snug">
              {typeof questions[currentStep].title === 'string' ? questions[currentStep].title : 'Phân tích cơ địa'}
            </h3>
            
            <div class="grid gap-3">
              {#each questions[currentStep].options as opt, idx}
                <button 
                  onclick={() => nextStep(opt.value)}
                  class="w-full p-5 bg-white/5 border border-white/10 rounded-2xl text-left flex items-center gap-4 group active:scale-[0.98] transition-all duration-200"
                >
                  <div class="w-10 h-10 bg-white/5 rounded-xl flex items-center justify-center text-xl group-hover:bg-blue-500/20 transition-colors">
                    {opt.icon || (idx + 1)}
                  </div>
                  <span class="text-white/90 font-bold text-sm uppercase tracking-tight">
                    {typeof opt.label === 'string' ? opt.label : 'Lựa chọn'}
                  </span>
                </button>
              {/each}
            </div>
          </div>
        {/key}
      {:else}
        <div class="text-center py-10" in:scale={{ duration: 500, start: 0.9 }}>
          <div class="w-20 h-20 bg-blue-500/20 rounded-full flex items-center justify-center mx-auto mb-8 border border-blue-500/30 shadow-[0_0_30px_rgba(59,130,246,0.2)]">
            <ShieldCheck class="w-10 h-10 text-blue-400" />
          </div>
          <h3 class="text-3xl font-black text-white mb-4 uppercase tracking-tighter italic">
            {@html labels.result_headline}
          </h3>
          <p class="text-white/60 text-[11px] mb-10 leading-relaxed font-bold uppercase tracking-widest">
            {@html labels.result_subheadline.replace('{quantity}', shopStore.quantity.toString())}
          </p>
          
          <div class="space-y-4">
            <button 
              onclick={() => shopStore.openCheckout()}
              class="w-full py-5 bg-blue-600 rounded-2xl font-black text-white text-sm tracking-[0.2em] flex items-center justify-center gap-3 shadow-[0_10px_30px_rgba(37,99,235,0.4)] active:scale-95 transition-transform"
            >
              {labels.result_cta} <ArrowRight class="w-4 h-4" />
            </button>
            <button 
              onclick={restart}
              class="flex items-center gap-2 mx-auto text-[10px] font-black text-white/20 uppercase tracking-[0.3em] hover:text-white/40 transition-colors"
            >
              <RefreshCw class="w-3 h-3" /> {labels.restart_label}
            </button>
          </div>
        </div>
      {/if}
    {:else}
      <div class="h-64 flex flex-col items-center justify-center gap-4" in:fade>
        <div class="w-10 h-10 border-2 border-blue-500/20 border-t-blue-500 rounded-full animate-spin"></div>
        <p class="text-[10px] font-black text-white/20 uppercase tracking-[0.4em]">Initializing AI Engine...</p>
      </div>
    {/if}
  </div>
</div>
