<script lang="ts">
  import type { ProductFormState } from "$lib/types";
  import ChevronDown from "@lucide/svelte/icons/chevron-down";

  let {
    editingId,
    formState = $bindable(),
    categories,
    generateSlug,
    onNameInput,
    errors,
  } = $props<{
    editingId: string | null;
    formState: ProductFormState;
    categories: { id: string; name: string }[];
    generateSlug: (name: string) => string;
    onNameInput: () => void;
    errors?: Record<string, string>;
  }>();

  // R102 Validation Rune: Track invalid price combinations
  const isDiscountInvalid = $derived(
    formState.discountPrice !== undefined &&
      formState.discountPrice !== null &&
      Number(formState.discountPrice) > 0 &&
      Number(formState.discountPrice) >= Number(formState.price),
  );
</script>

<!-- Left Column: Primary Data -->
<div class="flex flex-col gap-4 h-full">
  <!-- Tiêu đề -->
  <div class="field-group">
    <label class="field-label flex items-center gap-2">
      Tên sản phẩm
      <span class="text-amber-500">*</span>
    </label>
    <div class="relative">
      <input
        type="text"
        bind:value={formState.name}
        oninput={onNameInput}
        placeholder="Nhập tên sản phẩm..."
        class="field-input border-b-amber-500/30 focus:border-amber-500 text-xl font-bold"
      />
      <div class="field-line bg-amber-500/60"></div>
    </div>
    {#if errors?.name}
      <p class="text-red-500 text-[10px] mt-1 font-bold">{errors.name}</p>
    {/if}
  </div>

  <!-- Mô tả ngắn -->
  <div class="field-group">
    <label class="field-label flex items-center gap-2">
      Mô tả ngắn (Hiển thị Banner)
    </label>
    <div class="relative">
      <textarea
        bind:value={formState.shortDescription}
        placeholder="Nhập mô tả ngắn cho banner..."
        rows="2"
        class="field-input border-b-amber-500/30 focus:border-amber-500 text-sm italic text-white/70"
      ></textarea>
      <div class="field-line bg-amber-500/60"></div>
    </div>
  </div>

  <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
    <!-- Mã SKU -->
    <div class="field-group">
      <label class="field-label">Mã SKU</label>
      <div class="relative">
        <input
          type="text"
          bind:value={formState.sku}
          placeholder="SKU-XXXX..."
          class="field-input border-b-amber-500/30 font-mono text-sm text-amber-400 tracking-wider"
        />
        <div class="field-line bg-amber-500/60"></div>
      </div>
    </div>

    <!-- Phân loại -->
    <div class="field-group">
      <label class="field-label">Danh mục kết nối</label>
      <div class="relative">
        <select
          value={formState.category}
          onchange={(e) => (formState.category = e.currentTarget.value)}
          class="field-select border border-white/8 appearance-none bg-black/40"
        >
          <option value="" class="bg-[#0f0f0f]">Chưa phân loại</option>
          {#each categories as c}
            <option
              value={c.id}
              selected={c.id === formState.category}
              class="bg-[#0f0f0f]">{c.name}</option
            >
          {/each}
        </select>
        <div
          class="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-white/20"
        >
          <ChevronDown size={13} />
        </div>
      </div>
    </div>
  </div>

  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
    <!-- Giá bán -->
    <div class="field-group">
      <label class="field-label">Giá bán</label>
      <div class="relative flex items-center">
        <input
          type="number"
          bind:value={formState.price}
          placeholder="0"
          class="field-input border-b-amber-500/30 text-sm font-mono tracking-wider w-full pr-12"
        />
        <div class="field-line bg-amber-500/60"></div>
        <span class="absolute right-2 text-[9px] font-black text-amber-500/50"
          >VND</span
        >
      </div>
    </div>

    <!-- Giá khuyến mãi -->
    <div class="field-group">
      <label
        class="field-label flex items-center gap-2 {isDiscountInvalid
          ? 'text-red-500'
          : 'text-rose-500/60'} tracking-widest"
      >
        Giá khuyến mãi
        {#if isDiscountInvalid}
          <span class="text-[8px] font-bold text-red-500 normal-case"
            >(Phải nhỏ hơn Giá bán)</span
          >
        {/if}
      </label>
      <div class="relative flex items-center">
        <input
          type="number"
          bind:value={formState.discountPrice}
          placeholder="0"
          class="field-input transition-all !outline-none text-sm font-mono tracking-wider w-full pr-12
            {isDiscountInvalid
            ? 'border-b-red-500 text-red-400 bg-red-500/5'
            : 'border-b-rose-500/30 text-rose-400'}"
        />
        <div
          class="field-line {isDiscountInvalid
            ? 'bg-red-500'
            : 'bg-rose-500/60'}"
        ></div>
        <span
          class="absolute right-2 text-[9px] font-black {isDiscountInvalid
            ? 'text-red-500/50'
            : 'text-rose-500/50'}">VND</span
        >
      </div>
    </div>

    <!-- Tồn kho -->
    <div class="field-group">
      <label class="field-label">Kho lưu trữ</label>
      <div class="relative flex items-center">
        <input
          type="number"
          bind:value={formState.stock}
          placeholder="0"
          class="field-input border-b-amber-500/30 text-sm font-mono tracking-wider w-full pr-12"
        />
        <div class="field-line bg-amber-500/60"></div>
        <span class="absolute right-2 text-[9px] font-black text-amber-500/50"
          >Unit</span
        >
      </div>
    </div>

    <!-- Trạng thái -->
    <div class="field-group">
      <label class="field-label">Trạng thái vận hành</label>
      <div
        class="flex items-center gap-1 p-0.5 bg-black/40 rounded-xl border border-white/5 h-full"
      >
        {#each [["active", "H.Động"], ["draft", "Thảo"], ["archived", "Lưu"]] as [val, lbl]}
          <button
            onclick={() =>
              (formState.status = val as "active" | "draft" | "archived")}
            class="flex-1 h-full flex items-center justify-center text-[8px] font-black tracking-tight rounded-lg
               {formState.status === val
              ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30 shadow-inner'
              : 'text-gray-600 hover:text-white border border-transparent'}"
            >{lbl}</button
          >
        {/each}
      </div>
    </div>

    <!-- CTV Commission Rate Override -->
    <div class="field-group lg:col-span-1">
      <label class="field-label flex items-center gap-2 text-amber-500/75">
        Hoa hồng CTV (%)
      </label>
      <div class="relative flex items-center">
        <input
          type="number"
          bind:value={formState.ctvRateOverride}
          placeholder="Cố định"
          min="0"
          max="100"
          step="0.1"
          class="field-input border-b-amber-500/30 text-sm font-mono tracking-wider w-full pr-12 text-amber-400 focus:border-amber-400"
        />
        <div class="field-line bg-amber-500/60"></div>
        <span class="absolute right-2 text-[9px] font-black text-amber-500/50"
          >%</span
        >
      </div>
    </div>

    <!-- AI Featured Toggle (Elite V2.2) -->
    <div class="field-group lg:col-span-1">
      <label class="field-label">Elite Integration</label>
      <button
        onclick={() => (formState.isAiFeatured = !formState.isAiFeatured)}
        class="flex items-center justify-between gap-3 px-4 py-3 bg-black/40 rounded-xl border transition-all duration-500 group/ai
          {formState.isAiFeatured
          ? 'border-[#00FFFF]/40 shadow-[0_0_15px_rgba(0,255,255,0.1)]'
          : 'border-white/5 grayscale opacity-50'}"
      >
        <div class="flex flex-col items-start gap-0.5">
          <span
            class="text-[8px] font-black tracking-tighter {formState.isAiFeatured
              ? 'text-[#00FFFF]'
              : 'text-gray-500'}">AI Featured v2.2</span
          >
          <span class="text-[7px] text-white/20 tracking-widest"
            >{formState.isAiFeatured ? "Enabled" : "Disabled"}</span
          >
        </div>
        <div
          class="relative w-8 h-4 bg-white/5 rounded-full p-0.5 transition-colors {formState.isAiFeatured
            ? 'bg-[#00FFFF]/20'
            : ''}"
        >
          <div
            class="w-3 h-3 rounded-full transition-all duration-500 {formState.isAiFeatured
              ? 'translate-x-4 bg-[#00FFFF]'
              : 'bg-[#666]'}"
          ></div>
        </div>
      </button>
    </div>
  </div>
</div>

<style>
  @reference "tailwindcss";

  .field-group {
    @apply flex flex-col gap-2;
  }
  .field-label {
    @apply flex items-center gap-2 text-[9px] font-black text-white/25 tracking-[0.25em];
  }
  .field-input {
    @apply w-full bg-transparent border-b border-white/8 px-1 py-1.5 text-white placeholder:text-white/15 outline-none transition-colors;
  }
  .field-select {
    @apply w-full bg-transparent border-b border-white/8 px-1 py-[7px] text-white text-sm outline-none cursor-pointer;
  }
  .field-line {
    @apply absolute bottom-0 left-0 w-0 h-[1px] bg-amber-500/60 transition-all duration-300;
  }
  :global(.field-group:focus-within .field-line) {
    @apply w-full;
  }

  /* ⚡ ELITE UI: Hide Browser Default Spin Buttons */
  input::-webkit-outer-spin-button,
  input::-webkit-inner-spin-button {
    -webkit-appearance: none;
    margin: 0;
  }
  input[type="number"] {
    -moz-appearance: textfield;
    appearance: textfield;
  }
</style>
