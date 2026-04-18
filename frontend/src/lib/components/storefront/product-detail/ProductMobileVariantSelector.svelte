<script lang="ts">
  import { fade, fly } from 'svelte/transition';
  import { X, Minus, Plus, Check, Zap } from 'lucide-svelte';
  import type { Product, ProductVariant } from '$lib/types';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { resolveMediaUrl } from '$lib/state/utils';

  interface Props {
    product: Product;
    show: boolean;
    onClose: () => void;
    onConfirm: (variant: ProductVariant | undefined, qty: number) => void;
  }

  let { product, show, onClose, onConfirm }: Props = $props();
  const ui = getClientUi();

  const variations = $derived(product.tier_variations || product.tierVariations || product.attributes?.tier_variations || product.metadata?.tier_variations || []);
  const pVariants = $derived(product.variants || []);

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
    return pVariants.find(v => 
      v.tierIndex.length === selectedIndices.length && 
      v.tierIndex.every((val, idx) => val === selectedIndices[idx])
    );
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

  let currentPrice = $derived(currentVariant ? (currentVariant.discountPrice || currentVariant.discount_price || currentVariant.price) : (product.discountPrice || product.discount_price || product.price || 0));
  let currentStock = $derived(currentVariant ? currentVariant.stock : product.stock);

  function selectOption(tierIdx: number, optIdx: number) {
    const newSelected = [...selectedIndices];
    if (newSelected[tierIdx] === optIdx) {
      newSelected[tierIdx] = -1;
    } else {
      newSelected[tierIdx] = optIdx;
    }
    selectedIndices = newSelected;
    
    if (quantity > (currentStock || 0)) {
      quantity = currentStock > 0 ? 1 : 0;
    }
  }

  function handleQuantity(delta: number) {
    const newVal = quantity + delta;
    if (newVal >= 1 && newVal <= (currentStock || 99)) {
      quantity = newVal;
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
    class="fixed bottom-0 left-0 right-0 bg-white z-[101] rounded-t-2xl max-h-[85vh] overflow-hidden flex flex-col"
    in:fly={{ y: 400, duration: 400 }}
    out:fly={{ y: 400, duration: 300 }}
  >
    <!-- Header: Product Quick Info -->
    <div class="px-4 py-4 flex gap-4 border-b border-gray-50 relative">
      <div class="w-28 h-28 bg-gray-50 rounded-lg overflow-hidden border border-gray-100 shrink-0 shadow-sm">
        <img src={currentImage} alt={product.name} class="w-full h-full object-cover" />
      </div>
      <div class="flex flex-col justify-end pb-1 pr-8">
        <div class="flex items-baseline gap-2">
           <span class="text-[#ee4d2d] text-xl font-black">₫{currentPrice.toLocaleString('vi-VN')}</span>
        </div>
        <div class="text-[12px] text-gray-500 font-medium mt-1">Kho: {currentStock || 0} sản phẩm</div>
        <div class="text-[12px] text-gray-800 font-bold mt-1">
          {#if selectedIndices.every(idx => idx === -1)}
            Vui lòng chọn phân loại
          {:else}
            Đã chọn: {variations.map((t, i) => selectedIndices[i] >= 0 ? t.options[selectedIndices[i]] : '').filter(Boolean).join(', ')}
          {/if}
        </div>
      </div>
      <button onclick={onClose} class="absolute top-4 right-4 text-gray-400 hover:text-black transition-colors">
        <X size={24} />
      </button>
    </div>

    <!-- Body: Scrollable Variations -->
    <div class="flex-1 overflow-y-auto p-4 space-y-6 pb-20">
      {#if variations}
        {#each variations as tier, tIdx}
          <div class="space-y-3">
            <h3 class="text-[14px] font-bold text-gray-900 capitalize">{tier.name}</h3>
            <div class="flex flex-wrap gap-2">
              {#each tier.options as option, oIdx}
                {@const isSelected = selectedIndices[tIdx] === oIdx}
                <button 
                  onclick={() => selectOption(tIdx, oIdx)}
                  class="px-4 py-2 text-[13px] border transition-all rounded-sm
                  {isSelected ? 'border-[#ee4d2d] text-[#ee4d2d] bg-[#ee4d2d]/5' : 'border-gray-100 bg-gray-50 text-gray-800'}"
                >
                  {option}
                </button>
              {/each}
            </div>
          </div>
        {/each}
      {/if}

      <!-- COMBO & GIFTS PREVIEW (Viral 2026 Logic) -->
      {#if activeComboQty > 1 || activeGifts.length > 0}
        <div class="mt-4 p-3 bg-gradient-to-br from-[#fdf2f2] to-white rounded-xl border border-[#ee4d2d]/10 space-y-3">
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-black uppercase text-gray-800 flex items-center gap-1.5"><Zap size={12} class="text-[#ee4d2d]" /> Ưu đãi mẫu này</span>
            {#if activeComboQty > 1}
              <span class="bg-[#ee4d2d] text-white text-[9px] font-black px-2 py-0.5 rounded-full">COMBO X{activeComboQty}</span>
            {/if}
          </div>
          {#if activeGifts.length > 0}
            <div class="flex flex-wrap gap-2">
              {#each activeGifts as gift}
                <div class="flex items-center gap-2 bg-white/80 p-1.5 rounded-lg border border-[#ee4d2d]/5 shadow-sm">
                  <div class="w-8 h-8 rounded bg-gray-50 overflow-hidden border border-gray-100">
                    <img src={resolveMediaUrl(gift.image)} alt={gift.name} class="w-full h-full object-cover" />
                  </div>
                  <div class="flex flex-col">
                    <span class="text-[10px] font-bold text-gray-900 leading-tight">{gift.name}</span>
                    <span class="text-[9px] text-[#ee4d2d] font-black italic">Tặng kèm x{gift.qty}</span>
                  </div>
                </div>
              {/each}
            </div>
          {/if}
        </div>
      {/if}

      <!-- Quantity -->
      <div class="flex items-center justify-between pt-4 border-t border-gray-50">
        <span class="text-[14px] font-bold text-gray-900">Số lượng</span>
        <div class="flex items-center border border-gray-200 rounded-sm">
          <button 
            onclick={() => handleQuantity(-1)}
            disabled={quantity <= 1}
            class="w-10 h-10 flex items-center justify-center text-gray-400 disabled:opacity-20"
          >
            <Minus size={16} />
          </button>
          <div class="w-12 text-center text-[15px] font-black text-gray-900">{quantity}</div>
          <button 
            onclick={() => handleQuantity(1)}
            disabled={quantity >= (currentStock || 99)}
            class="w-10 h-10 flex items-center justify-center text-gray-400 disabled:opacity-20"
          >
            <Plus size={16} />
          </button>
        </div>
      </div>
    </div>

    <!-- Footer: Confirm Button -->
    <div class="p-4 bg-white border-t border-gray-50">
      <button 
        onclick={handleConfirm}
        class="w-full h-12 bg-[#ee4d2d] text-white font-black text-[15px] uppercase tracking-wider shadow-lg shadow-[#ee4d2d]/20 active:scale-[0.98] transition-all"
      >
        Xác nhận
      </button>
    </div>
  </div>
{/if}

<style>
  /* Elite V2.2: Liquid Glass Smoothness */
  div {
    -webkit-tap-highlight-color: transparent;
  }
</style>
