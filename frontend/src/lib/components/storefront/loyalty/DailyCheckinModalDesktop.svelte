<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { fly, fade, scale } from 'svelte/transition';
  import { checkinStore } from '$lib/state/commerce/checkin.svelte';
  import { loyaltyStore } from '$lib/state/commerce/loyalty.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { authStore } from '$lib/state/authStore.svelte';

  let { onClose }: { onClose: () => void } = $props();

  let countdownText = $state('');
  let cInterval: ReturnType<typeof setInterval> | null = null;
  let showConfetti = $state(false);
  let particles = $state<{x:number;y:number;color:string;d:number}[]>([]);

  const COLORS = ['#FFD700','#FF6B35','#FFA500','#FFE066','#FFFBE7','#FF9900'];

  function calcCountdown() {
    const now = new Date();
    const vnMs = now.getTime() + 7*3600*1000;
    const vnNow = new Date(vnMs);
    const end = new Date(vnMs);
    end.setUTCHours(23,59,59,999);
    const diff = Math.max(0, end.getTime() - vnNow.getTime());
    const h = Math.floor(diff/3600000).toString().padStart(2,'0');
    const m = Math.floor((diff%3600000)/60000).toString().padStart(2,'0');
    const s = Math.floor((diff%60000)/1000).toString().padStart(2,'0');
    return `${h}:${m}:${s}`;
  }

  function spawnConfetti() {
    particles = Array.from({length:30},(_,i)=>({
      x: 25 + Math.random()*50, y: 55,
      color: COLORS[i%COLORS.length],
      d: i*35,
    }));
    showConfetti = true;
    setTimeout(()=>{showConfetti=false;particles=[];},2200);
  }

  async function handleClaim() {
    if (!authStore.isAuthenticated) {
      onClose();
      setTimeout(()=>getClientUi().openLogin(),200);
      return;
    }
    if (!checkinStore.canClaim || checkinStore.claiming) return;
    const ok = await checkinStore.claimReward();
    if (ok) {
      spawnConfetti();
      getClientUi().showToast(`🎉 Nhận ${fmtVnd(checkinStore.status?.today_reward??100)} xu thành công!`,'success');
    } else if (checkinStore.error) {
      getClientUi().showToast(checkinStore.error,'error');
    }
  }

  function fmtVnd(v:number):string {
    if(v>=1000) return `${Math.round(v/1000)}K`;
    return String(v);
  }

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

  let displayDays = $derived(
    checkinStore.status?.days?.length ? checkinStore.status.days : PREVIEW_DAYS
  );
  let days = $derived(checkinStore.status?.days ?? []);
  let isCheckedIn = $derived(checkinStore.status?.is_checked_in_today ?? false);
  let streak = $derived(checkinStore.status?.current_streak ?? 0);
  let cycleLen = $derived(checkinStore.status?.cycle_length ?? 7);
  let todayReward = $derived(checkinStore.status?.today_reward ?? 100);
  let balance = $derived(loyaltyStore.data?.available_points ?? 0);
  let totalToday = $derived(checkinStore.status?.total_checkin_today ?? 0);

  onMount(()=>{
    countdownText = calcCountdown();
    cInterval = setInterval(()=>{countdownText=calcCountdown();},1000);
  });
  onDestroy(()=>{ if(cInterval) clearInterval(cInterval); });
</script>

<!-- Backdrop -->
<div
  role="button" tabindex="-1" aria-label="Đóng"
  class="fixed inset-0 z-[9998] bg-black/65 backdrop-blur-[2px]"
  onclick={onClose}
  onkeydown={(e)=>e.key==='Escape'&&onClose()}
  transition:fade={{duration:200}}
></div>

<!-- Center dialog -->
<div class="fixed inset-0 z-[9999] flex items-center justify-center p-4">
  <div
    class="relative w-full max-w-[420px] rounded-[24px] overflow-hidden shadow-2xl"
    style="background: #18181f;"
    transition:scale={{duration:280,start:0.94}}
  >
    <!-- ── TOP HEADER ──────────────────────── -->
    <div class="flex items-center justify-between px-5 py-4 border-b border-white/6">
      <button onclick={onClose} class="flex items-center gap-2 text-white/75 hover:text-white transition-colors">
        <span class="text-xl font-light leading-none mt-[-1px]">×</span>
        <span class="font-semibold text-[15px]">Trung tâm thưởng</span>
      </button>
      <button onclick={()=>checkinStore.openHistory()} class="text-[#FF9900] text-[13px] font-medium hover:underline">
        Quy định
      </button>
    </div>

    <!-- ── BALANCE ─────────────────────────── -->
    <div class="px-5 py-4 border-b border-white/6">
      <div class="flex items-start justify-between">
        <div>
          <div class="flex items-center gap-1.5 mb-1">
            <span class="text-[24px]">🪙</span>
            <span class="text-[#FFD700] font-black text-[28px] leading-none tracking-tight">
              {#if authStore.isAuthenticated}
                {fmtVnd(balance)}đ
              {:else}
                --đ
              {/if}
            </span>
          </div>
          {#if authStore.isAuthenticated}
            <p class="text-white/40 text-[12px]">
              {fmtVnd(todayReward)}.000đ tiền thưởng sẽ hết hạn sau
              <span class="text-[#FF9900] font-mono font-semibold">{countdownText}</span>
            </p>
          {:else}
            <p class="text-white/35 text-[12px]">Đăng nhập để xem và nhận xu điểm danh</p>
          {/if}
        </div>
        <button
          onclick={()=>checkinStore.openHistory()}
          class="flex items-center gap-1 text-white/55 text-[12px] font-medium bg-white/7 hover:bg-white/12 transition-colors border border-white/10 rounded-full px-3 py-1.5 mt-0.5"
        >Lịch sử <span class="text-white/30">›</span></button>
      </div>

      <!-- Social proof -->
      {#if totalToday > 0}
        <div class="flex items-center gap-1.5 mt-3">
          <span class="inline-block w-1.5 h-1.5 rounded-full bg-[#FF9900] animate-pulse"></span>
          <span class="text-white/35 text-[11px]">
            🔥 <strong class="text-white/50">{totalToday.toLocaleString('vi-VN')}</strong> người đã điểm danh hôm nay
          </span>
        </div>
      {/if}
    </div>

    <!-- ── MISSION CARD ────────────────────── -->
    <div class="mx-4 my-4 bg-white rounded-[16px] overflow-hidden">
      <div class="px-4 pt-4 pb-2">
        <h3 class="font-bold text-[#1a1a1a] text-[15px]">Nhiệm vụ thưởng</h3>
      </div>

      <div class="flex gap-2.5 px-4 pb-4 overflow-x-auto" style="-ms-overflow-style:none;scrollbar-width:none;">
        {#each displayDays as d (d.day)}
          {@const active = d.is_today}
          {@const done  = d.is_completed}
          {@const w     = active ? 72  : 58}
          {@const h     = active ? 88  : 74}
          {@const bagSz = active ? 26  : 18}
          {@const bgSz  = active ? 16  : 12}

          <div class="flex-shrink-0 flex flex-col items-center" style="gap:6px;">
            <div
              class="relative flex flex-col items-center justify-center rounded-[14px]"
              style="
                width:{w}px; height:{h}px;
                background:{done && !active ? '#F5F5F5' : active ? 'linear-gradient(to bottom,#FFF9CC,#FFE566)' : '#F8F8F8'};
                border:{active ? '2px solid rgba(255,214,0,0.7)' : '1px solid #E8E8E8'};
                box-shadow:{active ? '0 4px 12px rgba(255,200,0,0.25)' : 'none'};
              "
            >
              <!-- Done overlay -->
              {#if done && !active}
                <div class="absolute inset-0 flex items-center justify-center rounded-[13px]" style="background:rgba(255,255,255,0.75);">
                  <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="#C8960C" stroke-width="2.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/>
                  </svg>
                </div>
              {/if}

              <!-- Stacked money bags -->
              <div class="relative" style="width:{w-14}px;height:{bagSz+10}px;">
                <span class="absolute" style="font-size:{bgSz}px;bottom:0;left:0;opacity:0.4;transform:rotate(-14deg);">💰</span>
                <span class="absolute" style="font-size:{Math.round(bgSz*1.2)}px;bottom:2px;left:{bgSz-2}px;opacity:0.65;transform:rotate(-5deg);">💰</span>
                <span class="absolute" style="font-size:{bagSz}px;bottom:0;right:0;">💰</span>
              </div>

              <!-- Reward badge -->
              {#if !done}
                <div class="rounded-full" style="margin-top:6px;padding:1px 7px;background:{active?'#FFD600':'#E0E0E0'};">
                  <span class="font-black leading-none" style="font-size:10px;color:{active?'#4a3000':'#888'};">
                    {fmtVnd(d.reward)}
                  </span>
                </div>
              {/if}
            </div>

            <span class="font-semibold" style="font-size:10px;color:{active?'#FF9900':'#AAAAAA'};">
              {active ? 'Hôm nay' : `Ngày ${d.day}`}
            </span>
          </div>
        {/each}
      </div>


      <!-- Streak progress bar inside white card -->
      {#if streak > 0 || isCheckedIn}
        <div class="mx-4 mb-4 h-1.5 bg-gray-100 rounded-full overflow-hidden">
          <div
            class="h-full bg-gradient-to-r from-[#FFD700] to-[#FF9900] rounded-full transition-all duration-700"
            style="width:{Math.min(100,(streak/cycleLen)*100)}%"
          ></div>
        </div>
      {/if}
    </div>

    <!-- ── CTA ─────────────────────────────── -->
    <div class="px-4 pb-5">
      {#if isCheckedIn && authStore.isAuthenticated}
        <div class="w-full py-[14px] rounded-full bg-white/5 border border-white/8 flex items-center justify-center gap-2">
          <svg class="w-4 h-4 text-[#FFD700]" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/>
          </svg>
          <span class="text-white/45 text-[14px] font-semibold">Đã nhận thưởng hôm nay</span>
        </div>
        <p class="text-center text-white/25 text-[11px] mt-2.5">
          Quay lại ngày mai để duy trì chuỗi {streak} ngày 🔥
        </p>
      {:else}
        <button
          onclick={handleClaim}
          disabled={checkinStore.claiming}
          class="relative w-full py-[15px] rounded-full overflow-hidden
            bg-[#1f1e24] border border-white/10
            text-white font-bold text-[15px]
            shadow-[inset_0_1px_0_rgba(255,255,255,0.06),0_4px_24px_rgba(0,0,0,0.4)]
            hover:bg-[#2a2933] active:scale-[0.98]
            disabled:opacity-60 transition-all duration-150
            flex items-center justify-center gap-2.5"
        >
          {#if checkinStore.claiming}
            <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
            </svg>
            Đang nhận thưởng...
          {:else if authStore.isAuthenticated}
            <span>Nhận phần thưởng của hôm nay</span>
            <span class="text-[18px]">👆</span>
          {:else}
            <span>Đăng nhập để nhận thưởng</span>
            <span class="text-[16px]">🔑</span>
          {/if}
        </button>

        <!-- Tomorrow tease -->
        {#if authStore.isAuthenticated}
          {@const nextDay = days.find(d => d.day === streak + 2)}
          {#if nextDay}
            <p class="text-center text-white/30 text-[11px] mt-2.5">
              Mai nhận thêm <strong class="text-[#FFD700]/60">{fmtVnd(nextDay.reward)} xu</strong> — giữ chuỗi nhé!
            </p>
          {/if}
        {/if}
      {/if}
    </div>

    <!-- Confetti -->
    {#if showConfetti}
      <div class="absolute inset-0 pointer-events-none overflow-hidden z-20" aria-hidden="true">
        {#each particles as p}
          <div class="absolute w-2 h-1.5 rounded-sm animate-confetti"
            style="left:{p.x}%;top:{p.y}%;background:{p.color};animation-delay:{p.d}ms;"
          ></div>
        {/each}
      </div>
    {/if}
  </div>
</div>

<style>
  .scrollbar-hide{-ms-overflow-style:none;scrollbar-width:none;}
  .scrollbar-hide::-webkit-scrollbar{display:none;}
  @keyframes confetti{
    0%{transform:translateY(0) rotate(0deg) scaleX(1);opacity:1;}
    100%{transform:translateY(-200px) rotate(720deg) scaleX(0.5);opacity:0;}
  }
  .animate-confetti{animation:confetti 1.8s cubic-bezier(.25,.46,.45,.94) forwards;}
</style>
