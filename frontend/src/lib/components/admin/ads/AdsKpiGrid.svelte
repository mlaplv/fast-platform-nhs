<script lang="ts">
  import Zap from "@lucide/svelte/icons/zap";
  import ShieldAlert from "@lucide/svelte/icons/shield-alert";
  import Activity from "@lucide/svelte/icons/activity";
  import DollarSign from "@lucide/svelte/icons/dollar-sign";

  let { summary, fmt } = $props();
</script>

<section class="grid grid-cols-4 gap-4">
  <!-- TỔNG TRUY CẬP -->
  <div class="bg-white/[0.02] border border-white/5 p-5 rounded-sm relative overflow-hidden group hover:border-white/10 transition-all">
    <div class="absolute top-0 right-0 p-3 opacity-5 group-hover:opacity-10 transition-all">
      <Zap size={48} />
    </div>
    <div class="flex items-center gap-2 text-[9px] text-slate-500 font-black uppercase tracking-widest mb-3">
      <Zap size={10} class="text-cyan-400" />
      <span>TỔNG TRUY CẬP</span>
    </div>
    <div class="flex items-baseline gap-1.5">
      <span class="text-3xl font-black font-mono tracking-tighter text-white">{fmt(summary?.totals.all_clicks || 0)}</span>
      <span class="text-[9px] text-slate-600 font-bold uppercase">Click</span>
    </div>
  </div>

  <!-- PHÁT HIỆN GIAN LẬN -->
  <div class="bg-ruby/5 border border-ruby/10 p-5 rounded-sm relative overflow-hidden group hover:border-ruby/30 transition-all">
    <div class="absolute top-0 right-0 p-3 opacity-5 group-hover:opacity-10 transition-all text-ruby">
      <ShieldAlert size={48} />
    </div>
    <div class="flex items-center gap-2 text-[9px] text-ruby/80 font-black uppercase tracking-widest mb-3">
      <ShieldAlert size={10} />
      <span>GIAN LẬN</span>
    </div>
    <div class="flex items-baseline gap-1.5 text-ruby">
      <span class="text-3xl font-black font-mono tracking-tighter">{fmt(summary?.totals.fraud || 0)}</span>
      <span class="text-[9px] opacity-60 font-bold uppercase">Lỗi</span>
    </div>
  </div>

  <!-- RỦI RO -->
  <div class="bg-amber/5 border border-amber/10 p-5 rounded-sm relative overflow-hidden group hover:border-amber/30 transition-all">
    <div class="absolute top-0 right-0 p-3 opacity-5 group-hover:opacity-10 transition-all text-amber">
      <Activity size={48} />
    </div>
    <div class="flex items-center gap-2 text-[9px] text-amber/80 font-black uppercase tracking-widest mb-3">
      <Activity size={10} />
      <span>RỦI RO</span>
    </div>
    <div class="flex items-baseline gap-1.5 text-amber">
      <span class="text-3xl font-black font-mono tracking-tighter">{summary?.totals.suspected_rate_pct || 0}%</span>
      <span class="text-[9px] opacity-60 font-bold uppercase">Nghi vấn</span>
    </div>
  </div>

  <!-- TIẾT KIỆM -->
  <div class="bg-emerald-500/5 border border-emerald-500/10 p-5 rounded-sm relative overflow-hidden group hover:border-emerald-500/30 transition-all">
    <div class="absolute top-0 right-0 p-3 opacity-5 group-hover:opacity-10 transition-all text-emerald-500">
      <DollarSign size={48} />
    </div>
    <div class="flex items-center gap-2 text-[9px] text-emerald-400 font-black uppercase tracking-widest mb-3">
      <DollarSign size={10} />
      <span>TIẾT KIỆM</span>
    </div>
    <div class="flex items-baseline gap-1.5 text-emerald-400">
      <span class="text-3xl font-black font-mono tracking-tighter">{fmt(summary?.budget.estimated_wasted_vnd || 0)}₫</span>
      <span class="text-[9px] opacity-60 font-bold uppercase">VNĐ</span>
    </div>
  </div>
</section>
