<script lang="ts">
  import Settings from "@lucide/svelte/icons/settings";
  import Image from "@lucide/svelte/icons/image";
  import FileText from "@lucide/svelte/icons/file-text";
  import ShoppingCart from "@lucide/svelte/icons/shopping-cart";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import MissionControlShell from "../ui/MissionControlShell.svelte";
  import MediaVaultModal from "../../media/MediaVaultModal.svelte";
  import NeuralEditor from "../ui/tiptap/NeuralEditor.svelte";
  import ProductFormBase from "./ProductFormBase.svelte";
  import ProductFormMedia from "./ProductFormMedia.svelte";
  import ProductFormMetadata from "./ProductFormMetadata.svelte";
  import ProductFormSeo from "./ProductFormSeo.svelte";
  import ProductFormSpecs from "./ProductFormSpecs.svelte";
  import ProductFormVariants from "./ProductFormVariants.svelte";
  import ProductMarketPrice from "./ProductMarketPrice.svelte";
  import type { Product } from "$lib/types";
  import { Z_INDEX_ADMIN } from "$lib/core/constants/z_index_admin";
  import { portal } from "$lib/core/actions/portal";

  let {
    isOpen = false,
    editingId,
    formName = $bindable(),
    formSku = $bindable(),
    formPrice = $bindable(),
    formDiscountPrice = $bindable(),
    formStock = $bindable(),
    formCategory = $bindable(),
    formStatus = $bindable(),
    formShortDescription = $bindable(),
    formDescription = $bindable(),
    formSlug = $bindable(),
    formSeoTitle = $bindable(),
    formSeoDescription = $bindable(),
    formSeoKeywords = $bindable(),
    formImages = $bindable(),
    formMobileImages = $bindable(),
    formAttributes = $bindable(),
    formMetadata = $bindable(),
    formTierVariations = $bindable(),
    formVariants = $bindable(),
    categories = [],
    onSave,
    onClose,
    generateSlug,
    isSaving = false,
    errors = {},
    formIsAiFeatured = $bindable(),
    formAnalysisReport = $bindable(),
    formMarketData = $bindable(),
    formLastMarketSync = $bindable(),
  } = $props<{
    isOpen?: boolean;
    editingId: string | null;
    formName: string;
    formSku: string;
    formPrice: number;
    formDiscountPrice?: number;
    formStock: number;
    formCategory: string;
    formStatus: "active" | "draft" | "archived";
    formShortDescription: string;
    formDescription: string;
    formSlug: string;
    formSeoTitle: string;
    formSeoDescription: string;
    formSeoKeywords: string;
    formImages: string[];
    formMobileImages: string[];
    formAttributes: Record<string, string | number | boolean | null>;
    formMetadata: Product['metadata'];
    formTierVariations: Product['tierVariations'];
    formVariants: Product['variants'];
    categories: { id: string; name: string }[];
    onSave: () => void;
    onClose: () => void;
    generateSlug: (name: string) => string;
    isSaving?: boolean;
    errors?: Record<string, string>;
    formIsAiFeatured: boolean;
    formAnalysisReport?: Record<string, unknown>;
    formMarketData?: Product['market_data'];
    formLastMarketSync?: string;
  }>();

  let showMediaModal = $state(false);
  
  // Tracking which variant image is being edited
  let variantEditTierIndex = $state<number | null>(null);
  let variantEditOptionIndex = $state<number | null>(null);
  let variantEditIsMobile = $state(false);
  let albumReplaceIndex = $state<number | null>(null);

  let reserve_assets = $state<string[]>([]);
  let selectedAvatarUrl = $state<string | null>(null);
  let selectedAssetIndex = $state(0);

  function handleVariantImageSelect(url: string) {
    if (variantEditTierIndex !== null && variantEditOptionIndex !== null) {
      const tier = formTierVariations[variantEditTierIndex];
      if (tier) {
        const key = variantEditIsMobile ? 'mobile_images' : 'images';
        if (!tier[key]) tier[key] = [];
        tier[key][variantEditOptionIndex] = url;
        formTierVariations = [...formTierVariations];
      }
    }
    variantEditTierIndex = null;
    variantEditOptionIndex = null;
    variantEditIsMobile = false;
    giftEditVariantIndex = null;
    giftEditGiftIndex = null;
    showMediaModal = false;
  }

  function handleAlbumImageSelect(url: string) {
    if (albumReplaceIndex !== null) {
      if (isVaultForMobile) {
        formMobileImages[albumReplaceIndex] = url;
        formMobileImages = [...formMobileImages];
      } else {
        formImages[albumReplaceIndex] = url;
        formImages = [...formImages];
      }
    } else {
      // Standard append handled by bind:assets in MediaVaultModal
      // But we can ensure it here if needed. 
    }
    albumReplaceIndex = null;
    showMediaModal = false;
  }

  function handleGiftImageSelect(url: string) {
    if (giftEditVariantIndex !== null && giftEditGiftIndex !== null) {
      if (formVariants[giftEditVariantIndex].attributes?.gifts?.[giftEditGiftIndex]) {
        formVariants[giftEditVariantIndex].attributes.gifts[giftEditGiftIndex].image = url;
        formVariants = [...formVariants];
      }
    }
    giftEditVariantIndex = null;
    giftEditGiftIndex = null;
    showMediaModal = false;
  }

  let isVaultForMobile = $state(false);
  let giftEditVariantIndex = $state<number | null>(null);
  let giftEditGiftIndex = $state<number | null>(null);

  let isEditorFullScreen = $state(false);

  function openVaultForGeneral(isMobile = false, replaceIndex: number | null = null) {
    variantEditTierIndex = null;
    variantEditOptionIndex = null;
    albumReplaceIndex = replaceIndex;
    isVaultForMobile = isMobile;
    showMediaModal = true;
  }

  function openVaultForVariant(tIdx: number, oIdx: number, isMobile = false) {
    variantEditTierIndex = tIdx;
    variantEditOptionIndex = oIdx;
    variantEditIsMobile = isMobile;
    reserve_assets = []; // clear previous selection
    showMediaModal = true;
  }

  function openVaultForGift(vIdx: number, gIdx: number) {
    giftEditVariantIndex = vIdx;
    giftEditGiftIndex = gIdx;
    reserve_assets = [];
    showMediaModal = true;
  }

</script>

<MissionControlShell
  title={editingId ? `Inventory_Registry // EDIT_${String(editingId).slice(0, 8)}` : "Inventory_Registry // NEW_ENTRY"}
  variant="cyan"
  {isOpen}
  {onClose}
  headerIcon={ShoppingCart}
  fullScreen={true}
>
  <div class="w-full flex flex-col gap-0 pb-10">
    <div class="grid grid-cols-1 xl:grid-cols-12 gap-x-8 gap-y-8 px-5 pt-5" style="z-index: var(--z-surface)">

      <!-- MACRO LEFT COLUMN (8/12) -->
      <div class="xl:col-span-8 flex flex-col gap-8">

        <!-- Section 1 (Base Info) -->
        <div class="flex flex-col gap-4">
          <div class="section-label">
            <Settings size={11} />
            Thông tin cơ bản
          </div>
          <ProductFormBase
            {editingId}
            bind:formName bind:formSku bind:formPrice bind:formDiscountPrice bind:formStock bind:formCategory bind:formStatus bind:formShortDescription
            bind:formIsAiFeatured
            {categories} {generateSlug} {errors}
            onNameInput={() => { if (!editingId) formSlug = generateSlug(formName); }}
          />
        </div>

        <!-- NEW: Section 1.5 (Variants / Matrix) -->
        <div class="flex flex-col">
          <ProductFormVariants
            bind:formTierVariations={formTierVariations}
            bind:formVariants={formVariants}
            {formSku}
            onOpenVault={openVaultForVariant}
            onOpenVaultForGift={openVaultForGift}
          />
        </div>


        <!-- Section 2 (Editor) -->
        <div class="flex flex-col">
          <div class="flex items-center justify-between mb-3">
            <div class="section-label">
              <FileText size={11} />
              Thông tin mô tả sản phẩm
            </div>
            <div class="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-[#FFB800]/10 border border-[#FFB800]/20 shadow-[0_0_15px_rgba(255,184,0,0.1)]">
              <Sparkles size={10} class="text-[#FFB800] animate-pulse" />
              <span class="text-[8px] font-black text-[#FFB800] uppercase tracking-widest">Tiêu chí vàng AI</span>
            </div>
          </div>
          <div class="border border-white/5 rounded-2xl overflow-hidden bg-black/40 min-h-[500px] flex flex-col">
            <NeuralEditor
              bind:content={formDescription}
              topic={formName}
              editable={true}
              placeholder="Mô tả kỹ thuật, câu chuyện thiết kế của sản phẩm..."
              contentType="product"
              getMetadata={() => ({
                short_description: formShortDescription,
                sku: formSku,
                price: formPrice,
                brand: formMetadata.brand,
                origin: formMetadata.origin,
                attributes: formAttributes,
                science_claims: formMetadata.science_claims,
                faqs: formMetadata.faqs || []
              })}
              bind:analysisCache={formMetadata.analysis_cache}
              bind:analysisMetrics={formMetadata.analysis_metrics}
              bind:analysisReport={formAnalysisReport}
              bind:fullScreen={isEditorFullScreen}
            />
          </div>
        </div>

        <!-- Section 3 (SEO) -->
        <div class="flex flex-col pt-2">
          <ProductFormSeo
            {formName}
            bind:formSlug
            bind:formSeoTitle
            bind:formSeoDescription
            bind:formSeoKeywords
            {formImages}
            {generateSlug}
          />
        </div>

      </div>

      <!-- MACRO RIGHT COLUMN (4/12) -->
      <div class="xl:col-span-4 flex flex-col gap-8">

        <!-- Media Gallery -->
        <div class="flex flex-col gap-4">
          <div class="flex items-center gap-2 text-[9px] font-black text-white/25 uppercase tracking-[0.25em]">
            <Image size={11} class="text-amber-400/60" />
            Album hiển thị
            <span class="text-amber-500 ml-auto bg-amber-500/10 px-1.5 py-0.5 rounded text-[8px]">{formImages?.length || 0}</span>
          </div>
          <ProductFormMedia bind:formImages bind:formMobileImages onOpenVault={openVaultForGeneral} />
        </div>

        <!-- Product Metadata (Contextual) -->
        <div class="flex flex-col pt-2">
          <ProductFormMetadata bind:formMetadata={formMetadata} {formName} formDescription={formShortDescription || formDescription} />
        </div>

        <!-- Specs -->
        <div class="flex flex-col pt-2">
          <ProductFormSpecs bind:formAttributes />
        </div>

        <!-- Market Price Intel -->
        <div class="flex flex-col pt-2">
          <ProductMarketPrice 
            product_id={editingId} 
            bind:market_data={formMarketData} 
            last_sync={formLastMarketSync} 
          />
        </div>

      </div>
    </div>

    <!-- ACTION BAR (Elite V2.2: Solid Pop CTA) -->
    <div use:portal={isEditorFullScreen}>
      <section 
        class="{isEditorFullScreen ? 'fixed bottom-0 left-0 right-0 z-[950000]' : 'relative mt-auto'} px-8 py-10 flex justify-end items-center pointer-events-none" 
      >
        <div class="flex items-center gap-4 pointer-events-auto">
          <button
            onclick={onClose}
            class="px-8 py-3 bg-[#1a1a1a] text-white/60 hover:text-white rounded-xl text-[10px] font-black uppercase tracking-[0.2em] shadow-[0_10px_30px_rgba(0,0,0,0.5)] cursor-pointer active:scale-95 transition-all"
          >Huỷ bỏ</button>

          <button
            onclick={onSave}
            disabled={isSaving}
            class="px-10 py-3 bg-[#FFB800] text-black rounded-xl text-[10px] font-black uppercase tracking-[0.3em] shadow-[0_10px_40px_rgba(255,184,0,0.3)] disabled:opacity-40 disabled:grayscale disabled:cursor-not-allowed cursor-pointer active:scale-95 transition-all"
          >
            {#if isSaving}
              <div class="flex items-center gap-3">
                <div class="w-3 h-3 border-2 border-black/30 border-t-black rounded-full animate-spin"></div>
                <span>Syncing...</span>
              </div>
            {:else}
              {editingId ? "Ghi đè thay đổi" : "Xuất bản Inventory"}
            {/if}
          </button>
        </div>
      </section>
    </div>
  </div>
</MissionControlShell>

{#if isVaultForMobile}
  <MediaVaultModal
    isOpen={showMediaModal}
    onClose={() => { showMediaModal = false; variantEditTierIndex = null; variantEditOptionIndex = null; isVaultForMobile = false; variantEditIsMobile = false; }}
    onSelect={variantEditOptionIndex !== null ? handleVariantImageSelect : undefined}
    bind:assets={formMobileImages}
    bind:reserve_assets
    bind:selectedAvatarUrl
    bind:selectedAssetIndex
  />
{:else}
  <MediaVaultModal
    isOpen={showMediaModal}
    onClose={() => { showMediaModal = false; variantEditTierIndex = null; variantEditOptionIndex = null; isVaultForMobile = false; variantEditIsMobile = false; albumReplaceIndex = null; giftEditVariantIndex = null; giftEditGiftIndex = null; }}
    onSelect={variantEditOptionIndex !== null ? handleVariantImageSelect : (albumReplaceIndex !== null ? handleAlbumImageSelect : (giftEditGiftIndex !== null ? handleGiftImageSelect : undefined))}
    bind:assets={formImages}
    bind:reserve_assets
    bind:selectedAvatarUrl
    bind:selectedAssetIndex
  />
{/if}

<style>
  @reference "tailwindcss";
  .section-label {
    @apply flex items-center gap-2 text-[9px] font-black uppercase tracking-[0.35em] text-white/30;
  }
</style>
