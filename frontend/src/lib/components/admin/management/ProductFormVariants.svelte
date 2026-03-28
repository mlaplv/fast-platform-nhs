<script lang="ts">
  import { Plus, X, ImagePlus, Trash2, ListTree, Zap, ChevronRight, Check, Pencil } from "lucide-svelte";
  import { resolveMediaUrl } from "$lib/state/utils";
  import type { Product } from "$lib/types";

  let {
    formTierVariations = $bindable(),
    formVariants = $bindable(),
    onOpenVault
  } = $props<{
    formTierVariations: Product['tierVariations'];
    formVariants: Product['variants'];
    onOpenVault: (tierIndex: number, optionIndex: number) => void;
  }>();

  let hasCustomImages = $state(false);
  let batchPrice = $state<number>(0);
  let batchDiscountPrice = $state<number>(0);
  let batchStock = $state<number>(0);
  let batchSku = $state<string>('');
  
  let editingOption = $state<{ tIndex: number, oIndex: number } | null>(null);
  let editingValue = $state("");
  
  // R102 Validation Rune: Track invalid price combinations
  const variantValidation = $derived(formVariants.map(v => ({
    isInvalid: v.discountPrice > 0 && Number(v.discountPrice) >= Number(v.price)
  })));

  // Svelte 5 init
  $effect(() => {
    if (formTierVariations === undefined) formTierVariations = [];
    if (formVariants === undefined) formVariants = [];

    if (formTierVariations.length > 0 && formTierVariations[0].images?.some(img => img)) {
      hasCustomImages = true;
    }
  });

  function addTier() {
    if (formTierVariations.length >= 2) return;
    formTierVariations = [...formTierVariations, { 
      name: formTierVariations.length === 0 ? "Màu sắc" : "Kích cỡ", 
      options: [], 
      images: [] 
    }];
    rebuildMatrix();
  }

  function removeTier(tIndex: number) {
    formTierVariations.splice(tIndex, 1);
    formTierVariations = [...formTierVariations];
    
    // If we removed Tier 1 and there is a Tier 2, Tier 2 becomes Tier 1
    if (tIndex === 0 && hasCustomImages) {
      hasCustomImages = false; 
    }
    
    rebuildMatrix();
  }

  function addOption(tIndex: number, value: string) {
    if (!value.trim()) return;
    if (formTierVariations[tIndex].options.includes(value.trim())) return;
    
    formTierVariations[tIndex].options.push(value.trim());
    formTierVariations[tIndex].images.push(null);
    formTierVariations = [...formTierVariations];
    rebuildMatrix();
  }

  function removeOption(tIndex: number, oIndex: number) {
    formTierVariations[tIndex].options.splice(oIndex, 1);
    formTierVariations[tIndex].images.splice(oIndex, 1);
    formTierVariations = [...formTierVariations];
    
    // Cleanup empty tiers
    if (formTierVariations[tIndex].options.length === 0) {
       removeTier(tIndex);
       return;
    }
    rebuildMatrix();
  }

  function toggleCustomImages() {
    hasCustomImages = !hasCustomImages;
    if (!hasCustomImages && formTierVariations.length > 0) {
      formTierVariations[0].images = formTierVariations[0].options.map(() => null);
    }
  }

  function rebuildMatrix() {
    if (formTierVariations.length === 0) {
      formVariants = [];
      return;
    }

    const t1 = formTierVariations[0].options;
    const t2 = formTierVariations.length > 1 ? formTierVariations[1].options : [];

    const newVariants: Product['variants'] = [];

    if (t1.length === 0) {
      formVariants = [];
      return;
    }

    for (let i = 0; i < t1.length; i++) {
      if (t2.length > 0) {
        for (let j = 0; j < t2.length; j++) {
          const tIdx = [i, j];
          const existing = findExistingVariant(tIdx);
          newVariants.push(existing || { tierIndex: tIdx, sku: "", price: 0, discountPrice: 0, stock: 0 });
        }
      } else {
        const tIdx = [i];
        const existing = findExistingVariant(tIdx);
        newVariants.push(existing || { tierIndex: tIdx, sku: "", price: 0, discountPrice: 0, stock: 0 });
      }
    }

    formVariants = newVariants;
  }

  function startEdit(tIndex: number, oIndex: number) {
    editingOption = { tIndex, oIndex };
    editingValue = formTierVariations[tIndex].options[oIndex];
  }

  function saveEdit() {
    if (!editingOption) return;
    const { tIndex, oIndex } = editingOption;
    const newVal = editingValue.trim();
    if (newVal && (newVal === formTierVariations[tIndex].options[oIndex] || !formTierVariations[tIndex].options.includes(newVal))) {
      formTierVariations[tIndex].options[oIndex] = newVal;
      formTierVariations = [...formTierVariations];
      rebuildMatrix();
    }
    editingOption = null;
  }

  function findExistingVariant(targetIndex: number[]): Product['variants'][number] | undefined {
    return formVariants.find(v => 
      v.tierIndex.length === targetIndex.length && 
      v.tierIndex.every((val, idx) => val === targetIndex[idx])
    );
  }

  function applyBatch() {
    formVariants = formVariants.map(v => ({
      ...v,
      price: batchPrice > 0 ? batchPrice : v.price,
      discountPrice: batchDiscountPrice > 0 ? batchDiscountPrice : v.discountPrice,
      stock: batchStock > 0 ? batchStock : v.stock,
      sku: batchSku ? `${batchSku}-${v.tierIndex.join('-')}` : v.sku
    }));
  }

  function handleKeydown(e: KeyboardEvent, tIndex: number) {
    if (e.key === 'Enter') {
      e.preventDefault();
      addOption(tIndex, e.currentTarget.value);
      e.currentTarget.value = '';
    }
  }

  function removeImage(oIndex: number) {
    if (formTierVariations.length > 0) {
      formTierVariations[0].images[oIndex] = null;
    }
  }
</script>

<div class="flex flex-col gap-5 border border-white/5 rounded-2xl bg-[#0f0f0f] p-5 shadow-inner">
  
  <div class="flex items-center justify-between pb-3 border-b border-white/5">
    <div class="flex items-center gap-2">
      <div class="w-6 h-6 rounded-lg bg-amber-500/10 flex items-center justify-center text-amber-500">
        <ListTree size={12} />
      </div>
      <div class="flex flex-col">
        <span class="text-[10px] font-black uppercase tracking-widest text-white/50">Phân loại hàng</span>
        <span class="text-[9px] text-white/20 italic">Thiết lập biến thể (Màu sắc, Kích thước...)</span>
      </div>
    </div>
    
    {#if formTierVariations.length < 2}
      <button 
        onclick={addTier}
        class="flex items-center gap-1.5 px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-[9px] font-bold uppercase tracking-wider text-white/40 hover:text-white transition-colors"
      >
        <Plus size={11} /> Thêm Nhóm Phân Loại
      </button>
    {/if}
  </div>

  {#if formTierVariations.length === 0}
    <div class="flex flex-col items-center justify-center py-6 gap-2 opacity-50">
      <ListTree size={24} class="text-white/20" />
      <div class="text-[10px] text-white/30 uppercase tracking-widest font-black">Chưa có phân loại nào</div>
    </div>
  {:else}
    
    <div class="flex flex-col gap-6">
      {#each formTierVariations as tier, tIndex}
        <div class="flex flex-col gap-3 relative p-4 border border-white/5 rounded-xl bg-black/40">
          <button 
            onclick={() => removeTier(tIndex)}
            class="absolute top-2 right-2 p-1.5 text-white/20 hover:text-red-400 hover:bg-red-400/10 rounded-md transition-colors"
          ><X size={12} /></button>

          <!-- TIER HEADER -->
          <div class="flex items-center justify-between gap-4 pr-6">
            <div class="flex-1 max-w-[200px]">
              <label class="text-[8px] font-black uppercase tracking-widest text-amber-500/60 ml-1 mb-1 block">Tên nhóm phân loại {tIndex + 1}</label>
              <input 
                type="text" 
                bind:value={tier.name}
                placeholder="VD: Màu sắc, Kích cỡ..."
                class="w-full bg-transparent border-b border-white/10 px-1 py-1 text-sm text-white placeholder:text-white/20 outline-none focus:border-amber-500"
              />
            </div>

            {#if tIndex === 0}
              <div class="flex items-center gap-2">
                <span class="text-[9px] font-bold text-white/30 uppercase tracking-wider">Thêm hình ảnh?</span>
                <!-- Custom Toggle Switch -->
                <button 
                  onclick={toggleCustomImages}
                  class="w-8 h-4 rounded-full relative transition-colors {hasCustomImages ? 'bg-amber-500' : 'bg-white/10'}"
                >
                  <div class="absolute top-0.5 left-0.5 w-3 h-3 rounded-full bg-white transition-transform shadow-md {hasCustomImages ? 'translate-x-4' : 'translate-x-0'}"></div>
                </button>
              </div>
            {/if}
          </div>

          <!-- TIER OPTIONS -->
          <div class="flex flex-col gap-2 mt-2">
            <label class="text-[8px] font-black uppercase tracking-widest text-white/30 ml-1">Các thuộc tính (Ấn Enter để tạo)</label>
            <div class="flex flex-wrap gap-2 items-start">
              {#each tier.options as opt, oIndex}
                <div class="flex flex-col gap-2">
                  {#if editingOption && editingOption.tIndex === tIndex && editingOption.oIndex === oIndex}
                    <div class="flex items-center gap-1 bg-amber-500/10 border border-amber-500/30 rounded-lg px-2 py-1">
                      <input 
                        type="text" 
                        bind:value={editingValue} 
                        onkeydown={(e) => e.key === 'Enter' && saveEdit()}
                        onblur={saveEdit}
                        class="bg-transparent text-[11px] text-white outline-none w-[80px]"
                        autofocus
                      />
                    </div>
                  {:else}
                    <div class="flex items-center gap-1 bg-white/5 border border-white/10 rounded-lg pl-3 pr-1 py-1 group">
                      <span class="text-[11px] font-medium text-white max-w-[120px] truncate">{opt}</span>
                      <button 
                        onclick={() => startEdit(tIndex, oIndex)}
                        class="opacity-0 group-hover:opacity-100 text-white/20 hover:text-amber-500 p-1 transition-opacity"
                      >
                        <Pencil size={10} />
                      </button>
                      <button 
                        onclick={() => removeOption(tIndex, oIndex)}
                        class="text-white/20 hover:text-red-400 p-1"
                      >
                        <X size={10} />
                      </button>
                    </div>
                  {/if}
                  
                  <!-- IMAGE SELECTOR FOR TIER 1 -->
                  {#if tIndex === 0 && hasCustomImages}
                    <div class="w-14 h-14 border-2 border-dashed border-white/10 rounded-lg bg-black/40 flex items-center justify-center relative group/img cursor-pointer hover:border-amber-500/30 transition-colors mx-auto"
                         onclick={() => !tier.images[oIndex] && onOpenVault(tIndex, oIndex)}>
                      
                      {#if tier.images[oIndex]}
                         <img src={resolveMediaUrl(tier.images[oIndex])} alt={opt} class="w-full h-full object-cover rounded-md" />
                         <div class="absolute inset-0 bg-black/60 opacity-0 group-hover/img:opacity-100 flex items-center justify-center gap-1.5 transition-opacity rounded-md">
                           <button class="p-1 bg-white/20 hover:bg-white/40 rounded text-white" onclick={(e) => { e.stopPropagation(); onOpenVault(tIndex, oIndex); }}><ImagePlus size={10}/></button>
                           <button class="p-1 bg-red-500/40 hover:bg-red-500/80 rounded text-white" onclick={(e) => { e.stopPropagation(); removeImage(oIndex); }}><Trash2 size={10}/></button>
                         </div>
                      {:else}
                         <ImagePlus size={12} class="text-white/20 group-hover/img:text-amber-500/50" />
                      {/if}
                    </div>
                  {/if}

                </div>
              {/each}
              
              <div class="flex items-center border border-dashed border-white/20 bg-white/5 rounded-lg overflow-hidden">
                <input 
                  type="text" 
                  placeholder="Thêm lựa chọn..."
                  onkeydown={(e) => handleKeydown(e, tIndex)}
                  onblur={(e) => { addOption(tIndex, e.currentTarget.value); e.currentTarget.value = ''; }}
                  class="bg-transparent px-3 py-1.5 text-[11px] text-white placeholder:text-white/20 outline-none w-[120px]"
                />
              </div>
            </div>
          </div>
          
        </div>
      {/each}
    </div>

    <!-- MA TRẬN VARIANT TABLE -->
    {#if formVariants.length > 0}
      <div class="flex flex-col gap-3 mt-4">
        <!-- BATCH APPLY TOOL -->
        <div class="flex items-center gap-3 p-3 bg-gradient-to-r from-amber-500/10 to-transparent border border-amber-500/20 rounded-xl">
          <div class="flex items-center gap-1.5 text-amber-500 mr-2">
            <Zap size={14} />
            <span class="text-[9px] font-black uppercase tracking-widest">Áp dụng Hàng Loạt</span>
            <ChevronRight size={12} class="text-amber-500/40" />
          </div>
          <input type="number" bind:value={batchPrice} placeholder="Giá bán..." class="bg-black/40 border border-white/10 rounded px-2 py-1.5 text-xs text-amber-200 outline-none w-24 placeholder:text-white/20" />
          <input type="number" bind:value={batchDiscountPrice} placeholder="Giá KM..." class="bg-black/40 border border-rose-500/20 rounded px-2 py-1.5 text-xs text-rose-300 outline-none w-24 placeholder:text-white/20" />
          <input type="number" bind:value={batchStock} placeholder="Tồn kho..." class="bg-black/40 border border-white/10 rounded px-2 py-1.5 text-xs text-amber-200 outline-none w-24 placeholder:text-white/20" />
          <input type="text" bind:value={batchSku} placeholder="Mã SKU chung..." class="bg-black/40 border border-white/10 rounded px-2 py-1.5 text-xs text-amber-200 outline-none flex-1 placeholder:text-white/20 uppercase" />
          <button onclick={applyBatch} class="px-3 py-1.5 bg-amber-500 text-black text-[9px] font-black uppercase tracking-wider rounded-lg hover:brightness-110 flex items-center gap-1">
            <Check size={11} /> Áp dụng
          </button>
        </div>

        <div class="border border-white/5 rounded-xl overflow-x-auto bg-black/20 pb-1 custom-scrollbar">
          <table class="w-full text-left border-collapse">
            <thead>
              <tr class="bg-white/5 border-b border-white/5">
                {#each formTierVariations as tier}
                  <th class="py-2.5 px-4 text-[9px] font-black uppercase tracking-widest text-white/30 whitespace-nowrap">{tier.name}</th>
                {/each}
                <th class="py-2.5 px-4 text-[9px] font-black uppercase tracking-widest text-amber-500/60 w-32 border-l border-white/5 whitespace-nowrap">Giá Bán</th>
                <th class="py-2.5 px-4 text-[9px] font-black uppercase tracking-widest text-rose-500/60 w-32 border-l border-white/5 whitespace-nowrap">Giá Khuyến Mãi</th>
                <th class="py-2.5 px-4 text-[9px] font-black uppercase tracking-widest text-white/30 w-24 border-l border-white/5 whitespace-nowrap">Kho Hàng</th>
                <th class="py-2.5 px-4 text-[9px] font-black uppercase tracking-widest text-white/30 min-w-[150px] border-l border-white/5">SKU (Mã PL)</th>
              </tr>
            </thead>
            <tbody>
              {#each formVariants as variant, vIndex}
                <tr class="border-b border-white/[0.02] hover:bg-white/[0.02] transition-colors group">
                  <!-- Tier Options Display -->
                  {#each variant.tierIndex as tIdx, i}
                    <!-- ONLY SHOW TIER 1 IF IT IS THE FIRST IN ITS GROUP TO AVOID ROWSPAN COMPLEXITY (Like Shopee) -->
                    <!-- For simplicity and robustness, we just print it every time but dim repeats -->
                    <td class="py-2 px-4 text-[11px] font-medium text-white/80 whitespace-nowrap border-r border-white/5">
                      {formTierVariations[i].options[tIdx]}
                    </td>
                  {/each}

                  <td class="p-1 border-l border-white/5">
                    <input type="number" bind:value={variant.price} class="w-full bg-transparent border border-transparent group-hover:bg-black/40 group-hover:border-white/10 focus:border-amber-500/50 !outline-none px-3 py-2 text-xs text-amber-400 font-mono text-right rounded" placeholder="0" />
                  </td>

                  <!-- Discount Price -->
                  <td class="p-1 border-l border-white/5">
                    <input 
                      type="number" 
                      bind:value={variant.discountPrice} 
                      class="w-full bg-transparent border !outline-none px-3 py-2 text-xs font-mono text-right rounded transition-all 
                        {variantValidation[vIndex]?.isInvalid 
                          ? 'border-red-500 bg-red-500/10 text-red-400' 
                          : 'border-transparent group-hover:bg-black/40 group-hover:border-white/10 focus:border-rose-500/50 text-rose-400'}" 
                      placeholder="0" 
                    />
                  </td>

                  <!-- Stock -->
                  <td class="p-1 border-l border-white/5">
                    <input type="number" bind:value={variant.stock} class="w-full bg-transparent border border-transparent group-hover:bg-black/40 group-hover:border-white/10 focus:border-amber-500/50 !outline-none px-3 py-2 text-xs text-white/60 font-mono text-right rounded" placeholder="0" />
                  </td>

                  <!-- SKU -->
                  <td class="p-1 border-l border-white/5">
                    <input type="text" bind:value={variant.sku} class="w-full bg-transparent border border-transparent group-hover:bg-black/40 group-hover:border-white/10 focus:border-amber-500/50 !outline-none px-3 py-2 text-xs text-white/60 font-mono uppercase tracking-wider rounded" placeholder="SKU" />
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>

      </div>
    {/if}

  {/if}
</div>

<style>
  @reference "tailwindcss";
  /* Chrome, Safari, Edge, Opera */
  input::-webkit-outer-spin-button,
  input::-webkit-inner-spin-button {
    -webkit-appearance: none;
    margin: 0;
  }
  /* Firefox */
  input[type=number] {
    -moz-appearance: textfield;
  }
</style>
