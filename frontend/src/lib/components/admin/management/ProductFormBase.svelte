<script lang="ts">
  import ChevronDown from "lucide-svelte/icons/chevron-down";

  let {
    editingId,
    formName = $bindable(),
    formSku = $bindable(),
    formPrice = $bindable(),
    formStock = $bindable(),
    formCategory = $bindable(),
    formStatus = $bindable(),
    categories,
    generateSlug,
    onNameInput,
    errors,
  } = $props<{
    editingId: string | null;
    formName: string;
    formSku: string;
    formPrice: number;
    formStock: number;
    formCategory: string;
    formStatus: "active" | "draft" | "archived";
    categories: { id: string; name: string }[];
    generateSlug: (name: string) => string;
    onNameInput: () => void;
    errors?: Record<string, string>;
  }>();
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
        bind:value={formName}
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

  <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
    <!-- Mã SKU -->
    <div class="field-group">
      <label class="field-label">Mã SKU</label>
      <div class="relative">
        <input
          type="text"
          bind:value={formSku}
          placeholder="SKU-XXXX..."
          class="field-input border-b-amber-500/30 font-mono text-sm text-amber-400 uppercase tracking-wider"
        />
        <div class="field-line bg-amber-500/60"></div>
      </div>
    </div>

    <!-- Phân loại -->
    <div class="field-group">
      <label class="field-label">Danh mục kết nối</label>
      <div class="relative">
        <select 
          value={formCategory} 
          onchange={(e) => formCategory = e.currentTarget.value}
          class="field-select border border-white/8 appearance-none bg-black/40"
        >
          <option value="" class="bg-[#0f0f0f]">Chưa phân loại</option>
          {#each categories as c}
            <option value={c.id} selected={c.id === formCategory} class="bg-[#0f0f0f]">{c.name}</option>
          {/each}
        </select>
        <div class="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-white/20">
          <ChevronDown size={13} />
        </div>
      </div>
    </div>
  </div>

  <div class="grid grid-cols-1 md:grid-cols-3 gap-5">
    <!-- Giá bán -->
    <div class="field-group">
      <label class="field-label">Giá bán</label>
      <div class="relative flex items-center">
        <input
          type="number"
          bind:value={formPrice}
          placeholder="0"
          class="field-input border-b-amber-500/30 text-sm font-mono tracking-wider w-full pr-8"
        />
        <div class="field-line bg-amber-500/60"></div>
        <span class="absolute right-2 text-[9px] font-black uppercase text-amber-500/50">VND</span>
      </div>
    </div>

    <!-- Tồn kho -->
    <div class="field-group">
      <label class="field-label">Kho lưu trữ</label>
      <div class="relative flex items-center">
        <input
          type="number"
          bind:value={formStock}
          placeholder="0"
          class="field-input border-b-amber-500/30 text-sm font-mono tracking-wider w-full pr-8"
        />
        <div class="field-line bg-amber-500/60"></div>
        <span class="absolute right-2 text-[9px] font-black uppercase text-amber-500/50">Unit</span>
      </div>
    </div>

    <!-- Trạng thái -->
    <div class="field-group">
      <label class="field-label">Trạng thái vận hành</label>
      <div class="flex items-center gap-1 p-0.5 bg-black/40 rounded-xl border border-white/5 h-full">
        {#each [['active','H.Động'], ['draft','Thảo'], ['archived','Lưu']] as [val, lbl]}
           <button
             onclick={() => formStatus = val as "active"|"draft"|"archived"}
             class="flex-1 h-full flex items-center justify-center text-[8px] font-black uppercase tracking-tight rounded-lg
               {formStatus === val ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30 shadow-inner' : 'text-gray-600 hover:text-white border border-transparent'}"
           >{lbl}</button>
        {/each}
      </div>
    </div>
  </div>
</div>

<style>
  @reference "tailwindcss";
  
  .field-group { @apply flex flex-col gap-2; }
  .field-label { @apply flex items-center gap-2 text-[9px] font-black text-white/25 uppercase tracking-[0.25em]; }
  .field-input { @apply w-full bg-transparent border-b border-white/8 px-1 py-1.5 text-white placeholder:text-white/15 outline-none transition-colors; }
  .field-select { @apply w-full bg-transparent border-b border-white/8 px-1 py-[7px] text-white text-sm outline-none cursor-pointer; }
  .field-line { @apply absolute bottom-0 left-0 w-0 h-[1px] bg-amber-500/60 transition-all duration-300; }
  :global(.field-group:focus-within .field-line) { @apply w-full; }
</style>
