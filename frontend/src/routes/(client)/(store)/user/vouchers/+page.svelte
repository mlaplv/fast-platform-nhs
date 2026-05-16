<script lang="ts">
  import UserLayout from '$lib/components/storefront/user/UserLayout.svelte';
  import { onMount } from 'svelte';
  import { browser } from '$app/environment';
  import { fade, fly } from 'svelte/transition';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { apiClient } from '$lib/utils/apiClient';
  import type { Voucher } from '$lib/types';
  import VoucherWalletCard from '$lib/components/storefront/user/vouchers/VoucherWalletCard.svelte';
  import UserMenuMobile from '$lib/components/storefront/user/UserMenuMobile.svelte';
  import UserHeaderMobile from '$lib/components/storefront/user/UserHeaderMobile.svelte';
  import Ticket from "@lucide/svelte/icons/ticket";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import Loader2 from "@lucide/svelte/icons/loader-2";
  import { formatCurrency } from '$lib/utils/format';
  import SeoHead from '$lib/components/storefront/seo/SeoHead.svelte';


  const ui = getClientUi();
  let isMenuOpen = $state(false);

  // Elite V2.2 Tab State
  let activeTab = $state<'ALL' | 'SHIPPING' | 'DISCOUNT'>('ALL');
  const tabs = [
    { id: 'ALL', label: 'Tất cả' },
    { id: 'SHIPPING', label: 'Vận chuyển' },
    { id: 'DISCOUNT', label: 'Giảm giá' }
  ] as const;

  let vouchers = $state<Voucher[]>([]);
  let isLoading = $state(true);

  // Managed Layout Protocol
  // Managed Layout Protocol (Elite V2.2)
  onMount(() => {
    if (ui.isMobile) {
      ui.isHeaderHidden = true;
    } else {
      ui.isHeaderHidden = false;
    }
    ui.isFooterHidden = false;

    return () => {
      ui.isHeaderHidden = false;
      ui.isFooterHidden = false;
    };
  });

  onMount(async () => {
    await fetchVouchers();
  });

  async function fetchVouchers() {
    isLoading = true;
    try {
      // Elite V2.2: The API returns VoucherListResponse { data: Voucher[], total: number }
      const res = await apiClient.get<{ data: Voucher[] }>('/api/v1/client/home/vouchers');
      if (res && Array.isArray(res.data)) {
        vouchers = res.data;
      }
    } catch (err) {
      console.error("Failed to fetch vouchers", err);
    } finally {
      isLoading = false;
    }
  }

  const filteredVouchers = $derived(
    Array.isArray(vouchers) ? (
      activeTab === 'ALL' 
        ? vouchers 
        : vouchers.filter(v => v.category === activeTab)
    ) : []
  );

  const totalSavedValue = $derived(
    Array.isArray(vouchers) ?
      vouchers.reduce((acc, v) => acc + ((v.used_count || 0) * (v.value || 0)), 0) : 0
  );
</script>

<SeoHead 
  title="Kho Voucher | {ui.settings?.basic_info?.site_name || 'osmo Elite'}" 
  robots="noindex, nofollow"
/>


{#if browser}
  {#if !ui.isMobile}
    <UserLayout>
      <div class="space-y-8" in:fade>
        <!-- Header & Stats -->
        <div class="border-b border-stone-100 pb-5 flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <h1 class="text-xl font-serif italic text-stone-800 tracking-wide">Kho Voucher</h1>
            <p class="text-[13px] text-stone-400 mt-1 tracking-widest">Săn ưu đãi độc quyền từ osmo</p>
          </div>
          
          <div class="bg-stone-50 px-6 py-3 rounded-xl border border-stone-100 flex items-center gap-4">
             <div class="w-10 h-10 rounded-full bg-luxury-copper/10 flex items-center justify-center text-luxury-copper">
                <Sparkles size={20} />
             </div>
             <div>
                <p class="text-[10px] font-black text-stone-400 tracking-widest leading-none mb-1">Tổng quyền lợi</p>
                <p class="text-lg font-black text-stone-800 italic">~ {formatCurrency(totalSavedValue)}</p>
             </div>
          </div>
        </div>

        <!-- TABS -->
        <div class="flex items-center gap-1 bg-stone-50 p-1 rounded-xl w-fit">
          {#each tabs as tab}
            <button
              onclick={() => activeTab = tab.id}
              class="px-6 py-2 text-[11px] font-black tracking-widest rounded-lg transition-all
              {activeTab === tab.id ? 'bg-white text-stone-800 shadow-sm' : 'text-stone-400 hover:text-stone-600'}"
            >
              {tab.label}
            </button>
          {/each}
        </div>

        <!-- GRID -->
        {#if isLoading}
          <div class="py-20 flex flex-col items-center justify-center gap-4">
             <Loader2 class="w-10 h-10 text-stone-200 animate-spin" />
             <p class="text-[11px] font-black text-stone-300 tracking-widest italic">Đang tải kho báu...</p>
          </div>
        {:else if filteredVouchers.length > 0}
          <div class="grid grid-cols-1 xl:grid-cols-2 gap-4">
            {#each filteredVouchers as voucher (voucher.id)}
              <VoucherWalletCard {voucher} />
            {/each}
          </div>
        {:else}
          <div class="py-32 flex flex-col items-center justify-center text-center space-y-4">
             <div class="w-20 h-20 bg-stone-50 rounded-full flex items-center justify-center text-stone-200 border border-stone-100">
                <Ticket size={40} />
             </div>
             <div class="space-y-1">
                <p class="text-sm font-black text-stone-800 italic">Chưa có mã nào ở đây</p>
                <p class="text-[11px] text-stone-400 tracking-widest font-bold">Hãy quay lại sau khi sếp tung deal mới nhé!</p>
             </div>
          </div>
        {/if}
      </div>
    </UserLayout>
  {:else}
    <UserMenuMobile bind:active={isMenuOpen} onClose={() => isMenuOpen = false} />
    <UserHeaderMobile title="Kho Voucher" bind:isMenuOpen />

    <div
      class="pb-20 px-4 space-y-6 bg-[#f9f8f6] min-h-screen"
      style="padding-top: calc(env(safe-area-inset-top) + 80px);"
    >
      <!-- Mobile Stats Card -->
      <div class="bg-gradient-to-br from-stone-800 to-stone-800 p-6 rounded-2xl shadow-xl shadow-stone-200/50 relative overflow-hidden group">
         <div class="relative z-10 space-y-4">
            <div class="flex items-center gap-2">
               <div class="p-1.5 bg-luxury-copper/20 rounded-lg text-luxury-copper backdrop-blur-sm border border-luxury-copper/20">
                  <Ticket size={14} />
               </div>
               <span class="text-[10px] font-black text-stone-400 tracking-[3px]">Elite Wallet</span>
            </div>
            <div>
               <h2 class="text-2xl font-black text-white italic tracking-tight">{formatCurrency(totalSavedValue)}</h2>
               <p class="text-[9px] text-stone-500 font-black tracking-widest mt-1 italic">Ưu đãi lũy kế hệ thống</p>
            </div>
         </div>
         <Sparkles class="absolute top-4 right-4 text-luxury-copper/20 group-active:scale-125 transition-transform" />
         <div class="absolute -bottom-4 -right-4 w-24 h-24 bg-luxury-copper/10 rounded-full blur-2xl"></div>
      </div>

      <!-- Mobile Tabs -->
      <div class="sticky top-[80px] z-40 bg-[#f9f8f6] py-2">
        <div class="flex items-center gap-1 bg-stone-100 p-1 rounded-xl">
          {#each tabs as tab}
            <button
              onclick={() => activeTab = tab.id}
              class="flex-1 py-3 text-[10px] font-black tracking-widest rounded-lg transition-all
              {activeTab === tab.id ? 'bg-white text-stone-800 shadow-lg' : 'text-stone-400'}"
            >
              {tab.label}
            </button>
          {/each}
        </div>
      </div>

      <!-- Mobile List -->
      {#if isLoading}
        <div class="py-20 flex flex-col items-center justify-center gap-4">
           <Loader2 class="w-8 h-8 text-stone-300 animate-spin" />
        </div>
      {:else if filteredVouchers.length > 0}
        <div class="space-y-4" in:fade>
          {#each filteredVouchers as voucher (voucher.id)}
            <VoucherWalletCard {voucher} />
          {/each}
        </div>
      {:else}
        <div class="py-20 text-center space-y-4 px-10">
           <div class="text-stone-200 flex justify-center">
              <Ticket size={60} strokeWidth={1} />
           </div>
           <p class="text-[11px] font-black text-stone-400 tracking-widest">Kho báu đang trống, hẹn gặp sếp ở đợt sale tới!</p>
        </div>
      {/if}
    </div>
  {/if}
{/if}

<style>
  :global(.text-luxury-copper) { color: #c5a059; }
  :global(.bg-luxury-copper) { background-color: #c5a059; }

  /* Elite V2.2: Shimmer Animation for the Card Stub */
  @keyframes shimmer {
     0% { transform: translateX(-100%); }
     100% { transform: translateX(100%); }
  }
  :global(.animate-shimmer) {
     animation: shimmer 2s infinite;
  }
</style>
