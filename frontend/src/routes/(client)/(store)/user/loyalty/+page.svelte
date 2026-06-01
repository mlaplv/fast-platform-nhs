<script lang="ts">
  import { onMount } from 'svelte';
  import { loyaltyStore } from '$lib/state/commerce/loyalty.svelte';
  import { LOYALTY_TIERS } from '$lib/config/commerce';
  import TrendingUp from "@lucide/svelte/icons/trending-up";
  import History from "@lucide/svelte/icons/history";
  import Info from "@lucide/svelte/icons/info";
  import Gift from "@lucide/svelte/icons/gift";
  import Wallet from "@lucide/svelte/icons/wallet";
  import { fade } from 'svelte/transition';
  import UserPageWrapper from '$lib/components/storefront/user/UserPageWrapper.svelte';
  import MemberCard from '$lib/components/storefront/user/MemberCard.svelte';
  import { formatCurrency } from '$lib/utils/format';
  
  import { checkinStore } from '$lib/state/commerce/checkin.svelte';
  import { authStore } from '$lib/state/authStore.svelte';

  onMount(() => {
    loyaltyStore.fetchLoyalty();
    if (authStore.isAuthenticated) {
      checkinStore.fetchStatus();
    }
  });

  const PREVIEW_DAYS = [
    { day: 1, reward: 10000, is_completed: false, is_today: false, is_bonus: false },
    { day: 2, reward: 10000, is_completed: false, is_today: false, is_bonus: false },
    { day: 3, reward: 10000, is_completed: false, is_today: false, is_bonus: false },
    { day: 4, reward: 10000, is_completed: false, is_today: false, is_bonus: false },
    { day: 5, reward: 10000, is_completed: false, is_today: false, is_bonus: false },
    { day: 6, reward: 10000, is_completed: false, is_today: false, is_bonus: false },
    { day: 7, reward: 20000, is_completed: false, is_today: false, is_bonus: true },
  ];

  const displayDays = $derived(
    checkinStore.status?.days?.length ? checkinStore.status.days : PREVIEW_DAYS
  );
  const isCheckedIn = $derived(checkinStore.status?.is_checked_in_today ?? false);
  const completedCount = $derived(displayDays.filter(d => d.is_completed).length);
  
  // Completed count connects adjacent days. Each transition is 62px width on desktop.
  const progressWidth = $derived(
    completedCount <= 1 ? 0 : Math.min(372, (completedCount - 1) * 62)
  );

  async function handleClaim() {
    if (!authStore.isAuthenticated) return;
    const ok = await checkinStore.claimReward();
    if (ok) {
      // Re-fetch status to ensure sync
      await checkinStore.fetchStatus();
      await loyaltyStore.fetchLoyalty();
    }
  }

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

<UserPageWrapper 
  title="Tích điểm" 
  description="Tích điểm từ mỗi đơn hàng để nhận ưu đãi đặc quyền Elite."
>
  <div class="space-y-10" in:fade>
    {#if loyaltyStore.loading && !loyaltyStore.data}
      <div class="flex flex-col items-center justify-center py-20 space-y-4">
        <div class="w-10 h-10 border-2 border-stone-100 border-t-luxury-copper rounded-full animate-spin"></div>
        <p class="text-[10px] tracking-[3px] text-stone-300 font-bold">Synchronizing Matrix...</p>
      </div>
    {:else if loyaltyStore.data}
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-10 items-start">
        <!-- Main Member Card -->
        <div class="lg:col-span-6 space-y-6">
           <MemberCard />
           
           <div class="mt-4 flex items-center justify-center gap-6">
              <div class="text-center">
                 <span class="block text-[8px] tracking-widest text-stone-400 font-bold uppercase">Tổng chi tiêu (LTV)</span>
                 <span class="text-sm font-serif italic text-stone-700">{formatCurrency(loyaltyStore.data.total_spent)}</span>
              </div>
              <div class="w-px h-6 bg-stone-100"></div>
              <div class="text-center">
                <span class="block text-[8px] tracking-widest text-stone-400 font-bold uppercase">Hạng hiện tại</span>
                <span class="text-[10px] font-bold text-luxury-copper tracking-widest">{loyaltyStore.tierName}</span>
             </div>
           </div>

           <!-- EMBEDDED ATTENDANCE CARD (Premium Elite V2.2) -->
           <div class="p-6 bg-white border border-stone-100/90 rounded-2xl relative overflow-hidden group shadow-[0_4px_25px_rgba(0,0,0,0.015)]">
             <div class="relative z-10">
               <!-- Header block -->
               <div class="flex items-center justify-between mb-4.5">
                 <div class="flex items-center gap-2">
                   <div class="w-2.5 h-2.5 rounded-full bg-amber-500 animate-pulse"></div>
                   <span class="text-[10px] tracking-[2.5px] font-black text-stone-800 uppercase">ĐIỂM DANH NHẬN QUÀ</span>
                 </div>
                 <span class="px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-700 text-[9px] font-bold tracking-wider">
                   Chuỗi {checkinStore.status?.current_streak || 0} ngày 🔥
                 </span>
               </div>

               <!-- Sub-description -->
               <p class="text-[11.5px] text-stone-500 leading-relaxed font-medium mb-5">
                 Tích lũy chuỗi liên tục 7 ngày để nhân đôi phần thưởng! Điểm thưởng được tự động áp dụng để thanh toán hóa đơn của bạn.
               </p>

               <!-- Days horizontal timeline -->
               <div class="w-full overflow-x-auto scrollbar-hide py-2 mb-6">
                 <div class="relative min-w-[420px] flex items-center justify-between px-1">
                   
                   <!-- Progress Line Background -->
                   <div class="absolute top-[26px] left-[26px] right-[26px] h-1 bg-stone-100 rounded-full z-0"></div>
                   
                   <!-- Active Progress Line -->
                   <div 
                     class="absolute top-[26px] left-[26px] h-1 bg-gradient-to-r from-amber-400 to-[#c5a059] rounded-full z-0 transition-all duration-700"
                     style="width: {progressWidth}px;"
                   ></div>

                   <!-- 7 Day Cards -->
                   {#each displayDays as d}
                     <div class="flex flex-col items-center gap-2.5 z-10">
                       <div 
                         class="w-13 h-13 rounded-xl flex flex-col items-center justify-center relative transition-all duration-200
                           {d.is_completed 
                             ? 'bg-amber-50/70 border-2 border-amber-300 text-amber-800 shadow-sm' 
                             : d.is_today 
                               ? 'bg-white border-2 border-[#231b15] text-[#231b15] shadow-md scale-105' 
                               : 'bg-white border border-stone-200 text-stone-400'}"
                         style="width: 52px; height: 52px;"
                       >
                         <span class="text-[8px] font-black tracking-wider uppercase opacity-75 mb-0.5">Ngày {d.day}</span>
                         
                         {#if d.is_completed}
                           <div class="absolute -top-1.5 -right-1.5 w-4.5 h-4.5 rounded-full bg-green-500 border border-white flex items-center justify-center shadow-sm">
                             <svg class="w-2.5 h-2.5 text-white" fill="none" stroke="currentColor" stroke-width="4" viewBox="0 0 24 24">
                               <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/>
                             </svg>
                           </div>
                           <span class="text-[10px] font-black text-amber-900">+{d.reward / 1000}K</span>
                         {:else if d.is_bonus}
                           <span class="text-xs">🎁</span>
                         {:else}
                           <span class="text-[10px] font-bold text-stone-500">+{d.reward / 1000}K</span>
                         {/if}
                       </div>
                     </div>
                   {/each}
                 </div>
               </div>

               <!-- Action Button -->
               {#if isCheckedIn}
                 <button 
                   disabled
                   class="w-full py-3.5 bg-stone-50 border border-stone-100 rounded-xl text-stone-400 text-[10px] font-black tracking-[3px] uppercase cursor-not-allowed transition-all"
                 >
                   BẠN ĐÃ ĐIỂM DANH HÔM NAY
                 </button>
               {:else}
                 <button 
                   onclick={handleClaim}
                   disabled={checkinStore.loading}
                   class="w-full py-3.5 bg-[#231b15] hover:opacity-90 active:scale-[0.98] text-[#f5d7af] text-[10px] font-black tracking-[3px] uppercase rounded-xl transition-all shadow-md flex items-center justify-center gap-2"
                 >
                   {#if checkinStore.loading}
                     <div class="w-3.5 h-3.5 border-2 border-stone-400 border-t-white rounded-full animate-spin"></div>
                   {:else}
                     ĐIỂM DANH NHẬN THƯỞNG HÀNG NGÀY
                   {/if}
                 </button>
               {/if}
             </div>
           </div>
        </div>

        <!-- Tier Progress & Rules -->
        <div class="lg:col-span-6 space-y-8">
            <div class="space-y-4">
                <div class="flex justify-between items-center px-1">
                    <div class="flex items-center gap-2">
                        <TrendingUp class="w-4 h-4 text-luxury-copper" />
                        <span class="text-[11px] font-black text-stone-800 tracking-widest">TIẾN TRÌNH HẠNG</span>
                    </div>
                    {#if loyaltyStore.data.total_spent < LOYALTY_TIERS.GOLD}
                      <span class="text-[10px] font-bold text-stone-400 tracking-tighter italic">
                          {Math.max(0, LOYALTY_TIERS.GOLD - loyaltyStore.data.total_spent).toLocaleString()}đ nữa để thăng hạng Silver
                      </span>
                    {/if}
                </div>
                
                <div class="h-1.5 w-full bg-stone-50 rounded-full overflow-hidden border border-stone-100">
                    <div 
                        class="h-full bg-luxury-copper transition-all duration-1000 ease-out shadow-[0_0_10px_rgba(197,160,89,0.3)]"
                        style="width: {loyaltyStore.nextTierProgress}%"
                    ></div>
                </div>

                <div class="flex justify-between text-[9px] tracking-widest font-bold text-stone-300">
                    <span class="text-luxury-copper">Standard</span>
                    <span>Silver</span>
                    <span>Gold</span>
                    <span>Elite</span>
                </div>
            </div>

            <!-- Redemption Rule Box -->
            <div class="p-6 bg-[#fcfbf9] border border-[#f5f1e8] rounded-2xl relative overflow-hidden group">
                <Gift class="absolute -right-4 -bottom-4 w-20 h-20 text-luxury-copper/5 rotate-12 transition-transform duration-700 group-hover:scale-125" />
                <div class="relative z-10 space-y-2">
                    <div class="flex items-center gap-2">
                        <div class="w-2 h-2 rounded-full bg-luxury-copper animate-pulse"></div>
                        <span class="text-[10px] tracking-[2px] font-black text-stone-800">QUY TẮC ĐỔI THƯỞNG</span>
                    </div>
                    <p class="text-[13px] text-stone-600 font-medium">1 {loyaltyStore.data?.point_unit ?? "điểm"} = 10,000đ chiết khấu</p>
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
              <h2 class="text-[12px] tracking-[2px] font-bold text-stone-800 uppercase">Lịch sử biến động</h2>
          </div>

          <div class="bg-white border border-stone-100 rounded-2xl shadow-[0_10px_40px_rgba(0,0,0,0.02)] overflow-hidden">
              <div class="divide-y divide-stone-50">
                  {#if loyaltyStore.data.history.length === 0}
                      <div class="p-20 text-center flex flex-col items-center gap-4">
                          <History class="w-8 h-8 text-stone-100" />
                          <p class="text-[10px] tracking-[3px] text-stone-300 font-bold italic">Chưa có lịch sử giao dịch điểm</p>
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
                                      <span class="text-[13px] font-bold text-stone-800 tracking-tight">{tx.notes || 'Giao dịch điểm'}</span>
                                      <span class="text-[10px] text-stone-400 font-mono mt-0.5">{formatDate(tx.created_at)}</span>
                                  </div>
                              </div>
                              <div class="flex flex-col items-end">
                                  <span class="text-base font-black {getTransactionIcon(tx.transaction_type)} tracking-tighter">
                                      {tx.amount > 0 ? '+' : ''}{tx.amount.toLocaleString('vi-VN')}
                                  </span>
                                  <span class="text-[8px] tracking-widest opacity-40 font-black">{loyaltyStore.data?.point_unit ?? 'điểm'}</span>
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
            <p class="text-red-500 font-bold tracking-widest text-[11px] mb-1 uppercase">Hệ thống đang bảo trì dữ liệu</p>
            <p class="text-red-400/70 text-[10px] tracking-tighter">{loyaltyStore.error}</p>
          </div>
          <button onclick={() => loyaltyStore.fetchLoyalty()} class="px-8 py-2.5 bg-white border border-red-100 text-red-500 text-[10px] rounded-full tracking-widest font-black hover:bg-red-50/50 transition-colors">THỬ LẠI</button>
      </div>
    {/if}
  </div>
</UserPageWrapper>


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
