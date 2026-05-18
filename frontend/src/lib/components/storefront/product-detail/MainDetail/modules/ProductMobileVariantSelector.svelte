<script lang="ts">
  import { fade, fly } from 'svelte/transition';
  import Minus from "@lucide/svelte/icons/minus";
  import Plus from "@lucide/svelte/icons/plus";
  import Check from "@lucide/svelte/icons/check";
  import Zap from "@lucide/svelte/icons/zap";
import X from "@lucide/svelte/icons/x";
import Truck from "@lucide/svelte/icons/truck";
import ShieldCheck from "@lucide/svelte/icons/shield-check";
  import type { Product, ProductVariant } from '$lib/types';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { resolveMediaUrl } from '$lib/state/utils';
  import { formatCurrency } from '$lib/utils/format';
  import HelenIcon from '$lib/components/client/support/HelenIcon.svelte';
  import { supportAgent } from '$lib/state/commerce/supportAgent.svelte';

  interface Props {
    product: Product;
    show: boolean;
    onClose: () => void;
    onConfirm: (variant: ProductVariant | undefined, qty: number) => void;
  }

  let { product, show, onClose, onConfirm }: Props = $props();
  const ui = getClientUi();

  const variations = $derived(product.tier_variations || product.tierVariations || product.attributes?.tier_variations || product.metadata?.tier_variations || []);
  const pVariants = $derived((product.variants || []).filter(v => v.attributes?.is_active !== false));

  // Helper to check if a specific option is active
  function isOptionActive(tIdx: number, oIdx: number): boolean {
    const rawVariants = product.variants || [];
    if (variations.length === 1) {
      const v = rawVariants.find(x => {
        const idxs = x.tierIndex || x.tier_index || [];
        return idxs[0] === oIdx;
      });
      return v?.attributes?.is_active !== false;
    }
    return rawVariants.some(x => {
      const idxs = x.tierIndex || x.tier_index || [];
      return idxs[tIdx] === oIdx && x.attributes?.is_active !== false;
    });
  }

  let selectedIndices = $state<number[]>([]);
  $effect(() => {
    if (selectedIndices.length === 0 && variations.length > 0) {
      const defaultVariant = pVariants.find(v => v.is_default);
      if (defaultVariant && (defaultVariant.tierIndex || defaultVariant.tier_index)) {
        selectedIndices = [...(defaultVariant.tierIndex || defaultVariant.tier_index)];
      } else {
        selectedIndices = variations.map(() => 0);
      }
    }
  });
  let quantity = $state(1);

  const currentVariant = $derived.by(() => {
    if (selectedIndices.some(idx => idx === -1)) return undefined;
    return pVariants.find(v => {
      const vIndices = v.tierIndex || v.tier_index;
      if (!vIndices) return false;
      return vIndices.length === selectedIndices.length && 
             vIndices.every((val: number, idx: number) => val === selectedIndices[idx]);
    });
  });
  
  const activeComboQty = $derived((currentVariant)?.attributes?.combo_qty || (currentVariant)?.attributes?.comboQty || 0);
  const activeGifts = $derived((currentVariant)?.attributes?.gifts || []);

  let currentImage = $derived.by(() => {
    if (selectedIndices[0] >= 0 && variations?.[0]?.images?.[selectedIndices[0]]) {
      return variations[0].images[selectedIndices[0]];
    }
    const pImages = product.images || [];
    return pImages[0] || '/placeholder.png';
  });

  const effectiveUnitPrice = $derived.by(() => {
    const v = currentVariant;
    if (!v) return product.discountPrice || product.discount_price || product.price || 0;
    
    // Check if there's a better tier for THIS product based on quantity
    const comboVariants = pVariants.filter(cv => cv.attributes && cv.attributes.combo_qty);
    if (comboVariants.length === 0) return v.discountPrice || v.discount_price || v.price;

    const sortedTiers = [...comboVariants].sort((a, b) => Number(b.attributes.combo_qty) - Number(a.attributes.combo_qty));
    const bestTier = sortedTiers.find(t => Number(t.attributes.combo_qty) <= quantity);
    
    const finalV = bestTier || v;
    return finalV.discountPrice || finalV.discount_price || finalV.price;
  });

  // --- HELEN AI PRICE INTELLIGENCE (MOBILE VERSION) ---
  const helenAdvice = $derived.by(() => {
    const comboVariants = pVariants.filter(cv => cv.attributes && cv.attributes.combo_qty);
    if (comboVariants.length === 0) return "Cơ hội sở hữu liệu trình chuyên sâu với ưu đãi độc quyền.";
    
    const sortedTiers = [...comboVariants].sort((a, b) => Number(a.attributes.combo_qty) - Number(b.attributes.combo_qty));
    const nextTier = sortedTiers.find(t => Number(t.attributes.combo_qty) > quantity);
    
    if (nextTier) {
      const gap = Number(nextTier.attributes.combo_qty) - quantity;
      const nextUnitPrice = nextTier.discountPrice || nextTier.discount_price || nextTier.price;
      const currentUnitPrice = effectiveUnitPrice;
      const savingsPerUnit = currentUnitPrice - nextUnitPrice;
      const tierName = nextTier.tierIndex.map((idx, i) => variations?.[i]?.options?.[idx] || '').filter(Boolean).join(' ') || "Combo tiếp theo";
      
      if (savingsPerUnit > 0) {
        return `Thêm ${gap} sp để nâng cấp lên "${tierName}" (giảm ${formatCurrency(savingsPerUnit)}/sp)!`;
      }
      return `Chỉ thêm ${gap} sp để nhận trọn bộ quà tặng "${tierName}"!`;
    }
    
    return "Tuyệt vời! Bạn đang nhận được mức giá tối ưu nhất cho liệu trình này.";
  });

  let currentPrice = $derived(effectiveUnitPrice);
  let totalPrice = $derived(effectiveUnitPrice * quantity);
  let currentStock = $derived(currentVariant ? currentVariant.stock : product.stock);

  function selectOption(tierIdx: number, optIdx: number) {
    const newSelected = [...selectedIndices];
    if (newSelected[tierIdx] === optIdx) {
      newSelected[tierIdx] = -1;
    } else {
      newSelected[tierIdx] = optIdx;
    }
    selectedIndices = newSelected;
    
    // Sync quantity with combo_qty (Elite V2.2)
    const nextVariant = pVariants.find(v => {
      const vIndices = v.tierIndex || v.tier_index;
      if (!vIndices) return false;
      return vIndices.length === selectedIndices.length && 
             vIndices.every((val: number, i: number) => val === selectedIndices[i]);
    });
    if (nextVariant?.attributes?.combo_qty) {
      quantity = Number(nextVariant.attributes.combo_qty);
    } else if (quantity > (currentStock || 0)) {
      quantity = currentStock > 0 ? 1 : 0;
    }
  }

  function handleQuantity(delta: number) {
    const newVal = quantity + delta;
    if (newVal >= 1 && newVal <= (currentStock || 99)) {
      quantity = newVal;
      
      // SYNC BACK: Auto-select variant matching this quantity (Elite V2.2)
      const matchingVariant = pVariants.find(v => Number(v.attributes?.combo_qty || v.attributes?.comboQty || 0) === quantity);
      const mIndices = matchingVariant?.tierIndex || matchingVariant?.tier_index;
      if (mIndices) {
        selectedIndices = [...mIndices];
      }
    }
  }

  function handleConfirm() {
    if (variations.length > 0 && selectedIndices.includes(-1)) {
      ui.showToast('Vui lòng chọn phân loại', 'error');
      return;
    }
    onConfirm(currentVariant, quantity);
  }
</script>

{#if show}
  <!-- Overlay -->
  <button 
    class="fixed inset-0 bg-black/60 z-[100] backdrop-blur-sm"
    onclick={onClose}
    in:fade={{ duration: 200 }}
    out:fade={{ duration: 200 }}
    aria-label="Đóng"
  ></button>

  <!-- Bottom Sheet -->
  <div 
    class="fixed bottom-0 left-0 right-0 bg-white z-[101] rounded-t-2xl max-h-[90vh] overflow-hidden flex flex-col shadow-2xl border-t border-gray-100"
    in:fly={{ y: 400, duration: 400, opacity: 0 }}
    out:fly={{ y: 400, duration: 300, opacity: 0 }}
  >
    <!-- Clean Header -->
    <div class="px-4 py-4 flex gap-4 relative border-b border-gray-50">
      <div class="w-24 h-24 bg-gray-50 rounded-lg overflow-hidden border border-gray-100 shrink-0">
        <img src={currentImage} alt={product.name} class="w-full h-full object-cover" />
      </div>
      <div class="flex flex-col justify-end pb-1 pr-6">
        <div class="flex items-baseline gap-1">
           <span class="text-[#ee4d2d] text-xl font-black">{formatCurrency(currentPrice)}</span>
           <span class="text-[9px] text-gray-400 font-bold ">/ sp</span>
        </div>
        {#if quantity > 1}
          <div class="text-[12px] text-[#ee4d2d] font-bold mt-0.5">Tổng: {formatCurrency(totalPrice)}</div>
        {/if}
        <div class="flex items-center gap-1 mt-1 text-[10px] text-gray-500">
           Kho: {currentStock || 0} sản phẩm
        </div>
        
        <div class="text-[12px] text-gray-900 font-bold mt-2">
          {#if selectedIndices.every(idx => idx === -1)}
            <span class="text-[#ee4d2d]">Vui lòng chọn phân loại</span>
          {:else}
            <span>Đã chọn: {variations.map((t, i) => selectedIndices[i] >= 0 ? t.options[selectedIndices[i]] : '').filter(Boolean).join(', ')}</span>
          {/if}
        </div>
      </div>
      <button onclick={onClose} class="absolute top-3 right-3 w-8 h-8 flex items-center justify-center rounded-full bg-gray-50 text-gray-400 active:scale-90 transition-all">
        <X size={18} />
      </button>
    </div>

    <!-- Body: Focused Selection -->
    <div class="overflow-y-auto px-4 space-y-6 pt-4">
      {#if variations}
        {#each variations as tier, tIdx}
          <div class="space-y-3">
            <h3 class="text-[13px] font-bold text-gray-500 tracking-wider">{tier.name}</h3>
            <div class="flex flex-wrap gap-3">
              {#each tier.options as option, oIdx}
                {#if isOptionActive(tIdx, oIdx)}
                  {@const isSelected = selectedIndices[tIdx] === oIdx}
                  <button 
                    onclick={() => selectOption(tIdx, oIdx)}
                    class="relative px-5 py-2.5 text-[12px] font-black border-2 transition-all tracking-tight
                    {isSelected ? 'border-[#ee4d2d] text-[#ee4d2d] bg-[#ee4d2d]/5' : 'border-gray-100 bg-gray-50 text-gray-500'}"
                  >
                    {option}
                    {#if isSelected}
                      <div class="absolute top-[-2px] right-[-2px] w-0 h-0 border-t-[8px] border-t-[#ee4d2d] border-l-[8px] border-l-transparent"></div>
                    {/if}
                  </button>
                {/if}
              {/each}
            </div>
          </div>
        {/each}
      {/if}

      <!-- COMBO & GIFTS: Simple Row -->
      {#if activeComboQty > 1 || activeGifts.length > 0}
        <div class="p-3 bg-gray-50 rounded-xl border border-gray-100 space-y-3">
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-bold text-gray-400 flex items-center gap-1.5"><Zap size={12} class="text-[#ee4d2d]" /> Ưu đãi</span>
            {#if activeComboQty > 1}
              <span class="bg-[#ee4d2d] text-white text-[9px] font-black px-2 py-0.5 rounded">Combo x{activeComboQty}</span>
            {/if}
          </div>
          {#if activeGifts.length > 0}
            <div class="flex flex-wrap gap-2">
              {#each activeGifts as gift}
                <div class="flex items-center gap-2 bg-white p-1.5 rounded-lg border border-gray-100 shadow-sm">
                  <div class="w-8 h-8 rounded bg-gray-50 overflow-hidden border border-gray-100">
                    <img src={resolveMediaUrl(gift.image)} alt={gift.name} class="w-full h-full object-cover" />
                  </div>
                  <div class="flex flex-col">
                    <span class="text-[10px] font-bold text-gray-900 leading-tight">{gift.name}</span>
                    <span class="text-[9px] text-[#ee4d2d] font-bold italic">Tặng kèm x{gift.qty}</span>
                  </div>
                </div>
              {/each}
            </div>
          {/if}
        </div>
      {/if}

      <!-- Quantity -->
      <div class="flex items-center justify-between pt-4 border-t border-gray-50">
        <span class="text-[14px] font-bold text-gray-900">Số lượng mua</span>
        <div class="flex items-center bg-gray-50 rounded-lg border border-gray-100">
          <button 
            type="button"
            onclick={() => handleQuantity(-1)}
            disabled={quantity <= 1}
            class="w-10 h-10 flex items-center justify-center text-gray-400"
          >
            <Minus size={16} />
          </button>
          <div class="w-10 text-center text-[15px] font-black text-gray-900">{quantity}</div>
          <button 
            type="button"
            onclick={() => handleQuantity(1)}
            disabled={quantity >= (currentStock || 99)}
            class="w-10 h-10 flex items-center justify-center text-gray-400"
          >
            <Plus size={16} />
          </button>
        </div>
      </div>

      <!-- Agentic AI Advice: Clean Helen Box -->
      <div class="mt-4 flex items-center gap-3 bg-blue-50/50 p-4 rounded-xl border border-blue-100">
          <div class="flex flex-col items-center shrink-0">
              <HelenIcon size={20} color="#3b82f6" />
              <span class="text-[7px] text-blue-500 font-black mt-1 tracking-tighter">{supportAgent.config.agentName}</span>
          </div>
          <div class="flex-1">
              <p class="text-[12px] text-slate-700 font-bold leading-relaxed italic">
                 "{helenAdvice}"
              </p>
          </div>
      </div>
    </div>

    <!-- Footer: Clean Confirm with FOMO -->
    <div class="p-4 bg-white border-t border-gray-50">
      <div class="flex items-center justify-between px-1 mb-3">
         <div class="flex items-center gap-1.5 bg-emerald-50 px-2 py-1 rounded-md border border-emerald-100/50">
            <Truck size={12} class="text-emerald-500" />
            <span class="text-[10px] text-emerald-600 font-black tracking-tighter">Freeship</span>
         </div>
         <div class="flex items-center gap-1.5 bg-amber-50 px-2 py-1 rounded-md border border-amber-100/50">
            <Zap size={12} class="text-amber-500" />
            <span class="text-[10px] text-amber-600 font-black tracking-tighter">Giao nhanh 2h</span>
         </div>
         <div class="flex items-center gap-1.5 bg-blue-50 px-2 py-1 rounded-md border border-blue-100/50">
            <ShieldCheck size={12} class="text-blue-500" />
            <span class="text-[10px] text-blue-600 font-black tracking-tighter">Chính hãng</span>
         </div>
      </div>

      <button 
        onclick={handleConfirm}
        class="w-full h-12 bg-[#ee4d2d] text-white font-black text-[15px] tracking-wider rounded-xl shadow-lg shadow-[#ee4d2d]/20 active:scale-[0.98] transition-all"
      >
        Xác nhận lựa chọn
      </button>
      <div class="text-center mt-3">
         <span class="text-[9px] text-gray-400 font-bold tracking-widest opacity-60">Thanh toán an toàn • Bảo mật 100%</span>
      </div>
    </div>
  </div>
{/if}

<style>
  /* Elite V2.2: Liquid Glass Smoothness */
  div {
    -webkit-tap-highlight-color: transparent;
  }
</style>
