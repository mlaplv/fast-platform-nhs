<script lang="ts">
  import { onMount, type Snippet } from 'svelte';
  import { browser } from '$app/environment';
  import { goto } from '$app/navigation';
  import { fade, scale } from 'svelte/transition';
  import { authStore } from '$lib/state/authStore.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { apiClient } from '$lib/utils/apiClient';
  import UserLayout from './UserLayout.svelte';
  import UserMenuMobile from './UserMenuMobile.svelte';
  import UserHeaderMobile from './UserHeaderMobile.svelte';
  import SeoHead from '../seo/SeoHead.svelte';
  import { loyaltyStore } from '$lib/state/commerce/loyalty.svelte';
  
  import Award from '@lucide/svelte/icons/award';
  import ShieldCheck from '@lucide/svelte/icons/shield-check';
  import Sparkles from '@lucide/svelte/icons/sparkles';
 
  interface Props {
    title: string;
    mobileTitle?: string;
    description?: string;
    children: Snippet;
    requireAuth?: boolean;
    headerHiddenOnMobile?: boolean;
  }
 
  let { 
    title, 
    mobileTitle, 
    description = "Quản lý thông tin tài khoản và ưu đãi của bạn.",
    children, 
    requireAuth = true,
    headerHiddenOnMobile = true
  }: Props = $props();
 
  const ui = getClientUi();
  let isMenuOpen = $state(false);
  let showCtvPromo = $state(false);
  let isCtvRegistered = $state(true); // default true
 
  // Elite V2.2: Deterministic Layout Management + CTV Verification
  onMount(async () => {
    if (ui.isMobile) {
      ui.isHeaderHidden = headerHiddenOnMobile;
    } else {
      ui.isHeaderHidden = false;
    }
    ui.isFooterHidden = false;

    // Pre-fetch loyalty points to ensure user header mobile shows correct available points
    if (authStore.isAuthenticated) {
      loyaltyStore.fetchLoyalty();
    }

    // Async CTV Promo check
    if (browser) {
      await authStore.waitForSessionVerification();
      if (authStore.isAuthenticated && window.location.pathname !== '/user/ctv') {
        try {
          const ctvProfile = await apiClient.get<{ is_registered: boolean }>('/client/ctv/profile');
          isCtvRegistered = ctvProfile?.is_registered ?? false;
          if (!isCtvRegistered) {
            const dismissed = sessionStorage.getItem('ctv_promo_dismissed');
            if (!dismissed) {
              setTimeout(() => {
                showCtvPromo = true;
              }, 800);
            }
          }
        } catch (e: any) {
          isCtvRegistered = false;
          const dismissed = sessionStorage.getItem('ctv_promo_dismissed');
          if (!dismissed) {
            setTimeout(() => {
              showCtvPromo = true;
            }, 800);
          }
        }
      }
    }

    return () => {
      ui.isHeaderHidden = false;
      ui.isFooterHidden = false;
    };
  });

  // Security Protocol: Auth Guard
  $effect(() => {
    if (browser && requireAuth && !authStore.isAuthenticated) {
      ui.openLogin();
      goto('/');
    }
  });

  function dismissPromo(): void {
    showCtvPromo = false;
    sessionStorage.setItem('ctv_promo_dismissed', 'true');
  }

  function activatePromo(): void {
    showCtvPromo = false;
    goto('/user/ctv');
  }

  const displayMobileTitle = $derived(mobileTitle || title);
</script>

<SeoHead 
  title="{title} | {ui.settings?.basic_info?.site_name || 'osmo.vn'}" 
  description={description}
  robots="noindex, nofollow"
/>

{#if browser}
  {#if !ui.isMobile}
    <UserLayout>
      <div class="space-y-8" in:fade={{ duration: 400 }}>
        <div class="border-b border-stone-100 pb-5">
          <h1 class="text-xl font-serif italic text-stone-800 tracking-wide">{title}</h1>
          {#if description}
            <p class="text-[13px] text-stone-400 mt-1 tracking-widest">{description}</p>
          {/if}
        </div>
        {@render children()}
      </div>
    </UserLayout>
  {:else}
    <UserMenuMobile bind:active={isMenuOpen} onClose={() => isMenuOpen = false} />
    <UserHeaderMobile title={displayMobileTitle} bind:isMenuOpen />

    <div
      class="pb-20 px-4 space-y-6 bg-[#f9f8f6] min-h-screen"
      style="padding-top: calc(env(safe-area-inset-top) + 80px);"
      in:fade={{ duration: 300 }}
    >
      {@render children()}
    </div>
  {/if}

  {#if showCtvPromo}
    <div class="fixed inset-0 bg-stone-950/70 backdrop-blur-lg flex items-center justify-center p-4" style="z-index: var(--z-modal-overlay);" transition:fade={{ duration: 250 }}>
      <div class="bg-gradient-to-br from-sky-100/95 via-sky-50/90 to-white/98 text-sky-950 rounded-2xl w-full max-w-md border border-white p-6 md:p-8 relative overflow-hidden shadow-2xl backdrop-blur-xl" transition:scale={{ start: 0.95, duration: 300 }}>
        <!-- Glow highlights -->
        <div class="absolute -right-20 -top-20 w-48 h-48 bg-sky-300/30 rounded-full blur-3xl pointer-events-none"></div>
        <div class="absolute -left-20 -bottom-20 w-48 h-48 bg-luxury-copper/5 rounded-full blur-3xl pointer-events-none"></div>
        
        <div class="relative z-10 space-y-6">
          <!-- Premium Header Badge -->
          <div class="flex items-center gap-2.5">
            <div class="w-10 h-10 bg-luxury-copper/10 rounded-xl flex items-center justify-center border border-luxury-copper/20">
              <Award class="w-5 h-5 text-[#8C6239]" />
            </div>
            <div>
              <span class="text-[9px] tracking-[4px] text-[#8C6239] font-black block uppercase">Đặc quyền Thành viên</span>
              <h3 class="text-lg font-serif italic text-sky-900 font-light">Kích hoạt Kênh Đại lý số & CTV</h3>
            </div>
          </div>

          <!-- Highlight Promo Card -->
          <div class="bg-white/80 border border-white rounded-xl p-4 space-y-3.5 shadow-inner backdrop-blur-md">
            <div class="flex items-center justify-between">
              <span class="px-2 py-0.5 bg-amber-500/10 border border-amber-500/20 text-amber-600 text-[8px] tracking-[2px] font-black uppercase rounded-full">
                🔥 Hot Deal Commission
              </span>
              <span class="flex items-center gap-1 text-[8px] text-sky-850 font-mono tracking-widest font-bold">
                <ShieldCheck class="w-3.5 h-3.5 text-emerald-600" /> AES-GCM SECURED
              </span>
            </div>
            
            <p class="text-[11px] text-sky-900 leading-relaxed font-light">
              Nhận ngay chiết khấu chi trả độc quyền từ <strong class="text-[#8C6239]">5% đến 15%</strong> trên mỗi đơn hàng được giới thiệu thành công. Không cần ôm hàng, không lo vận chuyển!
            </p>

            <div class="grid grid-cols-2 gap-2 pt-2 border-t border-white/40 text-center">
              <div class="p-2 bg-white/70 rounded border border-white/80 shadow-sm">
                <span class="block text-[8px] text-sky-800/80 font-bold uppercase tracking-wider">HOA HỒNG LÊN TỚI</span>
                <span class="block text-base font-bold text-[#8C6239] mt-0.5 font-mono">15%</span>
              </div>
              <div class="p-2 bg-white/70 rounded border border-white/80 shadow-sm">
                <span class="block text-[8px] text-sky-800/80 font-bold uppercase tracking-wider">MÃ CTV ĐỘC QUYỀN</span>
                <span class="block text-xs font-bold text-sky-950 mt-1.5 uppercase font-mono tracking-wider">THEO TÊN BẠN</span>
              </div>
            </div>
          </div>

          <!-- Bullet Points -->
          <ul class="space-y-2 text-[11px] text-sky-900/80 font-light leading-relaxed">
            <li class="flex items-center gap-2">
              <Sparkles class="w-3.5 h-3.5 text-[#8C6239] shrink-0" />
              <span>Đối soát minh bạch, rút tiền nhanh chóng hàng tuần.</span>
            </li>
            <li class="flex items-center gap-2">
              <Sparkles class="w-3.5 h-3.5 text-[#8C6239] shrink-0" />
              <span>Depth limit d = 1, tối ưu biên lợi nhuận cao nhất cho bạn.</span>
            </li>
          </ul>

          <!-- Actions -->
          <div class="flex flex-col gap-2.5 pt-2">
            <button 
              onclick={activatePromo}
              class="w-full py-3.5 bg-luxury-copper hover:bg-amber-600 text-stone-950 font-black text-[10px] tracking-[4px] uppercase rounded-xl transition-all shadow-lg shadow-luxury-copper/15 active:scale-[0.98]"
            >
              KÍCH HOẠT MIỄN PHÍ NGAY
            </button>
            
            <button 
              onclick={dismissPromo}
              class="w-full py-2 text-sky-800/60 hover:text-sky-900 font-bold text-[9px] tracking-[2px] uppercase transition-colors"
            >
              ĐỂ SAU
            </button>
          </div>
        </div>
      </div>
    </div>
  {/if}
{/if}
