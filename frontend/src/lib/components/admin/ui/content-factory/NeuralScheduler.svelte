<script lang="ts">
    import Clock from "@lucide/svelte/icons/clock";
  import Calendar from "@lucide/svelte/icons/calendar";
  import Repeat from "@lucide/svelte/icons/repeat";
  import Zap from "@lucide/svelte/icons/zap";
  import ChevronDown from "@lucide/svelte/icons/chevron-down";
  import Bell from "@lucide/svelte/icons/bell";
  import Globe from "@lucide/svelte/icons/globe";

  interface SchedulingConfig {
    is_active: boolean;
    frequency: 'once' | 'daily' | 'weekly' | 'monthly' | 'custom';
    schedule_at: string; // ISO or HH:mm
    days?: number[]; // [0-6] for weekly, [1-31] for monthly
    timezone: string;
    notifications: boolean;
  }

  interface Props {
    config: Record<string, unknown>;
    onSync?: () => void | Promise<void>;
  }

  let { config = $bindable(), onSync }: Props = $props();

  // Initialize elite scheduling state
  if (!config.scheduling) {
    config.scheduling = {
      is_active: false,
      frequency: 'daily',
      schedule_at: '08:00',
      timezone: 'UTC+7',
      notifications: true
    } as SchedulingConfig;
  }

  const sch = $derived(config.scheduling as SchedulingConfig);

  const frequencies = [
    { id: 'once', label: 'Một lần', icon: '🎯' },
    { id: 'daily', label: 'Hàng ngày', icon: '🌅' },
    { id: 'weekly', label: 'Hàng tuần', icon: '📅' },
    { id: 'monthly', label: 'Hàng tháng', icon: '🗓️' }
  ];

  const weekDays = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'];

  function toggleDay(dayIdx: number) {
    const s = config.scheduling as SchedulingConfig;
    if (!s) return;
    if (!s.days) s.days = [];
    if (s.days.includes(dayIdx)) {
      s.days = s.days.filter(d => d !== dayIdx);
    } else {
      s.days = [...s.days, dayIdx];
    }
    if (onSync) onSync(); // Elite: Auto-sync when day changes
  }

  function toggleActive() {
    const s = config.scheduling as SchedulingConfig;
    if (s) {
      s.is_active = !s.is_active;
      if (onSync) onSync();
    }
  }

  // CNS V82.1: Neural Auto-ON Logic
  // Automatically activate autopilot if parameters are modified
  let initialLoad = true;
  $effect(() => {
    const s = config.scheduling as SchedulingConfig;
    if (initialLoad) {
      initialLoad = false;
      return;
    }
    if (s) {
       // Auto-ON if not active but modified
       if (!s.is_active) {
         s.is_active = true;
       }
       // Elite UX: Auto-Sync changes to backend
       if (onSync) onSync();
    }
  });
</script>

<div class="relative group/scheduler p-8 rounded-[2.5rem] bg-gradient-to-br from-white/[0.03] to-transparent border border-white/5 backdrop-blur-3xl transition-all duration-700 hover:shadow-[0_40px_100px_rgba(0,0,0,0.5)] overflow-hidden">
  
  <!-- Content Aura -->
  <div class="absolute -top-32 -right-32 w-64 h-64 bg-blue-500/10 blur-[80px] rounded-full group-hover/scheduler:bg-blue-400/20 transition-all duration-1000"></div>
  
  <div class="flex items-center justify-between mb-8 relative z-10">
    <div class="flex items-center gap-4">
      <div class="w-12 h-12 rounded-2xl bg-gradient-to-br from-blue-600 to-indigo-500 flex items-center justify-center shadow-2xl shadow-blue-500/20">
        <Repeat size={22} class="text-white" />
      </div>
      <div>
        <h4 class="text-sm font-black uppercase tracking-[0.2em] text-white">Neural Autopilot</h4>
        <div class="flex items-center gap-1.5 mt-1">
          <div class="w-1.5 h-1.5 rounded-full {sch.is_active ? 'bg-green-500 animate-pulse' : 'bg-white/20'}"></div>
          <p class="text-[10px] text-white/40 font-bold uppercase tracking-widest">
            {sch.is_active ? 'Live Deployment Active' : 'Manual Mode'}
          </p>
        </div>
      </div>
    </div>

    <!-- Pro Toggle -->
    <button 
      onclick={toggleActive}
      class="relative w-16 h-8 rounded-full transition-all duration-500 {sch.is_active ? 'bg-blue-500 shadow-[0_0_20px_rgba(59,130,246,0.4)]' : 'bg-white/5 border border-white/10'}"
    >
      <div class="absolute top-1 left-1 w-6 h-6 rounded-full bg-white shadow-2xl transition-all duration-500 transform {sch.is_active ? 'translate-x-8' : 'translate-x-0'}"></div>
    </button>
  </div>

  {#if sch.is_active}
    <div class="space-y-8 relative z-10 animate-in fade-in zoom-in-95 duration-700">
      
      <!-- Frequency Segment -->
      <div class="p-1.5 rounded-2xl bg-black/40 border border-white/5 flex gap-1 shadow-inner">
        {#each frequencies as freq}
          <button
            onclick={() => sch.frequency = freq.id as any}
            class="flex-1 flex items-center justify-center gap-2 py-3 rounded-xl transition-all duration-500 {sch.frequency === freq.id ? 'bg-white/10 text-white shadow-lg' : 'text-white/30 hover:text-white/60'}"
          >
            <span class="text-xs">{freq.icon}</span>
            <span class="text-[9px] font-black uppercase tracking-widest">{freq.label}</span>
          </button>
        {/each}
      </div>

      <!-- Contextual Controls -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- Time Selection -->
        <div class="p-5 rounded-3xl bg-white/[0.02] border border-white/5 space-y-3 transition-all hover:bg-white/[0.05]">
          <div class="flex items-center gap-2 text-white/40">
            <Clock size={12} />
            <span class="text-[9px] font-black uppercase tracking-[0.2em]">Khởi chạy lúc</span>
          </div>
          <div class="flex items-end gap-2">
            <input 
              type="time" 
              bind:value={sch.schedule_at}
              class="bg-transparent text-3xl font-black text-white outline-none [color-scheme:dark] tracking-tighter"
            />
            <span class="text-[10px] text-blue-400 font-black mb-1.5 tracking-widest">{sch.timezone}</span>
          </div>
        </div>

        <!-- Notification & Sync -->
        <div class="p-5 rounded-3xl bg-white/[0.02] border border-white/5 space-y-3 transition-all hover:bg-white/[0.05]">
          <div class="flex items-center gap-2 text-white/40">
            <Bell size={12} />
            <span class="text-[9px] font-black uppercase tracking-[0.2em]">Thông báo & Sync</span>
          </div>
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-1.5">
              <Globe size={14} class="text-indigo-400" />
              <span class="text-[11px] font-bold text-white/80">Global Sync</span>
            </div>
            <button 
              onclick={() => sch.notifications = !sch.notifications}
              class="w-8 h-4 rounded-full bg-white/5 border border-white/10 relative"
            >
              <div class="absolute top-0.5 left-0.5 w-3 h-3 rounded-full {sch.notifications ? 'bg-blue-400 translate-x-4' : 'bg-white/20 translate-x-0'} transition-all"></div>
            </button>
          </div>
        </div>
      </div>

      <!-- Weekly Selection -->
      {#if sch.frequency === 'weekly'}
        <div class="space-y-3 pt-2">
          <label class="text-[9px] text-white/40 font-black uppercase tracking-[0.2em] ml-1">Lặp lại vào các thứ</label>
          <div class="flex gap-2">
            {#each weekDays as day, i}
              <button
                onclick={() => toggleDay(i)}
                class="w-10 h-10 rounded-xl border font-black text-[10px] transition-all duration-500
                {(sch.days || []).includes(i) ? 'bg-blue-500 border-blue-400 text-white shadow-lg shadow-blue-500/20 scale-110' : 'bg-white/5 border-transparent text-white/30 hover:bg-white/10'}"
              >
                {day}
              </button>
            {/each}
          </div>
        </div>
      {/if}

      <!-- Monthly Selection -->
      {#if sch.frequency === 'monthly'}
        <div class="space-y-3 pt-2">
          <label class="text-[9px] text-white/40 font-black uppercase tracking-[0.2em] ml-1">Vào ngày trong tháng</label>
          <div class="grid grid-cols-7 gap-2">
            {#each Array(31).fill(0) as _, i}
              {@const dayNum = i + 1}
              <button
                onclick={() => toggleDay(dayNum)}
                class="aspect-square rounded-xl border font-black text-[10px] transition-all duration-500
                {(sch.days || []).includes(dayNum) ? 'bg-blue-500 border-blue-400 text-white shadow-lg shadow-blue-500/20 scale-110' : 'bg-white/5 border-transparent text-white/30 hover:bg-white/10'}"
              >
                {dayNum}
              </button>
            {/each}
          </div>
        </div>
      {/if}

      <!-- Intelligence Pulse -->
      <div class="p-4 rounded-2xl bg-blue-500/5 border border-blue-500/10 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <Zap size={14} class="text-amber-400 animate-pulse" />
          <span class="text-[10px] font-black uppercase tracking-[0.15em] text-white/60 underline decoration-blue-500/30">Next Session: Tomorrow 08:00 AM</span>
        </div>
        <ChevronDown size={14} class="text-white/20" />
      </div>
    </div>
  {:else}
    <div class="py-12 flex flex-col items-center justify-center opacity-20 group-hover/scheduler:opacity-40 transition-opacity duration-1000 space-y-4">
      <div class="w-16 h-16 rounded-full border-2 border-dashed border-white/20 flex items-center justify-center">
        <Calendar size={32} strokeWidth={1} />
      </div>
      <div class="text-center">
        <p class="text-[10px] font-black uppercase tracking-[0.3em]">Autopilot Standby</p>
        <p class="text-[8px] text-white/40 font-bold mt-1 uppercase">Ready for Elite Scheduling</p>
      </div>
    </div>
  {/if}
</div>
