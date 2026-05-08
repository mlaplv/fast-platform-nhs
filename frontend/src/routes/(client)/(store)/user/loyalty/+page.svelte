<script lang="ts">
  import { onMount } from 'svelte';
  import { loyaltyStore } from '$lib/state/commerce/loyalty.svelte';
  import { authStore } from '$lib/state/authStore.svelte';
  import Star from "@lucide/svelte/icons/star";
  import TrendingUp from "@lucide/svelte/icons/trending-up";
  import History from "@lucide/svelte/icons/history";
  import Info from "@lucide/svelte/icons/info";
  import ChevronRight from "@lucide/svelte/icons/chevron-right";
  import Gift from "@lucide/svelte/icons/gift";
  import Wallet from "@lucide/svelte/icons/wallet";
  import { fade, fly } from 'svelte/transition';
  import UserLayout from '$lib/components/storefront/user/UserLayout.svelte';
  import MemberCard from '$lib/components/storefront/user/MemberCard.svelte';
  import { formatCurrency } from '$lib/utils/format';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { browser } from '$app/environment';
  import UserHeaderMobile from '$lib/components/storefront/user/UserHeaderMobile.svelte';
  import UserMenuMobile from '$lib/components/storefront/user/UserMenuMobile.svelte';

  const ui = getClientUi();
  let isMenuOpen = $state(false);

  onMount(() => {
    loyaltyStore.fetchLoyalty();
    
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

  function formatDate(dateStr: string) {
    return new Date(dateStr).toLocaleString('vi-VN', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  function getTransactionIcon(type: string) {
    if (type.includes('EARN')) return 'text-green-500';
    if (type.includes('REDEEM')) return 'text-orange-500';
    return 'text-stone-400';
  }
</script>

{#if browser}
  {#if !ui.isMobile}
    <UserLayout>
  <div class="space-y-10" in:fade>
    <!-- Page Header -->
    <div class="border-b border-stone-100 pb-5 flex flex-col md:flex-row md:items-end justify-between gap-4">
      <div>
        <h1 class="text-xl font-serif italic text-stone-800 tracking-wide">Điểm thưởng & Thành viên</h1>
        <p class="text-[13px] text-stone-400 mt-1 uppercase tracking-widest">Tích điểm từ mỗi đơn hàng để nhận ưu đãi</p>
      </div>
      {#if loyaltyStore.data}
        <div class="flex items-center gap-3">
          {#if loyaltyStore.data.pending_points > 0}
            <div class="flex items-center gap-2 px-4 py-2 bg-luxury-copper/10 border border-luxury-copper/20 rounded-full animate-pulse-slow">
              <TrendingUp class="w-3.5 h-3.5 text-luxury-copper" />
              <span class="text-[10px] font-black text-luxury-copper tracking-tighter uppercase">+{loyaltyStore.data.pending_points} CHỜ DUYỆT</span>
            </div>
          {/if}
          <div class="flex items-center gap-2 px-4 py-2 bg-stone-50 border border-stone-100 rounded-full">
              <Wallet class="w-3.5 h-3.5 text-luxury-copper" />
              <span class="text-[11px] font-black text-stone-700 tracking-tighter uppercase">{loyaltyStore.data.available_points} PTS SẴN CÓ</span>
          </div>
        </div>
      {/if}
    </div>

    {#if loyaltyStore.loading && !loyaltyStore.data}
      <div class="flex flex-col items-center justify-center py-32 space-y-4">
        <div class="w-10 h-10 border-2 border-stone-100 border-t-luxury-copper rounded-full animate-spin"></div>
        <p class="text-[10px] uppercase tracking-[3px] text-stone-300 font-bold">Synchronizing Matrix...</p>
      </div>
    {:else if loyaltyStore.data}
      <!-- Modern Mini Matrix: Card & Quick Stats -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-10 items-start">
        <!-- Main Member Card -->
        <div class="lg:col-span-6">
           <MemberCard />
           <div class="mt-4 flex items-center justify-center gap-6">
              <div class="text-center">
                 <span class="block text-[8px] uppercase tracking-widest text-stone-400 font-bold">LTV</span>
                 <span class="text-sm font-serif italic text-stone-700">{formatCurrency(loyaltyStore.data.total_spent)}</span>
              </div>
              <div class="w-px h-6 bg-stone-100"></div>
              <div class="text-center">
                <span class="block text-[8px] uppercase tracking-widest text-stone-400 font-bold">Status</span>
                <span class="text-[10px] font-bold text-luxury-copper uppercase tracking-widest">{loyaltyStore.tierName}</span>
             </div>
           </div>
        </div>

        <!-- Tier Progress & Rules -->
        <div class="lg:col-span-6 space-y-8">
            <!-- Progress Section -->
            <div class="space-y-4">
                <div class="flex justify-between items-center px-1">
                    <div class="flex items-center gap-2">
                        <TrendingUp class="w-4 h-4 text-luxury-copper" />
                        <span class="text-[11px] font-black text-stone-800 uppercase tracking-widest">Tiến trình hạng</span>
                    </div>
                    <span class="text-[10px] font-bold text-stone-400 tracking-tighter italic">
                        {Math.max(0, 10000000 - loyaltyStore.data.total_spent).toLocaleString()}đ nữa để thăng hạng Silver
                    </span>
                </div>
                
                <div class="h-1.5 w-full bg-stone-50 rounded-full overflow-hidden border border-stone-100">
                    <div 
                        class="h-full bg-luxury-copper transition-all duration-1000 ease-out shadow-[0_0_10px_rgba(197,160,89,0.3)]"
                        style="width: {loyaltyStore.nextTierProgress}%"
                    ></div>
                </div>

                <div class="flex justify-between text-[9px] uppercase tracking-widest font-bold text-stone-300">
                    <span class="text-luxury-copper">Standard</span>
                    <span>Silver</span>
                    <span>Gold</span>
                    <span>Elite</span>
                </div>
            </div>

            <!-- Redemption Rule Box -->
            <div class="p-6 bg-[#fcfbf9] border border-[#f5f1e8] rounded-2xl relative overflow-hidden group">
                <div class="absolute -right-4 -bottom-4 w-20 h-20 text-luxury-copper/5 rotate-12 transition-transform duration-700 group-hover:scale-125">
                   <Gift class="w-full h-full" />
                </div>
                <div class="relative z-10 space-y-2">
                    <div class="flex items-center gap-2">
                        <div class="w-2 h-2 rounded-full bg-luxury-copper animate-pulse"></div>
                        <span class="text-[10px] uppercase tracking-[2px] font-black text-stone-800">Quy tắc đổi thưởng</span>
                    </div>
                    <p class="text-[13px] text-stone-600 font-medium">1 Điểm = 1.000 VNĐ chiết khấu</p>
                    <p class="text-[10px] text-stone-400 italic font-medium leading-relaxed">
                        Chính sách bảo vệ biên lợi nhuận Elite V2.2: Áp dụng tối đa 1% giá trị mỗi đơn hàng.
                    </p>
                </div>
            </div>
        </div>
      </div>

      <!-- Points History Section -->
      <div class="space-y-6 pt-6">
          <div class="flex items-center gap-3 border-b border-stone-100 pb-2">
              <History class="w-4 h-4 text-luxury-copper" />
              <h2 class="text-[12px] uppercase tracking-[2px] font-bold text-stone-800">Lịch sử biến động</h2>
          </div>

          <div class="bg-white border border-stone-100 rounded-2xl shadow-[0_10px_40px_rgba(0,0,0,0.02)] overflow-hidden">
              <div class="divide-y divide-stone-50">
                  {#if loyaltyStore.data.history.length === 0}
                      <div class="p-20 text-center flex flex-col items-center gap-4">
                          <History class="w-8 h-8 text-stone-100" />
                          <p class="text-[10px] uppercase tracking-[3px] text-stone-300 font-bold italic">Chưa có lịch sử giao dịch điểm</p>
                      </div>
                  {:else}
                      {#each loyaltyStore.data.history as tx}
                          <div class="px-6 py-5 flex justify-between items-center hover:bg-stone-50/50 transition-all duration-300 group">
                              <div class="flex items-center gap-4">
                                  <div class="w-10 h-10 rounded-full flex items-center justify-center transition-colors {tx.amount > 0 ? 'bg-green-50 text-green-600' : 'bg-amber-50 text-amber-600'}">
                                      {#if tx.amount > 0}
                                        <TrendingUp class="w-4 h-4" />
                                      {:else}
                                        <Gift class="w-4 h-4" />
                                      {/if}
                                  </div>
                                  <div class="flex flex-col">
                                      <span class="text-[13px] font-bold text-stone-800 group-hover:text-stone-900 transition-colors uppercase tracking-tight">{tx.notes || 'Giao dịch điểm'}</span>
                                      <span class="text-[10px] text-stone-400 font-mono mt-0.5">{formatDate(tx.created_at)}</span>
                                  </div>
                              </div>
                              <div class="flex flex-col items-end">
                                  <span class="text-base font-black {getTransactionIcon(tx.transaction_type)} tracking-tighter">
                                      {tx.amount > 0 ? '+' : ''}{tx.amount}
                                  </span>
                                  <span class="text-[8px] uppercase tracking-widest opacity-40 font-black">Points</span>
                              </div>
                          </div>
                      {/each}
                  {/if}
              </div>
          </div>
      </div>
    {:else if loyaltyStore.error}
      <div class="p-20 text-center flex flex-col items-center space-y-4 bg-red-50/30 border border-red-50 rounded-3xl">
          <Info class="w-10 h-10 text-red-200" />
          <div>
            <p class="text-red-500 font-bold uppercase tracking-widest text-[11px] mb-1">Hệ thống đang bảo trì dữ liệu</p>
            <p class="text-red-400/70 text-[10px] uppercase tracking-tighter">{loyaltyStore.error}</p>
          </div>
          <button onclick={() => loyaltyStore.fetchLoyalty()} class="px-8 py-2.5 bg-white border border-red-100 text-red-500 text-[10px] rounded-full uppercase tracking-widest font-black hover:bg-red-50/50 transition-colors">Thử lại</button>
      </div>
    {/if}
  </div>
    </UserLayout>
  {:else}
    <UserMenuMobile bind:active={isMenuOpen} onClose={() => isMenuOpen = false} />
    <UserHeaderMobile title="Điểm Thưởng" bind:isMenuOpen />

    <div
      class="pb-20 px-4 space-y-8 bg-[#f9f8f6] min-h-screen"
      style="padding-top: calc(env(safe-area-inset-top) + 80px);"
      in:fade
    >
      {#if loyaltyStore.loading && !loyaltyStore.data}
        <div class="flex flex-col items-center justify-center py-20 space-y-4">
          <div class="w-8 h-8 border-2 border-stone-100 border-t-luxury-copper rounded-full animate-spin"></div>
        </div>
      {:else if loyaltyStore.data}
        <!-- Mobile Member Card -->
        <MemberCard />
        
        <!-- Mobile Quick Stats -->
        <div class="grid grid-cols-2 gap-4">
          <div class="p-4 bg-stone-50 border border-stone-100 rounded-2xl flex flex-col gap-1">
             <span class="text-[8px] font-black text-stone-400 uppercase tracking-widest">Tổng chi tiêu</span>
             <span class="text-sm font-black text-stone-800">{formatCurrency(loyaltyStore.data.total_spent)}</span>
          </div>
          <div class="p-4 bg-stone-900 text-white rounded-2xl flex flex-col gap-1">
            <span class="text-[8px] font-black text-stone-500 uppercase tracking-widest">Hạng hiện tại</span>
            <span class="text-sm font-black text-luxury-copper uppercase italic">{loyaltyStore.tierName}</span>
         </div>
        </div>

        <!-- Tier Progress -->
        <div class="space-y-4 p-5 bg-white border border-stone-100 rounded-2xl">
            <div class="flex justify-between items-center">
                <span class="text-[10px] font-black text-stone-800 uppercase tracking-widest">Tiến trình hạng</span>
                <TrendingUp class="w-3 h-3 text-luxury-copper" />
            </div>
            
            <div class="h-1.5 w-full bg-stone-50 rounded-full overflow-hidden border border-stone-100">
                <div 
                    class="h-full bg-luxury-copper transition-all duration-1000 shadow-[0_0_8px_rgba(197,160,89,0.2)]"
                    style="width: {loyaltyStore.nextTierProgress}%"
                ></div>
            </div>

            <div class="flex justify-between text-[8px] uppercase tracking-widest font-black text-stone-300">
                <span>Standard</span>
                <span>Silver</span>
                <span>Gold</span>
                <span>Elite</span>
            </div>
        </div>

        <!-- Redemption Card -->
        <div class="p-6 bg-[#fcfbf9] border border-[#f5f1e8] rounded-2xl relative overflow-hidden group">
            <Gift class="absolute -right-4 -bottom-4 w-20 h-20 text-luxury-copper/5 rotate-12" />
            <div class="relative z-10 space-y-1">
                <span class="text-[9px] uppercase tracking-[2px] font-black text-stone-800">Quy tắc đổi thưởng</span>
                <p class="text-sm text-stone-600 font-serif italic">1 PTS = 1.000 VNĐ</p>
                <p class="text-[10px] text-stone-400 leading-relaxed font-medium">Hạn mức chiết khấu: 1% giá trị mỗi đơn hàng.</p>
            </div>
        </div>

        <!-- History -->
        <div class="space-y-5">
            <div class="flex items-center gap-2 border-b border-stone-100 pb-2">
                <History class="w-3.5 h-3.5 text-luxury-copper" />
                <h2 class="text-[11px] uppercase tracking-[2px] font-black text-stone-800">Lịch sử giao dịch</h2>
            </div>

            <div class="bg-white border border-stone-100 rounded-3xl overflow-hidden shadow-sm">
                <div class="divide-y divide-stone-50">
                    {#each loyaltyStore.data.history as tx}
                        <div class="px-5 py-4 flex justify-between items-center">
                            <div class="flex flex-col">
                                <span class="text-[12px] font-bold text-stone-800 tracking-tight">{tx.notes || 'Giao dịch điểm'}</span>
                                <span class="text-[9px] text-stone-400 font-mono mt-0.5">{formatDate(tx.created_at)}</span>
                            </div>
                            <div class="flex flex-col items-end">
                                <span class="text-base font-black {getTransactionIcon(tx.transaction_type)} tracking-tighter">
                                    {tx.amount > 0 ? '+' : ''}{tx.amount}
                                </span>
                                <span class="text-[8px] uppercase tracking-widest opacity-40 font-black">Points</span>
                            </div>
                        </div>
                    {/each}
                </div>
            </div>
        </div>
      {/if}
    </div>
  {/if}
{/if}

<style>
    :global(.text-luxury-copper) {
        color: #c5a059;
    }
    :global(.animate-pulse-slow) {
        animation: pulse-slow 3s cubic-bezier(0.4, 0, 0.6, 1) infinite;
    }
    @keyframes pulse-slow {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
</style>
