<script lang="ts">
  let { stats, formatCurrency } = $props<{
    stats: { total: number; active: number; draft: number; totalValue: number };
    formatCurrency: (n: number) => string;
  }>();
</script>

<div class="grid grid-cols-4 gap-4">
  <!-- Total Products -->
  <div
    class="group relative overflow-hidden bg-black/40 border border-white/5 rounded-2xl p-5 transition-all duration-300 hover:border-white/20 hover:shadow-[0_8px_30px_rgba(255,255,255,0.05)] hover:-translate-y-1"
  >
    <div
      class="absolute top-0 right-0 w-32 h-32 bg-white/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 group-hover:bg-white/10 transition-colors duration-500"
    ></div>
    <div class="flex items-center justify-between mb-3 relative z-10">
      <span
        class="text-[10px] font-bold font-mono text-gray-500 uppercase tracking-widest"
        >Registry Depth</span
      >
      <div
        class="w-2 h-2 rounded-full border border-white/20 shadow-[0_0_8px_rgba(255,255,255,0.1)]"
      ></div>
    </div>
    <div class="flex items-baseline gap-2 relative z-10">
      <span
        class="text-3xl font-black text-white tracking-widest leading-none drop-shadow-md"
        >{stats.total}</span
      >
      <span class="text-[9px] font-bold font-mono text-gray-600 uppercase"
        >Entries</span
      >
    </div>
    <div
      class="absolute bottom-0 inset-x-0 h-[2px] bg-gradient-to-r from-transparent via-white/20 to-transparent opacity-50 group-hover:opacity-100 transition-opacity"
    ></div>
  </div>

  <!-- Active Products -->
  <div
    class="group relative overflow-hidden bg-black/40 border border-[#39FF14]/20 rounded-2xl p-5 transition-all duration-300 hover:border-[#39FF14]/40 hover:shadow-[0_8px_30px_rgba(57,255,20,0.15)] hover:-translate-y-1"
  >
    <div
      class="absolute top-0 right-0 w-32 h-32 bg-[#39FF14]/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 group-hover:bg-[#39FF14]/20 transition-colors duration-500"
    ></div>
    <div class="flex items-center justify-between mb-3 relative z-10">
      <span
        class="text-[10px] font-bold font-mono text-[#39FF14]/70 uppercase tracking-widest drop-shadow-[0_0_5px_rgba(57,255,20,0.5)]"
        >Live Supply</span
      >
      <div
        class="w-2 h-2 rounded-full bg-[#39FF14] animate-pulse shadow-[0_0_12px_#39FF14]"
      ></div>
    </div>
    <div class="flex items-baseline gap-2 relative z-10">
      <span
        class="text-3xl font-black text-[#39FF14] tracking-widest leading-none drop-shadow-[0_0_8px_rgba(57,255,20,0.3)]"
        >{stats.active}</span
      >
      <span class="text-[9px] font-bold font-mono text-[#39FF14]/40 uppercase"
        >Active</span
      >
    </div>
    <div
      class="absolute bottom-0 inset-x-0 h-[2px] bg-gradient-to-r from-transparent via-[#39FF14]/50 to-transparent opacity-50 group-hover:opacity-100 transition-opacity"
    ></div>
  </div>

  <!-- Draft Products -->
  <div
    class="group relative overflow-hidden bg-black/40 border border-[#FFB800]/20 rounded-2xl p-5 transition-all duration-300 hover:border-[#FFB800]/40 hover:shadow-[0_8px_30px_rgba(255,184,0,0.15)] hover:-translate-y-1"
  >
    <div
      class="absolute top-0 right-0 w-32 h-32 bg-[#FFB800]/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 group-hover:bg-[#FFB800]/20 transition-colors duration-500"
    ></div>
    <div class="flex items-center justify-between mb-3 relative z-10">
      <span
        class="text-[10px] font-bold font-mono text-[#FFB800]/70 uppercase tracking-widest drop-shadow-[0_0_5px_rgba(255,184,0,0.5)]"
        >Staging Cache</span
      >
      <div
        class="w-2 h-2 rounded-full border border-[#FFB800]/50 shadow-[0_0_8px_rgba(255,184,0,0.2)]"
      ></div>
    </div>
    <div class="flex items-baseline gap-2 relative z-10">
      <span
        class="text-3xl font-black text-[#FFB800] tracking-widest leading-none drop-shadow-[0_0_8px_rgba(255,184,0,0.3)]"
        >{stats.draft}</span
      >
      <span class="text-[9px] font-bold font-mono text-[#FFB800]/40 uppercase"
        >Drafts</span
      >
    </div>
    <div
      class="absolute bottom-0 inset-x-0 h-[2px] bg-gradient-to-r from-transparent via-[#FFB800]/50 to-transparent opacity-50 group-hover:opacity-100 transition-opacity"
    ></div>
  </div>

  <!-- Total Value -->
  <div
    class="group relative overflow-hidden bg-black/40 border border-[#00FFFF]/20 rounded-2xl p-5 transition-all duration-300 hover:border-[#00FFFF]/40 hover:shadow-[0_8px_30px_rgba(0,255,255,0.15)] hover:-translate-y-1"
  >
    <div
      class="absolute top-0 right-0 w-32 h-32 bg-[#00FFFF]/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 group-hover:bg-[#00FFFF]/20 transition-colors duration-500"
    ></div>
    <div class="flex items-center justify-between mb-3 relative z-10">
      <span
        class="text-[10px] font-bold font-mono text-[#00FFFF]/70 uppercase tracking-widest drop-shadow-[0_0_5px_rgba(0,255,255,0.5)]"
        >Inventory Mass</span
      >
      <div
        class="w-2 h-2 rounded-full border border-[#00FFFF]/50 shadow-[0_0_8px_rgba(0,255,255,0.2)]"
      ></div>
    </div>
    <div class="flex flex-col relative z-10 mt-1">
      <span
        class="text-2xl font-black text-[#00FFFF] tracking-wider leading-none drop-shadow-[0_0_8px_rgba(0,255,255,0.3)]"
        >{formatCurrency(stats.totalValue)}</span
      >
      <span
        class="text-[9px] font-bold font-mono text-[#00FFFF]/40 uppercase mt-2"
        >Certified Value</span
      >
    </div>
    <div
      class="absolute bottom-0 inset-x-0 h-[2px] bg-gradient-to-r from-transparent via-[#00FFFF]/50 to-transparent opacity-50 group-hover:opacity-100 transition-opacity"
    ></div>
  </div>
</div>
