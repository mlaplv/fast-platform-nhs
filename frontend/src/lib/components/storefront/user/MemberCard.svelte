<script lang="ts">
  import { authStore } from '$lib/state/authStore.svelte';
  import { loyaltyStore } from '$lib/state/commerce/loyalty.svelte';
  import { fade } from 'svelte/transition';

  let user = $derived(authStore.user);
  let tier = $derived(loyaltyStore.data?.tier || user?.extra_metadata?.tier || 'STANDARD'); 
  let points = $derived(loyaltyStore.data?.available_points ?? (user?.extra_metadata?.points || 0));
  let pending = $derived(loyaltyStore.data?.pending_points || 0);

   const tierColors = {
    STANDARD: 'bg-[#8c857d]',
    MEMBER: 'bg-[#8c857d]', // Add for legacy support
    SILVER: 'bg-[#a3a3a3]',
    GOLD: 'bg-[#c5a059]',
    PLATINUM: 'bg-[#1c1c1c]'
  };

  const tierName = {
    STANDARD: 'Thành viên Standard',
    MEMBER: 'Thành viên Standard', // Add for legacy support
    SILVER: 'Thành viên Bạc',
    GOLD: 'Hội viên Vàng',
    PLATINUM: 'Thượng khách Kim cương'
  };

  function formatCardNumber(id: string = '') {
    if (!id) return '0000 0000 0000 0000';
    const cleanId = id.replace(/-/g, '').toUpperCase();
    const segment1 = cleanId.substring(0, 4).padEnd(4, '0');
    const segment2 = cleanId.substring(4, 8).padEnd(4, '0');
    const segment3 = cleanId.substring(8, 12).padEnd(4, '0');
    const segment4 = cleanId.substring(12, 16).padEnd(4, '0');
    return `${segment1} ${segment2} ${segment3} ${segment4}`;
  }

  let cardNumber = $derived(user?.extra_metadata?.cardNumber || formatCardNumber(user?.id));
</script>

<div
  in:fade={{ duration: 800 }}
  class="relative w-full h-48 rounded-[20px] overflow-hidden shadow-[0_15px_40px_rgba(0,0,0,0.12)] {tierColors[tier as keyof typeof tierColors]} p-6 md:p-8 text-white group"
>
  <!-- Subtle Grain Overly -->
  <div class="absolute inset-0 opacity-[0.03] mix-blend-overlay pointer-events-none">
     <svg xmlns='http://www.w3.org/2000/svg' width='200' height='200'>
        <filter id='noiseFilter'>
            <feTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/>
        </filter>
        <rect width='100%' height='100%' filter='url(#noiseFilter)'/>
     </svg>
  </div>

  <div class="relative h-full flex flex-col justify-between">
    <div class="flex justify-between items-start">
      <div class="space-y-0.5">
        <p class="text-[9px] uppercase tracking-[2px] opacity-70 font-medium">MICSMO.COM</p>
        <h3 class="text-lg font-serif italic tracking-wide">{tierName[tier as keyof typeof tierName]}</h3>
      </div>
      <div class="px-2 py-0.5 bg-white/20 backdrop-blur-sm rounded-md flex items-center justify-center border border-white/20 shadow-sm">
        <span class="text-[8px] font-black tracking-tighter italic opacity-80">CHIP</span>
      </div>
    </div>

    <!-- Card Number -->
    <div class="flex-1 flex items-center py-1">
      <p class="text-[17px] font-mono tracking-[4px] text-white select-all">
        {cardNumber}
      </p>
    </div>

    <div class="space-y-4">
      <div class="flex items-end justify-between">
        <div class="space-y-0.5">
          <p class="text-[9px] uppercase tracking-wider opacity-60 font-bold">Chủ thẻ</p>
          <p class="text-sm font-medium tracking-[2.5px] truncate max-w-[200px] uppercase">
            {user?.name || user?.username || 'GUEST'}
          </p>
        </div>
        <div class="text-right">
          <p class="text-[9px] uppercase tracking-wider opacity-60 font-bold">Tích lũy</p>
          <p class="text-xl font-black italic tracking-tighter">
            {points} <span class="text-[10px] not-italic font-bold opacity-80 uppercase tracking-tighter">Pts</span>
            {#if pending > 0}
               <span class="text-[10px] not-italic font-bold text-white/70 ml-1">(+{pending})</span>
            {/if}
          </p>
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
