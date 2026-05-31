<script lang="ts">
  /**
   * DailyCheckinLanding.svelte
   * Controller thông minh: Tự động load trạng thái, quyết định render Mobile/Desktop,
   * hiển thị Floating Trigger Button nếu user chưa điểm danh.
   */
  import { onMount } from 'svelte';
  import { fade, scale } from 'svelte/transition';
  import { checkinStore } from '$lib/state/commerce/checkin.svelte';
  import { authStore } from '$lib/state/authStore.svelte';
  import DailyCheckinModalMobile from './DailyCheckinModalMobile.svelte';
  import DailyCheckinModalDesktop from './DailyCheckinModalDesktop.svelte';

  // Responsive: detect mobile vs desktop
  let isMobile = $state(false);

  function updateIsMobile() {
    isMobile = window.innerWidth < 768;
  }

  // Fetch trạng thái điểm danh 1 lần khi mount (nếu đã login)
  onMount(() => {
    updateIsMobile();
    window.addEventListener('resize', updateIsMobile);

    if (authStore.isAuthenticated) {
      checkinStore.fetchStatus();
    }

    return () => {
      window.removeEventListener('resize', updateIsMobile);
    };
  });

  function handleClose() {
    checkinStore.closePopup();
  }
</script>

<!-- Floating Trigger: Chỉ hiện khi đã login, chưa điểm danh hôm nay, popup đang đóng -->
{#if authStore.isAuthenticated && checkinStore.status && !checkinStore.status.is_checked_in_today && !checkinStore.showPopup}
  <button
    onclick={() => checkinStore.openPopup()}
    class="fixed bottom-24 right-4 z-[9990] md:bottom-8 md:right-6 group"
    aria-label="Nhận thưởng điểm danh hàng ngày"
    transition:scale={{ duration: 300, start: 0.8 }}
  >
    <!-- Outer pulse ring -->
    <div class="absolute inset-0 rounded-full bg-[#FFD700] opacity-30 animate-ping"></div>
    <!-- Second pulse (delayed) -->
    <div class="absolute inset-0 rounded-full bg-[#FFD700] opacity-20 animate-ping" style="animation-delay: 0.4s"></div>
    
    <!-- Button body -->
    <div class="relative w-14 h-14 md:w-16 md:h-16 rounded-full
      bg-gradient-to-br from-[#FFD700] to-[#F7B731]
      shadow-[0_8px_24px_rgba(255,215,0,0.5)]
      flex items-center justify-center
      group-hover:scale-110 transition-transform duration-200">
      <span class="text-2xl md:text-3xl">🎁</span>
    </div>

    <!-- Tooltip badge -->
    <div class="absolute -top-8 left-1/2 -translate-x-1/2 bg-[#1a1a2e] border border-[#FFD700]/30
      text-[#FFD700] text-[10px] font-bold px-2 py-1 rounded-full whitespace-nowrap
      opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none">
      Nhận thưởng!
    </div>
  </button>
{/if}

<!-- Popup Modals -->
{#if checkinStore.showPopup}
  {#if isMobile}
    <DailyCheckinModalMobile onClose={handleClose} />
  {:else}
    <DailyCheckinModalDesktop onClose={handleClose} />
  {/if}
{/if}
