<script lang="ts">
  import { fade, fly } from 'svelte/transition';
  import { cubicIn, cubicOut } from 'svelte/easing';
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import { liveEditStore } from '$lib/state/commerce/liveEdit.svelte';
  import { resolveMediaUrl } from '$lib/state/utils';
  import Ticket from "@lucide/svelte/icons/ticket";
  import ArrowUpDown from "@lucide/svelte/icons/arrow-up-down";
  import ArrowDownNarrowWide from "@lucide/svelte/icons/arrow-down-narrow-wide";
  import ArrowUpWideNarrow from "@lucide/svelte/icons/arrow-up-wide-narrow";
  import type { ProductVariant, Voucher } from '$lib/types';

  let { 
    variant, 
    idx, 
    productVouchers, 
    voucherSortOrder,
    activeOfferTab,
    onClose,
    onToggleSort,
    onVoucherClick,
    onSetTab
  } = $props<{
    variant: ProductVariant;
    idx: number;
    productVouchers: Voucher[];
    voucherSortOrder: 'none' | 'asc' | 'desc';
    activeOfferTab: Record<number, 'vouchers' | 'gifts'>;
    onClose: () => void;
    onToggleSort: () => void;
    onVoucherClick: (v: Voucher) => void;
    onSetTab: (idx: number, tab: 'vouchers' | 'gifts') => void;
  }>();

  const shopStore = getShopStore();
  const currentTab = $derived(activeOfferTab[idx] || 'vouchers');
  const hasVouchers = $derived(productVouchers.length > 0);
  const hasGifts = $derived((variant.attributes?.gifts || []).length > 0);
</script>

<!-- 🎭 ELITE V2.2: LOCAL CONTEXT OVERLAY (INSIDE ITEM) -->
<div 
  class="absolute inset-0 z-[190] backdrop-blur-md pointer-events-auto rounded-3xl"
  in:fade={{ duration: 300 }}
  out:fade={{ duration: 200 }}
  onclick={onClose}
></div>

<div 
  class="absolute inset-x-0 bottom-0 z-[200] flex flex-col bg-[#0b0b0b] backdrop-blur-3xl rounded-3xl border-t border-white/10 shadow-[0_-20px_80px_rgba(0,0,0,1)] overflow-hidden h-auto max-h-[92%] transition-all pointer-events-auto"
  in:fly={{ y: '100%', duration: 600, easing: cubicOut }}
  out:fly={{ y: '100%', duration: 400, easing: cubicIn }}
  onclick={(e) => e.stopPropagation()}
>
  <!-- 💎 SHEET DRAG HANDLE (CLICK TO CLOSE) -->
  <button 
    onclick={(e) => { e.stopPropagation(); onClose(); }}
    class="flex justify-center pt-4 pb-2 shrink-0 group/handle cursor-pointer w-full"
    aria-label="Đóng"
  >
     <div class="w-12 h-1.5 rounded-full bg-white/10 group-hover/handle:bg-white/30 transition-colors"></div>
  </button>

  <div class="px-5 pb-4 flex-grow overflow-y-auto no-scrollbar scroll-smooth">
     <!-- TABS (MINI) -->
     <div class="offer-tabs-nav flex items-center gap-6 mb-5 border-b border-white/5 sticky top-0 bg-[#0b0b0b]/80 backdrop-blur-xl z-20 pt-2 pb-4">
       {#if hasVouchers}
         <button 
           onclick={(e) => { e.stopPropagation(); onSetTab(idx, 'vouchers'); }}
           class="text-[11px] font-black uppercase tracking-[0.2em] transition-all {currentTab === 'vouchers' ? 'text-luxury-sakura' : 'text-white/20'}"
         >
           ƯU ĐÃI ĐẶC QUYỀN
         </button>
       {/if}
       {#if hasGifts}
         <button 
           onclick={(e) => { e.stopPropagation(); onSetTab(idx, 'gifts'); }}
           class="text-[11px] font-black uppercase tracking-[0.2em] transition-all {currentTab === 'gifts' ? 'text-luxury-sakura' : 'text-white/20'}"
         >
           QUÀ TẶNG
         </button>
       {/if}

       <!-- ⚡ ELITE SORT TOGGLE -->
       {#if currentTab === 'vouchers' && productVouchers.length > 1}
         <button 
           onclick={(e) => { e.stopPropagation(); onToggleSort(); }}
           class="ml-auto flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-all active:scale-95"
         >
           {#if voucherSortOrder === 'desc'}
             <ArrowDownNarrowWide size={12} class="text-luxury-sakura" />
           {:else if voucherSortOrder === 'asc'}
             <ArrowUpWideNarrow size={12} class="text-luxury-sakura" />
           {:else}
             <ArrowUpDown size={12} class="text-white/20" />
           {/if}
         </button>
       {/if}
     </div>

     {#if currentTab === 'vouchers' && hasVouchers}
       <div class="flex flex-col gap-4 py-1">
         {#each productVouchers as v}
           {@const isApplied = shopStore.selectedVoucherIds.includes(v.id)}
            <div class="voucher-notch-container relative h-[78px] flex items-center bg-white/[0.03] rounded-2xl border border-white/5 transition-all {isApplied ? 'bg-luxury-sakura/5 border-luxury-sakura/20 shadow-[0_0_20px_rgba(255,183,197,0.05)]' : 'hover:bg-white/[0.06]'} group cursor-pointer" onclick={() => onVoucherClick(v)}>
               <!-- 🎫 NOTCHES (TikTok Style) -->
               <div class="absolute -left-2 top-1/2 -translate-y-1/2 w-4 h-4 rounded-full bg-[#0b0b0b] z-20 shadow-[inset_-1px_0_1px_rgba(255,255,255,0.1)]"></div>
               <div class="absolute -right-2 top-1/2 -translate-y-1/2 w-4 h-4 rounded-full bg-[#0b0b0b] z-20 shadow-[inset_1px_0_1px_rgba(255,255,255,0.1)]"></div>
              
              <div class="w-16 h-full bg-white/[0.02] flex items-center justify-center border-r border-dashed border-white/10 shrink-0 relative">
                 <Ticket class="{isApplied ? 'text-luxury-sakura' : 'text-white/10'} transition-all scale-110" size={20} />
              </div>
              <div class="flex-grow px-5 flex items-center justify-between gap-3 overflow-hidden">
                 <div class="flex flex-col text-left truncate">
                    <span class="text-[13px] font-black text-white truncate leading-none uppercase tracking-widest {isApplied ? 'text-luxury-sakura' : ''}">{v.label}</span>
                    <span class="text-[9px] font-bold text-white/30 uppercase truncate mt-1.5 tracking-tight">{v.sub}</span>
                 </div>
                 <button 
                   onclick={(e) => { e.stopPropagation(); onVoucherClick(v); }}
                   class="voucher-action-btn-mini {isApplied ? 'active' : ''} transition-all active:scale-90 h-8 min-w-[80px]"
                 >
                    {isApplied ? 'ĐANG DÙNG' : 'SỬ DỤNG'}
                 </button>
              </div>
           </div>
         {/each}
       </div>
     {:else if currentTab === 'gifts' && hasGifts}
       <div class="flex flex-col gap-3 py-1">
          {#each variant.attributes?.gifts || [] as gift}
           <div class="flex items-center gap-4 p-5 rounded-[2.5rem] bg-white/[0.03] border border-white/5 hover:bg-white/[0.06] transition-all">
             <div class="w-14 h-14 rounded-2xl overflow-hidden shrink-0 bg-black/60 flex items-center justify-center border border-white/10">
               {#if gift.image}
                 <img src={resolveMediaUrl(gift.image)} alt={gift.name} class="w-full h-full object-cover" />
               {:else}
                  <div class="w-6 h-6 border-2 border-luxury-sakura/20 rounded-full animate-pulse"></div>
               {/if}
             </div>
             <div class="flex flex-col">
                <span class="text-[12px] text-white font-black truncate tracking-wide uppercase">{gift.name}</span>
                <span class="text-[9px] text-luxury-sakura font-black uppercase tracking-[0.2em] mt-1">SỐ LƯỢNG: {gift.qty}</span>
             </div>
           </div>
          {/each}
       </div>
     {/if}
  </div>

  <div class="px-6 pt-6 pb-10 bg-gradient-to-t from-[#0b0b0b] via-[#0b0b0b] to-transparent z-30 flex justify-center shrink-0 border-t border-white/5">
    <button 
      onclick={(e) => { e.stopPropagation(); onClose(); }}
      class="liquid-done-btn-mini w-full py-5 rounded-[2.5rem] font-black text-[14px] uppercase tracking-[0.2em] transition-all hover:scale-[1.02] active:scale-95 shadow-[0_15px_40px_rgba(255,183,197,0.3)]"
    >
       XÁC NHẬN CHỌN
    </button>
  </div>
</div>
