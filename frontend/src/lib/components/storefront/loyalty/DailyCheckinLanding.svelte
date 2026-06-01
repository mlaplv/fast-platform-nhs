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

    const dismissedDate = localStorage.getItem('osmo:storefront:daily_checkin_dismissed_date');
    const isDismissed = dismissedDate === new Date().toDateString();

    checkinStore.fetchStatus().then(() => {
      const st = checkinStore.status;
      if (st && st.is_event_enabled === false) return;

      if (authStore.isAuthenticated) {
        if (st && !st.is_checked_in_today && !userDismissed && !isDismissed) {
          setTimeout(() => { if (!userDismissed) checkinStore.openPopup(); }, 1500);
        }
      } else {
        if (!isDismissed) {
          setTimeout(() => {
            if (!userDismissed) checkinStore.openPopup();
          }, 1500);
        }
      }
    }).catch(() => {
      // Fallback if fetch fails for guests
      if (!isDismissed) {
        setTimeout(() => {
          if (!userDismissed) checkinStore.openPopup();
        }, 1500);
      }
    });

    return () => window.removeEventListener('resize', updateIsMobile);
  });

  function handleClose() {
    userDismissed = true;
    checkinStore.closePopup();
  }
</script>

<!-- Floating Trigger (Gift 🎁) - Back up trigger to reopen Reward Center anytime (Desktop Only) -->
{#if !isMobile && !checkinStore.showPopup && (checkinStore.status?.is_event_enabled !== false)}
  {@const hasCheckedIn = checkinStore.status?.is_checked_in_today ?? false}
  <button
    onclick={() => { userDismissed = false; checkinStore.openPopup(); }}
    class="fixed group active:scale-95 transition-all duration-300"
    style="
      bottom: 200px;
      right: 20px;
      z-index: 9990;
    "
    aria-label="Trung tâm thưởng điểm danh"
  >
    {#if !hasCheckedIn}
      <!-- Outer pulse rings (Only shown if NOT checked in yet today) -->
      <div class="absolute inset-0 rounded-full bg-[#FFD700] opacity-30 animate-ping"></div>
      <div class="absolute inset-0 rounded-full bg-[#FFD700] opacity-20 animate-ping" style="animation-delay: 0.5s"></div>
    {/if}

    <!-- Liquid gradient premium gift/coin circle -->
    <div class="relative w-13 h-13 md:w-15 md:h-15 rounded-full
      bg-gradient-to-br {hasCheckedIn ? 'from-[#ffffff] to-[#cbd5e1] border border-slate-200 shadow-[0_8px_24px_rgba(255,255,255,0.15)]' : 'from-[#FFD700] to-[#F7B731] shadow-[0_8px_24px_rgba(255,215,0,0.4)]'}
      flex items-center justify-center
      group-hover:scale-110 transition-transform duration-200">
      <span class="text-[26px] md:text-[30px] select-none">{hasCheckedIn ? '🪙' : '🎁'}</span>
    </div>

    <!-- Elegant high-contrast tooltip banner -->
    <div class="absolute -top-9 left-1/2 -translate-x-1/2 bg-[#231b15] border border-[#FFD700]/30
      text-[#f5d7af] text-[10px] font-black px-2.5 py-1 rounded-full whitespace-nowrap shadow-md
      opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none tracking-wide">
      {hasCheckedIn ? 'THƯỞNG' : 'ĐIỂM DANH!'}
    </div>
  </button>
{/if}

<!-- Style adjustment to handle desktop responsive position cleanly -->
<style>
  @media (min-width: 768px) {
    button {
      bottom: 110px !important;
      right: 32px !important;
      z-index: 9990 !important;
    }
  }
</style>

<!-- Popup Modals -->
{#if checkinStore.showPopup}
  {#if isMobile}
    <DailyCheckinModalMobile onClose={handleClose} />
  {:else}
    <DailyCheckinModalDesktop onClose={handleClose} />
  {/if}
{/if}
