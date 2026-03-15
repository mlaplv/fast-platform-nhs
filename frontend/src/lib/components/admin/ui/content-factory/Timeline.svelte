<script lang="ts">
  import {
    Sparkles,
    Image as ImageIcon,
    FileText,
    Rocket,
    Check
  } from "lucide-svelte";
  import { vuiController } from "$lib/vui";

  let { 
    step = 1,
    viewingStep = $bindable(),
    isEditing = $bindable()
  } = $props();
</script>

{#if step > 1}
<div class="hidden md:block mb-12 px-6 relative z-10 w-full max-w-5xl mx-auto">
  <div class="relative z-10 flex items-start">
    {#each [
      { s: 1, icon: Sparkles, label: "Ý tưởng", desc: "Brainstorming" },
      { s: 2, icon: ImageIcon, label: "Hình ảnh", desc: "Asset Hunt" },
      { s: 3, icon: FileText, label: "Dàn bài", desc: "Architecture" },
      { s: 4, icon: FileText, label: "Nội dung", desc: "Creative Pen" },
      { s: 5, icon: Check, label: "Kiểm tra", desc: "Plagiarism Cop" },
      { s: 6, icon: Rocket, label: "Xuất bản", desc: "Media & SEO" }
    ] as phase, i}
      {@const isPast = phase.s < viewingStep}
      {@const isCurrent = phase.s === viewingStep}
      {@const isFuture = phase.s > viewingStep}
      {@const isUnlocked = phase.s <= step}
      
      <button
        type="button"
        disabled={!isUnlocked}
        onclick={() => { 
          viewingStep = phase.s; 
          isEditing = false; 
          vuiController.speak(`Đã chuyển sang bước ${phase.label}.`);
        }}
        class="group flex flex-col items-center gap-3 relative disabled:cursor-not-allowed outline-none shrink-0"
      >
        <div class="relative">
          <div class="absolute -inset-2 rounded-full blur-xl transition-opacity duration-700 {isCurrent ? 'bg-blue-500/40 opacity-100' : 'bg-transparent opacity-0'}"></div>
          <div class="w-12 h-12 rounded-full flex items-center justify-center transition-all duration-700 border backdrop-blur-xl relative z-10 {isCurrent ? 'bg-blue-600/90 border-blue-400 text-white shadow-[0_0_30px_rgba(59,130,246,0.5)] scale-110' : isPast ? 'bg-blue-900/60 border-blue-500/50 text-blue-200 cursor-pointer hover:bg-blue-800/80 shadow-[0_0_15px_rgba(59,130,246,0.3)]' : 'bg-white/5 border-white/10 text-white/20'} {!isFuture && isUnlocked ? 'hover:scale-110 active:scale-95' : ''}">
            {#if isCurrent}
               <div class="absolute inset-0 rounded-full bg-blue-400/20 animate-ping"></div>
               <div class="absolute -inset-1 rounded-full border border-blue-400/20 animate-pulse"></div>
            {/if}
            {#if isPast}
               <Check size={20} strokeWidth={3} class="animate-in zoom-in spin-in-12 duration-500" />
            {:else}
               <phase.icon size={isCurrent ? 22 : 18} strokeWidth={isCurrent ? 2.5 : 2} class="relative z-10 transition-all duration-500 {isCurrent ? 'rotate-[10deg]' : 'opacity-80'}" />
            {/if}
          </div>
          <div class="absolute -bottom-1 left-1/2 -translate-x-1/2 w-1.5 h-1.5 rounded-full transition-all duration-500 {isCurrent ? 'bg-blue-400 shadow-[0_0_10px_#60a5fa] scale-100' : 'bg-transparent scale-0'}"></div>
        </div>

        <div class="flex flex-col items-center transition-all duration-500 {isCurrent ? 'translate-y-1' : ''}">
          <span class="text-[9px] font-black uppercase tracking-[0.25em] transition-colors duration-500 {isCurrent ? 'text-blue-400' : isPast ? 'text-blue-300/40' : 'text-white/10'}">Step 0{phase.s}</span>
          <span class="text-[14px] font-black tracking-wide transition-colors duration-500 mt-0.5 {isCurrent ? 'text-white' : isPast ? 'text-white/60' : 'text-white/20'}">{phase.label}</span>
          {#if isCurrent}
            <span class="text-[8px] font-black uppercase tracking-wider text-blue-400/50 absolute -bottom-4 animate-in fade-in slide-in-from-top-1 duration-700 whitespace-nowrap bg-blue-500/5 px-2 py-0.5 rounded-full border border-blue-500/10">{phase.desc}</span>
          {/if}
        </div>
      </button>

      {#if i < 5}
         {@const isLinePast = (i + 1) < viewingStep}
         {@const isLineCurrent = (i + 1) === viewingStep}
         <div class="flex-1 h-[2px] mt-6 -translate-y-1/2 mx-2 transition-all duration-700 {isLinePast ? 'bg-gradient-to-r from-blue-600 to-cyan-400 shadow-[0_0_10px_rgba(37,99,235,0.4)]' : isLineCurrent ? 'bg-gradient-to-r from-blue-600 to-white/10' : 'bg-white/5'} rounded-full"></div>
      {/if}
    {/each}
  </div>
</div>
{/if}
