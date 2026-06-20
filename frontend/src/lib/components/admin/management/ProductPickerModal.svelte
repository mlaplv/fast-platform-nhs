<script lang="ts">
  import { untrack } from "svelte";
  import Search from "@lucide/svelte/icons/search";
  import X from "@lucide/svelte/icons/x";
  import Check from "@lucide/svelte/icons/check";
  import Package from "@lucide/svelte/icons/package";
  import { apiClient } from "$lib/utils/apiClient";
  import { resolveMediaUrl } from "$lib/state/utils";
  import { Z_INDEX_ADMIN } from "$lib/core/constants/z_index_admin";
  import type { Product } from "$lib/types";

  let {
    isOpen = false,
    selectedProductId = $bindable(),
    onClose,
    onSelect,
  } = $props<{
    isOpen: boolean;
    selectedProductId: string | null;
    onClose: () => void;
    onSelect: (product: { id: string; name: string; image: string | null }) => void;
  }>();

  let products = $state<Product[]>([]);
  let isLoading = $state(false);
  let searchQuery = $state("");
  let searchTimer: ReturnType<typeof setTimeout> | undefined;

  async function loadProducts(search: string = "") {
    isLoading = true;
    try {
      const params = new URLSearchParams({ limit: "50", status: "ACTIVE" });
      if (search.trim()) params.append("search", search.trim());
      const res = await apiClient.get<{ data: Product[]; total: number }>(`/api/v1/products?${params.toString()}`);
      products = res.data;
    } catch {
      products = [];
    } finally {
      isLoading = false;
    }
  }

  function handleSearchInput(e: Event) {
    const val = (e.target as HTMLInputElement).value;
    searchQuery = val;
    if (searchTimer) clearTimeout(searchTimer);
    searchTimer = setTimeout(() => loadProducts(val), 400);
  }

  function selectProduct(p: Product) {
    const image = p.images?.[0] || null;
    onSelect({ id: p.id, name: p.name, image });
  }

  function formatPrice(price: number): string {
    return new Intl.NumberFormat("vi-VN").format(price) + "₫";
  }

  // Load products khi modal mở
  $effect(() => {
    if (isOpen) {
      untrack(() => {
        searchQuery = "";
        loadProducts();
      });
    }
  });
</script>

{#if isOpen}
  <!-- Overlay -->
  <div
    class="fixed inset-0 flex items-center justify-center p-4"
    style="z-index: {Z_INDEX_ADMIN.MODAL + 10}; background: rgba(0,0,0,0.7); backdrop-filter: blur(8px);"
    role="dialog"
  >
    <!-- Modal -->
    <div class="w-full max-w-lg bg-[#0a0a0a] border border-white/10 rounded-2xl shadow-[0_20px_60px_rgba(0,0,0,0.8)] flex flex-col max-h-[80vh] overflow-hidden">
      
      <!-- Header -->
      <div class="flex items-center justify-between px-5 py-4 border-b border-white/5">
        <div class="flex items-center gap-2">
          <Package size={14} class="text-cyan-400/60" />
          <span class="text-[10px] font-black tracking-[0.3em] text-white/40">CHỌN SẢN PHẨM</span>
        </div>
        <button
          onclick={onClose}
          class="p-1.5 text-white/30 hover:text-white hover:bg-white/5 rounded-lg transition-all cursor-pointer"
        ><X size={14} /></button>
      </div>

      <!-- Search -->
      <div class="px-5 py-3 border-b border-white/5">
        <div class="relative">
          <Search size={13} class="absolute left-3 top-1/2 -translate-y-1/2 text-white/20" />
          <input
            type="text"
            value={searchQuery}
            oninput={handleSearchInput}
            placeholder="Tìm sản phẩm theo tên..."
            class="w-full bg-white/[0.03] border border-white/8 rounded-xl pl-9 pr-3 py-2.5 text-sm text-white/70 placeholder:text-white/15 outline-none focus:border-cyan-500/40 transition-colors"
          />
        </div>
      </div>

      <!-- Product List -->
      <div class="flex-1 overflow-y-auto custom-scrollbar px-2 py-2">
        {#if isLoading}
          <div class="flex items-center justify-center py-12">
            <div class="w-4 h-4 border-2 border-cyan-400/30 border-t-cyan-400 rounded-full animate-spin"></div>
            <span class="ml-3 text-[9px] font-black tracking-widest text-white/20">Đang tải...</span>
          </div>
        {:else if products.length === 0}
          <div class="text-center py-12">
            <p class="text-[10px] text-white/20 tracking-widest font-black">Không tìm thấy sản phẩm</p>
          </div>
        {:else}
          {#each products as product (product.id)}
            {@const isSelected = selectedProductId === product.id}
            <button
              onclick={() => selectProduct(product)}
              class="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all cursor-pointer mb-1
                {isSelected 
                  ? 'bg-cyan-500/10 border border-cyan-500/30' 
                  : 'hover:bg-white/[0.03] border border-transparent'}"
            >
              <!-- Product Image -->
              <div class="w-10 h-10 rounded-lg overflow-hidden bg-white/5 shrink-0 border border-white/5">
                {#if product.images?.[0]}
                  <img
                    src={resolveMediaUrl(product.images[0])}
                    alt={product.name}
                    class="w-full h-full object-cover"
                    loading="lazy"
                  />
                {:else}
                  <div class="w-full h-full flex items-center justify-center">
                    <Package size={14} class="text-white/10" />
                  </div>
                {/if}
              </div>

              <!-- Product Info -->
              <div class="flex-1 text-left min-w-0">
                <div class="text-sm text-white/80 truncate font-medium">{product.name}</div>
                <div class="flex items-center gap-2 mt-0.5">
                  {#if product.discountPrice || product.discount_price}
                    <span class="text-[10px] text-cyan-400 font-bold">{formatPrice((product.discountPrice || product.discount_price) as number)}</span>
                    <span class="text-[9px] text-white/20 line-through">{formatPrice(product.price)}</span>
                  {:else}
                    <span class="text-[10px] text-white/40 font-bold">{formatPrice(product.price)}</span>
                  {/if}
                </div>
              </div>

              <!-- Selection Indicator -->
              {#if isSelected}
                <div class="w-6 h-6 rounded-full bg-cyan-500 flex items-center justify-center shrink-0">
                  <Check size={12} class="text-black" />
                </div>
              {/if}
            </button>
          {/each}
        {/if}
      </div>

      <!-- Footer -->
      <div class="px-5 py-3 border-t border-white/5 flex items-center justify-between">
        <span class="text-[8px] text-white/15 font-black tracking-widest">{products.length} sản phẩm</span>
        <button
          onclick={onClose}
          class="px-4 py-1.5 bg-white/5 border border-white/10 rounded-lg text-[9px] font-black tracking-wider text-white/40 hover:text-white hover:bg-white/10 transition-all cursor-pointer"
        >Đóng</button>
      </div>
    </div>
  </div>
{/if}

<style>
  @reference "tailwindcss";

  .custom-scrollbar::-webkit-scrollbar { width: 4px; }
  .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
  .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.05); border-radius: 10px; }
  .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(6, 182, 212, 0.2); }
</style>
