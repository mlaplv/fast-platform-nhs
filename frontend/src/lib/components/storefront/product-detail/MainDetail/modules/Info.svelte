<script lang="ts">
  import type { Product, ProductVariant, ReviewStats } from '$lib/types';
  import Minus from "@lucide/svelte/icons/minus";
  import Plus from "@lucide/svelte/icons/plus";
  import ShoppingCart from "@lucide/svelte/icons/shopping-cart";
  import Gift from "@lucide/svelte/icons/gift";
  import Package from "@lucide/svelte/icons/package";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import HelenIcon from '$lib/components/client/support/HelenIcon.svelte';
  import { formatCurrency, formatNumber } from '$lib/utils/format';
  import ShareToUnlock from '../../shared/ShareToUnlock.svelte';

  interface Props {
    product: Product;
    stats: ReviewStats | null;
    displayPrice: {
      price: number | string;
      discountPrice?: number | string;
    };
    activePrices: {
      sale: number | string;
      original: number | string;
    };
    helenAdvice: string;
    productVouchers: Array<{
      id: string;
      label: string;
      sub?: string;
      type: 'ship' | 'discount';
    }>;
    selectedVouchers: string[];
    variations: Array<{
      name: string;
      options: string[];
      images?: string[];
    }>;
    selectedIndices: number[];
    quantity: number;
    currentStock: number;
    activeComboQty: number;
    activeGifts: Array<{
      id?: string;
      name: string;
      image?: string;
      qty: number;
    }>;
    isFlashSaleActive: boolean;
    timeLeft: { hours: number; minutes: number; seconds: number };
    isViralUnlocked: boolean;
    // Callbacks
    onToggleVoucher: (id: string) => void;
    onSelectOption: (tIdx: number, oIdx: number) => void;
    onQuantityChange: (delta: number) => void;
    onAddToCart: () => void;
    onBuyNow: () => void;
    onTriggerWriteReview: () => void;
    onTriggerViralFly: () => void;
  }

  let { 
    product, stats, displayPrice, activePrices, helenAdvice, 
    productVouchers, selectedVouchers, variations, selectedIndices, 
    quantity, currentStock, activeComboQty, activeGifts, 
    isFlashSaleActive, timeLeft, isViralUnlocked,
    onToggleVoucher, onSelectOption, onQuantityChange, 
    onAddToCart, onBuyNow, onTriggerWriteReview, onTriggerViralFly
  }: Props = $props();

</script>

<div class="flex-1 flex flex-col pt-0">
  <div class="flex items-start gap-4 mb-2">
    <h1 class="text-[24px] font-bold text-gray-900 leading-[1.2] tracking-tight">
      {product.name.replace(/40gr/g, '40g')}
    </h1>
  </div>

  <!-- Stats Row -->
  <div class="flex items-center gap-6 text-[15px] mb-2">
    <div class="flex items-center gap-2 text-[#ee4d2d] group cursor-default">
      <span class="text-[16px] font-black border-b-2 border-[#ee4d2d] leading-none pb-0.5">{stats?.average_rating || product.metadata?.rating || '5.0'}</span>
      <div class="flex gap-0.5">
         {#each Array(5) as _, i}
            <svg class="w-3.5 h-3.5 {i < Math.floor(stats?.average_rating || Number(product.metadata?.rating) || 5) ? 'text-orange-400' : 'text-gray-200'} fill-current drop-shadow-sm" viewBox="0 0 24 24"><path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"/></svg>
         {/each}
      </div>
    </div>
    <div class="w-[1.5px] h-4 bg-gray-200"></div>
    <button 
      onclick={onTriggerWriteReview}
      class="flex items-center gap-1.5 group cursor-pointer border-none bg-transparent hover:opacity-80 transition-opacity">
      <span class="text-black font-black border-b-2 border-black leading-none pb-0.5">{formatNumber(stats?.total_count ?? (product.metadata?.reviews?.length || 0))}</span>
      <span class="text-gray-500 font-bold text-[14px]">đánh giá</span>
    </button>
    <div class="w-[1.5px] h-4 bg-gray-200"></div>
    <div class="flex items-center gap-1.5">
      <span class="text-black font-black text-[16px]">{product.order_count_text || formatNumber(product.orderCount) || 0}</span>
      {#if !product.order_count_text}
        <span class="text-gray-500 font-bold text-[14px]">đã bán</span>
      {/if}
    </div>
    <div class="ml-auto">
       <button onclick={onTriggerWriteReview} class="text-[13px] text-gray-400 font-bold hover:text-[#ee4d2d] transition-colors flex items-center gap-1">
         Tố cáo
       </button>
    </div>
  </div>
  
  <div class="mb-2">
    <ShareToUnlock {product} compact={true} onUnlock={onTriggerViralFly} />
  </div>

  <!-- Price Bar -->
  <div class="bg-[#f6f6f6] px-5 py-1.5 flex items-center justify-between mb-2 relative overflow-hidden group border-y border-gray-100/50">
    <div class="flex flex-col">
        <div class="flex items-center gap-3 mb-0.5">
           <span class="text-[14px] text-gray-400 line-through">{formatCurrency(activePrices.original)}</span>
           {#if activePrices.original > activePrices.sale}
              <span class="text-[11px] font-black text-[#00bfa5] tracking-widest bg-[#e6f9f6] px-1.5 py-0.5">
                  Tiết kiệm {formatCurrency(Number(activePrices.original) - Number(activePrices.sale))}
              </span>
           {/if}
        </div>
        <div class="flex items-baseline gap-4">
            <span class="text-[32px] font-black text-[#d0011b] tracking-tighter leading-none">{formatCurrency(activePrices.sale)}</span>
        </div>

        <div class="mt-1 flex flex-col gap-2">
            <div class="flex items-center gap-2.5">
                {#if activeComboQty > 1}
                   <div class="bg-slate-900 text-white text-[8px] font-black px-1.5 py-0.5 rounded-sm tracking-widest flex items-center gap-1">
                       <Package size={10} class="text-white/70" /> {activeComboQty} sp đã áp dụng
                   </div>
                {/if}
                <div class="flex items-center gap-1.5 group/ai cursor-default">
                    <HelenIcon size={12} color="#3b82f6" />
                    <span class="text-[8px] text-blue-500 font-mono font-black tracking-[0.2em]">Helen</span>
                    <div class="w-0.5 h-0.5 bg-blue-400 rounded-full animate-pulse"></div>
                </div>
            </div>
            <div class="relative pl-4 border-l border-blue-200/40">
                <p class="text-[12.5px] text-slate-500 font-medium leading-[1.4] max-w-[580px] tracking-tight">
                    {helenAdvice}
                </p>
            </div>
        </div>
    </div>

    {#if isFlashSaleActive}
      <div class="flex flex-col items-end">
         <div class="flex items-center gap-2 mb-1">
            <div class="w-1.5 h-1.5 bg-[#ee4d2d] rounded-full animate-pulse shadow-[0_0_8px_#ee4d2d]"></div>
            <span class="text-[10px] font-black text-gray-500 tracking-[0.2em] opacity-80">Kết thúc sau</span>
         </div>
         <div class="flex gap-1 text-gray-800 font-black text-[17px] font-mono tabular-nums select-none">
            <div class="bg-gray-200/50 px-1.5 py-0.5 min-w-[30px] text-center rounded-sm">{timeLeft.hours < 10 ? '0' + timeLeft.hours : timeLeft.hours}</div>
            <span class="opacity-30 self-center w-1.5 text-center text-[12px]">:</span>
            <div class="bg-gray-200/50 px-1.5 py-0.5 min-w-[30px] text-center rounded-sm">{timeLeft.minutes < 10 ? '0' + timeLeft.minutes : timeLeft.minutes}</div>
            <span class="opacity-30 self-center w-1.5 text-center text-[12px]">:</span>
            <div class="bg-gray-200/50 px-1.5 py-0.5 min-w-[30px] text-center rounded-sm">{timeLeft.seconds < 10 ? '0' + timeLeft.seconds : timeLeft.seconds}</div>
         </div>
      </div>
    {/if}
  </div>

  <!-- Vouchers -->
  <div class="mb-2">
     <div class="flex items-start">
        <span class="w-[70px] shrink-0 text-[14px] text-gray-500 mt-2">Mã giảm giá</span>
        <div class="flex flex-wrap gap-3">
           {#each productVouchers as v}
             {@const isApplied = selectedVouchers.includes(v.id)}
             <button 
              onclick={() => onToggleVoucher(v.id)}
              class="relative flex items-center gap-2 bg-[#fff4f1] border-2 transition-all p-2 pr-4 shadow-sm group {isApplied ? 'border-[#ee4d2d]' : 'border-transparent hover:border-[#ee4d2d]/30'}">
                <div class="absolute -left-1 top-1/2 -translate-y-1/2 w-2 h-2 bg-white rounded-full border border-gray-100"></div>
                <div class="absolute -right-1 top-1/2 -translate-y-1/2 w-2 h-2 bg-white rounded-full border border-gray-100"></div>
                <div class="w-px h-6 bg-[#ee4d2d]/20 border-dashed border-l mx-1"></div>
                <div class="flex flex-col items-start translate-x-1">
                   <span class="text-[12px] font-black text-[#ee4d2d] leading-none">{v.label}</span>
                   <span class="text-[9px] text-gray-400 font-bold mt-1 tracking-tighter">{v.sub || ''}</span>
                </div>
                {#if isApplied}
                  <div class="absolute -top-2 -right-2 bg-[#ee4d2d] text-white rounded-full p-0.5 shadow-md">
                    <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" /></svg>
                  </div>
                {/if}
             </button>
           {/each}
        </div>
     </div>
  </div>


  <!-- Shipping -->
  <div class="space-y-2 mb-2">
     <div class="flex items-start">
        <span class="w-[70px] shrink-0 text-[14px] text-gray-500">Vận chuyển</span>
        <div class="space-y-2">
           <div class="flex items-center gap-2">
              <svg class="w-5 h-5 text-[#00bfa5]" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
              <span class="text-[14px] font-medium text-gray-800">Nhận hàng nhanh chóng</span>
              <svg class="w-3.5 h-3.5 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 5l7 7-7-7" /></svg>
           </div>
           <div class="text-[14px]">
              <span class="text-[#00bfa5] font-black">Phí ship 0₫</span>
              <p class="text-[12px] text-gray-400 mt-1">Giao hàng toàn quốc từ 2-4 ngày làm việc.</p>
           </div>
        </div>
     </div>
  </div>

  <!-- Variations -->
  {#if variations.length > 0}
    <div class="space-y-5 mb-3 mt-1">
      {#each variations as tier, tIdx}
        <div class="flex items-start">
          <span class="w-[70px] shrink-0 text-[14px] text-gray-500 mt-2 capitalize">{tier.name}</span>
          <div class="flex flex-wrap gap-2.5">
            {#each tier.options as option, oIdx}
              {@const isSelected = selectedIndices[tIdx] === oIdx}
              <button 
                type="button"
                onclick={() => onSelectOption(tIdx, oIdx)}
                class="relative min-w-[80px] h-10 px-4 border transition-all flex items-center justify-center text-[14px] hover:bg-[#ffeee8]/20 group
                {isSelected ? 'border-[#ee4d2d] text-[#ee4d2d] bg-white ring-1 ring-[#ee4d2d]/10' : 'border-gray-200 text-gray-800 bg-white'}"
              >
                {#if tIdx === 0 && tier.images?.[oIdx]}
                  <img src={tier.images[oIdx]} alt={option} class="w-6 h-6 object-cover mr-2 border border-gray-100" />
                {/if}
                <span class="font-medium">{option}</span>
                {#if isSelected}
                  <div class="absolute bottom-0 right-0 w-0 h-0 border-t-[12px] border-t-transparent border-r-[12px] border-r-[#ee4d2d]"></div>
                  <svg class="absolute bottom-0 right-0 w-2.5 h-2.5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="4"><path d="M20 6L9 17l-5-5" /></svg>
                {/if}
              </button>
            {/each}
          </div>
        </div>
      {/each}
    </div>
  {/if}

  <!-- Quantity -->
  <div class="flex items-center mb-2">
     <span class="w-[70px] shrink-0 text-[12px] font-bold text-gray-400 tracking-widest">Số lượng</span>
     <div class="flex items-center gap-8">
        <div class="flex items-center border border-gray-100 rounded-none h-9 group overflow-hidden bg-white shadow-sm">
           <button 
              type="button"
              class="w-10 h-full flex items-center justify-center text-gray-300 hover:text-black hover:bg-gray-50 transition-colors disabled:opacity-20 active:bg-gray-100"
              onclick={() => onQuantityChange(-1)} disabled={quantity <= 1}>
              <Minus class="w-3.5 h-3.5" strokeWidth={3} />
           </button>
           <input 
              type="text" 
              readonly
              class="w-12 h-full text-center border-x border-gray-100 text-[15px] font-black outline-none bg-white pointer-events-none text-gray-900"
              value={quantity} />
           <button 
              type="button"
              class="w-10 h-full flex items-center justify-center text-gray-300 hover:text-black hover:bg-gray-50 transition-colors disabled:opacity-20 active:bg-gray-100"
              onclick={() => onQuantityChange(1)} disabled={quantity >= (currentStock || 99)}>
              <Plus class="w-3.5 h-3.5" strokeWidth={3} />
           </button>
        </div>
        
        <div class="flex flex-col gap-0.5">
           <span class="text-[12px] text-gray-900 font-black tracking-tighter italic">Số lượng có hạn</span>
           {#if currentStock < 10}
             <span class="text-[11px] font-bold text-[#ee4d2d] flex items-center gap-1">
                <span class="w-1 h-1 bg-[#ee4d2d] rounded-full animate-ping"></span>
                Hàng hiếm, chỉ còn {currentStock} bộ trong kho
             </span>
           {:else}
             <span class="text-[11px] text-[#00bfa5] font-black tracking-tight italic">Đang có sẵn tại kho Mall chính hãng</span>
           {/if}
        </div>
     </div>
  </div>

  <!-- Gifts -->
  {#if activeGifts.length > 0}
    <div class="mb-6">
      <div class="bg-gradient-to-br from-[#fdf2f2] to-[#fff] border-2 border-[#ee4d2d]/10 p-5 relative overflow-hidden group/combo-box shadow-sm">
          <div class="flex items-start gap-4 relative z-10">
            <div class="mt-1">
              <div class="w-10 h-10 rounded-full bg-[#ee4d2d] flex items-center justify-center text-white shadow-lg shadow-[#ee4d2d]/20">
                <Gift size={20} />
              </div>
            </div>
            <div class="flex-1 space-y-3">
              <div class="flex items-center justify-between">
                <h3 class="text-[14px] font-black tracking-widest text-gray-800">Ưu đãi độc quyền</h3>
                {#if activeComboQty > 1}
                  <div class="bg-[#d0011b] text-white text-[10px] font-black px-2.5 py-1 rounded-full flex items-center gap-1.5 shadow-md">
                    <Package size={10} /> Combo x{activeComboQty}
                  </div>
                {/if}
              </div>
              <div class="grid grid-cols-1 gap-2.5">
                {#each activeGifts as gift}
                  <div class="flex items-center gap-3 bg-white/60 backdrop-blur-md p-2 border border-[#ee4d2d]/5 hover:border-[#ee4d2d]/20 transition-all group/gift-item rounded-sm">
                    <div class="w-12 h-12 rounded-sm overflow-hidden bg-gray-50 border border-gray-100 shrink-0 group-hover/gift-item:scale-105 transition-transform shadow-sm">
                      {#if gift.image}
                        <img src={gift.image} alt={gift.name} class="w-full h-full object-cover" />
                      {:else}
                        <div class="w-full h-full flex items-center justify-center bg-gray-50 text-gray-300">
                          <Sparkles size={16} />
                        </div>
                      {/if}
                    </div>
                    <div class="flex flex-col">
                      <span class="text-[13px] font-bold text-gray-900 leading-tight">{gift.name}</span>
                      <div class="flex items-center gap-2 mt-0.5">
                        <span class="text-[11px] text-gray-500 font-medium">Số lượng:</span>
                        <span class="text-[11px] text-[#ee4d2d] font-black italic">x{gift.qty}</span>
                      </div>
                    </div>
                  </div>
                {/each}
              </div>
            </div>
          </div>
      </div>
    </div>
  {/if}

  <!-- CTA Buttons -->
  <div class="flex gap-4 mt-4 pb-4">
      <button 
         onclick={onAddToCart}
         class="h-[52px] min-w-[210px] border border-[#d0011b] bg-[#ffeee8]/60 text-[#d0011b] font-medium flex items-center justify-center gap-2.5 hover:bg-[#ffeee8] transition-all rounded-none">
         <ShoppingCart class="w-5 h-5" />
         <span class="text-[14px] font-bold">Thêm vào giỏ hàng</span>
      </button>
      <button 
         onclick={onBuyNow}
         class="h-[52px] min-w-[180px] bg-[#d0011b] text-white font-bold text-[15px] hover:brightness-110 transition-all rounded-none">
         Mua ngay
      </button>
  </div>
</div>
