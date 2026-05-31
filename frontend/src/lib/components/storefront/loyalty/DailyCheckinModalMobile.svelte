<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { fly, fade } from 'svelte/transition';
  import { checkinStore } from '$lib/state/commerce/checkin.svelte';
  import { loyaltyStore } from '$lib/state/commerce/loyalty.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { authStore } from '$lib/state/authStore.svelte';

  let { onClose }: { onClose: () => void } = $props();

  let countdownText = $state('');
  let countdownInterval: ReturnType<typeof setInterval> | null = null;
  let showConfetti = $state(false);
  let particles = $state<{ x: number; y: number; color: string; delay: number }[]>([]);

  const COLORS = ['#FFD700', '#FF6B35', '#FFA500', '#FFE066', '#FFFBE7'];

  // Preview days cho guest (không cần API)
  const PREVIEW_DAYS = [
    { day: 1, reward: 100,  is_completed: false, is_today: true,  is_bonus: false },
    { day: 2, reward: 200,  is_completed: false, is_today: false, is_bonus: false },
    { day: 3, reward: 200,  is_completed: false, is_today: false, is_bonus: false },
    { day: 4, reward: 200,  is_completed: false, is_today: false, is_bonus: false },
    { day: 5, reward: 200,  is_completed: false, is_today: false, is_bonus: false },
    { day: 6, reward: 200,  is_completed: false, is_today: false, is_bonus: false },
    { day: 7, reward: 500,  is_completed: false, is_today: false, is_bonus: true  },
  ];

  function calcCountdown(): string {
    const now = new Date();
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

  // Dùng preview nếu chưa có data từ API (guest hoặc đang load)
  let displayDays = $derived(
    checkinStore.status?.days?.length ? checkinStore.status.days : PREVIEW_DAYS
  );
  let isCheckedIn  = $derived(checkinStore.status?.is_checked_in_today ?? false);
  let todayReward  = $derived(checkinStore.status?.today_reward ?? 100);
  let balance      = $derived(loyaltyStore.data?.available_points ?? 0);

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
  style="background:#1c1b22; max-height:88dvh;"
  transition:fly={{ y: 500, duration: 320, opacity: 1 }}
>
  <!-- Pull bar -->
  <div class="flex justify-center pt-2.5 pb-1 flex-shrink-0">
    <div class="w-9 h-1 rounded-full bg-white/15"></div>
  </div>

  <!-- HEADER -->
  <div class="flex items-center justify-between px-4 py-3 flex-shrink-0">
    <button onclick={onClose} class="flex items-center gap-2 text-white/80 active:opacity-60">
      <span class="text-lg leading-none">×</span>
      <span class="font-semibold text-[15px]">Trung tâm thưởng</span>
    </button>
    <button onclick={() => checkinStore.openHistory()} class="text-[#FF9900] text-[13px] font-medium">
      Quy định
    </button>
  </div>

  <!-- BALANCE -->
  <div class="px-4 pb-3 flex-shrink-0">
    <div class="flex items-start justify-between">
      <div>
        <div class="flex items-center gap-1.5 mb-0.5">
          <span style="font-size:22px;line-height:1;">🪙</span>
          <span class="text-[#FFD700] font-black text-[26px] leading-none tracking-tight">
            {authStore.isAuthenticated ? `${fmtVnd(balance)}đ` : '--'}
          </span>
        </div>
        {#if authStore.isAuthenticated}
          <p class="text-white/40 text-[11px] mt-0.5 leading-snug">
            {fmtVnd(todayReward)}.000đ tiền thưởng sẽ hết hạn sau
            <span class="text-[#FF9900] font-mono font-semibold">{countdownText}</span>
          </p>
        {:else}
          <p class="text-white/40 text-[11px] mt-0.5">Đăng nhập để xem số dư</p>
        {/if}
      </div>
      <button
        onclick={() => checkinStore.openHistory()}
        class="flex items-center gap-0.5 bg-white/8 border border-white/10 rounded-full px-3 py-1.5 text-white/55 text-[12px] font-medium mt-0.5"
      >
        Lịch sử <span class="text-white/30 ml-0.5 text-[11px]">›</span>
      </button>
    </div>
  </div>

  <!-- NHIỆM VỤ CARD (white) -->
  <div class="mx-3 mb-4 rounded-[16px] overflow-hidden flex-shrink-0" style="background:#ffffff;">
    <div class="px-4 pt-3 pb-2">
      <h3 class="font-bold text-[17px]" style="color:#1c1b22;">Nhiệm vụ thưởng</h3>
    </div>

    <!-- Day scroll -->
    <div class="flex gap-2.5 px-3 pb-4 overflow-x-auto" style="-ms-overflow-style:none;scrollbar-width:none;">
      {#each displayDays as d (d.day)}
        {@const active = d.is_today}
        {@const done  = d.is_completed}
        {@const w     = active ? 72  : 60}
        {@const h     = active ? 88  : 74}
        {@const bagSz = active ? 28  : 20}
        {@const bgSz  = active ? 18  : 13}

        <div class="flex-shrink-0 flex flex-col items-center" style="gap:6px;">
          <!-- Card -->
          <div
            class="relative flex flex-col items-center justify-center rounded-[14px]"
            style="
              width:{w}px; height:{h}px;
              background: {done && !active ? '#F5F5F5' : active ? 'linear-gradient(to bottom,#FFF9CC,#FFE566)' : '#F8F8F8'};
              border: {active ? '2px solid rgba(255,214,0,0.7)' : '1px solid #E8E8E8'};
              box-shadow: {active ? '0 4px 12px rgba(255,200,0,0.25)' : 'none'};
            "
          >
            <!-- Done overlay -->
            {#if done && !active}
              <div class="absolute inset-0 flex items-center justify-center rounded-[13px]" style="background:rgba(255,255,255,0.7);">
                <svg width="22" height="22" fill="none" viewBox="0 0 24 24" stroke="#C8960C" stroke-width="2.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/>
                </svg>
              </div>
            {/if}

            <!-- Stacked money bags -->
            <div class="relative" style="width:{w-12}px;height:{bagSz+10}px;">
              <span class="absolute" style="font-size:{bgSz}px;bottom:0;left:0;opacity:0.4;transform:rotate(-14deg);">💰</span>
              <span class="absolute" style="font-size:{Math.round(bgSz*1.15)}px;bottom:2px;left:{bgSz-4}px;opacity:0.65;transform:rotate(-5deg);">💰</span>
              <span class="absolute" style="font-size:{bagSz}px;bottom:0;right:0;">💰</span>
            </div>

            <!-- Reward badge -->
            {#if !done}
              <div
                class="rounded-full flex items-center justify-center"
                style="
                  margin-top:6px;
                  padding:1px 7px;
                  background:{active ? '#FFD600' : '#E0E0E0'};
                "
              >
                <span
                  class="font-black leading-none"
                  style="font-size:11px;color:{active ? '#4a3000' : '#888'};"
                >{fmtVnd(d.reward)}</span>
              </div>
            {/if}
          </div>

          <!-- Label -->
          <span
            class="font-semibold"
            style="font-size:10px;color:{active ? '#FF9900' : '#AAAAAA'};"
          >
            {active ? 'Hôm nay' : `Ngày ${d.day}`}
          </span>
        </div>
      {/each}
    </div>
  </div>

  <!-- CTA -->
  <div class="px-4 pb-8 flex-shrink-0">
    {#if isCheckedIn && authStore.isAuthenticated}
      <div class="w-full py-4 rounded-full flex items-center justify-center gap-2" style="background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.1);">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="#FFD700" stroke-width="2.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/>
        </svg>
        <span class="text-white/50 text-[14px] font-semibold">Đã nhận thưởng hôm nay</span>
      </div>
    {:else}
      <button
        onclick={handleClaim}
        disabled={checkinStore.claiming}
        class="relative w-full flex items-center justify-center gap-2.5 rounded-full font-bold text-[15px] text-white disabled:opacity-60 active:scale-[0.98] transition-all duration-150"
        style="padding:15px 0;background:#1f1e25;border:1px solid rgba(255,255,255,0.08);box-shadow:inset 0 1px 0 rgba(255,255,255,0.07);"
      >
        {#if checkinStore.claiming}
          <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
          </svg>
          <span>Đang nhận...</span>
        {:else if authStore.isAuthenticated}
          <span>Nhận phần thưởng của hôm nay</span>
          <span style="font-size:18px;">👆</span>
        {:else}
          <span>Đăng nhập để nhận thưởng</span>
          <span style="font-size:16px;">🔑</span>
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
          style="left:{p.x}%;top:{p.y}%;background:{p.color};animation-delay:{p.delay}ms;"
        ></div>
      {/each}
    </div>
  {/if}
</div>

<style>
  @keyframes confetti {
    0%   { transform: translateY(0) rotate(0deg); opacity: 1; }
    100% { transform: translateY(-160px) rotate(540deg); opacity: 0; }
  }
  .animate-confetti { animation: confetti 1.6s ease-out forwards; }
  .animate-spin { animation: spin 1s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
</style>
