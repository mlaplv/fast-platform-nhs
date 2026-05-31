<script lang="ts">
  /**
   * DailyCheckinLanding.svelte — v3
   * - Hiện cho TẤT CẢ users (kể cả khách chưa login)
   * - Auto-open sau 1.5s
   * - Nếu chưa login → click CTA → mở LoginModal
   */
  import { onMount } from 'svelte';
  import { scale } from 'svelte/transition';
  import { checkinStore } from '$lib/state/commerce/checkin.svelte';
  import { authStore } from '$lib/state/authStore.svelte';
  import DailyCheckinModalMobile from './DailyCheckinModalMobile.svelte';
  import DailyCheckinModalDesktop from './DailyCheckinModalDesktop.svelte';

  let isMobile = $state(false);
  let userDismissed = $state(false);

  function updateIsMobile() {
    isMobile = window.innerWidth < 768;
  }

  onMount(() => {
    updateIsMobile();
    window.addEventListener('resize', updateIsMobile);

    if (authStore.isAuthenticated) {
      // Đã login: fetch status rồi tự mở nếu chưa điểm danh
      checkinStore.fetchStatus().then(() => {
        const st = checkinStore.status;
        if (st && !st.is_checked_in_today && !userDismissed) {
          setTimeout(() => { if (!userDismissed) checkinStore.openPopup(); }, 1500);
        }
      });
    } else {
      // Khách chưa login: auto-open popup preview sau 1.5s (để kích thích đăng ký)
      setTimeout(() => {
        if (!userDismissed) checkinStore.openPopup();
      }, 1500);
    }

    return () => window.removeEventListener('resize', updateIsMobile);
  });

  function handleClose() {
    userDismissed = true;
    checkinStore.closePopup();
  }

  // Floating button: hiện khi popup đóng + chưa điểm danh (hoặc khách)
  let showFloating = $derived(
    !checkinStore.showPopup && userDismissed && (
      !authStore.isAuthenticated ||
      (checkinStore.status !== null && !checkinStore.status.is_checked_in_today)
    )
  );
</script>

<!-- Floating Trigger — backup sau khi user đóng popup -->
{#if showFloating}
  <button
    onclick={() => { userDismissed = false; checkinStore.openPopup(); }}
    class="fixed bottom-24 right-4 z-[9990] md:bottom-8 md:right-6 group"
    aria-label="Nhận thưởng điểm danh hàng ngày"
    transition:scale={{ duration: 300, start: 0.8 }}
  >
    <div class="absolute inset-0 rounded-full bg-[#FFD700] opacity-30 animate-ping"></div>
    <div class="absolute inset-0 rounded-full bg-[#FFD700] opacity-20 animate-ping" style="animation-delay: 0.5s"></div>

    <div class="relative w-14 h-14 md:w-16 md:h-16 rounded-full
      bg-gradient-to-br from-[#FFD700] to-[#F7B731]
      shadow-[0_8px_24px_rgba(255,215,0,0.5)]
      flex items-center justify-center
      group-hover:scale-110 transition-transform duration-200">
      <span class="text-2xl md:text-3xl">🎁</span>
    </div>

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
