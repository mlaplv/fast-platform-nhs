<script lang="ts">
  import Zap from "@lucide/svelte/icons/zap";
  import ShieldAlert from "@lucide/svelte/icons/shield-alert";
  import Activity from "@lucide/svelte/icons/activity";
  import DollarSign from "@lucide/svelte/icons/dollar-sign";

  let { summary, fmt } = $props();

  const totalClicks = $derived(summary?.totals.google_all_clicks || summary?.totals.all_clicks || 0);
  const totalInvalid = $derived(summary?.totals.google_invalid_clicks || summary?.totals.fraud || 0);
  const avgRate = $derived(totalClicks > 0 ? (totalInvalid / totalClicks * 100) : (summary?.totals.suspected_rate_pct || 0));
  const savedVnd = $derived(summary?.budget.google_estimated_wasted_vnd || summary?.budget.estimated_wasted_vnd || 0);
</script>

<section class="grid grid-cols-1 md:grid-cols-4 gap-6">
  <!-- TỔNG TRUY CẬP -->
  <div class="bg-white/[0.03] border border-white/10 p-6 rounded-none relative overflow-hidden group hover:bg-white/[0.05] hover:translate-y-[-4px] transition-all duration-500 shadow-2xl">
    <div class="absolute top-0 right-0 p-6 opacity-[0.05] group-hover:opacity-10 transition-all group-hover:scale-125 duration-1000 text-cyan-400">
      <Zap size={80} />
    </div>
    <div class="flex items-center justify-between mb-6 relative z-10">
      <div class="flex items-center gap-3">
        <div class="p-2 rounded-none bg-cyan-500/10 border border-cyan-500/20 shadow-[0_0_15px_rgba(6,182,212,0.1)]">
          <Zap size={14} class="text-cyan-400 animate-pulse" />
        </div>
        <span class="text-[10px] text-slate-500 font-black tracking-[0.2em]">Tổng truy cập</span>
      </div>
      {#if summary?.totals.google_all_clicks > 0}
        <span class="text-[8px] px-2 py-1 rounded-none bg-cyan-500/10 text-cyan-400 font-black border border-cyan-500/20 tracking-tighter shadow-inner">GOOGLE_CORE</span>
      {/if}
    </div>
    <div class="flex items-baseline gap-2 relative z-10">
      <span class="text-4xl font-black tracking-tighter text-white group-hover:text-cyan-400 transition-colors duration-500">
        {fmt(totalClicks)}
      </span>
      <span class="text-[10px] text-cyan-500/50 font-black tracking-widest ">Lượt click</span>
    </div>
    <div class="mt-5 h-1.5 w-full bg-black/40 rounded-none overflow-hidden border border-white/5 relative z-10 shadow-inner">
      <div class="h-full bg-gradient-to-r from-cyan-600 to-cyan-400 shadow-[0_0_15px_#06b6d4] rounded-none" style="width: 100%"></div>
    </div>
  </div>

  <!-- PHÁT HIỆN GIAN LẬN -->
  <div class="bg-rose-500/[0.03] border border-rose-500/10 p-6 rounded-none relative overflow-hidden group hover:bg-rose-500/[0.05] hover:translate-y-[-4px] transition-all duration-500 shadow-2xl">
    <div class="absolute top-0 right-0 p-6 opacity-[0.05] group-hover:opacity-10 transition-all group-hover:scale-125 duration-1000 text-rose-500">
      <ShieldAlert size={80} />
    </div>
    <div class="flex items-center justify-between mb-6 relative z-10">
      <div class="flex items-center gap-3">
        <div class="p-2 rounded-none bg-rose-500/10 border border-rose-500/20 shadow-[0_0_15px_rgba(244,63,94,0.1)]">
          <ShieldAlert size={14} class="text-rose-500 animate-pulse" />
        </div>
        <span class="text-[10px] text-slate-500 font-black tracking-[0.2em]">Phát hiện gian lận</span>
      </div>
      {#if summary?.totals.google_invalid_clicks > 0}
        <span class="text-[8px] px-2 py-1 rounded-none bg-rose-500/10 text-rose-500 font-black border border-rose-500/20 tracking-tighter shadow-inner">GOOGLE_CORE</span>
      {/if}
    </div>
    <div class="flex items-baseline gap-2 relative z-10 text-rose-500">
      <span class="text-4xl font-black tracking-tighter text-white group-hover:text-rose-500 transition-colors duration-500">
        {fmt(totalInvalid)}
      </span>
      <span class="text-[10px] text-rose-500/50 font-black tracking-widest ">Invalid</span>
    </div>
    <div class="mt-5 h-1.5 w-full bg-black/40 rounded-none overflow-hidden border border-white/5 relative z-10 shadow-inner">
      <div class="h-full bg-gradient-to-r from-rose-600 to-rose-400 shadow-[0_0_15px_#f43f5e] rounded-none" style="width: {Math.min((totalInvalid / Math.max(totalClicks, 1)) * 500, 100)}%"></div>
    </div>
  </div>

  <!-- TỶ LỆ VI PHẠM -->
  <div class="bg-amber-500/[0.03] border border-amber-500/10 p-6 rounded-none relative overflow-hidden group hover:bg-amber-500/[0.05] hover:translate-y-[-4px] transition-all duration-500 shadow-2xl">
    <div class="absolute top-0 right-0 p-6 opacity-[0.05] group-hover:opacity-10 transition-all group-hover:scale-125 duration-1000 text-amber-500">
      <Activity size={80} />
    </div>
    <div class="flex items-center gap-3 mb-6 relative z-10">
      <div class="p-2 rounded-none bg-amber-500/10 border border-amber-500/20 shadow-[0_0_15px_rgba(245,158,11,0.1)]">
        <Activity size={14} class="text-amber-500 animate-pulse" />
      </div>
      <span class="text-[10px] text-slate-500 font-black tracking-[0.2em]">Tỷ lệ vi phạm (%)</span>
    </div>
    <div class="flex items-baseline gap-2 relative z-10 text-amber-500">
      <span class="text-4xl font-black tracking-tighter text-white group-hover:text-amber-500 transition-colors duration-500">{avgRate.toFixed(2)}%</span>
      <span class="text-[10px] text-amber-500/50 font-black tracking-widest ">Avg Rate</span>
    </div>
    <div class="mt-5 h-1.5 w-full bg-black/40 rounded-none overflow-hidden border border-white/5 relative z-10 shadow-inner">
      <div class="h-full bg-gradient-to-r from-amber-600 to-amber-400 shadow-[0_0_15px_#f59e0b] rounded-none" style="width: {avgRate}%"></div>
    </div>
  </div>

  <!-- Tiết kiệm NGÂN SÁCH -->
  <div class="bg-emerald-500/[0.03] border border-emerald-500/10 p-6 rounded-none relative overflow-hidden group hover:bg-emerald-500/[0.05] hover:translate-y-[-4px] transition-all duration-500 shadow-2xl">
    <div class="absolute top-0 right-0 p-6 opacity-[0.05] group-hover:opacity-10 transition-all group-hover:scale-125 duration-1000 text-emerald-500">
      <DollarSign size={80} />
    </div>
    <div class="flex items-center justify-between mb-6 relative z-10">
      <div class="flex items-center gap-3">
        <div class="p-2 rounded-none bg-emerald-500/10 border border-emerald-500/20 shadow-[0_0_15px_rgba(16,185,129,0.1)]">
          <DollarSign size={14} class="text-emerald-500 animate-pulse" />
        </div>
        <span class="text-[10px] text-slate-500 font-black tracking-[0.2em]">Tiết kiệm ngân sách</span>
      </div>
      {#if summary?.budget.google_estimated_wasted_vnd > 0}
        <span class="text-[8px] px-2 py-1 rounded-none bg-emerald-500/10 text-emerald-400 font-black border border-emerald-500/20 tracking-tighter shadow-inner">GOOGLE_CORE</span>
      {/if}
    </div>
    <div class="flex items-baseline gap-2 relative z-10 text-emerald-400">
      <span class="text-4xl font-black tracking-tighter text-white group-hover:text-emerald-400 transition-colors duration-500">
        {fmt(savedVnd)}₫
      </span>
      <span class="text-[10px] text-emerald-500/50 font-black tracking-widest ">Saved</span>
    </div>
    <div class="mt-5 h-1.5 w-full bg-black/40 rounded-none overflow-hidden border border-white/5 relative z-10 shadow-inner">
      <div class="h-full bg-gradient-to-r from-emerald-600 to-emerald-400 shadow-[0_0_15px_#10b981] rounded-none" style="width: 100%"></div>
    </div>
  </div>
</section>
