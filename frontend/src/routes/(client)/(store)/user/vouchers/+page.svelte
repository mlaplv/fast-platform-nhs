<script lang="ts">
  import { onMount } from 'svelte';
  import { fade } from 'svelte/transition';
  import { apiClient } from '$lib/utils/apiClient';
  import type { Voucher } from '$lib/types';
  import VoucherWalletCard from '$lib/components/storefront/user/vouchers/VoucherWalletCard.svelte';
  import UserPageWrapper from '$lib/components/storefront/user/UserPageWrapper.svelte';
  import Ticket from "@lucide/svelte/icons/ticket";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import Loader2 from "@lucide/svelte/icons/loader-2";
  import { formatCurrency } from '$lib/utils/format';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';

  const ui = getClientUi();

  // Elite V2.2 Tab State
  let activeTab = $state<'ALL' | 'SHIPPING' | 'DISCOUNT'>('ALL');
  const tabs = [
    { id: 'ALL', label: 'Tất cả' },
    { id: 'SHIPPING', label: 'Vận chuyển' },
    { id: 'DISCOUNT', label: 'Giảm giá' }
  ] as const;

  let vouchers = $state<Voucher[]>([]);
  let isLoading = $state(true);

  onMount(async () => {
    await fetchVouchers();
  });

  async function fetchVouchers() {
    isLoading = true;
    try {
      const res = await apiClient.get<{ data: Voucher[] }>('/api/v1/client/home/vouchers');
      if (res && Array.isArray(res.data)) {
        vouchers = res.data;
      }
    } catch (err: unknown) {
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

<UserPageWrapper 
  title="Kho Voucher" 
  description="Săn ưu đãi độc quyền từ hệ thống dành riêng cho thành viên Elite."
>
  <div class="space-y-8" in:fade>
    <!-- Stats Banner (Desktop) -->
    {#if !ui.isMobile}
      <div class="bg-stone-50 px-6 py-4 rounded-2xl border border-stone-100 flex items-center justify-between">
          <div class="flex items-center gap-4">
            <div class="w-12 h-12 rounded-full bg-luxury-copper/10 flex items-center justify-center text-luxury-copper">
                <Sparkles size={24} />
            </div>
            <div>
                <p class="text-[10px] font-black text-stone-400 tracking-[3px] uppercase">Tổng quyền lợi tích lũy</p>
                <p class="text-xl font-black text-stone-800 italic">{formatCurrency(totalSavedValue)}</p>
            </div>
          </div>
          <div class="hidden xl:block">
              <p class="text-[10px] text-stone-300 italic font-medium">Hệ thống tự động áp dụng mã tốt nhất tại Checkout</p>
          </div>
      </div>
    {:else}
      <!-- Mobile Stats Card -->
      <div class="bg-gradient-to-br from-stone-800 to-stone-900 p-6 rounded-2xl shadow-xl shadow-stone-200/50 relative overflow-hidden group">
         <div class="relative z-10 space-y-4">
            <div class="flex items-center gap-2">
               <div class="p-1.5 bg-luxury-copper/20 rounded-lg text-luxury-copper backdrop-blur-sm border border-luxury-copper/20">
                  <Ticket size={14} />
               </div>
               <span class="text-[10px] font-black text-stone-400 tracking-[3px] uppercase">Elite Wallet</span>
            </div>
            <div>
               <h2 class="text-2xl font-black text-white italic tracking-tight">{formatCurrency(totalSavedValue)}</h2>
               <p class="text-[9px] text-stone-500 font-black tracking-widest mt-1 italic uppercase">Ưu đãi lũy kế hệ thống</p>
            </div>
         </div>
         <Sparkles class="absolute top-4 right-4 text-luxury-copper/20 group-active:scale-125 transition-transform" />
         <div class="absolute -bottom-4 -right-4 w-24 h-24 bg-luxury-copper/10 rounded-full blur-2xl opacity-20"></div>
      </div>
    {/if}

    <!-- TABS -->
    <div class="sticky top-[80px] md:static z-40 bg-inherit py-2">
      <div class="flex items-center gap-1 bg-stone-50 p-1 rounded-xl w-full md:w-fit border border-stone-100/50">
        {#each tabs as tab}
          <button
            onclick={() => activeTab = tab.id}
            class="flex-1 md:px-8 py-2.5 text-[10px] md:text-[11px] font-black tracking-widest rounded-lg transition-all
            {activeTab === tab.id ? 'bg-white text-stone-800 shadow-sm border border-stone-100' : 'text-stone-400 hover:text-stone-600'}"
          >
            {tab.label}
          </button>
        {/each}
      </div>
    </div>

    <!-- CONTENT GRID -->
    {#if isLoading}
      <div class="py-24 flex flex-col items-center justify-center gap-4">
         <Loader2 class="w-10 h-10 text-stone-200 animate-spin" />
         <p class="text-[11px] font-black text-stone-300 tracking-[4px] italic uppercase">Đang tải kho báu...</p>
      </div>
    {:else if filteredVouchers.length > 0}
      <div class="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {#each filteredVouchers as voucher (voucher.id)}
          <VoucherWalletCard {voucher} />
        {/each}
      </div>
    {:else}
      <div class="py-32 flex flex-col items-center justify-center text-center space-y-6">
         <div class="w-24 h-24 bg-stone-50 rounded-full flex items-center justify-center text-stone-200 border border-stone-100">
            <Ticket size={48} strokeWidth={1.5} />
         </div>
         <div class="space-y-2">
            <p class="text-sm font-black text-stone-800 italic uppercase tracking-wider">Kho báu đang trống</p>
            <p class="text-[11px] text-stone-400 tracking-[3px] font-bold uppercase leading-relaxed">
                Hãy quay lại sau khi hệ thống tung deal mới nhé!
            </p>
         </div>
      </div>
    {/if}
  </div>
</UserPageWrapper>

<style>
  :global(.text-luxury-copper) { color: #c5a059; }
  :global(.bg-luxury-copper) { background-color: #c5a059; }

  @keyframes shimmer {
     0% { transform: translateX(-100%); }
     100% { transform: translateX(100%); }
  }
  :global(.animate-shimmer) {
     animation: shimmer 2s infinite;
  }
</style>
