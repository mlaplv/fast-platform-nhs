<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { fly, fade } from 'svelte/transition';
  import { checkinStore } from '$lib/state/commerce/checkin.svelte';
  import { loyaltyStore } from '$lib/state/commerce/loyalty.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { authStore } from '$lib/state/authStore.svelte';

  let { onClose }: { onClose: () => void } = $props();

  // Countdown đến 23:59:59 GMT+7
  let countdownText = $state('');
  let countdownInterval: ReturnType<typeof setInterval> | null = null;

  // Confetti
  let showConfetti = $state(false);
  let particles = $state<{ x: number; y: number; color: string; delay: number }[]>([]);

  const COLORS = ['#FFD700', '#FF6B35', '#FFA500', '#FFE066', '#FFFBE7'];

  function calcCountdown(): string {
    const now = new Date();
    // Vietnam time = UTC+7
    const vnMs = now.getTime() + 7 * 3600 * 1000;
    const vnNow = new Date(vnMs);
    const midnight = new Date(vnMs);
    midnight.setUTCHours(23, 59, 59, 999);
    const diff = Math.max(0, midnight.getTime() - vnNow.getTime());
    const h = Math.floor(diff / 3_600_000).toString().padStart(2, '0');
    const m = Math.floor((diff % 3_600_000) / 60_000).toString().padStart(2, '0');
    const s = Math.floor((diff % 60_000) / 1_000).toString().padStart(2, '0');
    return `${h}:${m}:${s}`;
  }

  function spawnConfetti() {
    particles = Array.from({ length: 22 }, (_, i) => ({
      x: 20 + Math.random() * 60,
      y: 40 + Math.random() * 20,
      color: COLORS[i % COLORS.length],
      delay: i * 45,
    }));
    showConfetti = true;
    setTimeout(() => { showConfetti = false; particles = []; }, 2000);
  }

  async function handleClaim() {
    if (!authStore.isAuthenticated) {
      onClose();
      setTimeout(() => getClientUi().openLogin(), 200);
      return;
    }
    if (!checkinStore.canClaim || checkinStore.claiming) return;
    const ok = await checkinStore.claimReward();
    if (ok) {
      spawnConfetti();
      getClientUi().showToast(`🎉 Nhận ${fmtVnd(checkinStore.status?.today_reward ?? 100)} xu thành công!`, 'success');
    } else if (checkinStore.error) {
      getClientUi().showToast(checkinStore.error, 'error');
    }
  }

  function fmtVnd(v: number): string {
    if (v >= 1000) return `${Math.round(v / 1000)}K`;
    return String(v);
  }

  // Derived state
  let days = $derived(checkinStore.status?.days ?? []);
  let isCheckedIn = $derived(checkinStore.status?.is_checked_in_today ?? false);
  let streak = $derived(checkinStore.status?.current_streak ?? 0);
  let todayReward = $derived(checkinStore.status?.today_reward ?? 100);
  let balance = $derived(loyaltyStore.data?.available_points ?? 0);
  // Tiền hết hạn: giả định là today_reward (điểm danh ngày hôm nay sẽ hết hạn)
  let expireAmount = $derived(todayReward);

  onMount(() => {
    countdownText = calcCountdown();
    countdownInterval = setInterval(() => { countdownText = calcCountdown(); }, 1000);
  });
  onDestroy(() => { if (countdownInterval) clearInterval(countdownInterval); });
</script>

<!-- Backdrop -->
<div
  role="button" tabindex="-1" aria-label="Đóng"
  class="fixed inset-0 z-[9998] bg-black/55"
  onclick={onClose}
  onkeydown={(e) => e.key === 'Escape' && onClose()}
  transition:fade={{ duration: 180 }}
></div>

<!-- Bottom sheet -->
<div
  class="fixed bottom-0 left-0 right-0 z-[9999] flex flex-col rounded-t-[20px] overflow-hidden"
  style="background: #1c1b22; max-height: 88dvh;"
  transition:fly={{ y: 500, duration: 320, opacity: 1 }}
>
  <!-- Pull indicator -->
  <div class="flex justify-center pt-2.5 pb-1 flex-shrink-0">
    <div class="w-9 h-1 rounded-full bg-white/15"></div>
  </div>

  <!-- ── HEADER ──────────────────────────────── -->
  <div class="flex items-center justify-between px-4 py-3 flex-shrink-0">
    <button onclick={onClose} class="flex items-center gap-2 text-white/80 active:opacity-60" aria-label="Đóng">
      <span class="text-lg font-light">×</span>
      <span class="font-semibold text-[15px]">Trung tâm thưởng</span>
    </button>
    <button
      onclick={() => checkinStore.openHistory()}
      class="text-[#FF9900] text-[13px] font-medium"
    >Quy định</button>
  </div>

  <!-- ── BALANCE ROW ──────────────────────────── -->
  <div class="px-4 pb-4 flex-shrink-0">
    <div class="flex items-start justify-between">
      <div>
        <!-- Coin + amount -->
        <div class="flex items-center gap-1.5 mb-0.5">
          <span class="text-[22px] leading-none">🪙</span>
          <span class="text-[#FFD700] font-black text-[26px] leading-none tracking-tight">
            {#if authStore.isAuthenticated}
              {fmtVnd(balance)}đ
            {:else}
              --
            {/if}
          </span>
        </div>
        <!-- Expiry countdown -->
        {#if authStore.isAuthenticated && expireAmount > 0}
          <p class="text-white/40 text-[11px] leading-tight mt-1">
            {fmtVnd(expireAmount)}.000đ tiền thưởng sẽ hết hạn sau
            <span class="text-[#FF9900] font-mono font-semibold">{countdownText}</span>
          </p>
        {:else if !authStore.isAuthenticated}
          <p class="text-white/40 text-[11px] mt-1">Đăng nhập để xem số dư</p>
        {/if}
      </div>
      <!-- Lịch sử button -->
      <button
        onclick={() => checkinStore.openHistory()}
        class="flex items-center gap-1 bg-white/8 border border-white/10 rounded-full px-3 py-1.5 text-white/60 text-[12px] font-medium mt-0.5"
      >Lịch sử <span class="text-white/30 text-[10px]">›</span></button>
    </div>
  </div>

  <!-- ── NHIỆM VỤ CARD ──────────────────────── -->
  <div class="mx-3 mb-4 bg-white rounded-[16px] overflow-hidden flex-shrink-0">
    <!-- Card header -->
    <div class="px-4 pt-4 pb-3">
      <h3 class="font-bold text-[#1c1b22] text-[15px]">Nhiệm vụ thưởng</h3>
    </div>

    <!-- Day scroll -->
    {#if checkinStore.loading && days.length === 0}
      <div class="flex gap-3 px-4 pb-4 overflow-x-auto scrollbar-hide">
        {#each Array(7) as _}
          <div class="flex-shrink-0 w-[64px] h-[88px] rounded-xl bg-gray-100 animate-pulse"></div>
        {/each}
      </div>
    {:else}
      <div class="flex gap-2.5 px-4 pb-4 overflow-x-auto scrollbar-hide">
        {#each days as d (d.day)}
          {@const active = d.is_today}
          {@const done = d.is_completed}
          <div class="flex-shrink-0 flex flex-col items-center gap-1.5">
            <!-- Card box -->
            <div
              class="relative flex flex-col items-center justify-center rounded-[14px] transition-all
                {active
                  ? 'w-[72px] h-[88px] bg-gradient-to-b from-[#FFF3CC] to-[#FFE082] border-2 border-[#FFD600]/60 shadow-md'
                  : done
                    ? 'w-[60px] h-[76px] bg-[#F5F5F5] border border-gray-200'
                    : 'w-[60px] h-[76px] bg-[#F8F8F8] border border-gray-100 opacity-75'}"
            >
              <!-- Done checkmark overlay -->
              {#if done && !active}
                <div class="absolute inset-0 rounded-[13px] bg-white/60 flex items-center justify-center z-10">
                  <svg class="w-5 h-5 text-[#FFB800]" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/>
                  </svg>
                </div>
              {/if}

              <!-- Money bag stack (like reference image) -->
              <div class="relative flex items-end justify-center {active ? 'h-[46px] w-[56px]' : 'h-[40px] w-[46px]'}">
                <!-- Back bags (stacked effect) -->
                {#if !done}
                  <span class="absolute bottom-0 left-0 text-{active ? '[26px]' : '[20px]'} opacity-50 rotate-[-12deg]" style="font-size: {active ? '22px' : '17px'}">💰</span>
                  <span class="absolute bottom-0 left-[8px] text-[22px] opacity-75 rotate-[-5deg]" style="font-size: {active ? '24px' : '18px'}">💰</span>
                  <!-- Front main bag -->
                  <span class="relative z-10" style="font-size: {active ? '30px' : '22px'}">💰</span>
                {:else}
                  <span style="font-size: {active ? '30px' : '22px'}">💰</span>
                {/if}
              </div>

              <!-- Reward label on card -->
              {#if !done}
                <div class="mt-1 {active ? 'bg-[#FFD600] text-[#5a3a00]' : 'bg-gray-200 text-gray-500'} rounded-full px-2 py-0.5">
                  <span class="font-black text-[11px] leading-none">{fmtVnd(d.reward)}</span>
                </div>
              {/if}
            </div>
            <!-- Label below -->
            <span class="text-[10px] font-semibold {active ? 'text-[#FF9900]' : done ? 'text-gray-400' : 'text-gray-400'}">
              {active ? 'Hôm nay' : `Ngày ${d.day}`}
            </span>
          </div>
        {/each}

        <!-- Dots if more than shown -->
        {#if days.length === 0}
          <!-- Placeholder 7 days -->
          {#each Array(7) as _, i}
            <div class="flex-shrink-0 flex flex-col items-center gap-1.5">
              <div class="w-[60px] h-[76px] rounded-[14px] bg-gray-100 {i === 0 ? 'w-[72px] h-[88px]' : ''}"></div>
              <span class="text-[10px] text-gray-300">{i === 0 ? 'Hôm nay' : `Ngày ${i+1}`}</span>
            </div>
          {/each}
        {/if}
      </div>
    {/if}
  </div>

  <!-- ── CTA BUTTON ──────────────────────────── -->
  <div class="px-4 pb-8 flex-shrink-0">
    {#if isCheckedIn && authStore.isAuthenticated}
      <!-- Already claimed -->
      <div class="w-full py-4 rounded-full bg-white/6 border border-white/10 flex items-center justify-center gap-2">
        <svg class="w-4 h-4 text-[#FFD700]" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/>
        </svg>
        <span class="text-white/50 text-[14px] font-semibold">Đã nhận thưởng hôm nay</span>
      </div>
    {:else}
      <!-- Claim / Login CTA — dark pill button like reference -->
      <button
        onclick={handleClaim}
        disabled={checkinStore.claiming}
        class="relative w-full py-[15px] rounded-full font-bold text-[15px] overflow-hidden
          bg-[#1a1a1a] text-white
          shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]
          disabled:opacity-60 active:scale-[0.98] transition-all duration-150
          flex items-center justify-center gap-2"
      >
        {#if checkinStore.claiming}
          <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
          </svg>
          <span>Đang nhận...</span>
        {:else if authStore.isAuthenticated}
          <span>Nhận phần thưởng của hôm nay</span>
          <span class="text-[18px]">👆</span>
        {:else}
          <span>Đăng nhập để nhận thưởng</span>
          <span class="text-[18px]">🔑</span>
        {/if}
      </button>
    {/if}
  </div>

  <!-- Confetti -->
  {#if showConfetti}
    <div class="absolute inset-0 pointer-events-none overflow-hidden z-20" aria-hidden="true">
      {#each particles as p}
        <div
          class="absolute w-2 h-2 rounded-sm animate-confetti"
          style="left:{p.x}%; top:{p.y}%; background:{p.color}; animation-delay:{p.delay}ms;"
        ></div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
  .scrollbar-hide::-webkit-scrollbar { display: none; }

  @keyframes confetti {
    0%   { transform: translateY(0) rotate(0deg); opacity: 1; }
    100% { transform: translateY(-160px) rotate(540deg); opacity: 0; }
  }
  .animate-confetti { animation: confetti 1.6s ease-out forwards; }
</style>
