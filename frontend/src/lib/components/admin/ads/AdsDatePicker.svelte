<script lang="ts">
  import { fade } from 'svelte/transition';
  import ChevronLeft from "@lucide/svelte/icons/chevron-left";
  import ChevronRight from "@lucide/svelte/icons/chevron-right";

  let { value = $bindable(), label = "", align = "right" } = $props();

  let isOpen = $state(false);
  let viewDate = $state(value ? new Date(value) : new Date());
  if (isNaN(viewDate.getTime())) viewDate = new Date();

  const months = [
    "Tháng 1", "Tháng 2", "Tháng 3", "Tháng 4", "Tháng 5", "Tháng 6",
    "Tháng 7", "Tháng 8", "Tháng 9", "Tháng 10", "Tháng 11", "Tháng 12"
  ];

  const daysOfWeek = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"];

  let days = $derived.by(() => {
    const year = viewDate.getFullYear();
    const month = viewDate.getMonth();
    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    
    // Adjust first day to start from Monday (T2)
    const offset = firstDay === 0 ? 6 : firstDay - 1;
    
    const result = [];
    for (let i = 0; i < offset; i++) result.push(null);
    for (let i = 1; i <= daysInMonth; i++) result.push(new Date(year, month, i));
    return result;
  });

  function selectDate(d: Date) {
    value = d.toISOString().split('T')[0];
    isOpen = false;
  }

  function changeMonth(delta: number) {
    viewDate = new Date(viewDate.getFullYear(), viewDate.getMonth() + delta, 1);
  }

  function changeYear(year: number) {
    viewDate = new Date(year, viewDate.getMonth(), 1);
  }

  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: 5 }, (_, i) => currentYear - i);

  function toggle() { isOpen = !isOpen; }
</script>

<div class="relative w-full group">
  <span class="text-[8px] text-slate-600 font-black mb-2 block uppercase">{label}</span>
  <button 
    class="w-full bg-black/60 border border-white/10 rounded-none p-4 text-[11px] font-black text-white text-left focus:border-cyan-400/50 outline-none transition-all shadow-inner flex justify-between items-center"
    onclick={toggle}
  >
    <span>{value || "Chọn ngày..."}</span>
    <div class="w-1.5 h-1.5 rounded-none bg-cyan-400/30 group-hover:bg-cyan-400 transition-colors"></div>
  </button>

  {#if isOpen}
    <div 
      class="absolute top-full {align === 'left' ? 'left-0' : 'right-0'} mt-2 w-[280px] bg-[#0f0f0f] border border-white/10 shadow-[0_40px_100px_rgba(0,0,0,0.9)] z-[2000] p-4 rounded-none backdrop-blur-3xl"
      transition:fade={{duration: 150}}
    >
      <!-- HEADER: Month/Year selector -->
      <div class="flex items-center justify-between mb-4 border-b border-white/5 pb-3">
        <button class="p-1 hover:text-cyan-400" onclick={() => changeMonth(-1)}><ChevronLeft size={16} /></button>
        
        <div class="flex flex-col items-center">
           <div class="text-[10px] font-black text-white uppercase tracking-widest">{months[viewDate.getMonth()]}</div>
           <select 
             class="bg-transparent text-[10px] text-slate-500 font-mono outline-none border-none cursor-pointer hover:text-white transition-colors"
             value={viewDate.getFullYear()}
             onchange={(e) => changeYear(parseInt(e.currentTarget.value))}
           >
             {#each Array.from({length: 10}, (_, i) => currentYear - i) as y}
               <option value={y} class="bg-[#0f0f0f] text-white">{y}</option>
             {/each}
           </select>
        </div>

        <button class="p-1 hover:text-cyan-400" onclick={() => changeMonth(1)}><ChevronRight size={16} /></button>
      </div>

      <!-- DAYS GRID -->
      <div class="grid grid-cols-7 gap-1 mb-2">
        {#each daysOfWeek as dw}
          <div class="text-[8px] text-slate-600 font-black text-center py-1">{dw}</div>
        {/each}
      </div>

      <div class="grid grid-cols-7 gap-1">
        {#each days as day}
          {#if day}
            {@const isSelected = value === day.toISOString().split('T')[0]}
            {@const isToday = new Date().toDateString() === day.toDateString()}
            <button 
              class="aspect-square text-[10px] font-mono flex items-center justify-center transition-all
                {isSelected ? 'bg-cyan-500 text-black font-black' : 'hover:bg-white/5 text-slate-400'}
                {isToday && !isSelected ? 'text-cyan-400 border border-cyan-400/30' : ''}"
              onclick={() => selectDate(day)}
            >
              {day.getDate()}
            </button>
          {:else}
            <div class="aspect-square"></div>
          {/if}
        {/each}
      </div>

      <!-- QUICK YEARS -->
      <div class="mt-4 pt-3 border-t border-white/5 flex flex-wrap gap-2">
         {#each years as y}
            <button 
               class="px-2 py-1 text-[8px] font-black font-mono border border-white/5 hover:border-cyan-400/50 transition-all {viewDate.getFullYear() === y ? 'text-cyan-400' : 'text-slate-600'}"
               onclick={() => changeYear(y)}
            >
               {y}
            </button>
         {/each}
      </div>
    </div>
  {/if}
</div>

<style>
  /* Custom scrollbar for year dropdown if needed */
  select::-webkit-scrollbar { width: 4px; }
  select::-webkit-scrollbar-track { background: transparent; }
  select::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); }
</style>
