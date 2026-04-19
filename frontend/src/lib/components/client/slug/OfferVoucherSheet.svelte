<script lang="ts">
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import { resolveMediaUrl } from '$lib/state/utils';
  import { fly } from 'svelte/transition';
  import { cubicOut, cubicIn } from 'svelte/easing';
  import { Ticket, ArrowUpDown, ArrowDownNarrowWide, ArrowUpWideNarrow } from 'lucide-svelte';
  import type { ProductVariant } from '$lib/types';

  const { 
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
    productVouchers: any[];
    voucherSortOrder: 'none' | 'desc' | 'asc';
    activeOfferTab: Record<number, 'vouchers' | 'gifts'>;
    onClose: () => void;
    onToggleSort: () => void;
    onVoucherClick: (v: any) => void;
    onSetTab: (idx: number, tab: 'vouchers' | 'gifts') => void;
  }>();

  const shopStore = getShopStore();

  const hasVouchers = $derived(productVouchers.length > 0);
  const hasGifts = $derived(!!(variant.attributes?.gifts?.length));
  
  const currentTab = $derived.by(() => {
    if (activeOfferTab[idx]) return activeOfferTab[idx];
    if (hasVouchers) return 'vouchers';
    if (hasGifts) return 'gifts';
    return 'vouchers';
  });
</script>

<div 
  class="absolute inset-0 z-[100] flex flex-col bg-[#060606]/95 backdrop-blur-3xl rounded-[3rem] border border-white/10 shadow-[inner_0_0_40px_rgba(0,0,0,0.9)] overflow-hidden"
  in:fly={{ y: '100%', duration: 600, easing: cubicOut }}
  out:fly={{ y: '100%', duration: 400, easing: cubicIn }}
  onclick={(e) => e.stopPropagation()}
>
  <!-- 💎 SHEET DRAG HANDLE -->
  <div class="flex justify-center pt-5 pb-2 shrink-0">
     <div class="w-10 h-1.5 rounded-full bg-white/10"></div>
  </div>

  <div class="px-5 pb-4 flex-grow overflow-y-auto scrollbar-hide">
     <!-- TABS (MINI) -->
     <div class="offer-tabs-nav flex items-center gap-6 mb-5 border-b border-white/5 sticky top-0 bg-[#060606]/40 backdrop-blur-md z-20 pt-1 pb-3">
       {#if hasVouchers}
         <button 
           onclick={(e) => { e.stopPropagation(); onSetTab(idx, 'vouchers'); }}
           class="text-[10px] font-black uppercase tracking-[0.2em] transition-all {currentTab === 'vouchers' ? 'text-luxury-sakura' : 'text-white/30'}"
         >
           ƯU ĐÃI
         </button>
       {/if}
       {#if hasGifts}
         <button 
           onclick={(e) => { e.stopPropagation(); onSetTab(idx, 'gifts'); }}
           class="text-[10px] font-black uppercase tracking-[0.2em] transition-all {currentTab === 'gifts' ? 'text-luxury-sakura' : 'text-white/30'}"
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
           <span class="text-[8px] font-black text-white/50 uppercase tracking-tighter">
             {voucherSortOrder === 'none' ? 'Mặc định' : (voucherSortOrder === 'desc' ? 'Giá trị cao' : 'Giá trị thấp')}
           </span>
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
       <div class="flex flex-col gap-4 py-1 mb-24">
         {#each productVouchers as v}
           {@const isApplied = shopStore.selectedVoucherIds.includes(v.id)}
           <div class="voucher-notch-container relative h-[70px] flex items-center bg-white/5 rounded-2xl border border-white/5 overflow-hidden transition-all hover:bg-white/10 group cursor-pointer" onclick={() => onVoucherClick(v)}>
              <!-- 🎫 NOTCHES -->
              <div class="notch-marker notch-marker-left"></div>
              <div class="notch-marker notch-marker-right"></div>
              
              <div class="w-14 h-full bg-white/5 flex items-center justify-center border-r border-dashed border-white/20 shrink-0 relative">
                 <Ticket class="{isApplied ? 'text-luxury-sakura' : 'text-white/20'} transition-colors" size={18} />
                 <!-- Small circle highlight on divider -->
                 <div class="absolute -top-1 -right-[3px] w-1.5 h-1.5 rounded-full bg-[#060606]"></div>
                 <div class="absolute -bottom-1 -right-[3px] w-1.5 h-1.5 rounded-full bg-[#060606]"></div>
              </div>
              <div class="flex-grow px-4 flex items-center justify-between gap-2 overflow-hidden">
                 <div class="flex flex-col text-left truncate">
                    <span class="text-[12px] font-black text-white truncate leading-none uppercase tracking-widest">{v.label}</span>
                    <span class="text-[8px] font-bold text-luxury-sakura/60 uppercase truncate mt-1 tracking-tight">{v.sub}</span>
                 </div>
                 <button 
                   onclick={(e) => { e.stopPropagation(); onVoucherClick(v); }}
                   class="voucher-action-btn-mini {isApplied ? 'active' : ''} transition-all active:scale-90"
                 >
                    {isApplied ? 'ĐANG DÙNG' : 'SỬ DỤNG'}
                 </button>
              </div>
           </div>
         {/each}
       </div>
     {:else if currentTab === 'gifts' && hasGifts}
       <div class="flex flex-col gap-3 py-1 mb-24">
          {#each variant.attributes?.gifts || [] as gift}
           <div class="flex items-center gap-4 p-4 rounded-[2rem] bg-white/5 border border-white/5 hover:bg-white/10 transition-all">
             <div class="w-12 h-12 rounded-2xl overflow-hidden shrink-0 bg-black/40 flex items-center justify-center border border-white/10">
               {#if gift.image}
                 <img src={resolveMediaUrl(gift.image)} alt="" class="w-full h-full object-cover" />
               {/if}
             </div>
             <div class="flex flex-col">
                <span class="text-[11px] text-white font-black truncate tracking-wide uppercase">{gift.name}</span>
                <span class="text-[9px] text-luxury-sakura font-black uppercase tracking-[0.2em] mt-0.5">SỐ LƯỢNG: {gift.qty}</span>
             </div>
           </div>
          {/each}
       </div>
     {/if}
  </div>

  <div class="absolute inset-x-0 bottom-0 px-6 pt-10 pb-12 done-area-mini z-30 flex justify-center">
    <button 
      onclick={(e) => { e.stopPropagation(); onClose(); }}
      class="liquid-done-btn-mini w-full py-4.5 rounded-[2rem] font-black text-[13px] uppercase tracking-[0.3em] transition-all hover:scale-[1.02] active:scale-95"
    >
       XÁC NHẬN
    </button>
  </div>
</div>
