<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { fly, fade, scale } from 'svelte/transition';
  import { checkinStore } from '$lib/state/commerce/checkin.svelte';
  import { loyaltyStore } from '$lib/state/commerce/loyalty.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { authStore } from '$lib/state/authStore.svelte';

  let { onClose }: { onClose: () => void } = $props();

  let showConfetti = $state(false);
  let confettiParticles = $state<Array<{ x: number; y: number; r: number; color: string; delay: number; rot: number }>>([]);
  let countdownText = $state('00:00:00');
  let countdownInterval: ReturnType<typeof setInterval> | null = null;

  const CONFETTI_COLORS = ['#FFD700', '#FF6B35', '#F7B731', '#A29BFE', '#fd79a8', '#55efc4'];

  function calcCountdown(): string {
    const now = new Date();
    const vnNow = new Date(now.getTime() + 7 * 60 * 60 * 1000);
    const end = new Date(vnNow);
    end.setUTCHours(16, 59, 59, 999);
    if (end < vnNow) end.setUTCDate(end.getUTCDate() + 1);
    const diff = end.getTime() - vnNow.getTime();
    const h = Math.floor(diff / 3_600_000).toString().padStart(2, '0');
    const m = Math.floor((diff % 3_600_000) / 60_000).toString().padStart(2, '0');
    const s = Math.floor((diff % 60_000) / 1_000).toString().padStart(2, '0');
    return `${h}:${m}:${s}`;
  }

  function spawnConfetti() {
    confettiParticles = Array.from({ length: 40 }, (_, i) => ({
      x: 30 + Math.random() * 40,
      y: 45,
      r: 6 + Math.random() * 10,
      color: CONFETTI_COLORS[i % CONFETTI_COLORS.length],
      delay: i * 30,
      rot: Math.random() * 360,
    }));
    showConfetti = true;
    setTimeout(() => { showConfetti = false; confettiParticles = []; }, 2500);
  }

  async function handleClaim() {
    if (!authStore.isAuthenticated) {
      getClientUi().openLogin();
      return;
    }
    if (!checkinStore.canClaim) return;
    const success = await checkinStore.claimReward();
    if (success) {
      spawnConfetti();
      getClientUi().showToast(`🎉 Nhận thành công ${formatVnd(checkinStore.status?.today_reward ?? 100)} xu!`, 'success');
    } else if (checkinStore.error) {
      getClientUi().showToast(checkinStore.error, 'error');
    }
  }

  function formatVnd(val: number): string {
    if (val >= 1_000) return (val / 1_000).toFixed(0) + 'K';
    return val.toString();
  }

  let days = $derived(checkinStore.status?.days ?? []);
  let streak = $derived(checkinStore.status?.current_streak ?? 0);
  let totalCheckin = $derived(checkinStore.status?.total_checkin_today ?? 0);
  let availablePoints = $derived(loyaltyStore.data?.available_points ?? 0);

  onMount(() => {
    countdownText = calcCountdown();
    countdownInterval = setInterval(() => { countdownText = calcCountdown(); }, 1_000);
  });

  onDestroy(() => {
    if (countdownInterval) clearInterval(countdownInterval);
  });
</script>

<!-- Backdrop -->
<div
  role="button"
  tabindex="-1"
  aria-label="Đóng"
  class="fixed inset-0 z-[9998] bg-black/70 backdrop-blur-md"
  onclick={onClose}
  onkeydown={(e) => e.key === 'Escape' && onClose()}
  transition:fade={{ duration: 250 }}
></div>

<!-- Desktop Modal: Centered Dialog -->
<div
  class="fixed inset-0 z-[9999] flex items-center justify-center p-6"
  aria-modal="true"
  role="dialog"
>
  <div
    class="relative w-full max-w-[480px] rounded-[32px] overflow-hidden
      bg-gradient-to-b from-[#0f0f23] via-[#1a1a2e] to-[#0d0d1e]
      border border-white/10 shadow-[0_40px_120px_rgba(0,0,0,0.8),0_0_60px_rgba(255,215,0,0.08)]"
    transition:scale={{ duration: 300, start: 0.92, opacity: 0 }}
  >
    <!-- Decorative glows -->
    <div class="absolute top-0 left-1/2 -translate-x-1/2 w-64 h-40 bg-[#FFD700]/8 rounded-full blur-3xl pointer-events-none"></div>
    <div class="absolute bottom-0 right-0 w-48 h-48 bg-[#A29BFE]/6 rounded-full blur-3xl pointer-events-none"></div>

    <!-- Header -->
    <div class="relative flex items-center justify-between px-6 pt-6 pb-4">
      <div>
        <h2 class="text-white font-black text-xl tracking-tight">Trung tâm thưởng</h2>
        <p class="text-white/40 text-xs mt-0.5">Điểm danh mỗi ngày để nhân thưởng</p>
      </div>
      <div class="flex items-center gap-2">
        <button
          onclick={() => checkinStore.openHistory()}
          class="text-[#FFD700] text-xs font-semibold bg-[#FFD700]/10 hover:bg-[#FFD700]/20 px-3 py-1.5 rounded-full transition-colors border border-[#FFD700]/20"
        >
          Lịch sử
        </button>
        <button
          onclick={onClose}
          class="w-8 h-8 flex items-center justify-center rounded-full bg-white/8 text-white/50 hover:bg-white/15 transition-colors"
          aria-label="Đóng"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- Balance Showcase -->
    <div class="relative mx-5 mb-5">
      <div class="relative rounded-2xl p-5 overflow-hidden
        bg-gradient-to-br from-[#FFD700]/15 via-[#F7B731]/8 to-transparent
        border border-[#FFD700]/20">
        <!-- Inner glow -->
        <div class="absolute inset-0 bg-gradient-to-br from-[#FFD700]/5 to-transparent pointer-events-none rounded-2xl"></div>
        
        <div class="flex items-center justify-between">
          <div>
            <div class="flex items-center gap-3 mb-1">
              <!-- Animated coin icon -->
              <div class="relative w-12 h-12 rounded-2xl bg-gradient-to-br from-[#FFD700] to-[#F7B731] flex items-center justify-center shadow-lg shadow-[#FFD700]/30">
                <span class="text-xl">🪙</span>
                <div class="absolute inset-0 rounded-2xl ring-2 ring-[#FFD700]/30 animate-pulse"></div>
              </div>
              <div>
                <span class="text-[#FFD700] text-3xl font-black tracking-tighter block leading-none">
                  {availablePoints.toLocaleString('vi-VN')}đ
                </span>
                <span class="text-white/40 text-[11px]">Số dư hiện tại</span>
              </div>
            </div>
            <div class="flex items-center gap-1.5 mt-2">
              <div class="w-1.5 h-1.5 rounded-full bg-[#FF6B35] animate-pulse"></div>
              <span class="text-white/40 text-[11px]">
                Chuỗi đứt sau: <span class="text-[#FF6B35] font-mono font-bold">{countdownText}</span>
              </span>
            </div>
          </div>

          <!-- Streak badge -->
          <div class="text-center">
            <div class="relative inline-flex flex-col items-center justify-center w-16 h-16 rounded-2xl
              bg-gradient-to-br from-[#FF6B35] to-[#e84393]
              shadow-xl shadow-[#FF6B35]/30">
              <span class="text-white text-xl font-black leading-none">{streak}</span>
              <span class="text-white/80 text-[9px] font-bold uppercase tracking-wide">ngày</span>
              <div class="absolute -top-1.5 -right-1.5 w-5 h-5 bg-[#FFD700] rounded-full flex items-center justify-center text-[8px]">
                🔥
              </div>
            </div>
            <p class="text-white/30 text-[10px] mt-1">Chuỗi hiện tại</p>
          </div>
        </div>

        <!-- Social proof bar -->
        {#if totalCheckin > 0}
          <div class="mt-4 pt-3 border-t border-white/8 flex items-center gap-2">
            <div class="flex -space-x-1">
              {#each ['🧑', '👩', '🧑‍💼', '👨‍💼'] as emoji}
                <span class="w-6 h-6 rounded-full bg-white/10 flex items-center justify-center text-[10px] border border-white/10">
                  {emoji}
                </span>
              {/each}
            </div>
            <span class="text-white/40 text-[11px]">
              <strong class="text-white/60">{totalCheckin.toLocaleString('vi-VN')}</strong> người đã điểm danh hôm nay
            </span>
          </div>
        {/if}
      </div>
    </div>

    <!-- Day streak timeline -->
    <div class="px-5 mb-5">
      <div class="flex items-center justify-between mb-3">
        <h3 class="text-white/50 text-[10px] font-bold tracking-widest uppercase">Nhiệm vụ điểm danh</h3>
        <span class="text-[#FFD700]/60 text-[10px]">{streak}/{checkinStore.status?.cycle_length ?? 7} ngày</span>
      </div>

      {#if checkinStore.loading}
        <div class="grid grid-cols-7 gap-2">
          {#each Array(7) as _}
            <div class="h-[72px] rounded-xl bg-white/5 animate-pulse"></div>
          {/each}
        </div>
      {:else}
        <div class="grid gap-2" style="grid-template-columns: repeat({days.length || 7}, 1fr);">
          {#each days as day (day.day)}
            {@const isToday = day.is_today}
            {@const isDone = day.is_completed}
            {@const isBonus = day.is_bonus}
            <div class="flex flex-col items-center gap-1">
              <div
                class="relative w-full aspect-square rounded-xl flex flex-col items-center justify-center gap-0.5 transition-all duration-200
                  {isDone 
                    ? 'bg-gradient-to-br from-[#FFD700]/25 to-[#F7B731]/15 border border-[#FFD700]/30' 
                    : isToday 
                      ? 'bg-gradient-to-br from-[#FFD700] to-[#F7B731] shadow-lg shadow-[#FFD700]/40 ring-2 ring-[#FFD700]/40 scale-105' 
                      : 'bg-white/5 border border-white/8 opacity-60'}"
              >
                {#if isBonus}
                  <div class="absolute -top-1.5 left-1/2 -translate-x-1/2 bg-[#FF6B35] text-white text-[7px] font-black px-1.5 py-0.5 rounded-full whitespace-nowrap z-10">
                    BONUS
                  </div>
                {/if}
                {#if isDone}
                  <svg class="w-4 h-4 text-[#FFD700]" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/>
                  </svg>
                {:else}
                  <span class="text-[12px] leading-none">{isToday ? '🪙' : '💰'}</span>
                  <span class="text-[9px] font-black leading-none {isToday ? 'text-[#1a1a2e]' : 'text-white/50'}">
                    {formatVnd(day.reward)}
                  </span>
                {/if}
              </div>
              <span class="text-[9px] {isToday ? 'text-[#FFD700] font-bold' : 'text-white/30'}">
                {isToday ? 'Nay' : `N${day.day}`}
              </span>
            </div>
          {/each}
        </div>

        <!-- Progress bar -->
        <div class="mt-3 h-1 bg-white/8 rounded-full overflow-hidden">
          <div
            class="h-full bg-gradient-to-r from-[#FFD700] to-[#FF6B35] rounded-full transition-all duration-700"
            style="width: {Math.min(100, (streak / (checkinStore.status?.cycle_length ?? 7)) * 100)}%"
          ></div>
        </div>
      {/if}
    </div>

    <!-- CTA -->
    <div class="px-5 pb-6">
      {#if checkinStore.status?.is_checked_in_today}
        <div class="w-full py-4 rounded-2xl bg-white/5 border border-[#FFD700]/20 flex flex-col items-center gap-1">
          <div class="flex items-center gap-2">
            <svg class="w-5 h-5 text-[#FFD700]" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/>
            </svg>
            <span class="text-[#FFD700] font-bold text-sm">Đã điểm danh hôm nay!</span>
          </div>
          <span class="text-white/30 text-xs">Quay lại vào ngày mai để duy trì chuỗi 🔥</span>
        </div>
      {:else}
        <button
          onclick={handleClaim}
          disabled={checkinStore.claiming || (authStore.isAuthenticated && !checkinStore.canClaim)}
          class="relative w-full py-4 rounded-2xl font-black text-[15px] tracking-wide overflow-hidden
            bg-gradient-to-r from-[#FFD700] via-[#F7B731] to-[#FFD700] bg-[length:200%_100%]
            text-[#1a1a2e]
            shadow-[0_8px_32px_rgba(255,215,0,0.4)]
            hover:shadow-[0_12px_40px_rgba(255,215,0,0.5)]
            disabled:opacity-60 disabled:cursor-not-allowed
            active:scale-[0.98] transition-all duration-200
            animate-gradient-x"
        >
          <!-- Shine sweep -->
          <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/40 to-transparent
            -translate-x-full animate-shine pointer-events-none"></div>

          {#if checkinStore.claiming}
            <span class="flex items-center justify-center gap-2">
              <svg class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
              </svg>
              Đang nhận thưởng...
            </span>
          {:else}
            <span class="flex items-center justify-center gap-2">
              {#if authStore.isAuthenticated}
                🎁 Nhận {formatVnd(checkinStore.status?.today_reward ?? 100)} xu hôm nay
              {:else}
                🔑 Đăng nhập để nhận thưởng điểm danh
              {/if}
            </span>
          {/if}
        </button>

        <!-- Tomorrow teaser -->
        {#if days.length > 0}
          {@const tomorrowDay = days.find(d => d.day === (checkinStore.status?.current_streak ?? 0) + 2)}
          {#if tomorrowDay}
            <p class="text-center text-white/30 text-[11px] mt-2.5">
              ✨ Mai nhận <strong class="text-[#FFD700]/70">{formatVnd(tomorrowDay.reward)} xu</strong> — đừng bỏ lỡ!
            </p>
          {/if}
        {/if}
      {/if}
    </div>

    <!-- Confetti overlay -->
    {#if showConfetti}
      <div class="absolute inset-0 pointer-events-none overflow-hidden z-10" aria-hidden="true">
        {#each confettiParticles as p, i}
          <div
            class="absolute rounded-sm animate-confetti-desktop"
            style="
              left: {p.x}%;
              top: {p.y}%;
              width: {p.r}px;
              height: {p.r * 0.6}px;
              background: {p.color};
              animation-delay: {p.delay}ms;
              transform: rotate({p.rot}deg);
            "
          ></div>
        {/each}
      </div>
    {/if}
  </div>
</div>

<style>
  @keyframes shine {
    0% { transform: translateX(-100%); }
    50%, 100% { transform: translateX(300%); }
  }
  .animate-shine {
    animation: shine 2.8s ease-in-out infinite;
  }

  @keyframes gradient-x {
    0%, 100% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
  }
  .animate-gradient-x {
    animation: gradient-x 3s ease infinite;
  }

  @keyframes confetti-desktop {
    0% { transform: translateY(0) rotate(0deg) scale(1); opacity: 1; }
    80% { opacity: 0.8; }
    100% { transform: translateY(-220px) rotate(900deg) scale(0.5); opacity: 0; }
  }
  .animate-confetti-desktop {
    animation: confetti-desktop 2s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards;
  }
</style>
