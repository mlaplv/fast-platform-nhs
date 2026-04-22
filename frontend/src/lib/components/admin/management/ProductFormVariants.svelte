<script lang="ts">
  import { Plus, X, ImagePlus, Trash2, ListTree, Zap, ChevronRight, Check, Pencil } from "lucide-svelte";
  import AlertTriangle from "lucide-svelte/icons/triangle-alert";
  import { resolveMediaUrl } from "$lib/state/utils";
  import type { Product } from "$lib/types";

  let {
    formTierVariations = $bindable(),
    formVariants = $bindable(),
    formSku = "",
    onOpenVault,
    onOpenVaultForGift
  } = $props<{
    formTierVariations: Product['tierVariations'];
    formVariants: Product['variants'];
    formSku?: string;
    onOpenVault: (tierIndex: number, optionIndex: number, isMobile?: boolean) => void;
    onOpenVaultForGift: (vIndex: number, gIndex: number) => void;
  }>();

  let hasCustomImages = $state(false);
  let brokenVariantImages = $state<Set<string>>(new Set());
  let batchPrice = $state<number>(0);
  let batchDiscountPrice = $state<number>(0);
  let batchDiscountPercent = $state<number>(0);
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

  // Clear broken state when images change
  $effect(() => {
    formTierVariations;
    brokenVariantImages = new Set();
  });

  // Normalize loaded variants to ensure attributes exist and is_default is valid
  $effect(() => {
    // R102: Normalize attributes structure to stay compatible with V2.2 Pydantic schemas
    let structuralChange = false;
    
    // Track if we have any default selected
    const hasAnyDefault = formVariants.some(v => v.is_default);
    
    formVariants.forEach((v, i) => {
      // Attributes normalization
      if (!v.attributes) {
        v.attributes = { combo_qty: null, gifts: [] };
        structuralChange = true;
      } else if (!v.attributes.gifts) {
        v.attributes.gifts = [];
        structuralChange = true;
      }

      // R102: Ensure is_default is boolean and not undefined
      if (v.is_default === undefined) {
        v.is_default = false;
        structuralChange = true;
      }

      // Initialize discountPercent if it doesn't exist or is 0
      if (!v.discountPercent && v.discountPrice > 0) {
        v.discountPercent = calculateDiscountPercent(Number(v.price), Number(v.discountPrice));
        structuralChange = true;
      }
    });
    
    // R102: If variants exist but none are marked default, auto-select the first one
    if (formVariants.length > 0 && !hasAnyDefault) {
      if (formVariants[0]) {
        formVariants[0].is_default = true;
        structuralChange = true;
      }
    }
    
    // Only trigger re-assignment if we added missing nodes or corrected is_default
    if (structuralChange) {
      formVariants = [...formVariants];
    }
  });

  // R00 Auto-SKU Generator: Sync with main SKU pattern
  $effect(() => {
    if (!formSku) return;
    
    let changed = false;
    formVariants.forEach((v, idx) => {
      // Auto-fill if SKU is empty
      const isEmpty = !v.sku || v.sku.trim() === "";
      
      if (isEmpty) {
        v.sku = `${formSku}-${idx + 1}`;
        changed = true;
      }
    });

    if (changed) {
      formVariants = [...formVariants];
    }
  });

  function addTier() {
    if (formTierVariations.length >= 2) return;
    formTierVariations = [...formTierVariations, { 
      name: formTierVariations.length === 0 ? "Màu sắc" : "Kích cỡ", 
      options: [], 
      images: [],
      mobile_images: []
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
    if (!formTierVariations[tIndex].mobile_images) formTierVariations[tIndex].mobile_images = [];
    formTierVariations[tIndex].mobile_images.push(null);
    formTierVariations = [...formTierVariations];
    rebuildMatrix();
  }

  function removeOption(tIndex: number, oIndex: number) {
    formTierVariations[tIndex].options.splice(oIndex, 1);
    formTierVariations[tIndex].images.splice(oIndex, 1);
    if (formTierVariations[tIndex].mobile_images) formTierVariations[tIndex].mobile_images.splice(oIndex, 1);
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
      formTierVariations[0].mobile_images = formTierVariations[0].options.map(() => null);
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
          const newIdx = newVariants.length + 1;
          const generatedSku = formSku ? `${formSku}-${newIdx}` : "";
          newVariants.push(existing || { 
            tierIndex: tIdx, 
            sku: generatedSku, 
            price: 0, 
            discountPrice: 0, 
            discountPercent: 0,
            stock: 0, 
            is_default: false,
            attributes: { combo_qty: null, gifts: [] } 
          });
        }
      } else {
        const tIdx = [i];
        const existing = findExistingVariant(tIdx);
        const newIdx = newVariants.length + 1;
        const generatedSku = formSku ? `${formSku}-${newIdx}` : "";
        newVariants.push(existing || { 
          tierIndex: tIdx, 
          sku: generatedSku, 
          price: 0, 
          discountPrice: 0, 
          discountPercent: 0,
          stock: 0, 
          is_default: false,
          attributes: { combo_qty: null, gifts: [] } 
        });
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

  function calculateDiscountPrice(price: number, percent: number) {
    if (!price || price <= 0) return 0;
    return Math.round(price * (1 - percent / 100));
  }

  function calculateDiscountPercent(price: number, discountPrice: number) {
    if (!price || price <= 0 || !discountPrice || discountPrice <= 0) return 0;
    if (discountPrice >= price) return 0;
    const percent = ((price - discountPrice) / price) * 100;
    return Math.round(percent * 100) / 100; // Round to 2 decimal places
  }

  function applyBatch() {
    formVariants = formVariants.map(v => {
      let finalPrice = batchPrice > 0 ? batchPrice : v.price;
      let finalDiscountPrice = v.discountPrice;

      if (batchDiscountPercent > 0) {
        finalDiscountPrice = calculateDiscountPrice(finalPrice, batchDiscountPercent);
      } else if (batchDiscountPrice > 0) {
        finalDiscountPrice = batchDiscountPrice;
      }

      return {
        ...v,
        price: finalPrice,
        discountPrice: finalDiscountPrice,
        discountPercent: calculateDiscountPercent(finalPrice, finalDiscountPrice),
        stock: batchStock > 0 ? batchStock : v.stock,
        sku: batchSku ? `${batchSku}-${v.tierIndex.join('-')}` : v.sku
      };
    });
  }

  function setDefault(vIndex: number) {
    formVariants = formVariants.map((v, i) => ({
      ...v,
      is_default: i === vIndex
    }));
  }

  function handleKeydown(e: KeyboardEvent, tIndex: number) {
    if (e.key === 'Enter') {
      e.preventDefault();
      addOption(tIndex, e.currentTarget.value);
      e.currentTarget.value = '';
    }
  }

  function removeImage(oIndex: number, isMobile = false) {
    if (formTierVariations.length > 0) {
      if (isMobile) {
        if (!formTierVariations[0].mobile_images) formTierVariations[0].mobile_images = [];
        formTierVariations[0].mobile_images[oIndex] = null;
      } else {
        formTierVariations[0].images[oIndex] = null;
      }
    }
  }

  function handleVariantImageError(imgSrc: string) {
    brokenVariantImages = new Set([...brokenVariantImages, imgSrc]);
  }

  function ensureAttributes(vIndex: number) {
    if (!formVariants[vIndex].attributes) formVariants[vIndex].attributes = { combo_qty: null, gifts: [] };
    if (!formVariants[vIndex].attributes.gifts) formVariants[vIndex].attributes.gifts = [];
  }

  function addGift(vIndex: number) {
    ensureAttributes(vIndex);
    formVariants[vIndex].attributes!.gifts!.push({ name: '', qty: 1, image: '' });
    formVariants = [...formVariants];
  }

  function removeGift(vIndex: number, gIndex: number) {
    if (formVariants[vIndex].attributes?.gifts) {
      formVariants[vIndex].attributes!.gifts!.splice(gIndex, 1);
      formVariants = [...formVariants];
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
                  
                  <!-- IMAGE SELECTORS FOR TIER 1 -->
                  {#if tIndex === 0 && hasCustomImages}
                    <div class="flex items-center gap-2 mx-auto">
                      <!-- Desktop Image -->
                      <div class="w-12 h-12 border border-dashed border-white/10 rounded-lg bg-black/40 flex items-center justify-center relative group/img cursor-pointer hover:border-amber-500/30 transition-colors"
                           onclick={() => !tier.images[oIndex] && onOpenVault(tIndex, oIndex, false)}>
                        <div class="absolute -top-1.5 -left-1.5 w-3.5 h-3.5 rounded bg-amber-500 text-black text-[7px] font-black flex items-center justify-center shadow-lg border border-black/20 z-10">D</div>
                        
                        {#if tier.images[oIndex]}
                           {@const varResolved = resolveMediaUrl(tier.images[oIndex])}
                           {@const varBroken = brokenVariantImages.has(varResolved)}
                           {#if varBroken}
                             <!-- Broken Variant Desktop Image -->
                             <div class="absolute inset-0 flex flex-col items-center justify-center gap-0.5 bg-red-500/5 rounded-md border border-red-500/20">
                               <AlertTriangle size={10} class="text-red-400/60" />
                               <div class="flex items-center gap-0.5 z-20">
                                 <button class="p-0.5 bg-white/20 hover:bg-white/40 rounded text-white" onclick={(e) => { e.stopPropagation(); onOpenVault(tIndex, oIndex, false); }} title="Thay thế ảnh"><ImagePlus size={8}/></button>
                                 <button class="p-0.5 bg-red-500/40 hover:bg-red-500/80 rounded text-white" onclick={(e) => { e.stopPropagation(); removeImage(oIndex, false); }} title="Xóa ảnh"><Trash2 size={8}/></button>
                               </div>
                             </div>
                           {:else}
                             <img src={varResolved} alt={opt} class="w-full h-full object-cover rounded-md" onerror={() => handleVariantImageError(varResolved)} />
                             <div class="absolute inset-0 bg-black/60 opacity-0 group-hover/img:opacity-100 flex items-center justify-center gap-1.5 transition-opacity rounded-md z-20">
                               <button class="p-1 bg-white/20 hover:bg-white/40 rounded text-white" onclick={(e) => { e.stopPropagation(); onOpenVault(tIndex, oIndex, false); }}><ImagePlus size={10}/></button>
                               <button class="p-1 bg-red-500/40 hover:bg-red-500/80 rounded text-white" onclick={(e) => { e.stopPropagation(); removeImage(oIndex, false); }}><Trash2 size={10}/></button>
                             </div>
                           {/if}
                        {:else}
                           <ImagePlus size={10} class="text-white/10 group-hover/img:text-amber-500/50" />
                        {/if}
                      </div>

                      <!-- Mobile Image (9:16) -->
                      <div class="w-12 h-12 border border-dashed border-white/10 rounded-lg bg-black/40 flex items-center justify-center relative group/img-mob cursor-pointer hover:border-cyan-500/30 transition-colors"
                           onclick={() => (!tier.mobile_images?.[oIndex]) && onOpenVault(tIndex, oIndex, true)}>
                        <div class="absolute -top-1.5 -left-1.5 w-3.5 h-3.5 rounded bg-cyan-500 text-black text-[7px] font-black flex items-center justify-center shadow-lg border border-black/20 z-10">M</div>
                        
                        {#if tier.mobile_images?.[oIndex]}
                           {@const mobResolved = resolveMediaUrl(tier.mobile_images[oIndex])}
                           {@const mobBroken = brokenVariantImages.has(mobResolved)}
                           {#if mobBroken}
                             <!-- Broken Variant Mobile Image -->
                             <div class="absolute inset-0 flex flex-col items-center justify-center gap-0.5 bg-red-500/5 rounded-md border border-red-500/20">
                               <AlertTriangle size={10} class="text-red-400/60" />
                               <div class="flex items-center gap-0.5 z-20">
                                 <button class="p-0.5 bg-white/20 hover:bg-white/40 rounded text-white" onclick={(e) => { e.stopPropagation(); onOpenVault(tIndex, oIndex, true); }} title="Thay thế ảnh"><ImagePlus size={8}/></button>
                                 <button class="p-0.5 bg-red-500/40 hover:bg-red-500/80 rounded text-white" onclick={(e) => { e.stopPropagation(); removeImage(oIndex, true); }} title="Xóa ảnh"><Trash2 size={8}/></button>
                               </div>
                             </div>
                           {:else}
                             <img src={mobResolved} alt={opt} class="w-full h-full object-cover rounded-md" onerror={() => handleVariantImageError(mobResolved)} />
                             <div class="absolute inset-0 bg-black/60 opacity-0 group-hover/img-mob:opacity-100 flex items-center justify-center gap-1.5 transition-opacity rounded-md z-20">
                               <button class="p-1 bg-white/20 hover:bg-white/40 rounded text-white" onclick={(e) => { e.stopPropagation(); onOpenVault(tIndex, oIndex, true); }}><ImagePlus size={10}/></button>
                               <button class="p-1 bg-red-500/40 hover:bg-red-500/80 rounded text-white" onclick={(e) => { e.stopPropagation(); removeImage(oIndex, true); }}><Trash2 size={10}/></button>
                             </div>
                           {/if}
                        {:else}
                           <ImagePlus size={10} class="text-white/10 group-hover/img-mob:text-cyan-500/50" />
                        {/if}
                      </div>
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
          <div class="flex items-center bg-black/40 border border-rose-500/20 rounded overflow-hidden">
            <input type="number" bind:value={batchDiscountPercent} placeholder="%" class="w-12 bg-transparent px-2 py-1.5 text-xs text-rose-300 outline-none border-r border-white/5 placeholder:text-white/10" />
            <input type="number" bind:value={batchDiscountPrice} placeholder="Giá KM..." class="w-24 bg-transparent px-2 py-1.5 text-xs text-rose-300 outline-none placeholder:text-white/20" />
          </div>
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
                <th class="py-2.5 px-4 text-[9px] font-black uppercase tracking-widest text-white/30 w-12 text-center border-l border-white/5 whitespace-nowrap">Mặc định</th>
                <th class="py-2.5 px-4 text-[9px] font-black uppercase tracking-widest text-amber-500/60 w-28 border-l border-white/5 whitespace-nowrap">Giá Bán</th>
                <th class="py-2.5 px-4 text-[9px] font-black uppercase tracking-widest text-rose-500/40 w-16 border-l border-white/5 whitespace-nowrap text-center">Giảm %</th>
                <th class="py-2.5 px-4 text-[9px] font-black uppercase tracking-widest text-rose-500/60 w-28 border-l border-white/5 whitespace-nowrap">Giá Khuyến Mãi / 1 sản phẩm</th>
                <th class="py-2.5 px-4 text-[9px] font-black uppercase tracking-widest text-white/30 w-20 border-l border-white/5 whitespace-nowrap">Kho Hàng</th>
                <th class="py-2.5 px-4 text-[9px] font-black uppercase tracking-widest text-cyan-400/60 min-w-[200px] border-l border-white/5">Thiết Lập Combo(Số lượng bắt buộc để áp dụng) & Quà(nếu có)</th>
                <th class="py-2.5 px-4 text-[9px] font-black uppercase tracking-widest text-white/30 min-w-[120px] border-l border-white/5">SKU (Mã PL)</th>
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

                  <td class="p-1 border-l border-white/5 text-center">
                    <button 
                      onclick={() => setDefault(vIndex)}
                      class="p-2 transition-all rounded-md {variant.is_default ? 'text-amber-500 bg-amber-500/10' : 'text-white/20 hover:text-white/40'}"
                      title={variant.is_default ? 'Đang là mặc định' : 'Đặt làm mặc định'}
                    >
                      <Zap size={14} fill={variant.is_default ? 'currentColor' : 'none'} />
                    </button>
                  </td>

                  <td class="p-1 border-l border-white/5">
                    <input 
                      type="number" 
                      bind:value={variant.price} 
                      oninput={() => {
                        if (variant.discountPercent > 0) {
                          variant.discountPrice = calculateDiscountPrice(Number(variant.price), Number(variant.discountPercent));
                        } else if (variant.discountPrice > 0) {
                          variant.discountPercent = calculateDiscountPercent(Number(variant.price), Number(variant.discountPrice));
                        }
                        formVariants = [...formVariants];
                      }}
                      class="w-full bg-transparent border border-transparent group-hover:bg-black/40 group-hover:border-white/10 focus:border-amber-500/50 !outline-none px-3 py-2 text-xs text-amber-400 font-mono text-right rounded" 
                      placeholder="0" 
                    />
                  </td>

                  <td class="p-1 border-l border-white/5">
                    <input 
                      type="number" 
                      bind:value={variant.discountPercent} 
                      oninput={() => {
                        variant.discountPrice = calculateDiscountPrice(Number(variant.price), Number(variant.discountPercent));
                        formVariants = [...formVariants];
                      }}
                      class="w-full bg-transparent border border-transparent group-hover:bg-black/40 group-hover:border-white/10 focus:border-rose-500/50 !outline-none px-2 py-2 text-xs text-rose-400/70 font-mono text-center rounded" 
                      placeholder="0" 
                    />
                  </td>

                  <!-- Discount Price -->
                  <td class="p-1 border-l border-white/5">
                    <div class="relative group/price">
                      <input 
                        type="number" 
                        bind:value={variant.discountPrice} 
                        oninput={() => {
                          variant.discountPercent = calculateDiscountPercent(Number(variant.price), Number(variant.discountPrice));
                          formVariants = [...formVariants];
                        }}
                        class="w-full bg-transparent border !outline-none px-3 py-2 text-xs font-mono text-right rounded transition-all 
                          {variantValidation[vIndex]?.isInvalid 
                            ? 'border-red-500 bg-red-500/10 text-red-400' 
                            : 'border-transparent group-hover:bg-black/40 group-hover:border-white/10 focus:border-rose-500/50 text-rose-400'}" 
                        placeholder="0" 
                      />
                      {#if variantValidation[vIndex]?.isInvalid}
                        <div class="absolute -bottom-6 right-0 whitespace-nowrap bg-red-500 text-white text-[8px] font-bold px-1.5 py-0.5 rounded shadow-lg z-50 pointer-events-none uppercase">
                          Giá KM ≥ Giá bán
                        </div>
                      {/if}
                    </div>
                  </td>

                  <!-- Stock -->
                  <td class="p-1 border-l border-white/5">
                    <input type="number" bind:value={variant.stock} class="w-full bg-transparent border border-transparent group-hover:bg-black/40 group-hover:border-white/10 focus:border-amber-500/50 !outline-none px-3 py-2 text-xs text-white/60 font-mono text-right rounded" placeholder="0" />
                  </td>

                  <!-- Combo Config -->
                  <td class="p-2 border-l border-white/5 align-top">
                    <div class="flex flex-col gap-2">
                       <div class="flex items-center gap-2">
                         <span class="text-[9px] font-black uppercase text-cyan-500/60 w-12 shrink-0">Số lượng</span>
                         <input 
                           type="number" 
                           bind:value={variant.attributes.combo_qty} 
                           oninput={() => formVariants = [...formVariants]}
                           class="flex-1 bg-black/40 border border-white/10 focus:border-cyan-500/50 outline-none px-2 py-1 text-[10px] text-cyan-400 font-mono rounded placeholder:text-cyan-900" 
                           placeholder="1 (Gói lẻ)" 
                         />
                       </div>
                       
                       {#each variant.attributes.gifts as gift, gIdx}
                         <div class="flex gap-2 items-center bg-cyan-900/10 p-1.5 rounded border border-cyan-500/10 relative group/gift cursor-default">
                           <!-- Small Thumbnail for Gift (Rule R03: Premium UX) -->
                           <button 
                             onclick={() => onOpenVaultForGift(vIndex, gIdx)}
                             class="w-6 h-6 rounded border border-white/10 bg-black/40 flex items-center justify-center overflow-hidden shrink-0 group/img-gift hover:border-cyan-500/50 transition-colors"
                           >
                             {#if gift.image}
                               <img src={resolveMediaUrl(gift.image)} alt={gift.name} class="w-full h-full object-cover" />
                             {:else}
                               <ImagePlus size={10} class="text-cyan-500/40 group-hover/img-gift:text-cyan-400 transition-colors" />
                             {/if}
                           </button>

                           <div class="flex flex-1 gap-1 items-start">
                             <input type="text" bind:value={gift.name} oninput={() => formVariants = [...formVariants]} placeholder="Tên quà (VD: Mặt nạ)" class="flex-1 min-w-[80px] bg-transparent border-b border-white/10 outline-none text-[9px] text-white px-1" />
                             <input type="number" bind:value={gift.qty} oninput={() => formVariants = [...formVariants]} placeholder="SL" class="w-10 bg-transparent border-b border-white/10 outline-none text-[9px] text-center text-rose-400 font-bold px-1" />
                           </div>
                           
                           <button onclick={() => removeGift(vIndex, gIdx)} class="text-white/20 hover:text-red-400 opacity-0 group-hover/gift:opacity-100 transition-opacity p-0.5"><X size={10}/></button>
                         </div>
                       {/each}
                       
                       <button onclick={() => addGift(vIndex)} class="self-start text-[9px] font-black text-cyan-500 hover:text-cyan-300 uppercase tracking-widest flex items-center gap-1 mt-1">
                          <Plus size={10} /> Quà Tặng ({variant.attributes.gifts?.length || 0})
                       </button>
                    </div>
                  </td>

                  <!-- SKU -->
                  <td class="p-1 border-l border-white/5 align-top">
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
