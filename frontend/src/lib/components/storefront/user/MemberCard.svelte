<script lang="ts">
  import { authStore } from '$lib/state/authStore.svelte';
  import { fade } from 'svelte/transition';

  let user = $derived(authStore.user);
  let tier = $derived(user?.extra_metadata?.tier || 'MEMBER'); // Default tier
  let points = $derived(user?.extra_metadata?.points || 0);

  const tierColors = {
    MEMBER: 'from-stone-400 to-stone-600',
    SILVER: 'from-slate-300 to-slate-500',
    GOLD: 'from-amber-200 via-yellow-400 to-amber-500',
    PLATINUM: 'from-cyan-700 via-blue-800 to-slate-900'
  };

  const tierName = {
    MEMBER: 'Thành viên Standard',
    SILVER: 'Thành viên Bạc',
    GOLD: 'Hội viên Vàng',
    PLATINUM: 'Thượng khách Kim cương'
  };
</script>

<div
  in:fade={{ duration: 800 }}
  class="relative w-full h-48 rounded-2xl overflow-hidden shadow-2xl bg-gradient-to-br {tierColors[tier as keyof typeof tierColors]} p-6 text-white group"
>
  <!-- Background Pattern -->
  <div class="absolute inset-0 opacity-10 pointer-events-none group-hover:scale-110 transition-transform duration-1000">
    <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
          <path d="M 40 0 L 0 0 0 40" fill="none" stroke="currentColor" stroke-width="0.5"/>
        </pattern>
      </defs>
      <rect width="100%" height="100%" fill="url(#grid)" />
    </svg>
  </div>

  <div class="relative h-full flex flex-col justify-between">
    <div class="flex justify-between items-start">
      <div class="space-y-1">
        <p class="text-[10px] uppercase tracking-[3px] opacity-80 font-medium">Micsmo.com</p>
        <h3 class="text-xl font-serif italic tracking-wide">{tierName[tier as keyof typeof tierName]}</h3>
      </div>
      <div class="w-12 h-8 bg-white/20 backdrop-blur-md rounded-md flex items-center justify-center border border-white/30">
        <span class="text-[10px] font-bold tracking-tighter italic">CHIP</span>
      </div>
    </div>

    <div class="space-y-3">
      <div class="flex items-end justify-between">
        <div class="space-y-0.5">
          <p class="text-[10px] uppercase tracking-wider opacity-60">Chủ thẻ</p>
          <p class="text-lg font-medium tracking-[2px] truncate max-w-[200px] uppercase">
            {user?.name || user?.username || 'GUEST'}
          </p>
        </div>
        <div class="text-right">
          <p class="text-[10px] uppercase tracking-wider opacity-60">Tích lũy</p>
          <p class="text-xl font-bold italic">{points.toLocaleString()} <span class="text-xs not-italic font-normal opacity-80">Pts</span></p>
        </div>
      </div>
    </div>
  </div>

  <!-- Gloss effect -->
  <div class="absolute -inset-full top-0 block transform -skew-x-12 bg-gradient-to-r from-transparent via-white/10 to-transparent opacity-50 group-hover:animate-shine pointer-events-none"></div>
</div>

<style>
  @keyframes shine {
    from { transform: translateX(-100%) skewX(-12deg); }
    to { transform: translateX(200%) skewX(-12deg); }
  }
  .animate-shine {
    animation: shine 1.5s infinite;
  }
</style>
