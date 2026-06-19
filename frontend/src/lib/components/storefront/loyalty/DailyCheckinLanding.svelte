<script lang="ts">
  /**
   * DailyCheckinLanding.svelte — v3
   * - Hiện cho TẤT CẢ users (kể cả khách chưa login)
   * - Auto-open sau 1.5s
   * - Nếu chưa login → click CTA → mở LoginModal
   */
  import { onMount, untrack } from 'svelte';
  import { scale } from 'svelte/transition';
  import { page } from '$app/state';
  import { browser } from '$app/environment';
  import { afterNavigate } from '$app/navigation';
  import { checkinStore } from '$lib/state/commerce/checkin.svelte';
  import { authStore } from '$lib/state/authStore.svelte';
  import DailyCheckinModalMobile from './DailyCheckinModalMobile.svelte';
  import DailyCheckinModalDesktop from './DailyCheckinModalDesktop.svelte';

  let isMobile = $state(false);
  let userDismissed = $state(false);
  let isScrolled = $state(false);

  let resizeTicking = false;
  function updateIsMobile() {
    if (!browser || resizeTicking) return;
    resizeTicking = true;
    requestAnimationFrame(() => {
      isMobile = window.innerWidth < 768;
      resizeTicking = false;
    });
  }

  let scrollTicking = false;
  function handleScroll() {
    if (!browser || scrollTicking) return;
    scrollTicking = true;
    requestAnimationFrame(() => {
      isScrolled = window.scrollY > 100;
      scrollTicking = false;
    });
  }

  onMount(() => {
    window.addEventListener('resize', updateIsMobile);
    if (browser) {
      window.addEventListener('scroll', handleScroll, { passive: true });
      requestAnimationFrame(() => {
        updateIsMobile();
        handleScroll();
      });
      // Fetch status globally to determine campaign visibility
      if (!checkinStore.status && !checkinStore.loading) {
        checkinStore.fetchStatus();
      }
    }
    return () => {
      window.removeEventListener('resize', updateIsMobile);
      if (browser) window.removeEventListener('scroll', handleScroll);
    };
  });


  function getVnDateString(): string {
    const now = new Date();
    const utcMs = now.getTime() + now.getTimezoneOffset() * 60000;
    const vnTime = new Date(utcMs + 7 * 3600000);
    const y = vnTime.getFullYear();
    const m = String(vnTime.getMonth() + 1).padStart(2, '0');
    const d = String(vnTime.getDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
  }

  // Elite V2.2: Svelte 5 Reactive Route Guard and Popup Auto-trigger
  // Triggers reactively when navigating to the homepage, respecting dismissal and authentication state.
  $effect(() => {
    // Read reactive variables synchronously to register them as Svelte 5 dependencies
    const currentPathname = page.url.pathname;
    const isAuthenticated = authStore.isAuthenticated;
    const status = checkinStore.status;
    const loading = checkinStore.loading;

    // Elite V2.2: Exclude critical checkout and auth pages from auto-triggering the checkin popup
    const isExcludedPage = currentPathname.startsWith('/checkout') || currentPathname.startsWith('/auth');
    if (isExcludedPage) {
      userDismissed = false;
      return;
    }

    if (loading || !status) return;

    if (status.is_event_enabled === false) return;

    const dismissedDate = localStorage.getItem('osmo:storefront:daily_checkin_dismissed_date');
    const isDismissed = dismissedDate === getVnDateString();
    if (isDismissed || userDismissed) return;

    if (checkinStore.showPopup) return;

    if (isAuthenticated && status.is_checked_in_today) return;

    const timerId = setTimeout(() => {
      if (!userDismissed && page.url.pathname === currentPathname && !checkinStore.showPopup) {
        checkinStore.openPopup();
      }
    }, 1500); // 1.5s as per design spec

    return () => {
      clearTimeout(timerId);
    };
  });

  afterNavigate(() => {
    if (checkinStore.showPopup) {
      checkinStore.closePopup();
    }
  });

  // Auto-reopen reward center modal immediately after successful login
  $effect(() => {
    if (authStore.isAuthenticated) {
      const shouldReopen = localStorage.getItem('osmo:loyalty:reopen_after_login');
      if (shouldReopen === 'true') {
        localStorage.removeItem('osmo:loyalty:reopen_after_login');
        checkinStore.fetchStatus().then(() => {
          checkinStore.openPopup();
        });
      }
    }
  });

  function handleClose() {
    userDismissed = true;
    checkinStore.closePopup();
  }
</script>

<!-- Floating Trigger (Gift 🎁) - Back up trigger to reopen Reward Center anytime (Desktop Only) -->
{#if !isMobile && !checkinStore.showPopup && checkinStore.status?.is_event_enabled === true}
  {@const hasCheckedIn = checkinStore.status?.is_checked_in_today ?? false}
  <button
    onclick={() => { userDismissed = false; checkinStore.openPopup(); }}
    class="fixed group active:scale-95 transition-all duration-700 ease-[cubic-bezier(0.16,1,0.3,1)]"
    style="
      bottom: {isMobile ? '200px' : (isScrolled ? '90px' : '110px')};
      right: {isMobile ? '20px' : '32px'};
      z-index: 9990;
      transform: {isMobile ? 'none' : (isScrolled ? 'translateY(8px)' : 'translateY(0)')};
    "
    aria-label="Trung tâm thưởng điểm danh"
  >
    {#if !hasCheckedIn}
      <!-- Outer pulse rings (Only shown if NOT checked in yet today) -->
      <div class="absolute inset-0 rounded-full bg-[#FFD700] opacity-30 animate-ping"></div>
      <div class="absolute inset-0 rounded-full bg-[#FFD700] opacity-20 animate-ping" style="animation-delay: 0.5s"></div>
    {/if}
 
    <!-- Liquid gradient premium gift/coin circle -->
    <div class="relative rounded-full
      bg-gradient-to-br {hasCheckedIn ? 'from-[#ffffff] to-[#cbd5e1] border border-slate-200 shadow-[0_8px_24px_rgba(255,255,255,0.15)]' : 'from-[#FFD700] to-[#F7B731] shadow-[0_8px_24px_rgba(255,215,0,0.4)]'}
      flex items-center justify-center
      group-hover:scale-110 transition-all duration-700 ease-[cubic-bezier(0.16,1,0.3,1)]"
      style="
        width: {isMobile ? '52px' : (isScrolled ? '48px' : '60px')};
        height: {isMobile ? '52px' : (isScrolled ? '48px' : '60px')};
      "
    >
      <!-- Premium vector gift box SVG -->
      <div class="flex items-center justify-center bg-gradient-to-br {hasCheckedIn ? 'from-slate-100 to-slate-200 shadow-[0_2px_8px_rgba(0,0,0,0.05)]' : 'from-[#FFD700] to-[#E5A93C] shadow-[0_2px_8px_rgba(229,169,60,0.3)]'} rounded-full transition-all duration-700 ease-[cubic-bezier(0.16,1,0.3,1)]"
        style="
          width: {isMobile ? '38px' : (isScrolled ? '30px' : '38px')};
          height: {isMobile ? '38px' : (isScrolled ? '30px' : '38px')};
        "
      >
        <svg 
          class="{hasCheckedIn ? 'text-slate-700' : 'text-[#231b15]'} transition-all duration-700 ease-[cubic-bezier(0.16,1,0.3,1)]" 
          viewBox="0 0 24 24" 
          fill="none" 
          stroke="currentColor" 
          stroke-width="2.2" 
          stroke-linecap="round" 
          stroke-linejoin="round"
          style="
            width: {isMobile ? '22px' : (isScrolled ? '18px' : '22px')};
            height: {isMobile ? '22px' : (isScrolled ? '18px' : '22px')};
          "
        >
          <!-- Lid & Box -->
          <path d="M20 12v10H4V12" />
          <!-- Ribbon vertically -->
          <path d="M12 22V7" />
          <!-- Ribbon horizontally -->
          <path d="M2 12h20" />
          <!-- Bow -->
          <path d="M12 7H7.5a2.5 2.5 0 0 1 0-5C11 2 12 7 12 7z" />
          <path d="M12 7h4.5a2.5 2.5 0 0 0 0-5C13 2 12 7 12 7z" />
        </svg>
      </div>
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
