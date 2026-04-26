<script lang="ts">
  import Lock from "lucide-svelte/icons/lock";
  import AlertCircle from "lucide-svelte/icons/alert-circle";

  interface Props {
    title: string;
    requirement: string;
    currentValue: string | number;
    targetValue: string | number;
    colorClass: string;
    onAction?: () => void;
    actionLabel?: string;
  }

  let { title, requirement, currentValue, targetValue, colorClass, onAction, actionLabel }: Props = $props();
</script>

<div class="p-6 rounded-2xl border border-white/5 bg-black/40 backdrop-blur-xl flex flex-col items-center text-center gap-4 group relative overflow-hidden">
  <!-- Grid Background -->
  <div class="absolute inset-0 opacity-[0.03] pointer-events-none" style="background-image: radial-gradient(circle at 2px 2px, white 1px, transparent 0); background-size: 24px 24px;"></div>
  
  <div class="w-16 h-16 rounded-full bg-white/5 border border-white/10 flex items-center justify-center relative group-hover:scale-110 transition-transform duration-500">
    <div class="absolute inset-0 rounded-full blur-xl opacity-20 {colorClass.replace('text-', 'bg-')}"></div>
    <Lock size={24} class="text-white/20 group-hover:text-white/60 transition-colors" />
  </div>

  <div class="flex flex-col gap-1 z-10">
    <h3 class="text-[13px] font-black uppercase tracking-[0.2em] text-white/90">{title}</h3>
    <p class="text-[10px] text-white/40 font-medium px-4">{requirement}</p>
  </div>

  <div class="flex items-center gap-6 py-2 z-10">
    <div class="flex flex-col items-center">
      <span class="text-[8px] font-black text-white/20 uppercase tracking-widest mb-1">Hiện tại</span>
      <span class="text-[14px] font-mono font-bold {colorClass} opacity-60">{currentValue}</span>
    </div>
    <div class="h-8 w-px bg-white/10"></div>
    <div class="flex flex-col items-center">
      <span class="text-[8px] font-black text-white/20 uppercase tracking-widest mb-1">Mục tiêu</span>
      <span class="text-[14px] font-mono font-bold {colorClass}">{targetValue}+</span>
    </div>
  </div>

  {#if onAction}
    <button 
      onclick={onAction}
      class="mt-2 px-6 py-2.5 rounded-xl border border-white/10 bg-white/5 hover:bg-white/10 hover:border-white/20 text-[10px] font-black uppercase tracking-widest text-white/70 hover:text-white transition-all flex items-center gap-2 group/btn z-10"
    >
      <AlertCircle size={12} class="text-white/40 group-hover/btn:text-white" />
      {actionLabel || 'Quay lại bước trước'}
    </button>
  {/if}

  <!-- Status Bar -->
  <div class="absolute bottom-0 left-0 right-0 h-1 bg-white/5 overflow-hidden">
    <div class="h-full {colorClass.replace('text-', 'bg-')} transition-all duration-1000" style="width: {Math.min((Number(currentValue) / Number(targetValue)) * 100, 100)}%"></div>
  </div>
</div>

<style>
  .shadow-glow {
    box-shadow: 0 0 20px rgba(255,255,255,0.05);
  }
</style>
