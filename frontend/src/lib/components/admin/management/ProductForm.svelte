<script lang="ts">
  import { onMount, untrack } from "svelte";
  import Settings from "lucide-svelte/icons/settings";
  import Image from "lucide-svelte/icons/image";
  import FileText from "lucide-svelte/icons/file-text";
  import ShoppingCart from "lucide-svelte/icons/shopping-cart";
  import MissionControlShell from "../ui/MissionControlShell.svelte";
  import MediaVaultModal from "../../media/MediaVaultModal.svelte";
  import NeuralEditor from "../ui/tiptap/NeuralEditor.svelte";
  import ProductFormBase from "./ProductFormBase.svelte";
  import ProductFormMedia from "./ProductFormMedia.svelte";
  import ProductFormSeo from "./ProductFormSeo.svelte";
  import ProductFormSpecs from "./ProductFormSpecs.svelte";
  import ProductFormVariants from "./ProductFormVariants.svelte";
  import { processContentImages } from "$lib/state/utils";
  import type { MediaAsset, Product } from "$lib/types";

  let {
    isOpen = false,
    editingId,
    formName = $bindable(),
    formSku = $bindable(),
    formPrice = $bindable(),
    formStock = $bindable(),
    formCategory = $bindable(),
    formStatus = $bindable(),
    formDescription = $bindable(),
    formSlug = $bindable(),
    formSeoTitle = $bindable(),
    formSeoDescription = $bindable(),
    formSeoKeywords = $bindable(),
    formImages = $bindable(),
    formAttributes = $bindable(),
    formTierVariations = $bindable(),
    formVariants = $bindable(),
    categories,
    onSave,
    onClose,
    generateSlug,
    isSaving,
    errors,
  } = $props<{
    isOpen?: boolean;
    editingId: string | null;
    formName: string;
    formSku: string;
    formPrice: number;
    formStock: number;
    formCategory: string;
    formStatus: "active" | "draft" | "archived";
    formDescription: string;
    formSlug: string;
    formSeoTitle: string;
    formSeoDescription: string;
    formSeoKeywords: string;
    formImages: string[];
    formAttributes: Record<string, string | number | boolean | null>;
    formTierVariations: Product['tierVariations'];
    formVariants: Product['variants'];
    categories: { id: string; name: string }[];
    onSave: () => void;
    onClose: () => void;
    generateSlug: (name: string) => string;
    isSaving?: boolean;
    errors?: Record<string, string>;
  }>();

  let showMediaModal = $state(false);
  
  // Tracking which variant image is being edited
  let variantEditTierIndex = $state<number | null>(null);
  let variantEditOptionIndex = $state<number | null>(null);

  let reserve_assets = $state<string[]>([]);
  let selectedAvatarUrl = $state<string | null>(null);
  let selectedAssetIndex = $state(0);
  let contentAssets = $state<(MediaAsset | string)[]>([]);

  // ⚡ PERF: One-time asset extraction
  let assetsExtracted = false;

  $effect(() => {
    if (formDescription && formDescription.includes("[IMAGE_")) {
      const assets = untrack(() => contentAssets);
      formDescription = processContentImages(formDescription, assets);
    }
  });

  onMount(() => {
    if (formDescription && !assetsExtracted) {
      assetsExtracted = true;
      const imgRegex = /<img[^>]+src=["']([^"']+)["']/g;
      const found: string[] = [];
      let match: RegExpExecArray | null;
      while ((match = imgRegex.exec(formDescription)) !== null) {
        if (match[1] && !found.includes(match[1])) found.push(match[1]);
      }
      if (found.length > 0) contentAssets = found;
    }

    if (formName === undefined) formName = "";
    if (formSku === undefined) formSku = "";
    if (formPrice === undefined) formPrice = 0;
    if (formStock === undefined) formStock = 0;
    if (formCategory === undefined) formCategory = "";
    if (formStatus === undefined) formStatus = "draft";
    if (formDescription === undefined) formDescription = "";
    if (formSlug === undefined) formSlug = "";
    if (formSeoTitle === undefined) formSeoTitle = "";
    if (formSeoDescription === undefined) formSeoDescription = "";
    if (formSeoKeywords === undefined) formSeoKeywords = "";
    if (formImages === undefined) formImages = [];
    if (formAttributes === undefined) formAttributes = {};
    if (formVariants === undefined) formVariants = [];
  });

  function handleVariantImageSelect(url: string) {
    if (variantEditTierIndex !== null && variantEditOptionIndex !== null) {
      if (formTierVariations[variantEditTierIndex]) {
        // Ensure images array exists
        if (!formTierVariations[variantEditTierIndex].images) {
          formTierVariations[variantEditTierIndex].images = [];
        }
        formTierVariations[variantEditTierIndex].images[variantEditOptionIndex] = url;
        // Trigger reactivity
        formTierVariations = [...formTierVariations];
      }
    }
    variantEditTierIndex = null;
    variantEditOptionIndex = null;
    showMediaModal = false;
  }

  function openVaultForGeneral() {
    variantEditTierIndex = null;
    variantEditOptionIndex = null;
    showMediaModal = true;
  }

  function openVaultForVariant(tIdx: number, oIdx: number) {
    variantEditTierIndex = tIdx;
    variantEditOptionIndex = oIdx;
    reserve_assets = []; // clear previous selection
    showMediaModal = true;
  }

</script>

<MissionControlShell
  title={editingId ? `Inventory_Registry // EDIT_${editingId.slice(0, 8)}` : "Inventory_Registry // NEW_ENTRY"}
  variant="amber"
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
            bind:formName bind:formSku bind:formPrice bind:formStock bind:formCategory bind:formStatus
            {categories} {generateSlug} {errors}
            onNameInput={() => { if (!editingId) formSlug = generateSlug(formName); }}
          />
        </div>

        <!-- NEW: Section 1.5 (Variants / Matrix) -->
        <div class="flex flex-col">
          <ProductFormVariants
            bind:formTierVariations={formTierVariations}
            bind:formVariants={formVariants}
            onOpenVault={openVaultForVariant}
          />
        </div>

        <!-- Section 2 (Editor) -->
        <div class="flex flex-col">
          <div class="section-label mb-3">
            <FileText size={11} />
            Thông tin mô tả sản phẩm
          </div>
          <div class="border border-white/5 rounded-2xl overflow-hidden bg-black/40 min-h-[500px] flex flex-col">
            <NeuralEditor
              bind:content={formDescription}
              topic={formName}
              editable={true}
              placeholder="Mô tả kỹ thuật, câu chuyện thiết kế của sản phẩm..."
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
          <ProductFormMedia bind:formImages onOpenVault={openVaultForGeneral} />
        </div>

        <!-- Specs -->
        <div class="flex flex-col pt-2">
          <ProductFormSpecs bind:formAttributes />
        </div>

      </div>
    </div>

    <!-- ACTION BAR -->
    <section class="relative px-5 pt-5 pb-2 mt-auto" style="z-index: var(--z-layout_header)">
      <div class="flex items-center justify-between gap-4 py-2 border-t border-white/5 pt-4">
        <div class="flex items-center gap-2 text-[9px] font-black uppercase tracking-widest text-white/20">
          <div class="w-1.5 h-1.5 rounded-full bg-amber-400"></div>
          Neural Catalog Sync Link
        </div>

        <div class="flex items-center gap-3">
          <button
            onclick={onClose}
            class="px-5 py-2.5 text-[10px] font-black uppercase tracking-wider text-white/30 hover:text-white transition-colors cursor-pointer"
          >Huỷ bỏ</button>

          <button
            onclick={onSave}
            disabled={isSaving}
            class="flex items-center gap-2 px-8 py-3 bg-gradient-to-r from-amber-500 to-amber-600 text-black rounded-xl text-[10px] font-black uppercase tracking-wider cursor-pointer hover:brightness-110 active:scale-95 disabled:opacity-40 disabled:grayscale disabled:cursor-not-allowed shadow-[0_0_20px_rgba(245,158,11,0.2)]"
          >
            {#if isSaving}
              <div class="w-3 h-3 border-2 border-black/30 border-t-black rounded-full animate-spin"></div>
              Đang đồng bộ...
            {:else}
              {editingId ? "Ghi đè thay đổi" : "Xuất bản Inventory"}
            {/if}
          </button>
        </div>
      </div>
    </section>
  </div>
</MissionControlShell>

<MediaVaultModal
  isOpen={showMediaModal}
  onClose={() => { showMediaModal = false; variantEditTierIndex = null; variantEditOptionIndex = null; }}
  onSelect={variantEditOptionIndex !== null ? handleVariantImageSelect : undefined}
  bind:assets={formImages}
  bind:reserve_assets
  bind:selectedAvatarUrl
  bind:selectedAssetIndex
/>

<style>
  @reference "tailwindcss";
  .section-label {
    @apply flex items-center gap-2 text-[9px] font-black uppercase tracking-[0.35em] text-white/30;
  }
</style>
