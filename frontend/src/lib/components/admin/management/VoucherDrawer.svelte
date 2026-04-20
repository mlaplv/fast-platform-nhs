<script lang="ts">
  import { fade, fly } from "svelte/transition";
  import X from "lucide-svelte/icons/x";
  import Gift from "lucide-svelte/icons/gift";
  import Save from "lucide-svelte/icons/save";
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

  let isLoading = $state(false);
  let isSaving = $state(false);

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
    subtitle: ""
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
          subtitle: voucher.subtitle || ""
        };
      }
    } catch (error: unknown) {
      nanobot.showToast("Không thể tải thông tin voucher", "error");
    } finally {
      isLoading = false;
    }
  }

  function resetForm() {
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
      subtitle: ""
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
        await apiClient.patch(`/api/v1/admin/vouchers/${voucherId}`, payload);
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
          <h2 class="text-sm font-bold text-white tracking-widest uppercase">{voucherId ? 'CHỈNH SỬA VOUCHER' : 'TẠO VOUCHER MỚI'}</h2>
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
            <label class="text-[10px] font-mono text-gray-500 uppercase tracking-widest" for="v-code">Mã Voucher</label>
            <input
              id="v-code"
              type="text"
              bind:value={form.id}
              placeholder="VD: SALE30K..."
              class="w-full bg-white/[0.03] border border-white/10 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-neon-cyan/50 text-sm font-bold tracking-widest uppercase disabled:opacity-50"
            />
          </div>

          <!-- Title & Subtitle -->
          <div class="grid grid-cols-2 gap-4">
            <div class="space-y-2">
              <label class="text-[10px] font-mono text-gray-500 uppercase tracking-widest" for="v-title">Tiêu đề (Hiển thị)</label>
              <input
                id="v-title"
                type="text"
                bind:value={form.title}
                placeholder="VD: Giảm 60K"
                class="w-full bg-white/[0.03] border border-white/10 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-neon-cyan/50 text-sm"
              />
            </div>
            <div class="space-y-2">
              <label class="text-[10px] font-mono text-gray-500 uppercase tracking-widest" for="v-subtitle">Mô tả phụ</label>
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
              <label class="text-[10px] font-mono text-gray-500 uppercase tracking-widest" for="v-type">Loại</label>
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
              <label class="text-[10px] font-mono text-gray-500 uppercase tracking-widest" for="v-value">Giá trị</label>
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
                <span class="block text-[11px] font-black text-emerald-400 tracking-widest uppercase">Thiết lập mặc định</span>
                <span class="text-[9px] text-gray-500 uppercase tracking-tighter">Elite Auto-Stick Engine</span>
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
                <label class="text-[10px] font-mono text-gray-500 uppercase tracking-widest" for="v-category">Phân loại (Tab)</label>
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
                <label class="text-[10px] font-mono text-gray-500 uppercase tracking-widest" for="v-priority">Độ ưu tiên</label>
                <input
                  id="v-priority"
                  type="number"
                  bind:value={form.priority}
                  class="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500/50 text-sm font-mono"
                />
              </div>
            </div>
          </div>

          <!-- Limits -->
          <div class="grid grid-cols-2 gap-4">
            <div class="space-y-2">
              <label class="text-[10px] font-mono text-gray-500 uppercase tracking-widest" for="v-limit">Giới hạn dùng</label>
              <input
                id="v-limit"
                type="number"
                bind:value={form.usage_limit}
                placeholder="Để trống = vô hạn"
                class="w-full bg-white/[0.03] border border-white/10 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-neon-cyan/50 text-sm font-mono"
              />
            </div>
            <div class="space-y-2">
              <label class="text-[10px] font-mono text-gray-500 uppercase tracking-widest" for="v-min">Đơn tối thiểu</label>
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
              <label class="text-[10px] font-mono text-gray-500 uppercase tracking-widest" for="v-start">Ngày bắt đầu</label>
              <input
                id="v-start"
                type="date"
                bind:value={form.start_date}
                class="w-full bg-white/[0.03] border border-white/10 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-neon-cyan/50 text-sm font-mono"
              />
            </div>
            <div class="space-y-2">
              <label class="text-[10px] font-mono text-gray-500 uppercase tracking-widest" for="v-end">Ngày kết thúc</label>
              <input
                id="v-end"
                type="date"
                bind:value={form.end_date}
                class="w-full bg-white/[0.03] border border-white/10 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-neon-cyan/50 text-sm font-mono"
              />
            </div>
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
          <span class="tracking-widest uppercase">LƯU CẤU HÌNH</span>
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
