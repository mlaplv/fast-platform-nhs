<script lang="ts">
  import Plus from "@lucide/svelte/icons/plus";
  import X from "@lucide/svelte/icons/x";
  import ImagePlus from "@lucide/svelte/icons/image-plus";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import ListTree from "@lucide/svelte/icons/list-tree";
  import Zap from "@lucide/svelte/icons/zap";
  import ChevronRight from "@lucide/svelte/icons/chevron-right";
  import Check from "@lucide/svelte/icons/check";
  import Pencil from "@lucide/svelte/icons/pencil";
  import AlertTriangle from "@lucide/svelte/icons/triangle-alert";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import Database from "@lucide/svelte/icons/database";
  import Search from "@lucide/svelte/icons/search";
  import Link2Off from "@lucide/svelte/icons/link-2-off";
  import { resolveMediaUrl } from "$lib/state/utils";
  import { apiClient } from "$lib/utils/apiClient";
  import type { Product, ProductFormState, ProductVariant } from "$lib/types";
  import { onDestroy } from "svelte";

  let {
    formState = $bindable(),
    onOpenVault,
    onOpenVaultForGift
  } = $props<{
    formState: ProductFormState;
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

  // Xohi Assistant State (Elite V2.2 Cyberpunk theme)
  let showXohiPanel = $state(false);
  let xohiPrompt = $state("tạo 3 combo 1 2 3, giá lấy giá bán giảm lần lượt 5% 10% 15%, combo 3 mua 3 tặng 1, số lượng mặc định 99, mặc định là combo 1");
  let isGeneratingXohi = $state(false);
  let xohiStep = $state("");
  let xohiTimer = $state<any>(null);

  function toggleXohiAssistant() {
    showXohiPanel = !showXohiPanel;
  }

  onDestroy(() => {
    if (xohiTimer) clearInterval(xohiTimer);
  });

  function parseXohiPrompt(promptText: string, basePrice: number) {
    const text = promptText.toLowerCase();
    
    // 1. Detect Combo Count
    let comboCount = 3;
    const comboMatch = text.match(/(?:tạo|thêm)\s*(\d+)\s*combo/);
    if (comboMatch) {
      comboCount = parseInt(comboMatch[1]);
    } else {
      const simpleNumMatch = text.match(/(\d+)\s*combo/);
      if (simpleNumMatch) comboCount = parseInt(simpleNumMatch[1]);
    }
    
    // 2. Detect discounts list
    let discounts = [5, 10, 15];
    const discountMatch = text.match(/giảm\s*(?:giá)?\s*(?:lần\s*lượt)?\s*([\d\s%,-]+)/);
    if (discountMatch) {
      const rawNums = discountMatch[1].match(/\d+/g);
      if (rawNums && rawNums.length > 0) {
        discounts = rawNums.map(n => parseInt(n));
      }
    }
    
    // 3. Detect gift info (Elite V2.2 high-precision parsing)
    let giftVariantIndex = comboCount - 1; // Default to last combo
    let giftName = "Mua 3 tặng 1";
    
    // First detect target combo for gift if explicitly defined near the gift action (e.g. "combo 3 mua 3 tặng 1")
    const comboGiftMatch = text.match(/(?:combo|phân\s*loại)\s*(\d+)(?=[^,]*tặng)/);
    if (comboGiftMatch) {
      giftVariantIndex = parseInt(comboGiftMatch[1]) - 1;
    } else {
      // Fallback: pick the last combo mention
      const targetComboMatch = text.match(/(?:combo|phân\s*loại)\s*(\d+)/g);
      if (targetComboMatch && targetComboMatch.length > 0) {
        const lastMention = targetComboMatch[targetComboMatch.length - 1];
        const numMatch = lastMention.match(/\d+/);
        if (numMatch) giftVariantIndex = parseInt(numMatch[0]) - 1;
      }
    }
    
    // Now extract the exact gift name strictly
    const quotedMatch = text.match(/['"“]([^'"“”]+)['"”]/);
    if (quotedMatch) {
      giftName = quotedMatch[1].trim();
    } else {
      // Look for standard "mua \d+ tặng \d+" pattern first
      const buyGiftMatch = text.match(/mua\s*(\d+)\s*tặng\s*(\d+)/);
      if (buyGiftMatch) {
        giftName = `Mua ${buyGiftMatch[1]} tặng ${buyGiftMatch[2]}`;
      } else {
        // Fallback to "tặng <something>" excluding other options keywords
        const giftWordMatch = text.match(/tặng\s+([^,;!\.\n\r]+)/);
        if (giftWordMatch) {
          const candidate = giftWordMatch[1].trim();
          if (!candidate.includes("mặc định") && !candidate.includes("số lượng") && !candidate.includes("kho")) {
            giftName = candidate.charAt(0).toUpperCase() + candidate.slice(1);
          }
        }
      }
    }
    
    // 4. Default stock level
    let defaultStock = 99;
    const stockMatch = text.match(/(?:kho|số\s*lượng|tồn|stock)\s*(?:mặc\s*định)?\s*(\d+)/);
    if (stockMatch) {
      defaultStock = parseInt(stockMatch[1]);
    } else {
      const simpleStockMatch = text.match(/(\d+)\s*(?:mặc\s*định|tồn|cái|chiếc)/);
      if (simpleStockMatch) defaultStock = parseInt(simpleStockMatch[1]);
    }
    
    // 5. Default variant
    let defaultIndex = 0;
    const defaultMatch = text.match(/mặc\s*định\s*(?:là)?\s*(?:combo|phân\s*loại)?\s*(\d+)/);
    if (defaultMatch) {
      defaultIndex = parseInt(defaultMatch[1]) - 1;
    }

    return {
      comboCount,
      discounts,
      giftVariantIndex,
      giftName,
      defaultStock,
      defaultIndex
    };
  }

  function applyXohiPreset(presetType: 'miccosmo' | 'colors' | 'sizes') {
    if (presetType === 'miccosmo') {
      xohiPrompt = "tạo 3 combo 1 2 3, giá lấy giá bán giảm lần lượt 5% 10% 15%, combo 3 mua 3 tặng 1, số lượng mặc định 99, mặc định là combo 1";
    } else if (presetType === 'colors') {
      xohiPrompt = "tạo phân loại Màu sắc gồm 3 tùy chọn: Đỏ, Xanh, Vàng, số lượng mặc định 99, mặc định là màu thứ nhất";
    } else if (presetType === 'sizes') {
      xohiPrompt = "tạo phân loại Kích cỡ gồm 3 tùy chọn: S, M, L, số lượng mặc định 99, mặc định kích cỡ thứ nhất";
    }
    runXohiAssistant();
  }

  function runXohiAssistant() {
    if (isGeneratingXohi) return;
    isGeneratingXohi = true;
    
    const steps = [
      "Đang khởi động Xohi Cognitive Engine...",
      "Đang phân tích cấu trúc sản phẩm...",
      "Đang quét thông số giá bán gốc...",
      "Đang tự động thiết lập ma trận combo...",
      "Đang cấu hình chương trình quà tặng tối ưu...",
      "Hoàn tất đồng bộ biến thể sản phẩm!"
    ];
    
    let currentStepIdx = 0;
    xohiStep = steps[0];
    
    xohiTimer = setInterval(() => {
      currentStepIdx++;
      if (currentStepIdx < steps.length) {
        xohiStep = steps[currentStepIdx];
      } else {
        clearInterval(xohiTimer);
        executeVariantGeneration();
        isGeneratingXohi = false;
        showXohiPanel = false;
      }
    }, 150);
  }

  function executeVariantGeneration() {
    const basePrice = formState.price && Number(formState.price) > 0 ? Number(formState.price) : 650000;
    const promptValue = xohiPrompt.trim();
    const isColors = promptValue.toLowerCase().includes("màu sắc") || promptValue.toLowerCase().includes("màu");
    const isSizes = promptValue.toLowerCase().includes("kích cỡ") || promptValue.toLowerCase().includes("kích thước") || promptValue.toLowerCase().includes("size");
    
    if (isColors) {
      formState.tierVariations = [
        {
          name: "Màu sắc",
          options: ["Đỏ", "Xanh", "Vàng"],
          images: [null, null, null],
          mobile_images: [null, null, null]
        }
      ];
      rebuildMatrix();
      
      formState.variants = formState.variants.map((v, i) => ({
        ...v,
        price: basePrice,
        discountPrice: 0,
        discountPercent: 0,
        stock: 99,
        is_default: i === 0,
        attributes: { combo_qty: null, gifts: [] }
      }));
      return;
    }
    
    if (isSizes) {
      formState.tierVariations = [
        {
          name: "Kích cỡ",
          options: ["S", "M", "L"],
          images: [null, null, null],
          mobile_images: [null, null, null]
        }
      ];
      rebuildMatrix();
      
      formState.variants = formState.variants.map((v, i) => ({
        ...v,
        price: basePrice,
        discountPrice: 0,
        discountPercent: 0,
        stock: 99,
        is_default: i === 0,
        attributes: { combo_qty: null, gifts: [] }
      }));
      return;
    }
    
    const config = parseXohiPrompt(xohiPrompt, basePrice);
    const options = Array.from({ length: config.comboCount }, (_, i) => `Combo ${i + 1}`);
    
    formState.tierVariations = [
      {
        name: "Combo",
        options: options,
        images: Array(config.comboCount).fill(null),
        mobile_images: Array(config.comboCount).fill(null)
      }
    ];
    
    rebuildMatrix();
    
    formState.variants = formState.variants.map((v, i) => {
      const pct = config.discounts[i] !== undefined ? config.discounts[i] : 0;
      const discPrice = pct > 0 ? Math.round(basePrice * (1 - pct / 100)) : 0;
      const giftsList = i === config.giftVariantIndex ? [{ name: config.giftName, qty: 1, image: "" }] : [];
      
      return {
        ...v,
        price: basePrice,
        discountPercent: pct,
        discountPrice: discPrice,
        stock: config.defaultStock,
        is_default: i === config.defaultIndex,
        attributes: {
          combo_qty: i + 1,
          gifts: giftsList
        }
      };
    });
  }
  
  // R102 Validation Rune: Track invalid price combinations
  const variantValidation = $derived(formState.variants.map(v => ({
    isInvalid: v.discountPrice > 0 && Number(v.discountPrice) >= Number(v.price)
  })));

  // Svelte 5 init
  $effect(() => {
    if (formState.tierVariations === undefined) formState.tierVariations = [];
    if (formState.variants === undefined) formState.variants = [];

    if (formState.tierVariations.length > 0 && formState.tierVariations[0].images?.some(img => img)) {
      hasCustomImages = true;
    }
  });

  // Clear broken state when images change
  $effect(() => {
    formState.tierVariations;
    brokenVariantImages = new Set();
  });

  // Normalize loaded variants to ensure attributes exist and is_default is valid
  $effect(() => {
    // R102: Normalize attributes structure to stay compatible with V2.2 Pydantic schemas
    let structuralChange = false;
    
    // Track if we have any default selected
    const hasAnyDefault = formState.variants.some(v => v.is_default);
    
    formState.variants.forEach((v, i) => {
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
    if (formState.variants.length > 0 && !hasAnyDefault) {
      if (formState.variants[0]) {
        formState.variants[0].is_default = true;
        structuralChange = true;
      }
    }
  });

  // R00 Auto-SKU Generator: Sync with main SKU pattern
  $effect(() => {
    if (!formState.sku) return;
    
    formState.variants.forEach((v, idx) => {
      // Auto-fill if SKU is empty
      const isEmpty = !v.sku || v.sku.trim() === "";
      
      if (isEmpty) {
        v.sku = `${formState.sku}-${idx + 1}`;
      }
    });
  });

  function addTier() {
    if (formState.tierVariations.length >= 2) return;
    formState.tierVariations.push({ 
      name: formState.tierVariations.length === 0 ? "Màu sắc" : "Kích cỡ", 
      options: [], 
      images: [],
      mobile_images: []
    });
    rebuildMatrix();
  }

  function removeTier(tIndex: number) {
    formState.tierVariations.splice(tIndex, 1);
    
    // If we removed Tier 1 and there is a Tier 2, Tier 2 becomes Tier 1
    if (tIndex === 0 && hasCustomImages) {
      hasCustomImages = false; 
    }
    
    rebuildMatrix();
  }

  function addOption(tIndex: number, value: string) {
    if (!value.trim()) return;
    if (formState.tierVariations[tIndex].options.includes(value.trim())) return;
    
    formState.tierVariations[tIndex].options.push(value.trim());
    formState.tierVariations[tIndex].images.push(null);
    if (!formState.tierVariations[tIndex].mobile_images) formState.tierVariations[tIndex].mobile_images = [];
    formState.tierVariations[tIndex].mobile_images.push(null);
    rebuildMatrix();
  }

  function removeOption(tIndex: number, oIndex: number) {
    formState.tierVariations[tIndex].options.splice(oIndex, 1);
    formState.tierVariations[tIndex].images.splice(oIndex, 1);
    if (formState.tierVariations[tIndex].mobile_images) formState.tierVariations[tIndex].mobile_images.splice(oIndex, 1);
    
    // Cleanup empty tiers
    if (formState.tierVariations[tIndex].options.length === 0) {
       removeTier(tIndex);
       return;
    }
    rebuildMatrix();
  }

  function toggleCustomImages() {
    hasCustomImages = !hasCustomImages;
    if (!hasCustomImages && formState.tierVariations.length > 0) {
      formState.tierVariations[0].images = formState.tierVariations[0].options.map(() => null);
      formState.tierVariations[0].mobile_images = formState.tierVariations[0].options.map(() => null);
    }
  }

  function rebuildMatrix() {
    if (formState.tierVariations.length === 0) {
      formState.variants = [];
      return;
    }

    const t1 = formState.tierVariations[0].options;
    const t2 = formState.tierVariations.length > 1 ? formState.tierVariations[1].options : [];

    const newVariants: Product['variants'] = [];

    if (t1.length === 0) {
      formState.variants = [];
      return;
    }

    for (let i = 0; i < t1.length; i++) {
      if (t2.length > 0) {
        for (let j = 0; j < t2.length; j++) {
          const tIdx = [i, j];
          const existing = findExistingVariant(tIdx);
          const newIdx = newVariants.length + 1;
          const generatedSku = formState.sku ? `${formState.sku}-${newIdx}` : "";
          newVariants.push(existing || { 
            tierIndex: tIdx, 
            sku: generatedSku, 
            price: 0, 
            discountPrice: 0, 
            discountPercent: 0,
            stock: 0, 
            is_default: false,
            is_active: true,
            attributes: { combo_qty: null, gifts: [] } 
          });
        }
      } else {
        const tIdx = [i];
        const existing = findExistingVariant(tIdx);
        const newIdx = newVariants.length + 1;
        const generatedSku = formState.sku ? `${formState.sku}-${newIdx}` : "";
        newVariants.push(existing || { 
          tierIndex: tIdx, 
          sku: generatedSku, 
          price: 0, 
          discountPrice: 0, 
          discountPercent: 0,
          stock: 0, 
          is_default: false,
          is_active: true,
          attributes: { combo_qty: null, gifts: [] } 
        });
      }
    }

    formState.variants = newVariants;
  }

  function startEdit(tIndex: number, oIndex: number) {
    editingOption = { tIndex, oIndex };
    editingValue = formState.tierVariations[tIndex].options[oIndex];
  }

  function saveEdit() {
    if (!editingOption) return;
    const { tIndex, oIndex } = editingOption;
    const newVal = editingValue.trim();
    if (newVal && (newVal === formState.tierVariations[tIndex].options[oIndex] || !formState.tierVariations[tIndex].options.includes(newVal))) {
      formState.tierVariations[tIndex].options[oIndex] = newVal;
      rebuildMatrix();
    }
    editingOption = null;
  }

  function findExistingVariant(targetIndex: number[]): Product['variants'][number] | undefined {
    return formState.variants.find(v => 
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
    formState.variants = formState.variants.map(v => {
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
    formState.variants = formState.variants.map((v, i) => ({
      ...v,
      is_default: i === vIndex,
      is_active: i === vIndex ? true : (v.is_active !== false)
    }));
  }

  function toggleVariantActive(vIndex: number) {
    const variant = formState.variants[vIndex];
    if (variant.is_default && variant.is_active !== false) {
      alert("Không thể tắt biến thể mặc định! Vui lòng chọn biến thể khác làm mặc định trước khi tắt.");
      return;
    }
    variant.is_active = variant.is_active === false ? true : false;
  }

  function handleKeydown(e: KeyboardEvent, tIndex: number) {
    if (e.key === 'Enter') {
      e.preventDefault();
      addOption(tIndex, e.currentTarget.value);
      e.currentTarget.value = '';
    }
  }

  function removeImage(oIndex: number, isMobile = false) {
    if (formState.tierVariations.length > 0) {
      if (isMobile) {
        if (!formState.tierVariations[0].mobile_images) formState.tierVariations[0].mobile_images = [];
        formState.tierVariations[0].mobile_images[oIndex] = null;
      } else {
        formState.tierVariations[0].images[oIndex] = null;
      }
    }
  }

  function handleVariantImageError(imgSrc: string) {
    brokenVariantImages = new Set([...brokenVariantImages, imgSrc]);
  }

  function ensureAttributes(vIndex: number) {
    if (!formState.variants[vIndex].attributes) formState.variants[vIndex].attributes = { combo_qty: null, gifts: [] };
    if (!formState.variants[vIndex].attributes.gifts) formState.variants[vIndex].attributes.gifts = [];
  }

  function addGift(vIndex: number) {
    ensureAttributes(vIndex);
    formState.variants[vIndex].attributes!.gifts!.push({ name: '', qty: 1, image: '' });
  }

  function removeGift(vIndex: number, gIndex: number) {
    if (formState.variants[vIndex].attributes?.gifts) {
      formState.variants[vIndex].attributes!.gifts!.splice(gIndex, 1);
    }
  }

  // --- ADVANCED GIFT DB PRODUCT SEARCH STATES & FUNCTIONS ---
  let activeSearchVIdx = $state<number | null>(null);
  let activeSearchGIdx = $state<number | null>(null);
  let dbSearchQuery = $state("");
  let dbSearchResults = $state<Product[]>([]);
  let isSearchingDb = $state(false);
  let searchDebounceTimer: any = null;
  let loadedGiftProducts = $state<Record<string, Product>>({});

  async function searchDbProducts(query: string) {
    if (!query.trim()) {
      dbSearchResults = [];
      return;
    }
    isSearchingDb = true;
    try {
      const res = await apiClient.get<{ data: Product[]; total: number }>("/api/v1/products", {
        params: { search: query, limit: "10" }
      });
      dbSearchResults = res.data || [];
    } catch (err) {
      console.error("Lỗi tìm kiếm sản phẩm:", err);
      dbSearchResults = [];
    } finally {
      isSearchingDb = false;
    }
  }

  function handleDbSearchInput(e: Event) {
    const val = (e.target as HTMLInputElement).value;
    dbSearchQuery = val;
    if (searchDebounceTimer) clearTimeout(searchDebounceTimer);
    searchDebounceTimer = setTimeout(() => {
      searchDbProducts(val);
    }, 300);
  }

  function selectDbProductForGift(vIndex: number, gIndex: number, product: Product) {
    ensureAttributes(vIndex);
    const gifts = formState.variants[vIndex].attributes!.gifts!;
    if (gifts[gIndex]) {
      gifts[gIndex].product_id = product.id;
      gifts[gIndex].name = product.name;
      gifts[gIndex].image = product.images?.[0] || "";
      gifts[gIndex].slug = product.slug;
      
      const productVariants = product.variants || [];
      if (productVariants.length > 0) {
        gifts[gIndex].variant_id = productVariants[0].id;
      } else {
        gifts[gIndex].variant_id = undefined;
      }
      
      // Save product details to local cache
      loadedGiftProducts[product.id] = product;
    }
    
    activeSearchVIdx = null;
    activeSearchGIdx = null;
    dbSearchQuery = "";
    dbSearchResults = [];
  }

  async function loadGiftProductDetails(productId: string) {
    if (loadedGiftProducts[productId]) return;
    try {
      const p = await apiClient.get<Product>(`/api/v1/products/${productId}`);
      if (p) {
        loadedGiftProducts[productId] = p;
      }
    } catch (err) {
      console.error("Lỗi tải chi tiết sản phẩm quà tặng:", err);
    }
  }

  function getVariantLabel(product: Product, variant: ProductVariant): string {
    if (!variant.tierIndex || variant.tierIndex.length === 0) {
      if (variant.tier_index && variant.tier_index.length > 0) {
        variant.tierIndex = variant.tier_index;
      } else {
        return variant.sku || "Biến thể";
      }
    }
    const tierVariations = product.tierVariations || product.tier_variations || [];
    return variant.tierIndex
      .map((tIdx, i) => {
        const tier = tierVariations[i];
        return tier ? tier.options[tIdx] : "";
      })
      .filter(Boolean)
      .join(" - ") || variant.sku || "Biến thể";
  }

  $effect(() => {
    // Reactively load product details for all DB-linked gifts
    if (formState && formState.variants) {
      formState.variants.forEach(v => {
        v.attributes?.gifts?.forEach(g => {
          if (g.product_id && !loadedGiftProducts[g.product_id]) {
            loadGiftProductDetails(g.product_id);
          }
        });
      });
    }
  });
</script>

<div class="flex flex-col gap-5 border border-white/5 rounded-2xl bg-[#0f0f0f] p-5 shadow-inner">
  
  <div class="flex items-center justify-between pb-3 border-b border-white/5">
    <div class="flex items-center gap-2">
      <div class="w-6 h-6 rounded-lg bg-amber-500/10 flex items-center justify-center text-amber-500">
        <ListTree size={12} />
      </div>
      <div class="flex flex-col">
        <span class="text-[10px] font-black tracking-widest text-white/50">Phân loại hàng</span>
        <span class="text-[9px] text-white/20 italic">Thiết lập biến thể (Màu sắc, Kích thước...)</span>
      </div>
    </div>
    
    <div class="flex items-center gap-2">
      <!-- ✨ Nút Trợ lý Xohi AI -->
      <button 
        type="button"
        onclick={toggleXohiAssistant}
        class="flex items-center gap-1.5 px-3 py-1.5 bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/20 rounded-lg text-[9px] font-black tracking-wider text-cyan-400 hover:text-cyan-300 transition-all shadow-[0_0_12px_rgba(6,182,212,0.1)] active:scale-95"
      >
        <Sparkles size={11} class="animate-pulse" /> Trợ lý Xohi AI
      </button>

      {#if formState.tierVariations.length < 2}
        <button 
          type="button"
          onclick={addTier}
          class="flex items-center gap-1.5 px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-[9px] font-bold tracking-wider text-white/40 hover:text-white transition-colors"
        >
          <Plus size={11} /> Thêm Nhóm Phân Loại
        </button>
      {/if}
    </div>
  </div>

  <!-- ✨ Bảng Điều Khiển Xohi AI Glassmorphism HUD -->
  {#if showXohiPanel}
    <div class="flex flex-col gap-4 p-4 border border-cyan-500/20 rounded-xl bg-[#070e14]/90 backdrop-blur-xl shadow-[0_0_24px_rgba(6,182,212,0.15)] transition-all relative overflow-hidden">
      <!-- Liquid shimmer background line -->
      <div class="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-cyan-500/60 to-transparent animate-pulse"></div>
      
      {#if isGeneratingXohi}
        <!-- AI Loading Overlay -->
        <div class="flex flex-col items-center justify-center py-6 gap-3">
          <div class="relative w-8 h-8 flex items-center justify-center">
            <!-- Neon glow ring -->
            <div class="absolute inset-0 rounded-full border border-cyan-500/30 animate-ping"></div>
            <!-- Spinning sparks -->
            <div class="w-8 h-8 rounded-full border-t-2 border-r-2 border-cyan-400 animate-spin"></div>
            <Sparkles size={12} class="absolute text-cyan-400 animate-pulse" />
          </div>
          <div class="flex flex-col items-center gap-1">
            <span class="text-[10px] font-black text-cyan-400 tracking-wider uppercase animate-pulse">{xohiStep}</span>
            <span class="text-[8px] text-white/30 italic">Hệ thống đang cấu hình tối ưu...</span>
          </div>
        </div>
      {:else}
        <!-- AI Input & Presets -->
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-1.5">
            <Sparkles size={12} class="text-cyan-400" />
            <span class="text-[9px] font-black tracking-widest text-cyan-400 uppercase">Trợ lý Phân loại Xohi AI</span>
          </div>
          <button 
            type="button"
            onclick={() => showXohiPanel = false} 
            class="text-white/30 hover:text-white transition-colors"
          >
            <X size={12} />
          </button>
        </div>

        <div class="flex flex-col gap-2">
          <label class="text-[9px] font-bold text-white/50 tracking-wider">Khẩu lệnh thông dịch AI (Tiếng Việt):</label>
          <div class="flex gap-2">
            <input 
              type="text" 
              bind:value={xohiPrompt} 
              placeholder="Nhập yêu cầu phân loại, ví dụ: tạo 3 combo, giảm lần lượt 5 10 15%..."
              class="flex-1 px-3 py-2 bg-black/60 border border-white/5 focus:border-cyan-500/40 rounded-lg text-[10px] text-white placeholder-white/20 outline-none transition-all shadow-inner"
            />
            <button 
              type="button"
              onclick={runXohiAssistant}
              class="px-4 py-2 bg-cyan-500 hover:bg-cyan-400 text-black font-black text-[10px] tracking-wider rounded-lg transition-all shadow-[0_0_12px_rgba(6,182,212,0.25)] hover:shadow-[0_0_16px_rgba(6,182,212,0.4)] active:scale-95"
            >
              Thực thi ✨
            </button>
          </div>
        </div>

        <div class="flex flex-col gap-1.5 pt-2 border-t border-white/5">
          <span class="text-[8px] font-bold text-white/30 uppercase tracking-widest">Presets Tự Động Nhanh (One-click Setup):</span>
          <div class="flex flex-wrap gap-2">
            <button 
              type="button"
              onclick={() => applyXohiPreset('miccosmo')} 
              class="flex items-center gap-1 px-2.5 py-1.5 bg-cyan-500/5 hover:bg-cyan-500/10 border border-cyan-500/10 hover:border-cyan-500/30 rounded-lg text-[9px] font-bold text-cyan-400 transition-all"
            >
              🎁 Combo 3 Cấp (5% - 10% - 15% + Quà tặng)
            </button>
            <button 
              type="button"
              onclick={() => applyXohiPreset('colors')} 
              class="flex items-center gap-1 px-2.5 py-1.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-[9px] font-bold text-white/60 hover:text-white transition-all"
            >
              🎨 3 Màu Sắc Cơ Bản (Đen, Trắng, Be)
            </button>
            <button 
              type="button"
              onclick={() => applyXohiPreset('sizes')} 
              class="flex items-center gap-1 px-2.5 py-1.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-[9px] font-bold text-white/60 hover:text-white transition-all"
            >
              📏 3 Kích Cỡ Tiêu Chuẩn (S, M, L)
            </button>
          </div>
        </div>
      {/if}
    </div>
  {/if}

  {#if formState.tierVariations.length === 0}
    <div class="flex flex-col items-center justify-center py-6 gap-2 opacity-50">
      <ListTree size={24} class="text-white/20" />
      <div class="text-[10px] text-white/30 tracking-widest font-black">Chưa có phân loại nào</div>
    </div>
  {:else}
    
    <div class="flex flex-col gap-6">
      {#each formState.tierVariations as tier, tIndex}
        <div class="flex flex-col gap-3 relative p-4 border border-white/5 rounded-xl bg-black/40">
          <button 
            onclick={() => removeTier(tIndex)}
            class="absolute top-2 right-2 p-1.5 text-white/20 hover:text-red-400 hover:bg-red-400/10 rounded-md transition-colors"
          ><X size={12} /></button>

          <!-- TIER HEADER -->
          <div class="flex items-center justify-between gap-4 pr-6">
            <div class="flex-1 max-w-[200px]">
              <label class="text-[8px] font-black tracking-widest text-amber-500/60 ml-1 mb-1 block">Tên nhóm phân loại {tIndex + 1}</label>
              <input 
                type="text" 
                bind:value={tier.name}
                placeholder="VD: Màu sắc, Kích cỡ..."
                class="w-full bg-transparent border-b border-white/10 px-1 py-1 text-sm text-white placeholder:text-white/20 outline-none focus:border-amber-500"
              />
            </div>

            {#if tIndex === 0}
              <div class="flex items-center gap-2">
                <span class="text-[9px] font-bold text-white/30 tracking-wider">Thêm hình ảnh?</span>
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
            <label class="text-[8px] font-black tracking-widest text-white/30 ml-1">Các thuộc tính (Ấn Enter để tạo)</label>
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
    {#if formState.variants.length > 0}
      <div class="flex flex-col gap-3 mt-4">
        <!-- BATCH APPLY TOOL -->
        <div class="flex items-center gap-3 p-3 bg-gradient-to-r from-amber-500/10 to-transparent border border-amber-500/20 rounded-xl">
          <div class="flex items-center gap-1.5 text-amber-500 mr-2">
            <Zap size={14} />
            <span class="text-[9px] font-black tracking-widest">Áp dụng Hàng Loạt</span>
            <ChevronRight size={12} class="text-amber-500/40" />
          </div>
          <input type="number" bind:value={batchPrice} placeholder="Giá bán..." class="bg-black/40 border border-white/10 rounded px-2 py-1.5 text-xs text-amber-200 outline-none w-24 placeholder:text-white/20" />
          <div class="flex items-center bg-black/40 border border-rose-500/20 rounded overflow-hidden">
            <input type="number" bind:value={batchDiscountPercent} placeholder="%" class="w-12 bg-transparent px-2 py-1.5 text-xs text-rose-300 outline-none border-r border-white/5 placeholder:text-white/10" />
            <input type="number" bind:value={batchDiscountPrice} placeholder="Giá KM..." class="w-24 bg-transparent px-2 py-1.5 text-xs text-rose-300 outline-none placeholder:text-white/20" />
          </div>
          <input type="number" bind:value={batchStock} placeholder="Tồn kho..." class="bg-black/40 border border-white/10 rounded px-2 py-1.5 text-xs text-amber-200 outline-none w-24 placeholder:text-white/20" />
          <input type="text" bind:value={batchSku} placeholder="Mã SKU chung..." class="bg-black/40 border border-white/10 rounded px-2 py-1.5 text-xs text-amber-200 outline-none flex-1 placeholder:text-white/20 " />
          <button onclick={applyBatch} class="px-3 py-1.5 bg-amber-500 text-black text-[9px] font-black tracking-wider rounded-lg hover:brightness-110 flex items-center gap-1">
            <Check size={11} /> Áp dụng
          </button>
        </div>

        <div class="border border-white/5 rounded-xl overflow-x-auto bg-black/20 pb-1 custom-scrollbar">
          <table class="w-full text-left border-collapse">
            <thead>
              <tr class="bg-white/5 border-b border-white/5">
                <th class="py-2.5 px-4 text-[9px] font-black tracking-widest text-white/30 w-16 text-center whitespace-nowrap">Bật/Tắt</th>
                {#each formState.tierVariations as tier}
                  <th class="py-2.5 px-4 text-[9px] font-black tracking-widest text-white/30 whitespace-nowrap">{tier.name}</th>
                {/each}
                <th class="py-2.5 px-4 text-[9px] font-black tracking-widest text-white/30 w-12 text-center border-l border-white/5 whitespace-nowrap">Mặc định</th>
                <th class="py-2.5 px-4 text-[9px] font-black tracking-widest text-amber-500/60 w-28 border-l border-white/5 whitespace-nowrap">Giá Bán</th>
                <th class="py-2.5 px-4 text-[9px] font-black tracking-widest text-rose-500/40 w-16 border-l border-white/5 whitespace-nowrap text-center">Giảm %</th>
                <th class="py-2.5 px-4 text-[9px] font-black tracking-widest text-rose-500/60 w-28 border-l border-white/5 whitespace-nowrap">Giá Khuyến Mãi / 1 sản phẩm</th>
                <th class="py-2.5 px-4 text-[9px] font-black tracking-widest text-white/30 w-20 border-l border-white/5 whitespace-nowrap">Kho Hàng</th>
                <th class="py-2.5 px-4 text-[9px] font-black tracking-widest text-cyan-400/60 min-w-[200px] border-l border-white/5">Thiết Lập Combo(Số lượng bắt buộc để áp dụng) & Quà(nếu có)</th>
                <th class="py-2.5 px-4 text-[9px] font-black tracking-widest text-white/30 min-w-[120px] border-l border-white/5">SKU (Mã PL)</th>
              </tr>
            </thead>
            <tbody>
              {#each formState.variants as variant, vIndex}
                <tr class="border-b border-white/[0.02] hover:bg-white/[0.02] transition-colors group {variant.is_active === false ? 'opacity-40 saturate-50 bg-white/[0.01]' : ''}">
                  <!-- Bật/Tắt toggle -->
                  <td class="p-1 text-center whitespace-nowrap w-16">
                    <button 
                      type="button"
                      onclick={() => toggleVariantActive(vIndex)}
                      class="p-1.5 rounded-lg border transition-all {variant.is_active !== false ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400' : 'bg-white/5 border-white/10 text-white/20'}"
                      title={variant.is_active !== false ? 'Biến thể đang hoạt động' : 'Biến thể đang bị tắt'}
                    >
                      {#if variant.is_active !== false}
                        <span class="text-[9px] font-black px-1.5">ON</span>
                      {:else}
                        <span class="text-[9px] font-black px-1.5">OFF</span>
                      {/if}
                    </button>
                  </td>

                  <!-- Tier Options Display -->
                  {#each variant.tierIndex as tIdx, i}
                    <!-- ONLY SHOW TIER 1 IF IT IS THE FIRST IN ITS GROUP TO AVOID ROWSPAN COMPLEXITY (Like Shopee) -->
                    <!-- For simplicity and robustness, we just print it every time but dim repeats -->
                    <td class="py-2 px-4 text-[11px] font-medium text-white/80 whitespace-nowrap border-r border-white/5">
                      {formState.tierVariations[i].options[tIdx]}
                    </td>
                  {/each}

                  <td class="p-1 border-l border-white/5 text-center">
                    <button 
                      type="button"
                      disabled={variant.is_active === false}
                      onclick={() => setDefault(vIndex)}
                      class="p-2 transition-all rounded-md {variant.is_default ? 'text-amber-500 bg-amber-500/10' : 'text-white/20 hover:text-white/40'} disabled:opacity-30 disabled:cursor-not-allowed"
                      title={variant.is_default ? 'Đang là mặc định' : 'Đặt làm mặc định'}
                    >
                      <Zap size={14} fill={variant.is_default ? 'currentColor' : 'none'} />
                    </button>
                  </td>

                  <td class="p-1 border-l border-white/5">
                    <input 
                      type="number" 
                      bind:value={variant.price} 
                      disabled={variant.is_active === false}
                      oninput={() => {
                        if (variant.discountPercent > 0) {
                          variant.discountPrice = calculateDiscountPrice(Number(variant.price), Number(variant.discountPercent));
                        } else if (variant.discountPrice > 0) {
                          variant.discountPercent = calculateDiscountPercent(Number(variant.price), Number(variant.discountPrice));
                        }
                      }}
                      class="w-full bg-transparent border border-transparent group-hover:bg-black/40 group-hover:border-white/10 focus:border-amber-500/50 !outline-none px-3 py-2 text-xs text-amber-400 font-mono text-right rounded disabled:opacity-50 disabled:cursor-not-allowed" 
                      placeholder="0" 
                    />
                  </td>

                  <td class="p-1 border-l border-white/5">
                    <input 
                      type="number" 
                      bind:value={variant.discountPercent} 
                      disabled={variant.is_active === false}
                      oninput={() => {
                        variant.discountPrice = calculateDiscountPrice(Number(variant.price), Number(variant.discountPercent));
                      }}
                      class="w-full bg-transparent border border-transparent group-hover:bg-black/40 group-hover:border-white/10 focus:border-rose-500/50 !outline-none px-2 py-2 text-xs text-rose-400/70 font-mono text-center rounded disabled:opacity-50 disabled:cursor-not-allowed" 
                      placeholder="0" 
                    />
                  </td>

                  <!-- Discount Price -->
                  <td class="p-1 border-l border-white/5">
                    <div class="relative group/price">
                      <input 
                        type="number" 
                        bind:value={variant.discountPrice} 
                        disabled={variant.is_active === false}
                        oninput={() => {
                          variant.discountPercent = calculateDiscountPercent(Number(variant.price), Number(variant.discountPrice));
                        }}
                        class="w-full bg-transparent border !outline-none px-3 py-2 text-xs font-mono text-right rounded transition-all disabled:opacity-50 disabled:cursor-not-allowed 
                          {variantValidation[vIndex]?.isInvalid 
                            ? 'border-red-500 bg-red-500/10 text-red-400' 
                            : 'border-transparent group-hover:bg-black/40 group-hover:border-white/10 focus:border-rose-500/50 text-rose-400'}" 
                        placeholder="0" 
                      />
                      {#if variantValidation[vIndex]?.isInvalid}
                        <div class="absolute -bottom-6 right-0 whitespace-nowrap bg-red-500 text-white text-[8px] font-bold px-1.5 py-0.5 rounded shadow-lg z-50 pointer-events-none ">
                          Giá KM ≥ Giá bán
                        </div>
                      {/if}
                    </div>
                  </td>

                  <!-- Stock -->
                  <td class="p-1 border-l border-white/5">
                    <input 
                      type="number" 
                      bind:value={variant.stock} 
                      disabled={variant.is_active === false}
                      class="w-full bg-transparent border border-transparent group-hover:bg-black/40 group-hover:border-white/10 focus:border-amber-500/50 !outline-none px-3 py-2 text-xs text-white/60 font-mono text-right rounded disabled:opacity-50 disabled:cursor-not-allowed" 
                      placeholder="0" 
                    />
                  </td>

                  <!-- Combo Config -->
                  <td class="p-2 border-l border-white/5 align-top">
                    <div class="flex flex-col gap-2">
                       <div class="flex items-center gap-2">
                          <span class="text-[9px] font-black text-cyan-500/60 w-12 shrink-0">Số lượng</span>
                          <input 
                            type="number" 
                            bind:value={variant.attributes.combo_qty} 
                            disabled={variant.is_active === false}
                            class="flex-1 bg-black/40 border border-white/10 focus:border-cyan-500/50 outline-none px-2 py-1 text-[10px] text-cyan-400 font-mono rounded placeholder:text-cyan-900 disabled:opacity-50 disabled:cursor-not-allowed" 
                            placeholder="1 (Gói lẻ)" 
                          />
                       </div>
                       
                       {#each variant.attributes.gifts as gift, gIdx}
                          {#if activeSearchVIdx === vIndex && activeSearchGIdx === gIdx}
                            <!-- DB Search Mode Inline Panel -->
                            <div class="flex flex-col gap-1.5 bg-[#070e14]/90 p-2 rounded-lg border border-cyan-500/30 relative">
                              <div class="flex items-center gap-1.5">
                                <Search size={10} class="text-cyan-400" />
                                <span class="text-[8px] font-black text-cyan-400 tracking-wider uppercase">Tìm quà từ DB</span>
                                <button 
                                  type="button"
                                  onclick={() => { activeSearchVIdx = null; activeSearchGIdx = null; }}
                                  class="ml-auto text-white/30 hover:text-white transition-colors"
                                >
                                  <X size={10} />
                                </button>
                              </div>
                              <input 
                                type="text"
                                placeholder="Gõ để tìm kiếm sản phẩm..."
                                value={dbSearchQuery}
                                oninput={handleDbSearchInput}
                                class="w-full bg-black/60 border border-white/10 rounded px-2 py-1 text-[9px] text-white placeholder-white/20 outline-none focus:border-cyan-500/40"
                                autofocus
                              />
                              
                              {#if isSearchingDb}
                                <div class="text-[8px] text-cyan-400/50 italic animate-pulse">Đang tìm kiếm...</div>
                              {/if}

                              {#if dbSearchResults.length > 0}
                                <div class="flex flex-col gap-1 max-h-[120px] overflow-y-auto mt-1 custom-scrollbar border border-white/5 bg-black/80 rounded p-1">
                                  {#each dbSearchResults as p}
                                    <button
                                      type="button"
                                      onclick={() => selectDbProductForGift(vIndex, gIdx, p)}
                                      class="flex items-center gap-2 p-1.5 rounded hover:bg-cyan-500/10 text-left transition-colors"
                                    >
                                      <img src={resolveMediaUrl(p.images?.[0] || "")} alt={p.name} class="w-5 h-5 object-cover rounded bg-white/5 border border-white/10 shrink-0" />
                                      <div class="flex-1 min-w-0">
                                        <div class="text-[9px] font-medium text-white truncate">{p.name}</div>
                                        <div class="text-[7px] text-cyan-400 font-mono">{new Intl.NumberFormat('vi-VN').format(p.price)}đ</div>
                                      </div>
                                    </button>
                                  {/each}
                                </div>
                              {:else if dbSearchQuery.trim() && !isSearchingDb}
                                <div class="text-[8px] text-white/30 italic">Không tìm thấy sản phẩm</div>
                              {/if}
                            </div>
                          {:else if gift.product_id}
                            <!-- DB-linked Gift Item View -->
                            <div class="flex gap-2 items-center bg-violet-950/20 p-1.5 rounded border border-violet-500/20 relative group/gift cursor-default">
                              <div class="w-6 h-6 rounded border border-violet-500/20 bg-black/40 flex items-center justify-center overflow-hidden shrink-0 relative">
                                {#if gift.image}
                                  <img src={resolveMediaUrl(gift.image)} alt={gift.name} class="w-full h-full object-cover" />
                                {:else}
                                  <Database size={10} class="text-violet-400" />
                                {/if}
                                <div class="absolute inset-0 bg-violet-500/10 pointer-events-none"></div>
                              </div>

                              <div class="flex flex-col flex-1 min-w-0">
                                <div class="flex items-center gap-1">
                                  <span class="text-[7px] font-black text-violet-400 bg-violet-500/15 px-1 rounded uppercase tracking-wider shrink-0">DB</span>
                                  <span class="text-[9px] font-bold text-white truncate" title={gift.name}>{gift.name}</span>
                                </div>
                                
                                {#if loadedGiftProducts[gift.product_id] && loadedGiftProducts[gift.product_id].variants?.length > 0}
                                  {@const giftProd = loadedGiftProducts[gift.product_id]}
                                  <div class="flex items-center gap-1 mt-0.5">
                                    <span class="text-[7px] text-white/30 shrink-0">PL:</span>
                                    <select 
                                      bind:value={gift.variant_id}
                                      disabled={variant.is_active === false}
                                      onchange={(e) => {
                                        const selectedVarId = (e.target as HTMLSelectElement).value;
                                        const selectedVar = giftProd.variants.find(v => v.id === selectedVarId);
                                        if (selectedVar) {
                                          const tierVariations = giftProd.tierVariations || giftProd.tier_variations || [];
                                          if (tierVariations.length > 0 && selectedVar.tierIndex && selectedVar.tierIndex.length > 0) {
                                            const varImg = tierVariations[0].images?.[selectedVar.tierIndex[0]];
                                            if (varImg) {
                                              gift.image = varImg;
                                            }
                                          }
                                        }
                                      }}
                                      class="bg-[#12081f] border border-violet-500/20 rounded px-1 py-0.5 text-[8px] text-violet-300 outline-none max-w-[120px] truncate"
                                    >
                                      {#each giftProd.variants as v}
                                        <option value={v.id}>{getVariantLabel(giftProd, v)}</option>
                                      {/each}
                                    </select>
                                  </div>
                                {/if}
                              </div>

                              <input 
                                type="number" 
                                bind:value={gift.qty} 
                                disabled={variant.is_active === false}
                                placeholder="SL" 
                                class="w-8 bg-transparent border-b border-white/10 outline-none text-[9px] text-center text-rose-400 font-bold px-1 disabled:opacity-50 disabled:cursor-not-allowed" 
                              />

                              <div class="flex items-center gap-0.5 opacity-0 group-hover/gift:opacity-100 transition-opacity">
                                <button 
                                  type="button"
                                  title="Hủy liên kết DB (Chuyển tự nhập)"
                                  onclick={() => {
                                    gift.product_id = undefined;
                                    gift.variant_id = undefined;
                                    gift.slug = undefined;
                                  }}
                                  class="text-white/20 hover:text-amber-400 p-0.5 transition-colors"
                                >
                                  <Link2Off size={10} />
                                </button>
                                <button 
                                  type="button"
                                  disabled={variant.is_active === false}
                                  onclick={() => removeGift(vIndex, gIdx)} 
                                  class="text-white/20 hover:text-red-400 p-0.5"
                                >
                                  <X size={10}/>
                                </button>
                              </div>
                            </div>
                          {:else}
                            <!-- Manual/Free text Gift Item View -->
                            <div class="flex gap-2 items-center bg-cyan-900/10 p-1.5 rounded border border-cyan-500/10 relative group/gift cursor-default">
                              <!-- Small Thumbnail for Gift (Rule R03: Premium UX) -->
                              <button 
                                type="button"
                                disabled={variant.is_active === false}
                                onclick={() => onOpenVaultForGift(vIndex, gIdx)}
                                class="w-6 h-6 rounded border border-white/10 bg-black/40 flex items-center justify-center overflow-hidden shrink-0 group/img-gift hover:border-cyan-500/50 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                              >
                                {#if gift.image}
                                  <img src={resolveMediaUrl(gift.image)} alt={gift.name} class="w-full h-full object-cover" />
                                {:else}
                                  <ImagePlus size={10} class="text-cyan-500/40 group-hover/img-gift:text-cyan-400 transition-colors" />
                                {/if}
                              </button>

                              <div class="flex flex-1 gap-1 items-start">
                                <input 
                                  type="text" 
                                  bind:value={gift.name} 
                                  disabled={variant.is_active === false}
                                  placeholder="Tên quà (VD: Mặt nạ)" 
                                  class="flex-1 min-w-[80px] bg-transparent border-b border-white/10 outline-none text-[9px] text-white px-1 disabled:opacity-50 disabled:cursor-not-allowed" 
                                />
                                <input 
                                  type="number" 
                                  bind:value={gift.qty} 
                                  disabled={variant.is_active === false}
                                  placeholder="SL" 
                                  class="w-10 bg-transparent border-b border-white/10 outline-none text-[9px] text-center text-rose-400 font-bold px-1 disabled:opacity-50 disabled:cursor-not-allowed" 
                                />
                              </div>
                              
                              <div class="flex items-center gap-0.5 opacity-0 group-hover/gift:opacity-100 transition-opacity">
                                <button 
                                  type="button"
                                  title="Liên kết sản phẩm DB"
                                  onclick={() => {
                                    activeSearchVIdx = vIndex;
                                    activeSearchGIdx = gIdx;
                                    dbSearchQuery = gift.name || "";
                                    dbSearchResults = [];
                                    if (dbSearchQuery) searchDbProducts(dbSearchQuery);
                                  }}
                                  class="text-white/20 hover:text-cyan-400 p-0.5 transition-colors"
                                >
                                  <Database size={10} />
                                </button>
                                <button 
                                  type="button"
                                  disabled={variant.is_active === false}
                                  onclick={() => removeGift(vIndex, gIdx)} 
                                  class="text-white/20 hover:text-red-400 p-0.5"
                                >
                                  <X size={10}/>
                                </button>
                              </div>
                            </div>
                          {/if}
                       {/each}
                       
                       <button 
                         type="button"
                         disabled={variant.is_active === false}
                         onclick={() => addGift(vIndex)} 
                         class="self-start text-[9px] font-black text-cyan-500 hover:text-cyan-300 tracking-widest flex items-center gap-1 mt-1 disabled:opacity-30 disabled:cursor-not-allowed"
                       >
                          <Plus size={10} /> Quà Tặng ({variant.attributes.gifts?.length || 0})
                       </button>
                    </div>
                  </td>

                  <!-- SKU -->
                  <td class="p-1 border-l border-white/5 align-top">
                    <input 
                      type="text" 
                      bind:value={variant.sku} 
                      disabled={variant.is_active === false}
                      class="w-full bg-transparent border border-transparent group-hover:bg-black/40 group-hover:border-white/10 focus:border-amber-500/50 !outline-none px-3 py-2 text-xs text-white/60 font-mono tracking-wider rounded disabled:opacity-50 disabled:cursor-not-allowed" 
                      placeholder="SKU" 
                    />
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
