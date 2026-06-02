<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { fly, fade, scale } from 'svelte/transition';
  import { browser } from '$app/environment';
  import { checkinStore } from '$lib/state/commerce/checkin.svelte';
  import { loyaltyStore } from '$lib/state/commerce/loyalty.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { authStore } from '$lib/state/authStore.svelte';
  import { LOYALTY_CONFIG } from '$lib/constants/loyalty';

  let { onClose }: { onClose: () => void } = $props();

  let countdownText = $state('');
  let countdownInterval: ReturnType<typeof setInterval> | null = null;
  let showConfetti = $state(false);
  let particles = $state<{ x: number; y: number; color: string; delay: number }[]>([]);

  const COLORS = ['#FFD700', '#FF6B35', '#FFA500', '#FFE066', '#FFFBE7'];



  let products = $state<any[]>([]);
  let isLoadingProducts = $state(true);

  async function loadProducts() {
    try {
      const res = await fetch('/api/v1/client/products?limit=50');
      if (res.ok) {
        const json = await res.json();
        const rawProducts = json.data || [];
        
        // Lọc sản phẩm có discount
        const activeProducts = rawProducts.filter((p: any) => {
          const price = p.price || 0;
          const discountPrice = p.discountPrice || p.discount_price || 0;
          return price > 0 && discountPrice > 0 && discountPrice < price;
        });

        const mappedProducts = activeProducts.map((p: any) => {
          const price = p.price;
          const discountPrice = p.discountPrice || p.discount_price;
          const discountAmount = price - discountPrice;
          const discountPercent = Math.round((discountAmount / price) * 100);
          
          return {
            id: p.id,
            name: p.name,
            image: p.mobileImages?.[0] || p.images?.[0] || '/favicon.svg',
            price: price,
            discountPrice: discountPrice,
            discountPercent: discountPercent,
            slug: p.slug
          };
        });

        // Sắp xếp theo phần trăm giảm giá giảm dần
        mappedProducts.sort((a: any, b: any) => b.discountPercent - a.discountPercent);

        // Lấy đúng 4 sản phẩm có mức khuyến mãi cao nhất
        products = mappedProducts.slice(0, 4);
      }
    } catch (e) {
      console.error("Failed to load live recommendation products:", e);
    } finally {
      isLoadingProducts = false;
    }
  }

  /**
   * Format giá sản phẩm (VNĐ) — dùng cho giá hiển thị trong danh sách sản phẩm
   */
  function fmtPrice(v: number): string {
    return v.toLocaleString('vi-VN') + 'đ';
  }

  /**
   * Format VNĐ money — đầu vào đã là VNĐ (dùng cho today_reward và days[].reward)
   * API trả về sẵn: today_reward=10000 (VNĐ), days[].reward=10000 (VNĐ)
   */
  function fmtVnd(vnd: number): string {
    return `${vnd.toLocaleString('vi-VN')}đ`;
  }

  /**
   * Format điểm sang VNĐ — đầu vào là ĐIỂM (dùng cho tx.amount và available_points)
   * DB lưu: available_points=1 (điểm), tx.amount=1 (điểm)
   */
  function fmtPts(pts: number): string {
    return fmtVnd(pts * LOYALTY_CONFIG.POINT_VALUE);
  }

  function calcCountdown(): string {
    const now = new Date();
    const utcMs = now.getTime() + now.getTimezoneOffset() * 60 * 1000;
    const vnNow = new Date(utcMs + 7 * 3600 * 1000);
    const midnight = new Date(vnNow);
    midnight.setHours(23, 59, 59, 999);
    const diff = Math.max(0, midnight.getTime() - vnNow.getTime());
    const h = Math.floor(diff / 3_600_000).toString().padStart(2, '0');
    const m = Math.floor((diff % 3_600_000) / 60_000).toString().padStart(2, '0');
    const s = Math.floor((diff % 60_000) / 1_000).toString().padStart(2, '0');
    return `${h}:${m}:${s}`;
  }

  let flyingCoins = $state<{ id: number; rx: number; ry: number; tx: number; ty: number; delay: number }[]>([]);

  function triggerCoinExplosion() {
    flyingCoins = Array.from({ length: 15 }, (_, i) => {
      const rx = (Math.random() - 0.5) * 80;
      const ry = -50 - Math.random() * 60;
      return {
        id: i,
        rx: rx,
        ry: ry,
        tx: -180 + (Math.random() - 0.5) * 20,
        ty: -290 + (Math.random() - 0.5) * 20,
        delay: i * 50
      };
    });
    setTimeout(() => {
      flyingCoins = [];
    }, 1800);
  }

  function spawnConfetti() {
    particles = Array.from({ length: 25 }, (_, i) => ({
      x: 20 + Math.random() * 60,
      y: 40 + Math.random() * 25,
      color: COLORS[i % COLORS.length],
      delay: i * 40,
    }));
    showConfetti = true;
    setTimeout(() => { showConfetti = false; particles = []; }, 2000);
  }

  async function handleClaim() {
    if (!authStore.isAuthenticated) {
      localStorage.setItem('osmo:loyalty:reopen_after_login', 'true');
      onClose();
      setTimeout(() => getClientUi().openLogin(), 200);
      return;
    }
    if (!checkinStore.canClaim || checkinStore.claiming) return;
    const ok = await checkinStore.claimReward();
    if (ok) {
      triggerCoinExplosion();
      spawnConfetti();
      const earnedVnd = checkinStore.status?.today_reward ?? 10000; // đã là VNĐ từ API
      const totalToday = checkinStore.status?.total_checkin_today ?? 569;
      getClientUi().showToast(
        `🎉 Tuyệt vời! Bạn cùng ${totalToday.toLocaleString('vi-VN')} người khác đã điểm danh hôm nay! (+${fmtVnd(earnedVnd)} đã được cộng vào ví)`,
        'success'
      );
      
      // Auto-save dismissal date so it won't pop up again today
      dontShowToday = true;
      localStorage.setItem('osmo:storefront:daily_checkin_dismissed_date', getVnDateString());
      
      // Auto-close (thu nhỏ thành icon) after animations finish
      setTimeout(() => {
        onClose();
      }, 1600);
    } else if (checkinStore.error) {
      if (!authStore.isAuthenticated || checkinStore.error.includes('đăng nhập')) {
        localStorage.setItem('osmo:loyalty:reopen_after_login', 'true');
        onClose();
        setTimeout(() => {
          getClientUi().openLogin();
          getClientUi().showToast(checkinStore.error || 'Phiên đăng nhập hết hạn, vui lòng đăng nhập lại!', 'warning');
        }, 300);
      } else {
        getClientUi().showToast(checkinStore.error, 'error');
      }
    }
  }

  let displayDays = $derived(checkinStore.status?.days ?? []);
  let isCheckedIn  = $derived(checkinStore.status?.is_checked_in_today ?? false);
  let todayReward  = $derived(checkinStore.status?.today_reward ?? 10000);
  let balance      = $derived(loyaltyStore.data?.available_points ?? 0);

  let completedCount = $derived(displayDays.filter(d => d.is_completed).length);
  let progressWidth  = $derived(
    completedCount <= 1 ? 0 : Math.min(384, (completedCount - 1) * 64)
  );

  let activeTab = $state<'history' | 'rules'>('history');

  function formatDate(dateStr: string) {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleString('vi-VN', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  function formatSetupPeriod(start?: string, end?: string): string {
    if (!start && !end) return '';
    const fmt = (d?: string) => {
      if (!d) return '';
      const parts = d.split('-');
      if (parts.length === 3) {
        return `${parts[2]}/${parts[1]}/${parts[0]}`;
      }
      return d;
    };
    if (start && end) return `Sự kiện: ${fmt(start)} - ${fmt(end)}`;
    if (start) return `Bắt đầu: ${fmt(start)}`;
    if (end) return `Hạn cuối: ${fmt(end)}`;
    return '';
  }

  function getVnDateString(): string {
    const now = new Date();
    const utcMs = now.getTime() + now.getTimezoneOffset() * 60000;
    const vnTime = new Date(utcMs + 7 * 3600000);
    const y = vnTime.getFullYear();
    const m = String(vnTime.getMonth() + 1).padStart(2, '0');
    const d = String(vnTime.getDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
  }

  let dontShowToday = $state(
    browser && localStorage.getItem('osmo:storefront:daily_checkin_dismissed_date') === getVnDateString()
  );

  // Elite V2.2: Reactive synchronization of dontShowToday with localStorage using Svelte 5 runes
  $effect(() => {
    if (dontShowToday) {
      localStorage.setItem('osmo:storefront:daily_checkin_dismissed_date', getVnDateString());
    } else {
      localStorage.removeItem('osmo:storefront:daily_checkin_dismissed_date');
    }
  });

  onMount(() => {
    countdownText = calcCountdown();
    countdownInterval = setInterval(() => { countdownText = calcCountdown(); }, 1000);
    loadProducts();
    if (authStore.isAuthenticated) {
      checkinStore.fetchStatus();
      loyaltyStore.fetchLoyalty();
    }
  });
  onDestroy(() => { if (countdownInterval) clearInterval(countdownInterval); });
</script>

<!-- Backdrop -->
<div
  role="button" tabindex="-1" aria-label="Đóng"
  class="fixed inset-0 z-[9998] bg-black/60 backdrop-blur-[3px]"
  onclick={onClose}
  onkeydown={(e) => e.key === 'Escape' && onClose()}
  transition:fade={{ duration: 200 }}
></div>

<!-- Bottom Sheet Mobile (Pixel-Perfect from Screenshot) -->
<div
  class="fixed bottom-0 left-0 right-0 z-[9999] w-full max-w-[480px] mx-auto rounded-t-[5px] overflow-hidden flex flex-col pointer-events-auto shadow-[0_-10px_35px_rgba(0,0,0,0.6)]"
  style="
    height: 85vh;
    background: linear-gradient(180deg, #09090c 0%, #1a160f 45%, #2a2012 100%);
    border-top: 1px solid rgba(255, 255, 255, 0.1);
  "
  transition:fly={{ y: 600, duration: 320 }}
>
  <!-- TOP HEADER (Modern 2026 Left-aligned style) -->
  <div class="flex items-start justify-between px-5 pt-6 pb-2 flex-shrink-0 text-white">
    <div class="flex flex-col gap-1.5">
      <h1 class="font-black text-[22px] tracking-tight leading-none text-white">Trung tâm thưởng</h1>
      
      <!-- Left-aligned Lịch sử & Quy định links -->
      <div class="flex items-center gap-3 mt-2">
        <button 
          onclick={() => { activeTab = 'history'; checkinStore.openHistory(); }} 
          class="text-white/60 hover:text-white text-[12px] font-bold tracking-wider flex items-center gap-1 transition-colors"
        >
          <span>Lịch sử tích lũy</span>
          <span class="text-white/30 text-[10px]">&rsaquo;</span>
        </button>
        <span class="w-1 h-1 rounded-full bg-white/20"></span>
        <button 
          onclick={() => { activeTab = 'rules'; checkinStore.openHistory(); }} 
          class="text-[#ffd600] hover:brightness-110 text-[12px] font-bold tracking-wider flex items-center gap-1 transition-colors"
        >
          <span>Quy định thưởng</span>
          <span class="text-[#ffd600]/50 text-[10px]">&rsaquo;</span>
        </button>
      </div>
    </div>

    <!-- Sleek X Close Button on the Right (No circle, Modern 2026) -->
    <button 
      onclick={onClose} 
      class="flex items-center justify-center w-6 h-6 text-white/50 hover:text-white active:scale-90 transition-all mt-0.5" 
      aria-label="Close"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/>
      </svg>
    </button>
  </div>

  <!-- BALANCE BLOCK -->
  <div class="px-5 pt-3 pb-5 flex-shrink-0 flex flex-col justify-start">
    <div class="flex items-center gap-1.5 mb-1.5">
      <!-- Premium round golden treasury coin -->
      <div class="w-7.5 h-7.5 rounded-full flex items-center justify-center bg-gradient-to-br from-[#FFD700] to-[#E5A93C] shadow-[0_2px_6px_rgba(229,169,60,0.3)]">
        <svg class="w-4.5 h-4.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.2">
          <circle cx="12" cy="12" r="9" />
          <path d="M12 6.5L7.5 9h9L12 6.5zM9 10v4.5M12 10v4.5M15 10v4.5M7 15.5h10" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </div>
      <span class="text-white font-black text-[30px] leading-none tracking-tight">
        {#if authStore.isAuthenticated}
          {fmtPts(balance)}
        {:else}
          10.000đ
        {/if}
      </span>
    </div>

    <!-- Countdown time -->
    <p class="text-[#a89e80] text-[11px] font-medium leading-none">
      {#if authStore.isAuthenticated}
        {fmtVnd(todayReward)} tiền thưởng sẽ hết hạn sau <span class="font-mono font-bold text-[#ff9900] ml-0.5">{countdownText}</span>
      {:else}
        10.000đ tiền thưởng sẽ hết hạn sau <span class="font-mono font-bold text-[#ff9900] ml-0.5">{countdownText}</span>
      {/if}
    </p>
  </div>

  <!-- WHITE BODY SCROLLABLE (Bottom Sheet Body) -->
  <div class="bg-white rounded-t-[28px] -mt-2.5 p-5 flex-1 overflow-y-auto scrollbar-hide flex flex-col">
    <!-- SECTION 1: NHIỆM VỤ THƯỞNG -->
    <div>
      <div class="flex items-center justify-between mb-4 flex-wrap gap-2">
        <h3 class="font-black text-[17px] tracking-wide text-black leading-none">Nhiệm vụ thưởng</h3>
        {#if checkinStore.status?.start_date || checkinStore.status?.end_date}
          <span class="text-[10px] font-bold text-gray-500 bg-gray-100 px-2.5 py-1 rounded-full leading-none">
            {formatSetupPeriod(checkinStore.status.start_date, checkinStore.status.end_date)}
          </span>
        {/if}
      </div>

      <!-- Timeline & Day Cards Container (ELITE V2.2: Full-Bleed Edge-to-Edge with symmetric offsets) -->
      <div class="relative flex items-center pb-6 mt-2 overflow-hidden -mx-5">
        <!-- Scrollable Cards Box -->
        <div class="relative w-full flex items-center gap-2.5 justify-start z-10 overflow-x-auto scrollbar-hide py-1 px-5">
          <!-- Horizontal Timeline Grey Connecting Line (Perfect Scroll Sync) -->
          <div class="absolute top-[31px] h-[2px] bg-gray-100 z-0" style="left: 47px; width: 384px;"></div>
          <!-- Horizontal Timeline Active Gold Connecting Line (Perfect Live Link) -->
          <div class="absolute top-[31px] h-[2px] bg-gradient-to-r from-[#FFD600] to-[#ff9900] z-0 transition-all duration-500 shadow-[0_1px_4px_rgba(255,214,0,0.4)]"
            style="left: 47px; width: {progressWidth}px;"></div>

          {#each displayDays as d (d.day)}
            {@const active = d.is_today}
            {@const done  = d.is_completed}

            <div class="flex-shrink-0 flex flex-col items-center gap-2" style="width: 54px;">
              <!-- Gold ingots / cards stack (Standardized height to 54px to prevent misalignment) -->
              <div
                class="relative flex flex-col items-center justify-center rounded-[12px] transition-all duration-300"
                style="
                  width: 54px;
                  height: 54px;
                  background: {active ? '#FFFBEB' : 'transparent'};
                  border: {active ? '1.5px solid #FFD600' : 'none'};
                  box-shadow: {active ? '0 4px 10px rgba(255, 214, 0, 0.25)' : 'none'};
                "
              >
                <!-- Gold ticket stack SVG -->
                <svg class="w-11 h-8 drop-shadow-[0_2.5px_4.5px_rgba(229,169,60,0.35)]" viewBox="0 0 50 36" fill="none">
                  <defs>
                    <linearGradient id="goldBack" x1="0" y1="0" x2="1" y2="1">
                      <stop offset="0%" stop-color="#FFF099"/>
                      <stop offset="100%" stop-color="#E6B800"/>
                    </linearGradient>
                    <linearGradient id="goldMid" x1="0" y1="0" x2="1" y2="1">
                      <stop offset="0%" stop-color="#FFE680"/>
                      <stop offset="100%" stop-color="#FFCC00"/>
                    </linearGradient>
                    <linearGradient id="goldFront" x1="0" y1="0" x2="1" y2="1">
                      <stop offset="0%" stop-color="#FFF5CC"/>
                      <stop offset="50%" stop-color="#FFD700"/>
                      <stop offset="100%" stop-color="#F5B041"/>
                    </linearGradient>
                  </defs>
                  <!-- Back card -->
                  <path d="M5 14L40 6C42 6 44 8 44 10L42 26C42 28 40 30 38 30L5 30" fill="url(#goldBack)" opacity="0.5"/>
                  <!-- Mid card -->
                  <path d="M8 10L43 4C45 4 47 6 47 8L45 24C45 26 43 28 41 28L8 28" fill="url(#goldMid)" opacity="0.75"/>
                  <!-- Front card -->
                  <rect x="2" y="10" width="38" height="22" rx="3" fill="url(#goldFront)"/>
                  <rect x="2" y="10" width="38" height="22" rx="3" stroke="#FFF" stroke-width="0.7" opacity="0.4"/>
                  <!-- Reward text on card -->
                  <text x="21" y="24.5" font-family="system-ui, -apple-system" font-size="7.5" font-weight="900" fill="#6E4D00" text-anchor="middle" letter-spacing="-0.3">
                    {fmtVnd(d.reward)}
                  </text>
                </svg>
              </div>

              <!-- Indicator Lock or Dot (Perfect layout alignment) -->
              <div class="h-4 flex items-center justify-center">
                {#if active}
                  <span class="w-2.5 h-2.5 rounded-full bg-[#f44336] shadow-sm animate-pulse"></span>
                {:else if done}
                  <!-- Checkmark if done -->
                  <svg class="w-3.5 h-3.5 text-[#ff9900]" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
                  </svg>
                {:else}
                  <!-- Grey padlock -->
                  <svg class="w-3 h-3 text-gray-300" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z"/>
                  </svg>
                {/if}
              </div>

              <!-- Label text -->
              <span class="font-extrabold text-[11px] leading-tight transition-colors duration-300" style="color: {active ? '#000000' : '#9CA3AF'};">
                {active ? 'Hôm nay' : `Ngày ${d.day}`}
              </span>
            </div>
          {/each}
        </div>
      </div>
    </div>

    <!-- CTA BẰNG NÚT CAPSULE TỐI MỸ THUẬT -->
    <div class="mt-4 flex flex-col items-center">
      {#if isCheckedIn && authStore.isAuthenticated}
        <div class="w-full py-4 rounded-full bg-gray-50 border border-gray-100 flex items-center justify-center gap-2">
          <svg class="w-4 h-4 text-[#ff9900]" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
          </svg>
          <span class="text-gray-400 text-[14px] font-bold">Đã nhận phần thưởng hôm nay</span>
        </div>
      {:else}
        <!-- Dark capsule CTA with gold peach text -->
        <button
          onclick={handleClaim}
          disabled={checkinStore.claiming}
          class="relative w-full py-4 rounded-full overflow-visible
            text-[#f5d7af] font-black text-[15px] tracking-wide
            shadow-[0_8px_25px_rgba(35,27,21,0.25)]
            hover:brightness-110 active:scale-[0.98]
            disabled:opacity-60 transition-all duration-150
            flex items-center justify-center gap-2"
          style="
            background: #231b15;
            border: 1.5px solid #2e241d;
          "
        >
          {#if checkinStore.claiming}
            <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
            </svg>
            Đang nhận thưởng...
          {:else if authStore.isAuthenticated}
            <span>Nhận phần thưởng của hôm nay</span>
          {:else}
            <span>Đăng nhập để nhận thưởng</span>
          {/if}

          <!-- Micro-animated bouncy pointing hand 👉 at bottom right -->
          <div class="absolute -right-1.5 -bottom-2.5 w-11 h-11 pointer-events-none animate-bounce-hand">
            <span class="text-[32px] block" style="transform: rotate(-135deg);">👉</span>
          </div>
        </button>
      {/if}

      <!-- Opt-out option checkbox below CTA (Always visible to ensure UI consistency and prevent layout confusion) -->
      <div class="flex items-center justify-center gap-1.5 mt-4 select-none">
        <label class="flex items-center gap-2 cursor-pointer text-gray-400 hover:text-gray-600 transition-colors text-[12px] font-semibold">
          <input
            type="checkbox"
            bind:checked={dontShowToday}
            class="rounded border-gray-300 bg-gray-50 text-[#ff9900] focus:ring-0 focus:ring-offset-0 w-3.5 h-3.5 cursor-pointer"
          />
          <span>Không hiển thị lại hôm nay</span>
        </label>
      </div>
    </div>

    <!-- TIẾT KIỆM THÊM VỚI TIỀN THƯỞNG (Shopping Recommendations) -->
    <div class="mt-8 flex-1 flex flex-col">
      <h3 class="font-black text-[17px] tracking-wide text-black mb-4">Tiết kiệm thêm với tiền thưởng</h3>

      {#if isLoadingProducts}
        <div class="grid grid-cols-2 gap-3.5 pb-6">
          {#each Array(4) as _}
            <div class="flex flex-col bg-[#F9F9FB] rounded-[16px] overflow-hidden animate-pulse border border-gray-100/50">
              <div class="w-full aspect-square bg-gray-200"></div>
              <div class="p-3 flex flex-col gap-2">
                <div class="h-4 bg-gray-200 rounded w-5/6"></div>
                <div class="h-4 bg-gray-200 rounded w-3/4"></div>
                <div class="h-3 bg-gray-200 rounded w-1/2 mt-1"></div>
              </div>
            </div>
          {/each}
        </div>
      {:else if products.length > 0}
        <!-- 2 Columns Product Grid -->
        <div class="grid grid-cols-2 gap-3.5 pb-6">
          {#each products as p (p.id)}
            <div class="flex flex-col bg-[#F9F9FB] rounded-[16px] overflow-hidden shadow-[0_2px_8px_rgba(0,0,0,0.02)] border border-gray-100/50">
              <!-- Product Image -->
              <div class="relative w-full aspect-square bg-gray-100 overflow-hidden">
                <img src={p.image} alt={p.name} class="w-full h-full object-cover" />
              </div>

              <!-- Content -->
              <div class="p-3 flex flex-col flex-1">
                <!-- Title -->
                <h4 class="font-bold text-[12.5px] leading-tight text-gray-800 line-clamp-2 min-h-[34px] mb-2.5">
                  {p.name}
                </h4>

                <!-- Tags container -->
                <div class="flex flex-wrap gap-1 mb-3">
                  <!-- Tag 1: Freeship -->
                  <span class="text-[9px] font-extrabold px-1.5 py-0.5 rounded-[4px] bg-[#e0f7f4] text-[#00a896]">
                    XTRA Freeship
                  </span>
                  <!-- Tag 2: Discount Percent -->
                  <span class="text-[9px] font-extrabold px-1.5 py-0.5 rounded-[4px] bg-[#ffebee] text-[#e53935]">
                    EXTRA Giảm {p.discountPercent}%
                  </span>
                  <!-- Tag 3: Cashback -->
                  <span class="text-[9px] font-extrabold px-1.5 py-0.5 rounded-[4px] bg-[#fffde7] text-[#fbc02d]">
                    Bonus Hoàn tiền
                  </span>
                </div>

                <!-- Price & Buy Button Row -->
                <div class="mt-auto flex items-center justify-between">
                  <div class="flex flex-col">
                    <span class="text-[#ff9900] font-extrabold text-[13px] leading-none mb-0.5">{fmtPrice(p.discountPrice)}</span>
                    <span class="text-gray-400 text-[10px] line-through leading-none">{fmtPrice(p.price)}</span>
                  </div>
                  <button 
                    onclick={() => window.open('/' + p.slug, '_blank')}
                    class="bg-[#231b15] hover:opacity-90 active:scale-95 text-[#f5d7af] text-[10px] font-extrabold px-2.5 py-1.5 rounded-full transition-all"
                  >
                    Mua ngay
                  </button>
                </div>
              </div>
            </div>
          {/each}
        </div>
      {:else}
        <div class="py-6 text-center text-gray-400 text-sm">
          Không có sản phẩm khuyến mãi nào khả dụng.
        </div>
      {/if}
    </div>
  </div>

  <!-- DYNAMIC RULES & HISTORY BOTTOM PANEL (Sheet-in-Sheet transition) -->
  {#if checkinStore.showHistory}
    <div
      class="absolute inset-x-0 bottom-0 z-50 bg-white rounded-t-[24px] shadow-[0_-15px_40px_rgba(0,0,0,0.2)] flex flex-col pointer-events-auto"
      style="top: 146px; height: auto; border-top: 1px solid rgba(0, 0, 0, 0.06);"
      transition:fly={{ y: 500, duration: 280 }}
    >
      <!-- Header drag bar indicator -->
      <button 
        onclick={() => checkinStore.closeHistory()}
        class="w-12 h-1 bg-gray-200 hover:bg-gray-300 rounded-full mx-auto mt-3 mb-1.5 flex-shrink-0 cursor-pointer active:scale-95 transition-all"
        aria-label="Đóng"
      ></button>

      <!-- Header panel title & Close (Sleek X, No circle background) -->
      <div class="flex items-center px-5 py-3 flex-shrink-0 border-b border-gray-50">
        <span class="font-black text-[18px] text-gray-900 tracking-wide">
          Lịch sử tích lũy
        </span>
      </div>

      <!-- Modern Tab Switcher Pill -->
      <div class="flex bg-gray-100/70 p-1 rounded-full mx-5 my-4.5 flex-shrink-0">
        <button 
          onclick={() => activeTab = 'history'} 
          class="flex-1 py-2 text-[11px] font-black tracking-wider rounded-full transition-all duration-200
            {activeTab === 'history' ? 'bg-[#231b15] text-[#f5d7af] shadow-md' : 'text-gray-500 hover:text-gray-800'}"
        >
          LỊCH SỬ NHẬN
        </button>
        <button 
          onclick={() => activeTab = 'rules'} 
          class="flex-1 py-2 text-[11px] font-black tracking-wider rounded-full transition-all duration-200
            {activeTab === 'rules' ? 'bg-[#231b15] text-[#f5d7af] shadow-md' : 'text-gray-500 hover:text-gray-800'}"
        >
          QUY ĐỊNH CHUNG
        </button>
      </div>

      <!-- Tab Content (Scrollable) -->
      <div class="flex-1 overflow-y-auto px-5 pb-8 scrollbar-hide">
        {#if activeTab === 'history'}
          <!-- HISTORY VIEW -->
          {#if !authStore.isAuthenticated}
            <div class="flex flex-col items-center justify-center py-12 text-center animate-fade-in">
              <span class="text-4xl mb-3">🔑</span>
              <h5 class="text-gray-900 font-black text-[14px]">Yêu cầu đăng nhập</h5>
              <p class="text-gray-400 text-[11px] mt-1 max-w-[200px] leading-normal font-medium mb-4">
                Lịch sử tích lũy chỉ hiển thị khi tài khoản đã được xác thực.
              </p>
              <button
                onclick={() => {
                  localStorage.setItem('osmo:loyalty:reopen_after_login', 'true');
                  onClose();
                  setTimeout(() => getClientUi().openLogin(), 200);
                }}
                class="px-6 py-2.5 rounded-full bg-[#231b15] text-[#f5d7af] font-black text-[12px] tracking-wider hover:brightness-110 active:scale-95 shadow-md transition-all duration-150"
              >
                ĐĂNG NHẬP NGAY
              </button>
            </div>
          {:else if loyaltyStore.loading}
            <div class="flex flex-col items-center justify-center py-16">
              <div class="w-7 h-7 border-2 border-gray-100 border-t-[#ff9900] rounded-full animate-spin"></div>
            </div>
          {:else if !loyaltyStore.data?.history || loyaltyStore.data.history.length === 0}
            <div class="flex flex-col items-center justify-center py-16 text-center">
              <span class="text-4xl mb-3">⏱️</span>
              <h5 class="text-gray-800 font-black text-[14px]">Chưa có biến động điểm</h5>
              <p class="text-gray-400 text-[11px] mt-1 max-w-[200px] leading-normal font-medium">Hãy nhận phần thưởng hôm nay để bắt đầu tích luỹ ví điểm nhé!</p>
            </div>
          {:else}
            <div class="space-y-3">
              {#each loyaltyStore.data.history as tx}
                <div class="flex items-center justify-between p-3.5 bg-gray-50/70 rounded-[16px] border border-gray-100/50">
                  <div class="flex items-center gap-3">
                    <!-- Premium golden treasury coin vector -->
                    <div class="w-8.5 h-8.5 rounded-full flex items-center justify-center bg-gradient-to-br from-[#FFD700] to-[#E5A93C] shadow-[0_2px_6px_rgba(229,169,60,0.25)] flex-shrink-0">
                      <svg class="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.2">
                        <circle cx="12" cy="12" r="9" />
                        <path d="M12 6.5L7.5 9h9L12 6.5zM9 10v4.5M12 10v4.5M15 10v4.5M7 15.5h10" stroke-linecap="round" stroke-linejoin="round"/>
                      </svg>
                    </div>
                    <div class="flex flex-col">
                      <span class="text-gray-800 font-bold text-[13px] tracking-tight">{tx.notes || 'Điểm danh hàng ngày'}</span>
                      <span class="text-gray-400 text-[10px] font-medium mt-0.5">{formatDate(tx.created_at)}</span>
                    </div>
                  </div>
                  <div class="flex flex-col items-end">
                    <span class="text-[14.5px] font-black text-green-600 tracking-tight">
                      +{(tx.amount * LOYALTY_CONFIG.POINT_VALUE).toLocaleString('vi-VN')}đ
                    </span>
                    <span class="text-[8px] font-bold text-gray-400 uppercase tracking-widest mt-0.5">Tiền thưởng</span>
                  </div>
                </div>
              {/each}
            </div>
          {/if}
        {:else}
          <!-- RULES VIEW -->
          <div class="space-y-4">
            <!-- Rule 1 -->
            <div class="flex items-start gap-4.5 p-4 bg-amber-50/20 rounded-[18px] border border-amber-100/30">
              <span class="text-2xl mt-0.5">🎁</span>
              <div class="flex-1">
                <h4 class="font-black text-[13.5px] text-[#8c6200] tracking-wide mb-1">ĐIỂM DANH MỖI NGÀY</h4>
                <p class="text-[11.5px] text-gray-600 leading-relaxed font-medium">
                  Mỗi ngày điểm danh, bạn nhận ngay <strong class="text-amber-700">10.000đ</strong> vào ví tích lũy của cửa hàng để mua sắm.
                </p>
              </div>
            </div>

            <!-- Rule 2 -->
            <div class="flex items-start gap-4.5 p-4 bg-orange-50/20 rounded-[18px] border border-orange-100/30">
              <span class="text-2xl mt-0.5">🔥</span>
              <div class="flex-1">
                <h4 class="font-black text-[13.5px] text-[#a04000] tracking-wide mb-1">DUY TRÌ CHUỖI LIÊN TỤC</h4>
                <p class="text-[11.5px] text-gray-600 leading-relaxed font-medium">
                  Không bỏ lỡ ngày nào! Đạt chuỗi liên tục đến <strong class="text-orange-700">Ngày 7</strong> để nhận phần quà cực lớn nhân đôi giá trị!
                </p>
              </div>
            </div>

            <!-- Rule 3 -->
            <div class="flex items-start gap-4.5 p-4 bg-teal-50/20 rounded-[18px] border border-teal-100/30">
              <span class="text-2xl mt-0.5">🛒</span>
              <div class="flex-1">
                <h4 class="font-black text-[13.5px] text-[#006050] tracking-wide mb-1">TIẾT KIỆM KHI MUA SẮM</h4>
                <p class="text-[11.5px] text-gray-600 leading-relaxed font-medium">
                  Điểm thưởng được áp dụng trừ trực tiếp vào hóa đơn của bạn. Mua sắm thông minh và tiết kiệm tối đa cùng Elite.
                </p>
              </div>
            </div>

            <!-- Rule 4 -->
            <div class="flex items-start gap-4.5 p-4 bg-slate-50/70 rounded-[18px] border border-slate-100">
              <span class="text-2xl mt-0.5">⏳</span>
              <div class="flex-1">
                <h4 class="font-black text-[13.5px] text-[#475569] tracking-wide mb-1">CHÍNH SÁCH BẢO VỆ</h4>
                <p class="text-[11.5px] text-gray-500 leading-relaxed font-medium">
                  Chính sách bảo vệ biên lợi nhuận Elite V2.2: Áp dụng tối đa 1% giá trị mỗi đơn hàng. Điểm thưởng có thời hạn sử dụng theo quy định của hệ thống.
                </p>
              </div>
            </div>
          </div>
        {/if}
      </div>
    </div>
  {/if}
</div>

<!-- Confetti Canvas/Overlay -->
{#if showConfetti}
  <div class="fixed inset-0 pointer-events-none overflow-hidden z-[10000]" aria-hidden="true">
    {#each particles as p}
      <div class="absolute w-1.5 h-1.5 rounded-sm animate-confetti"
        style="left:{p.x}%;top:{p.y}%;background:{p.color};animation-delay:{p.delay}ms;"
      ></div>
    {/each}
  </div>
{/if}

<!-- Golden Coins Flying Animation -->
{#if flyingCoins.length > 0}
  <div class="fixed inset-0 pointer-events-none overflow-hidden z-[10000]" aria-hidden="true">
    {#each flyingCoins as coin (coin.id)}
      <div
        class="absolute w-6 h-6 rounded-full bg-gradient-to-br from-[#FFD700] to-[#E5A93C] border border-white flex items-center justify-center shadow-lg animate-coin-fly"
        style="
          left: 50%;
          top: 65%;
          transform: translate(-50%, -50%);
          --rx: {coin.rx}px;
          --ry: {coin.ry}px;
          --tx: {coin.tx}px;
          --ty: {coin.ty}px;
          animation-delay: {coin.delay}ms;
        "
      >
        <span class="text-[11px] select-none">🪙</span>
      </div>
    {/each}
  </div>
{/if}

<style>
  .scrollbar-hide::-webkit-scrollbar {
    display: none;
  }
  @keyframes confetti {
    0%   { transform: translateY(0) rotate(0deg); opacity: 1; }
    100% { transform: translateY(-160px) rotate(540deg); opacity: 0; }
  }
  .animate-confetti { animation: confetti 1.6s ease-out forwards; }
  .animate-spin { animation: spin 1s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }

  /* Micro-animation for bouncing pointing hand */
  @keyframes bounce-hand {
    0%, 100% { transform: translate(0, 0); }
    50%      { transform: translate(-5px, -5px); }
  }
  .animate-bounce-hand {
    animation: bounce-hand 1.2s infinite ease-in-out;
  }

  /* Flying coins animation */
  @keyframes coin-fly-anim {
    0% {
      transform: translate(-50%, -50%) scale(0.3) rotate(0deg);
      opacity: 0;
    }
    15% {
      transform: translate(calc(-50% + var(--rx)), calc(-50% + var(--ry))) scale(1.3) rotate(90deg);
      opacity: 1;
    }
    100% {
      transform: translate(calc(-50% + var(--tx)), calc(-50% + var(--ty))) scale(0.5) rotate(360deg);
      opacity: 0;
    }
  }
  .animate-coin-fly {
    animation: coin-fly-anim 1.2s cubic-bezier(0.25, 1, 0.5, 1) forwards;
  }
</style>
