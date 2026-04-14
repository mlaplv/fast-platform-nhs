<script lang="ts">
  import { fade, fly, scale } from 'svelte/transition';
  import { cn } from '$lib/utils/cn';
  import { ChevronLeft, ChevronRight, Clock, Calendar as CalendarIcon, Check } from 'lucide-svelte';

  let { 
    value = $bindable(''), 
    min = '', 
    onSelect 
  } = $props();

  // 🚀 ELITE STATE: Svelte 5 Runes
  let viewDate = $state(new Date());
  if (value) viewDate = new Date(value);

  let selectedDate = $derived(value ? new Date(value) : null);
  let showTime = $state(false);

  const daysOfWeek = ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7'];
  const months = [
    'Tháng 1', 'Tháng 2', 'Tháng 3', 'Tháng 4', 'Tháng 5', 'Tháng 6',
    'Tháng 7', 'Tháng 8', 'Tháng 9', 'Tháng 10', 'Tháng 11', 'Tháng 12'
  ];

  // Logic: Calendar Grid
  const calendarDays = $derived.by(() => {
    const year = viewDate.getFullYear();
    const month = viewDate.getMonth();
    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    
    const days = [];
    // Padding for previous month
    const prevMonthLastDate = new Date(year, month, 0).getDate();
    for (let i = firstDay; i > 0; i--) {
      days.push({ day: prevMonthLastDate - i + 1, month: month - 1, current: false });
    }
    // Current month
    for (let i = 1; i <= daysInMonth; i++) {
      days.push({ day: i, month, current: true });
    }
    // Padding for next month
    const remaining = 42 - days.length;
    for (let i = 1; i <= remaining; i++) {
      days.push({ day: i, month: month + 1, current: false });
    }
    return days;
  });

  function changeMonth(delta: number) {
    const d = new Date(viewDate);
    d.setMonth(d.getMonth() + delta);
    viewDate = d;
  }

  function selectDay(day: number, month: number) {
    const d = new Date(viewDate);
    d.setMonth(month);
    d.setDate(day);
    updateValue(d);
    showTime = true; // Automatically shift focus to time
  }

  function updateValue(date: Date) {
    // Keep time if existing
    if (value) {
        const old = new Date(value);
        date.setHours(old.getHours());
        date.setMinutes(old.getMinutes());
    } else {
        date.setHours(9, 0, 0, 0); // Default 9 AM
    }
    
    // Format to local datetime-local string (yyyy-MM-ddThh:mm)
    const tzoffset = date.getTimezoneOffset() * 60000;
    value = new Date(date.getTime() - tzoffset).toISOString().slice(0, 16);
    if (onSelect) onSelect(value);
  }

  function handleTimeChange(type: 'h' | 'm', val: number) {
    if (!value) updateValue(new Date());
    const d = new Date(value);
    if (type === 'h') d.setHours(val);
    else d.setMinutes(val);
    updateValue(d);
  }

  let hours = $derived(value ? new Date(value).getHours() : 9);
  let mins = $derived(value ? new Date(value).getMinutes() : 0);
  let isPM = $derived(hours >= 12);
  let displayHour = $derived(hours % 12 || 12);

</script>

<div class="viral-datepicker-container">
  <!-- Header: Month/Year -->
  <div class="flex items-center justify-between p-4 border-b border-white/5">
    <div class="flex items-center gap-3">
        <button 
            type="button"
            class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 transition-colors text-xs font-bold text-white uppercase italic"
            onclick={() => showTime = !showTime}
        >
            {#if showTime}
                <CalendarIcon class="w-3.5 h-3.5 text-pink-400" />
                Dịp Ngày
            {:else}
                <Clock class="w-3.5 h-3.5 text-sky-400" />
                Giờ Giao
            {/if}
        </button>
        <div class="text-sm font-black text-white uppercase tracking-tighter">
            {months[viewDate.getMonth()]} {viewDate.getFullYear()}
        </div>
    </div>
    <div class="flex items-center gap-1">
      <button type="button" onclick={() => changeMonth(-1)} class="nav-btn"><ChevronLeft class="w-4 h-4" /></button>
      <button type="button" onclick={() => changeMonth(1)} class="nav-btn"><ChevronRight class="w-4 h-4" /></button>
    </div>
  </div>

  <div class="relative overflow-hidden min-h-[280px]">
    <!-- Calendar View -->
    {#if !showTime}
      <div 
        class="p-4 grid grid-cols-7 gap-1"
        in:fly={{ x: -20, duration: 300 }}
        out:fly={{ x: 20, duration: 300 }}
      >
        {#each daysOfWeek as day}
          <div class="text-[10px] font-black text-slate-500 text-center pb-2">{day}</div>
        {/each}
        
        {#each calendarDays as { day, month, current }}
          {@const isSelected = selectedDate?.getDate() === day && selectedDate?.getMonth() === month && selectedDate?.getFullYear() === viewDate.getFullYear()}
          {@const isToday = new Date().getDate() === day && new Date().getMonth() === month && new Date().getFullYear() === viewDate.getFullYear()}
          <button
            type="button"
            onclick={() => selectDay(day, month)}
            class={cn(
              "relative h-9 rounded-lg text-xs font-bold transition-all flex items-center justify-center group",
              current ? "text-slate-200" : "text-slate-600",
              isSelected ? "bg-sky-500 text-white shadow-[0_0_15px_rgba(14,165,233,0.4)] z-10" : "hover:bg-white/10"
            )}
          >
            {day}
            {#if isToday && !isSelected}
                <div class="absolute bottom-1 w-1 h-1 bg-pink-500 rounded-full"></div>
            {/if}
          </button>
        {/each}
      </div>
    {:else}
      <!-- Time View -->
      <div 
        class="absolute inset-0 p-8 flex flex-col items-center justify-center gap-8"
        in:fly={{ x: 20, duration: 300 }}
        out:fly={{ x: -20, duration: 300 }}
      >
        <div class="flex items-center gap-4">
            <div class="flex flex-col items-center gap-2">
                <div class="text-[10px] font-black text-slate-500 uppercase italic">Giờ</div>
                <div class="flex flex-col gap-1 items-center">
                    <button type="button" class="time-nav" onclick={() => handleTimeChange('h', (hours + 1) % 24)}>▲</button>
                    <div class="text-4xl font-black text-white px-4 py-2 bg-white/5 rounded-xl border border-white/10">
                        {displayHour.toString().padStart(2, '0')}
                    </div>
                    <button type="button" class="time-nav" onclick={() => handleTimeChange('h', (hours + 23) % 24)}>▼</button>
                </div>
            </div>
            <div class="text-4xl font-black text-sky-500 pt-6">:</div>
            <div class="flex flex-col items-center gap-2">
                <div class="text-[10px] font-black text-slate-500 uppercase italic">Phút</div>
                <div class="flex flex-col gap-1 items-center">
                    <button type="button" class="time-nav" onclick={() => handleTimeChange('m', (mins + 5) % 60)}>▲</button>
                    <div class="text-4xl font-black text-white px-4 py-2 bg-white/5 rounded-xl border border-white/10">
                        {mins.toString().padStart(2, '0')}
                    </div>
                    <button type="button" class="time-nav" onclick={() => handleTimeChange('m', (mins + 55) % 60)}>▼</button>
                </div>
            </div>
            <div class="flex flex-col items-center gap-2 ml-4">
                <div class="text-[10px] font-black text-slate-500 uppercase italic">AM/PM</div>
                <button 
                    type="button"
                    onclick={() => handleTimeChange('h', isPM ? hours - 12 : hours + 12)}
                    class="h-full px-4 py-2 bg-white/5 border border-white/10 rounded-xl text-lg font-black text-white hover:bg-sky-500/20 transition-all"
                >
                    {isPM ? 'PM' : 'AM'}
                </button>
            </div>
        </div>

        <button 
            type="button" 
            onclick={() => showTime = false}
            class="flex items-center gap-2 px-6 py-2 bg-sky-500 text-white rounded-full font-black text-[10px] tracking-widest shadow-lg hover:scale-105 active:scale-95 transition-all"
        >
            <Check class="w-3 h-3" /> XÁC NHẬN GIỜ
        </button>
      </div>
    {/if}
  </div>
</div>

<style>
  @reference "../../../../routes/layout.css";

  .viral-datepicker-container {
    background: rgba(15, 23, 42, 0.4);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    backdrop-filter: blur(12px);
    overflow: hidden;
  }

  .nav-btn {
    @apply p-2 text-slate-400 hover:text-white hover:bg-white/10 rounded-lg transition-all;
  }

  .time-nav {
    @apply text-slate-600 hover:text-sky-400 transition-colors text-xs font-black p-1;
  }

  /* Utility if needed */
  :global(.group:hover .group-hover\:scale-110) {
    transform: scale(1.1);
  }
</style>
