<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { fly, fade } from 'svelte/transition';
  import { checkinStore, type CheckinDay } from '$lib/state/commerce/checkin.svelte';
  import { loyaltyStore } from '$lib/state/commerce/loyalty.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { authStore } from '$lib/state/authStore.svelte';

  // Props từ Landing Controller
  let { onClose }: { onClose: () => void } = $props();

  let showConfetti = $state(false);
  let confettiParticles = $state<{ x: number; y: number; r: number; color: string; vx: number; vy: number }[]>([]);
  let countdownText = $state('00:00:00');
  let countdownInterval: ReturnType<typeof setInterval> | null = null;

  const COIN_COLORS = ['#FFD700', '#FF6B35', '#F7B731', '#A29BFE', '#fd79a8'];

  // Tính countdown đến 23:59:59 hôm nay (GMT+7)
  function calcCountdown(): string {
    const now = new Date();
    const vnNow = new Date(now.getTime() + 7 * 60 * 60 * 1000);
    const end = new Date(vnNow);
    end.setUTCHours(16, 59, 59, 999); // 23:59:59 GMT+7 = 16:59:59 UTC
    if (end < vnNow) end.setUTCDate(end.getUTCDate() + 1);
    const diff = end.getTime() - vnNow.getTime();
    const h = Math.floor(diff / 3_600_000).toString().padStart(2, '0');
    const m = Math.floor((diff % 3_600_000) / 60_000).toString().padStart(2, '0');
    const s = Math.floor((diff % 60_000) / 1_000).toString().padStart(2, '0');
    return `${h}:${m}:${s}`;
  }

  function startCountdown() {
    countdownText = calcCountdown();
    countdownInterval = setInterval(() => {
      countdownText = calcCountdown();
    }, 1_000);
  }

  function spawnConfetti() {
    confettiParticles = Array.from({ length: 28 }, (_, i) => ({
      x: 40 + Math.random() * 20,
      y: 50,
      r: 5 + Math.random() * 8,
      color: COIN_COLORS[i % COIN_COLORS.length],
      vx: (Math.random() - 0.5) * 12,
      vy: -(8 + Math.random() * 8),
    }));
    showConfetti = true;
    setTimeout(() => { showConfetti = false; confettiParticles = []; }, 2200);
  }

  async function handleClaim() {
    // Guest guard: mở login modal
    if (!authStore.isAuthenticated) {
      getClientUi().openLogin();
      return;
    }
    if (!checkinStore.canClaim) return;
    const success = await checkinStore.claimReward();
    if (success) {
      spawnConfetti();
      getClientUi().showToast(`🎉 Đã nhận ${formatVnd(checkinStore.status?.today_reward ?? 100)} xu điểm danh!`, 'success');
    } else if (checkinStore.error) {
      getClientUi().showToast(checkinStore.error, 'error');
    }
  }

  function formatVnd(val: number): string {
    if (val >= 1_000) return (val / 1_000).toFixed(0) + 'K';
    return val.toString();
  }

  function formatPoints(val: number): string {
    return val.toLocaleString('vi-VN');
  }

  let days = $derived(checkinStore.status?.days ?? []);
  let totalCheckin = $derived(checkinStore.status?.total_checkin_today ?? 0);
  let availablePoints = $derived(loyaltyStore.data?.available_points ?? 0);

  onMount(() => {
    startCountdown();
  });

  onDestroy(() => {
    if (countdownInterval) clearInterval(countdownInterval);
  });
</script>

<!-- Backdrop -->
<div
  role="button"
  tabindex="-1"
  aria-label="Đóng popup"
  class="fixed inset-0 z-[9998] bg-black/60 backdrop-blur-sm"
  onclick={onClose}
  onkeydown={(e) => e.key === 'Escape' && onClose()}
  transition:fade={{ duration: 200 }}
></div>

<!-- Bottom Sheet -->
<div
  class="fixed bottom-0 left-0 right-0 z-[9999] bg-[#1a1a2e] rounded-t-[28px] overflow-hidden shadow-2xl"
  style="max-height: 90dvh;"
  transition:fly={{ y: 400, duration: 350, opacity: 1 }}
>
  <!-- Handle bar -->
  <div class="flex justify-center pt-3 pb-1">
    <div class="w-10 h-1 rounded-full bg-white/20"></div>
  </div>

  <!-- Header -->
  <div class="flex items-center justify-between px-5 pt-2 pb-3">
    <button
      onclick={onClose}
      class="w-8 h-8 flex items-center justify-center rounded-full bg-white/10 text-white/70 hover:bg-white/20 transition-colors"
      aria-label="Đóng"
    >
      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/>
      </svg>
    </button>
    <h2 class="text-white font-bold text-base tracking-wide">Trung tâm thưởng</h2>
    <button
      onclick={() => checkinStore.openHistory()}
      class="text-[#FFD700] text-xs font-semibold hover:underline"
    >
      Quy định
    </button>
  </div>

  <!-- Balance Card -->
  <div class="mx-4 mb-4">
    <div class="relative rounded-2xl overflow-hidden bg-gradient-to-br from-[#2d2d4e] to-[#1a1a2e] border border-white/10 p-4">
      <!-- Glow -->
      <div class="absolute -top-6 -left-6 w-32 h-32 bg-[#FFD700]/10 rounded-full blur-2xl pointer-events-none"></div>
      
      <div class="flex items-center justify-between">
        <div>
          <div class="flex items-center gap-2 mb-0.5">
            <span class="text-2xl">🪙</span>
            <span class="text-[#FFD700] text-2xl font-black tracking-tight">
              {formatVnd(availablePoints)}đ
            </span>
          </div>
          <p class="text-white/50 text-[11px]">
            Chuỗi sẽ đứt sau: 
            <span class="text-[#FF6B35] font-mono font-bold">{countdownText}</span>
          </p>
        </div>
        <button
          onclick={() => checkinStore.openHistory()}
          class="flex items-center gap-1 bg-white/10 hover:bg-white/20 text-white/70 text-xs px-3 py-1.5 rounded-full transition-colors border border-white/10"
        >
          Lịch sử <span class="text-white/40">›</span>
        </button>
      </div>

      <!-- Social Proof -->
      {#if totalCheckin > 0}
        <div class="mt-3 flex items-center gap-1.5">
          <span class="inline-block w-1.5 h-1.5 rounded-full bg-[#FF6B35] animate-pulse"></span>
          <span class="text-white/40 text-[10px]">
            🔥 <strong class="text-white/60">{totalCheckin.toLocaleString('vi-VN')}</strong> khách đã điểm danh hôm nay
          </span>
        </div>
      {/if}
    </div>
  </div>

  <!-- Nhiệm vụ thưởng -->
  <div class="px-4 mb-3">
    <h3 class="text-white/50 text-[11px] font-semibold tracking-widest uppercase mb-3">Nhiệm vụ thưởng</h3>
    
    {#if checkinStore.loading}
      <div class="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
        {#each Array(7) as _}
          <div class="flex-shrink-0 w-[64px] h-[80px] rounded-2xl bg-white/5 animate-pulse"></div>
        {/each}
      </div>
    {:else}
      <div class="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
        {#each days as day (day.day)}
          {@const isToday = day.is_today}
          {@const isDone = day.is_completed}
          {@const isBonus = day.is_bonus}
          <div class="flex-shrink-0 flex flex-col items-center gap-1.5 w-[64px]">
            <!-- Coin icon -->
            <div
              class="relative w-[60px] h-[60px] rounded-2xl flex flex-col items-center justify-center
                {isDone ? 'bg-gradient-to-br from-[#FFD700]/30 to-[#F7B731]/20 border border-[#FFD700]/40' : 
                 isToday ? 'bg-gradient-to-br from-[#FFD700] to-[#F7B731] shadow-lg shadow-[#FFD700]/30 scale-105' : 
                 'bg-white/5 border border-white/10'}"
            >
              {#if isBonus}
                <div class="absolute -top-1.5 -right-1.5 bg-[#FF6B35] text-white text-[8px] font-black px-1 py-0.5 rounded-full leading-none">
                  HOT
                </div>
              {/if}
              {#if isDone}
                <svg class="w-5 h-5 text-[#FFD700]" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/>
                </svg>
              {:else}
                <span class="text-[10px] font-black {isToday ? 'text-[#1a1a2e]' : 'text-white/60'}">
                  {formatVnd(day.reward)}
                </span>
              {/if}
              <div class="text-[14px]">{isDone ? '' : isToday ? '🪙' : '💰'}</div>
            </div>
            <span class="text-[10px] {isToday ? 'text-[#FFD700] font-bold' : 'text-white/40'}">
              {isToday ? 'Hôm nay' : `Ngày ${day.day}`}
            </span>
          </div>
        {/each}
      </div>
    {/if}
  </div>

  <!-- CTA Button -->
  <div class="px-4 pb-8 pt-1">
    {#if checkinStore.status?.is_checked_in_today}
      <div class="w-full py-4 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center gap-2">
        <svg class="w-5 h-5 text-[#FFD700]" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/>
        </svg>
        <span class="text-white/60 text-sm font-semibold">Đã điểm danh hôm nay ✓</span>
      </div>
    {:else}
      <button
        onclick={handleClaim}
        disabled={checkinStore.claiming || (authStore.isAuthenticated && !checkinStore.canClaim)}
        class="relative w-full py-4 rounded-2xl font-black text-base tracking-wide overflow-hidden
          bg-gradient-to-r from-[#FFD700] to-[#F7B731] text-[#1a1a2e]
          shadow-xl shadow-[#FFD700]/30
          disabled:opacity-60 disabled:cursor-not-allowed
          active:scale-[0.98] transition-all duration-150"
      >
        <!-- Shine sweep -->
        <div class="absolute inset-0 -skew-x-12 bg-gradient-to-r from-transparent via-white/30 to-transparent
          translate-x-[-200%] animate-shine pointer-events-none"></div>
        
        {#if checkinStore.claiming}
          <span class="flex items-center justify-center gap-2">
            <svg class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
            </svg>
            Đang nhận...
          </span>
        {:else}
          {#if authStore.isAuthenticated}
            👋 Nhận phần thưởng của hôm nay
          {:else}
            🔑 Đăng nhập để nhận thưởng
          {/if}
        {/if}
      </button>
    {/if}
  </div>

  <!-- Confetti Overlay -->
  {#if showConfetti}
    <div class="absolute inset-0 pointer-events-none overflow-hidden" aria-hidden="true">
      {#each confettiParticles as p, i}
        <div
          class="absolute rounded-sm animate-confetti"
          style="
            left: {p.x}%;
            top: {p.y}%;
            width: {p.r}px;
            height: {p.r}px;
            background: {p.color};
            animation-delay: {i * 40}ms;
            transform: rotate({Math.random() * 360}deg);
          "
        ></div>
      {/each}
    </div>
  {/if}
</div>

<style>
  @keyframes shine {
    0% { transform: translateX(-200%) skewX(-12deg); }
    60%, 100% { transform: translateX(300%) skewX(-12deg); }
  }
  .animate-shine {
    animation: shine 2.4s ease-in-out infinite;
  }

  @keyframes confetti {
    0% { transform: translateY(0) rotate(0deg); opacity: 1; }
    100% { transform: translateY(-180px) rotate(720deg); opacity: 0; }
  }
  .animate-confetti {
    animation: confetti 1.8s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards;
  }

  .scrollbar-hide::-webkit-scrollbar { display: none; }
  .scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
</style>
