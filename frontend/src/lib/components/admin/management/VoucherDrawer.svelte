<script lang="ts">
  import { fade, fly } from "svelte/transition";
  import X from "@lucide/svelte/icons/x";
  import Gift from "@lucide/svelte/icons/gift";
  import Save from "@lucide/svelte/icons/save";
  import { apiClient } from "$lib/utils/apiClient";
  import { useNanobot } from "$lib/state/nanobot.svelte";
  const nanobot = useNanobot();

  import type { Voucher } from "$lib/types";

  let { 
    voucherId = null, 
    isOpen = $bindable(false), 
    onSaved = () => {} 
  } = $props<{
    voucherId: string | null;
    isOpen: boolean;
    onSaved: () => void;
  }>();

  import type { Product } from "$lib/types";
  import { formatCurrency } from "$lib/utils/format";

  let isLoading = $state(false);
  let isSaving = $state(false);

  // Dynamic Product Search State
  let searchQuery = $state("");
  let searchResults = $state<Product[]>([]);
  let isSearchingProducts = $state(false);
  let searchTimeout = null as any;

  let form = $state({
    id: "",
    type: "FIXED",
    value: 0,
    min_spend: 0,
    max_discount: null as number | null,
    usage_limit: null as number | null,
    start_date: "",
    end_date: "",
    is_active: true,
    category: "",
    is_default: false,
    priority: 0,
    title: "",
    subtitle: "",
    is_viral: false,
    metadata_json: {
      applicable_product_ids: [] as string[],
      applicable_product_display: [] as string[],
      viral_suite: {
        enabled: true, // Internal flag for the engine section, but is_viral is the master
        share_target: 1000,
        voucher_label: "",
        cta_text: "",
        share_text: ""
      }
    }
  });

  // [ELITE V2.2] Auto-Sync Category selection with Voucher Type
  $effect(() => {
    if (form.type === 'SHIPPING' && (form.category === '' || form.category === 'DISCOUNT')) {
      form.category = 'SHIPPING';
    } else if (['FIXED', 'PERCENT'].includes(form.type) && (form.category === '' || form.category === 'SHIPPING')) {
      form.category = 'DISCOUNT';
    }
  });

  $effect(() => {
    if (isOpen) {
      if (voucherId) {
        loadVoucher();
      } else {
        resetForm();
      }
    }
  });

  function handleSearchInput(e: Event) {
    const input = e.target as HTMLInputElement;
    const query = input.value;
    
    if (searchTimeout) {
      clearTimeout(searchTimeout);
    }
    
    if (!query.trim()) {
      searchResults = [];
      return;
    }
    
    searchTimeout = setTimeout(async () => {
      isSearchingProducts = true;
      try {
        const res = await apiClient.get<{ data: Product[] }>(`/api/v1/products?search=${encodeURIComponent(query)}&limit=10`);
        searchResults = res.data || [];
      } catch (err) {
        console.error("Lỗi khi tìm kiếm sản phẩm", err);
      } finally {
        isSearchingProducts = false;
      }
    }, 250);
  }

  function selectProduct(prod: Product) {
    if (!form.metadata_json.applicable_product_ids) {
      form.metadata_json.applicable_product_ids = [];
    }
    if (!form.metadata_json.applicable_product_display) {
      form.metadata_json.applicable_product_display = [];
    }
    
    if (form.metadata_json.applicable_product_ids.includes(prod.id)) {
      nanobot.showToast("Sản phẩm này đã được chọn", "info");
      return;
    }
    
    form.metadata_json.applicable_product_ids.push(prod.id);
    form.metadata_json.applicable_product_display.push(`${prod.name} (${prod.slug})`);
    
    // Clear search query and results after selection
    searchQuery = "";
    searchResults = [];
  }

  function removeProduct(index: number) {
    form.metadata_json.applicable_product_ids.splice(index, 1);
    form.metadata_json.applicable_product_display.splice(index, 1);
  }

  async function loadVoucher() {
    isLoading = true;
    try {
      const res = await apiClient.get<{ data: Voucher[] }>(`/api/v1/admin/vouchers`);
      const voucher = res.data.find((v: Voucher) => v.id === voucherId);
      if (voucher) {
        form = {
          id: voucher.id,
          type: voucher.type,
          value: voucher.value,
          min_spend: voucher.min_spend,
          max_discount: voucher.max_discount,
          usage_limit: voucher.usage_limit,
          start_date: voucher.start_date ? voucher.start_date.split('T')[0] : "",
          end_date: voucher.end_date ? voucher.end_date.split('T')[0] : "",
          is_active: voucher.is_active,
          category: voucher.category || "DISCOUNT",
          is_default: voucher.is_default || false,
          priority: voucher.priority || 0,
          title: voucher.title || "",
          subtitle: voucher.subtitle || "",
          is_viral: voucher.is_viral || false,
          metadata_json: {
            applicable_product_ids: voucher.metadata_json?.applicable_product_ids || [],
            applicable_product_display: voucher.metadata_json?.applicable_product_display || [],
            viral_suite: {
              enabled: false,
              share_target: 1000,
              voucher_label: "",
              cta_text: "",
              share_text: "",
              ...(voucher.metadata_json?.viral_suite || {})
            }
          }
        };
      }
    } catch (error: unknown) {
      nanobot.showToast("Không thể tải thông tin voucher", "error");
    } finally {
      isLoading = false;
    }
  }

  function resetForm() {
    searchQuery = "";
    searchResults = [];
    form = {
      id: "",
      type: "FIXED",
      value: 0,
      min_spend: 0,
      max_discount: null,
      usage_limit: null,
      start_date: "",
      end_date: "",
      is_active: true,
      category: "",
      is_default: false,
      priority: 0,
      title: "",
      subtitle: "",
      is_viral: false,
      metadata_json: {
        applicable_product_ids: [],
        applicable_product_display: [],
        viral_suite: {
          enabled: true,
          share_target: 1000,
          voucher_label: "",
          cta_text: "",
          share_text: ""
        }
      }
    };
  }


  async function handleSave() {
    isSaving = true;
    try {
      const payload: Record<string, unknown> = { ...form };
      // [ELITE V2.2] Strict Payload Sanitization for Pydantic Compatibility
      payload.start_date = payload.start_date ? new Date(payload.start_date as string).toISOString() : null;
      payload.end_date = payload.end_date ? new Date(payload.end_date as string).toISOString() : null;
      
      // Handle empty numeric strings
      if (payload.max_discount === "" || payload.max_discount === undefined) payload.max_discount = null;
      if (payload.usage_limit === "" || payload.usage_limit === undefined) payload.usage_limit = null;
      if (payload.min_spend === "" || payload.min_spend === undefined) payload.min_spend = 0;
      if (payload.value === "" || payload.value === undefined) payload.value = 0;
      if (payload.priority === "" || payload.priority === undefined) payload.priority = 0;
      
      if (voucherId) {
        // Update (ID is now editable)
        await apiClient.patch(`/api/v1/admin/vouchers/${encodeURIComponent(voucherId)}`, payload);
        nanobot.showToast(`Đã cập nhật voucher ${payload.id}`, "success");
      } else {
        // Create
        await apiClient.post(`/api/v1/admin/vouchers`, payload);
        nanobot.showToast(`Đã tạo voucher ${payload.id}`, "success");
      }
      onSaved();
      isOpen = false;
    } catch (error: unknown) {
      const msg = error instanceof Error ? error.message : "Lỗi khi lưu voucher";
      nanobot.showToast(msg, "error");
    } finally {
      isSaving = false;
    }
  }
</script>

{#if isOpen}
  <!-- Backdrop -->
  <div
    class="fixed inset-0 bg-black/60 backdrop-blur-sm z-[2000]"
    transition:fade={{ duration: 300 }}
    onclick={() => (isOpen = false)}
    onkeydown={(e) => e.key === "Escape" && (isOpen = false)}
    role="button"
    tabindex="0"
    aria-label="Close Drawer"
  ></div>

  <!-- Drawer Shell -->
  <div
    class="fixed top-0 right-0 h-full w-full max-w-lg bg-[#050505] border-l border-white/5 shadow-2xl z-[2001] flex flex-col overflow-hidden"
    transition:fly={{ x: 500, duration: 400, opacity: 1 }}
  >
    <!-- Header -->
    <div class="px-6 py-5 border-b border-white/5 flex items-center justify-between bg-white/[0.02]">
      <div class="flex items-center gap-3">
        <div class="p-2 bg-neon-cyan/10 rounded-lg">
          <Gift size={18} class="text-neon-cyan" />
        </div>
        <div>
          <h2 class="text-sm font-bold text-white tracking-widest ">{voucherId ? 'Chỉnh sửa VOUCHER' : 'TẠO VOUCHER MỚI'}</h2>
          <p class="text-[10px] text-gray-500 font-mono tracking-wider">{voucherId || 'Elite V2.2 Promotion Engine'}</p>
        </div>
      </div>
      <button
        onclick={() => (isOpen = false)}
        class="p-2 hover:bg-white/5 rounded-full transition-colors text-gray-400 hover:text-white"
      >
        <X size={20} />
      </button>
    </div>

    <!-- Body -->
    <div class="flex-1 overflow-y-auto p-6 custom-scrollbar">
      {#if isLoading}
        <div class="h-full flex flex-col items-center justify-center gap-4">
          <div class="w-8 h-8 border-2 border-neon-cyan/20 border-t-neon-cyan rounded-full animate-spin"></div>
          <span class="text-[10px] font-mono text-neon-cyan/40">FETCHING_DATA...</span>
        </div>
      {:else}
        <div class="space-y-6">
          <!-- Code Section -->
          <div class="space-y-2">
            <label class="text-[10px] font-mono text-gray-500 tracking-widest" for="v-code">Mã Voucher</label>
            <input
              id="v-code"
              type="text"
              bind:value={form.id}
              placeholder="VD: SALE30K..."
              class="w-full bg-white/[0.03] border border-white/10 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-neon-cyan/50 text-sm font-bold tracking-widest disabled:opacity-50"
            />
          </div>

          <!-- Title & Subtitle -->
          <div class="grid grid-cols-2 gap-4">
            <div class="space-y-2">
              <label class="text-[10px] font-mono text-gray-500 tracking-widest" for="v-title">Tiêu đề (Hiển thị)</label>
              <input
                id="v-title"
                type="text"
                bind:value={form.title}
                placeholder="VD: Giảm 60K"
                class="w-full bg-white/[0.03] border border-white/10 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-neon-cyan/50 text-sm"
              />
            </div>
            <div class="space-y-2">
              <label class="text-[10px] font-mono text-gray-500 tracking-widest" for="v-subtitle">Mô tả phụ</label>
              <input
                id="v-subtitle"
                type="text"
                bind:value={form.subtitle}
                placeholder="VD: Cho đơn từ 200K"
                class="w-full bg-white/[0.03] border border-white/10 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-neon-cyan/50 text-sm"
              />
            </div>
          </div>

          <!-- Type & Value -->
          <div class="grid grid-cols-2 gap-4">
            <div class="space-y-2">
              <label class="text-[10px] font-mono text-gray-500 tracking-widest" for="v-type">Loại</label>
              <select
                id="v-type"
                bind:value={form.type}
                class="w-full bg-white/[0.03] border border-white/10 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-neon-cyan/50 text-sm"
              >
                <option value="FIXED" class="bg-[#050505]">Số tiền cố định (đ)</option>
                <option value="PERCENT" class="bg-[#050505]">Phần trăm (%)</option>
                <option value="SHIPPING" class="bg-[#050505]">Phí vận chuyển (đ)</option>
              </select>
            </div>
            <div class="space-y-2">
              <label class="text-[10px] font-mono text-gray-500 tracking-widest" for="v-value">Giá trị</label>
              <input
                id="v-value"
                type="number"
                bind:value={form.value}
                class="w-full bg-white/[0.03] border border-white/10 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-neon-cyan/50 text-sm font-mono"
              />
            </div>
          </div>

          <!-- Elite V2.2: Category, Priority & Default (Promoted to Top) -->
          <div class="p-4 bg-emerald-500/5 border border-emerald-500/10 rounded-xl space-y-4">
            <div class="flex items-center justify-between">
              <div>
                <span class="block text-[11px] font-black text-emerald-400 tracking-widest ">Thiết lập mặc định</span>
                <span class="text-[9px] text-gray-500 tracking-tighter">Elite Auto-Stick Engine</span>
              </div>
              <button
                onclick={() => (form.is_default = !form.is_default)}
                class="w-12 h-6 rounded-full transition-all relative {form.is_default ? 'bg-emerald-500 shadow-[0_0_15px_rgba(16,185,129,0.3)]' : 'bg-gray-800'}"
                aria-label="Toggle default status"
                role="switch"
                aria-checked={form.is_default}
              >
                <div class="absolute top-1 w-4 h-4 bg-white rounded-full transition-all {form.is_default ? 'left-7' : 'left-1'}"></div>
              </button>
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div class="space-y-2">
                <label class="text-[10px] font-mono text-gray-500 tracking-widest" for="v-category">Phân loại (Tab)</label>
                <select
                  id="v-category"
                  bind:value={form.category}
                  class="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500/50 text-sm"
                >
                  <option value="" disabled class="bg-[#050505]">--- Chọn phân loại ---</option>
                  <option value="DISCOUNT" class="bg-[#050505]">Giảm giá (Discount)</option>
                  <option value="SHIPPING" class="bg-[#050505]">Vận chuyển (Shipping)</option>
                  <option value="GIFT" class="bg-[#050505]">Quà tặng (Gift)</option>
                </select>
              </div>
              <div class="space-y-2">
                <label class="text-[10px] font-mono text-gray-500 tracking-widest" for="v-priority">Độ ưu tiên</label>
                <input
                  id="v-priority"
                  type="number"
                  bind:value={form.priority}
                  class="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500/50 text-sm font-mono"
                />
              </div>
            </div>
          </div>

          <!-- Phạm vi áp dụng (Product Scope Filter) -->
          <div class="space-y-3 p-4 bg-white/[0.02] border border-white/5 rounded-xl">
            <div class="flex items-center justify-between">
              <span class="text-[10px] font-black text-neon-cyan tracking-widest uppercase">Phạm vi áp dụng</span>
              <span class="text-[9px] text-gray-500 font-mono">Elite Scope Filter</span>
            </div>

            <div class="relative">
              <input
                type="text"
                placeholder="Gõ tìm kiếm theo tên, slug hoặc ID sản phẩm..."
                bind:value={searchQuery}
                oninput={handleSearchInput}
                class="w-full bg-[#050505] border border-white/10 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-neon-cyan/50 text-xs"
              />
              
              {#if isSearchingProducts}
                <div class="absolute right-3 top-3 w-4 h-4 border border-neon-cyan/20 border-t-neon-cyan rounded-full animate-spin"></div>
              {/if}

              <!-- Search Results Dropdown -->
              {#if searchResults.length > 0}
                <div class="absolute left-0 right-0 mt-1 bg-[#090909] border border-white/10 rounded-xl shadow-2xl z-[2005] max-h-60 overflow-y-auto custom-scrollbar">
                  {#each searchResults as prod}
                    <button
                      type="button"
                      onclick={() => selectProduct(prod)}
                      class="w-full text-left px-4 py-3 hover:bg-white/[0.03] border-b border-white/5 flex items-center gap-3 transition-colors animate-fade-in"
                    >
                      {#if prod.images?.length}
                        <img src={prod.images[0]} alt={prod.name} class="w-8 h-8 rounded object-cover" />
                      {/if}
                      <div class="flex-1 min-w-0">
                        <span class="block text-xs font-bold text-white truncate">{prod.name}</span>
                        <span class="block text-[10px] text-gray-500 font-mono truncate">{prod.slug} | {prod.id.slice(0,8)}...</span>
                      </div>
                      <span class="text-xs font-black text-neon-cyan">{formatCurrency(prod.price)}</span>
                    </button>
                  {/each}
                </div>
              {/if}
            </div>

            <!-- Selected Products Display Tags -->
            <div class="space-y-2">
              {#if form.metadata_json.applicable_product_ids && form.metadata_json.applicable_product_ids.length > 0}
                <span class="block text-[9px] text-gray-500 font-mono tracking-wider">Sản phẩm đã liên kết ({form.metadata_json.applicable_product_ids.length}):</span>
                <div class="flex flex-wrap gap-2">
                  {#each form.metadata_json.applicable_product_ids as id, index}
                    <div class="flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 px-2.5 py-1 rounded-lg text-xs font-medium">
                      <span>{form.metadata_json.applicable_product_display[index] || id}</span>
                      <button
                        type="button"
                        onclick={() => removeProduct(index)}
                        class="hover:text-red-400 transition-colors"
                        aria-label="Remove Product"
                      >
                        ×
                      </button>
                    </div>
                  {/each}
                </div>
              {:else}
                <div class="py-2 px-3 bg-emerald-500/5 border border-emerald-500/10 rounded-lg text-center">
                  <span class="text-[10px] font-bold text-emerald-400 tracking-wider">✓ ÁP DỤNG TOÀN SÀN (Mặc định cho tất cả sản phẩm)</span>
                </div>
              {/if}
            </div>
          </div>

          <!-- Limits -->

          <div class="grid grid-cols-2 gap-4">
            <div class="space-y-2">
              <label class="text-[10px] font-mono text-gray-500 tracking-widest" for="v-limit">Giới hạn dùng</label>
              <input
                id="v-limit"
                type="number"
                bind:value={form.usage_limit}
                placeholder="Để trống = vô hạn"
                class="w-full bg-white/[0.03] border border-white/10 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-neon-cyan/50 text-sm font-mono"
              />
            </div>
            <div class="space-y-2">
              <label class="text-[10px] font-mono text-gray-500 tracking-widest" for="v-min">Đơn tối thiểu</label>
              <input
                id="v-min"
                type="number"
                bind:value={form.min_spend}
                class="w-full bg-white/[0.03] border border-white/10 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-neon-cyan/50 text-sm font-mono"
              />
            </div>
          </div>

          <!-- Dates -->
          <div class="grid grid-cols-2 gap-4">
            <div class="space-y-2">
              <label class="text-[10px] font-mono text-gray-500 tracking-widest" for="v-start">Ngày bắt đầu</label>
              <input
                id="v-start"
                type="date"
                bind:value={form.start_date}
                class="w-full bg-white/[0.03] border border-white/10 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-neon-cyan/50 text-sm font-mono"
              />
            </div>
            <div class="space-y-2">
              <label class="text-[10px] font-mono text-gray-500 tracking-widest" for="v-end">Ngày kết thúc</label>
              <input
                id="v-end"
                type="date"
                bind:value={form.end_date}
                class="w-full bg-white/[0.03] border border-white/10 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-neon-cyan/50 text-sm font-mono"
              />
            </div>
          </div>

          <!-- Viral Configuration (Elite V2.2) -->
          <div class="p-5 bg-pink-500/5 border border-pink-500/10 rounded-2xl space-y-5">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-lg bg-pink-500/10 flex items-center justify-center">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-pink-500"><path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/><polyline points="16 6 12 2 8 6"/><line x1="12" y1="2" x2="12" y2="15"/></svg>
                </div>
                <div>
                  <span class="block text-[11px] font-black text-pink-400 tracking-[0.2em] ">Chiến dịch Lan tỏa</span>
                  <span class="text-[9px] text-gray-500 tracking-tighter">Elite Viral Engine 2026</span>
                </div>
              </div>
              <button
                onclick={() => {
                  if (!form.is_viral && !confirm("Kích hoạt mã này làm Voucher Viral DUY NHẤT toàn sàn? Các mã Viral cũ sẽ bị hủy kích hoạt.")) return;
                  form.is_viral = !form.is_viral;
                }}
                class="w-12 h-6 rounded-full transition-all relative {form.is_viral ? 'bg-pink-500 shadow-[0_0_15px_rgba(236,72,153,0.3)]' : 'bg-gray-800'}"
                role="switch"
                aria-checked={form.is_viral}
              >
                <div class="absolute top-1 w-4 h-4 bg-white rounded-full transition-all {form.is_viral ? 'left-7' : 'left-1'}"></div>
              </button>
            </div>

            {#if form.is_viral}
              <div class="space-y-4 animate-in fade-in slide-in-from-top-2 duration-300">
                <div class="grid grid-cols-2 gap-4">
                  <div class="space-y-2">
                    <label class="text-[10px] font-mono text-gray-500 tracking-widest">Mục tiêu (Share)</label>
                    <input
                      type="number"
                      bind:value={form.metadata_json.viral_suite.share_target}
                      class="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-pink-500/50 text-sm font-mono"
                    />
                  </div>
                  <div class="space-y-2">
                    <label class="text-[10px] font-mono text-gray-500 tracking-widest">Nhãn phần thưởng</label>
                    <input
                      type="text"
                      bind:value={form.metadata_json.viral_suite.voucher_label}
                      placeholder="VD: Giảm 50.000₫"
                      class="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-pink-500/50 text-sm"
                    />
                  </div>
                </div>

                <div class="space-y-2">
                  <label class="text-[10px] font-mono text-gray-500 tracking-widest">Nút hành động (CTA)</label>
                  <input
                    type="text"
                    bind:value={form.metadata_json.viral_suite.cta_text}
                    placeholder="VD: Chia sẻ để nhận mã"
                    class="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-pink-500/50 text-sm"
                  />
                </div>

                <div class="space-y-2">
                  <label class="text-[10px] font-mono text-gray-500 tracking-widest">Nội dung chia sẻ (Mồi)</label>
                  <textarea
                    bind:value={form.metadata_json.viral_suite.share_text}
                    placeholder="Nội dung khách sẽ share lên MXH..."
                    rows="3"
                    class="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-pink-500/50 text-sm custom-scrollbar"
                  ></textarea>
                </div>
              </div>
            {/if}
          </div>

          <!-- Status Toggle -->
          <div class="pt-4 flex items-center justify-between border-t border-white/5">
            <div>
              <span class="block text-sm font-bold text-gray-200">Kích hoạt Voucher</span>
              <span class="text-[10px] text-gray-500">Người dùng có thể áp dụng mã này khi thanh toán</span>
            </div>
            <button
              onclick={() => (form.is_active = !form.is_active)}
              class="w-12 h-6 rounded-full transition-all relative {form.is_active ? 'bg-neon-cyan shadow-[0_0_15px_rgba(0,243,255,0.3)]' : 'bg-gray-800'}"
              aria-label="Toggle active status"
              role="switch"
              aria-checked={form.is_active}
            >
              <div
                class="absolute top-1 w-4 h-4 bg-white rounded-full transition-all {form.is_active ? 'left-7' : 'left-1'}"
              ></div>
            </button>
          </div>
        </div>
      {/if}
    </div>

    <!-- Footer -->
    <div class="p-6 border-t border-white/5 bg-white/[0.01]">
      <button
        onclick={handleSave}
        disabled={isSaving || !form.id}
        class="w-full bg-neon-cyan text-black font-black py-4 rounded-xl flex items-center justify-center gap-3 hover:brightness-110 active:scale-[0.98] transition-all disabled:opacity-50"
      >
        {#if isSaving}
          <div class="w-5 h-5 border-2 border-black/20 border-t-black rounded-full animate-spin"></div>
        {:else}
          <Save size={18} />
          <span class="tracking-widest ">LƯU CẤU HÌNH</span>
        {/if}
      </button>
    </div>
  </div>
{/if}

<style>
  .custom-scrollbar::-webkit-scrollbar {
    width: 4px;
  }
  .custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 4px;
  }
</style>
