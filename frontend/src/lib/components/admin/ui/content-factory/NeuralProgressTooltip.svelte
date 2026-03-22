<script lang="ts">
  import { fade, slide, fly } from 'svelte/transition';
  import { Sparkles, Brain, Cpu, Loader2, CheckCircle2, Zap } from 'lucide-svelte';
  import { tick } from 'svelte';

  interface Props {
    active: boolean;
    logs: string[];
    status: string;
  }

  let { active, logs = [], status }: Props = $props();

  let scrollContainer: HTMLElement | null = $state(null);

  $effect(() => {
    if (logs.length > 0) {
      tick().then(() => {
        if (scrollContainer) {
          scrollContainer.scrollTo({
            top: scrollContainer.scrollHeight,
            behavior: 'smooth'
          });
        }
      });
    }
  });

  const getIcon = (log: string) => {
    if (log.includes('Lỗi') || log.includes('⚠️')) return 'text-red-400';
    if (log.includes('thành công') || log.includes('✅')) return 'text-emerald-400';
    if (log.includes('AI') || log.includes('phẫu thuật')) return 'text-purple-400';
    if (log.includes('Quét') || log.includes('phát hiện')) return 'text-blue-400';
    return 'text-slate-400';
  };
</script>

{#if active}
  <div 
    class="fixed bottom-24 right-8 z-[200000] w-80 md:w-96 flex flex-col pointer-events-auto"
    in:fly={{ y: 20, duration: 800, opacity: 0 }}
    out:fade={{ duration: 300 }}
  >
    <!-- iOS Style Card -->
    <div class="bg-slate-900/80 backdrop-blur-3xl border border-white/10 rounded-[28px] shadow-[0_32px_64px_-16px_rgba(0,0,0,0.6)] overflow-hidden flex flex-col">
      
      <!-- Header Area -->
      <div class="p-5 flex items-center justify-between border-b border-white/5 bg-white/[0.02]">
        <div class="flex items-center gap-3">
          <div class="relative">
            <div class="absolute -inset-1 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 rounded-full blur opacity-40 animate-pulse"></div>
            <div class="relative w-8 h-8 rounded-full bg-slate-900 flex items-center justify-center border border-white/10">
              <Sparkles size={14} class="text-blue-400" />
            </div>
          </div>
          <div class="flex flex-col">
            <span class="text-[12px] font-black tracking-widest text-white uppercase opacity-80">XOHI</span>
            <span class="text-[10px] font-bold text-blue-400/80 uppercase tracking-tighter">Neural Surgeon v2.2</span>
          </div>
        </div>
        
        <div class="flex items-center gap-2 px-3 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/20">
          <div class="w-1.5 h-1.5 rounded-full bg-blue-400 animate-ping"></div>
          <span class="text-[9px] font-black text-blue-300 uppercase tracking-widest">{status || 'Processing'}</span>
        </div>
      </div>

      <!-- Live Logs Area -->
      <div 
        bind:this={scrollContainer}
        class="max-h-60 overflow-y-auto p-5 space-y-3 custom-scrollbar list-none"
      >
        {#each logs as log, i (i)}
          <div 
            class="flex items-start gap-3 group"
            in:fly={{ x: -10, duration: 400, delay: 50 }}
          >
            <div class="mt-1 shrink-0">
              {#if i === logs.length - 1 && !log.includes('✅') && !log.includes('⚠️')}
                <Loader2 size={12} class="animate-spin text-blue-400" />
              {:else if log.includes('✅') || log.includes('thành công')}
                <CheckCircle2 size={12} class="text-emerald-400" />
              {:else if log.includes('AI') || log.includes('Neural')}
                <Brain size={12} class="text-purple-400" />
              {:else if log.includes('phẫu thuật') || log.includes('quét')}
                <Zap size={12} class="text-yellow-400" />
              {:else}
                <div class="w-1.5 h-1.5 rounded-full bg-white/20 mt-1.5"></div>
              {/if}
            </div>
            
            <p class="text-[11px] leading-relaxed font-medium text-white/70 {i === logs.length - 1 ? 'text-white font-bold opacity-100' : 'opacity-40'} transition-all duration-500">
              {log}
            </p>
          </div>
        {/each}

        {#if logs.length === 0}
            <div class="py-8 flex flex-col items-center justify-center opacity-20">
                <Brain size={32} class="mb-2" />
                <span class="text-[10px] font-black uppercase tracking-[0.2em]">Khởi động Neural Engine...</span>
            </div>
        {/if}
      </div>

      <!-- Progress Bar (iOS Style) -->
      <div class="px-5 pb-5">
        <div class="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
          <div 
            class="h-full bg-gradient-to-r from-blue-500 via-purple-500 to-emerald-500 transition-all duration-1000 ease-out"
            style="width: {logs.length > 0 ? (Math.min(100, (logs.length / 8) * 100)) : 10}%"
          ></div>
        </div>
      </div>
    </div>
    
    <!-- Glossy reflection effect -->
    <div class="absolute inset-0 rounded-[28px] border border-white/20 pointer-events-none opacity-20 bg-gradient-to-tr from-transparent via-white/5 to-white/10"></div>
  </div>
{/if}

<style>
  .custom-scrollbar::-webkit-scrollbar {
    width: 2px;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.1);
  }
</style>
