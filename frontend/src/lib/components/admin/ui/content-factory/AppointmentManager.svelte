<script lang="ts">
    import CalendarIcon from "@lucide/svelte/icons/calendar";
  import Plus from "@lucide/svelte/icons/plus";
  import ChevronRight from "@lucide/svelte/icons/chevron-right";
  import Clock from "@lucide/svelte/icons/clock";
  import User from "@lucide/svelte/icons/user";
  import { onMount } from "svelte";

  interface Appointment {
    id: string;
    title: string;
    start_time: string;
    type: 'strategy' | 'deployment' | 'review';
    attendees: string[];
  }

  interface Props {
    config: Record<string, unknown>;
  }

  let { config = $bindable() }: Props = $props();

  // Initialize appointments if missing
  if (!config.appointments) {
    config.appointments = [
      { id: '1', title: 'Neural Strategy Sync', start_time: '2026-03-25T10:00:00', type: 'strategy', attendees: ['AI Agent Alpha', 'Sếp'] },
    ];
  }

  const appointments: Appointment[] = $derived(config.appointments || []);

  function addAppointment() {
    const newAppt: Appointment = {
      id: Math.random().toString(36).substr(2, 9),
      title: 'New Neural Session',
      start_time: new Date().toISOString(),
      type: 'strategy',
      attendees: ['Sếp']
    };
    config.appointments = [...appointments, newAppt];
  }

  function formatTime(iso: string) {
    return new Date(iso).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
  }
</script>

<div class="relative p-6 rounded-[2.5rem] bg-gradient-to-br from-white/[0.03] to-transparent border border-white/5 backdrop-blur-3xl overflow-hidden group/calendar transition-all duration-700 hover:shadow-[0_40px_100px_rgba(0,0,0,0.4)]">
  <!-- Neural Aura -->
  <div class="absolute -bottom-20 -left-20 w-64 h-64 bg-fuchsia-500/10 blur-[80px] rounded-full group-hover/calendar:bg-fuchsia-400/20 transition-all duration-1000"></div>

  <div class="flex items-center justify-between mb-8 relative z-10">
    <div class="flex items-center gap-4">
      <div class="w-12 h-12 rounded-[1.25rem] bg-white/[0.03] border border-white/10 flex items-center justify-center text-fuchsia-400 shadow-inner">
        <CalendarIcon size={22} strokeWidth={1.5} />
      </div>
      <div>
        <h3 class="text-lg font-black tracking-tight text-white leading-none mb-1">Elite Calendar</h3>
        <p class="text-[10px] text-white/30 font-black tracking-[0.2em]">Neural Session Manager</p>
      </div>
    </div>
    
    <button 
      onclick={addAppointment}
      class="w-10 h-10 rounded-full bg-white text-black flex items-center justify-center hover:scale-110 active:scale-95 transition-all shadow-[0_10px_30px_rgba(255,255,255,0.2)]"
    >
      <Plus size={20} strokeWidth={3} />
    </button>
  </div>

  <!-- Upcoming Sessions List -->
  <div class="space-y-3 relative z-10">
    {#each appointments as appt}
      <div class="group/item relative flex items-center gap-4 p-4 rounded-3xl bg-white/[0.02] border border-white/5 transition-all duration-500 hover:bg-white/[0.05] hover:border-fuchsia-500/20 hover:translate-x-1 cursor-pointer">
        <!-- Time Badge -->
        <div class="flex flex-col items-center justify-center px-3 py-2 rounded-2xl bg-black/40 border border-white/5 min-w-[60px]">
          <span class="text-[12px] font-black text-white leading-none">{formatTime(appt.start_time)}</span>
          <span class="text-[8px] font-black text-fuchsia-400 tracking-tighter mt-1">Today</span>
        </div>

        <div class="flex-1">
          <h4 class="text-[13px] font-bold text-white/90 group-hover/item:text-white transition-colors tracking-tight">{appt.title}</h4>
          <div class="flex items-center gap-3 mt-1.5">
            <div class="flex items-center gap-1 text-[10px] text-white/30">
              <User size={10} />
              <span>{appt.attendees.length} Attendees</span>
            </div>
            <div class="w-1 h-1 rounded-full bg-white/10"></div>
            <div class="flex items-center gap-1 text-[10px] text-fuchsia-400/80 font-black tracking-widest">
              <div class="w-1.5 h-1.5 rounded-full bg-fuchsia-500 animate-pulse"></div>
              {appt.type}
            </div>
          </div>
        </div>

        <ChevronRight size={16} class="text-white/10 group-hover/item:text-fuchsia-400 transition-all group-hover/item:translate-x-1" />
      </div>
    {/each}
  </div>

  <!-- Global Pulse Visualizer -->
  <div class="mt-8 pt-6 border-t border-white/5 flex items-center justify-between opacity-50 relative z-10">
    <div class="flex items-center gap-2">
      <Clock size={12} class="text-blue-400" />
      <span class="text-[10px] font-bold text-white tracking-widest leading-none">Global Sync Active</span>
    </div>
    <div class="flex gap-1">
      <div class="w-1 h-3 rounded-full bg-blue-500/40 animate-[pulse_1s_infinite]"></div>
      <div class="w-1 h-3 rounded-full bg-blue-500/40 animate-[pulse_1.2s_infinite]"></div>
      <div class="w-1 h-3 rounded-full bg-blue-500/40 animate-[pulse_0.8s_infinite]"></div>
    </div>
  </div>
</div>
