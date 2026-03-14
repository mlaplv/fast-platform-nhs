<script lang="ts">
  import Sparkles from 'lucide-svelte/icons/sparkles';
  import Check from 'lucide-svelte/icons/check';

  let { 
    visible = $bindable(false), 
    x, 
    y, 
    type, 
    text, 
    isFixing,
    onFix 
  }: {
    visible: boolean;
    x: number;
    y: number;
    type: string;
    text: string;
    isFixing: boolean;
    onFix: () => void;
  } = $props();

  let tooltipEl = $state<HTMLElement | null>(null);

  const isFixed = $derived(type === 'fixed');
  const isInternal = $derived(type === 'internal-dedup');
</script>

{#if visible && (text || isFixed)}
  <div 
    bind:this={tooltipEl}
    class="tiptap-tooltip fixed z-[100001] pointer-events-none transition-opacity duration-150"
    style="left: {x}px; top: {y}px; transform: translate(-50%, -100%)"
  >
    <div class="shadow-2xl border backdrop-blur-xl p-3 text-[10px] leading-relaxed w-64 pointer-events-auto {
      isFixed ? 'bg-emerald-950/95 border-emerald-500/30 text-emerald-100' : 
      isInternal ? 'bg-fuchsia-950/95 border-fuchsia-500/30 text-fuchsia-100' :
      type === 'copyright' || type === 'external' ? 'bg-orange-950/95 border-orange-500/30 text-orange-100' :
      type.startsWith('seo-') || type.includes('seo') ? 'bg-blue-950/95 border-blue-400/30 text-blue-50' :
      'bg-slate-900/95 border-white/10 text-white'
    }">
      <div class="flex flex-col gap-2">
        <div class="flex items-start justify-between gap-3">
          <span class="font-black uppercase tracking-widest opacity-40 shrink-0 text-[8px] mt-0.5">
            {isFixed ? '✨ Hoàn tất' : `PHÂN TÍCH · ${type.replace(/_/g, ' ')}`}
          </span>
          {#if isFixed}
            <span class="text-emerald-400 font-bold bg-emerald-400/10 px-1.5 py-0.5 flex items-center gap-1 shrink-0">
              <Check size={10} /> ĐÃ SỬA
            </span>
          {/if}
        </div>

        <p class="font-medium { isFixed ? 'text-emerald-200/80' : isInternal ? 'text-fuchsia-200/80' : 'text-white/80' }">
          {isFixed ? 'Đoạn văn này đã được Surgical Agent xử lý chuẩn xác.' : text}
        </p>
        
        {#if !isFixed}
          <div class="h-px bg-white/5 my-1"></div>
          <div class="flex items-center justify-between">
            <span class="text-[8px] opacity-30 italic shrink-0">Surgical Agent Ready</span>
            <button 
              class="flex items-center gap-1.5 px-2.5 py-1 bg-white/10 hover:bg-white/20 text-white transition-all font-bold disabled:opacity-40"
              onclick={onFix}
              disabled={isFixing}
            >
              {#if isFixing}
                <span class="inline-block w-2.5 h-2.5 border-2 border-white/20 border-t-white rounded-full animate-spin"></span>
                SỬA...
              {:else}
                <Sparkles size={10} class="text-yellow-400" />
                SỬA LỖI
              {/if}
            </button>
          </div>
        {/if}
      </div>
    </div>
  </div>
{/if}
