<script lang="ts">
  import { getClientUi } from "$lib/state/commerce/ui.svelte";
  import { fade, scale } from "svelte/transition";
  import { quintOut } from "svelte/easing";
  import { Z_INDEX_CLIENT } from "$lib/core/constants/zIndex";
  import { apiClient } from "$lib/utils/apiClient";
  import Flag from "@lucide/svelte/icons/flag";
  import X from "@lucide/svelte/icons/x";
  import Send from "@lucide/svelte/icons/send";
  import Loader2 from "@lucide/svelte/icons/loader-2";

  const ui = getClientUi();
  const modal = $derived(ui.reportModal);

  let reason = $state("");
  let details = $state("");
  let isSubmitting = $state(false);

  const reportReasons = [
    { id: 'SPAM', label: 'Spam / Quảng cáo', icon: '📢' },
    { id: 'OFFENSIVE', label: 'Ngôn từ xúc phạm', icon: '🤬' },
    { id: 'FAKE', label: 'Đánh giá giả mạo', icon: '🚫' },
    { id: 'INAPPROPRIATE', label: 'Hình ảnh nhạy cảm', icon: '🔞' },
    { id: 'OTHER', label: 'Lý do khác', icon: '❓' }
  ];

  async function handleSubmit() {
    if (!reason || !modal) return;
    isSubmitting = true;
    try {
      await apiClient.post(`/client/reviews/${modal.reviewId}/report`, { 
        reason: `${reason}: ${details}`.trim() 
      });
      ui.showToast('Báo cáo đã được gửi tới quản trị viên.', 'success');
      modal.onSuccess?.();
      ui.closeReportModal();
    } catch (e) {
      ui.showToast('Không thể gửi báo cáo, vui lòng thử lại.', 'error');
    } finally {
      isSubmitting = false;
    }
  }
</script>

{#if modal}
  <!-- svelte-ignore a11y_click_events_have_key_events -->
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div 
    class="fixed inset-0 bg-black/90 backdrop-blur-2xl transition-all z-[calc(var(--z-modal)-1)]"
    style="--z-modal: {Z_INDEX_CLIENT.MODAL || 50};"
    transition:fade={{ duration: 400 }}
    onclick={ui.closeReportModal}
  ></div>

  <div 
    class="fixed inset-0 flex items-center justify-center p-4 pointer-events-none z-[var(--z-modal)]"
    style="--z-modal: {Z_INDEX_CLIENT.MODAL || 50};"
  >
    <div 
      class="w-full max-w-lg bg-[#050505] border border-white/10 shadow-[0_0_100px_rgba(0,0,0,0.5)] pointer-events-auto overflow-hidden relative rounded-2xl"
      transition:scale={{ duration: 500, start: 0.9, easing: quintOut }}
    >
      <!-- Neural Gradient Glows -->
      <div class="absolute -top-40 -left-40 w-80 h-80 bg-red-600/10 rounded-full blur-[100px]"></div>
      <div class="absolute -bottom-40 -right-40 w-80 h-80 bg-orange-600/10 rounded-full blur-[100px]"></div>

      <!-- Close Button -->
      <button 
        onclick={ui.closeReportModal}
        class="absolute top-6 right-6 text-gray-500 hover:text-white transition-colors z-20"
      >
        <X size={20} />
      </button>

      <div class="relative z-10 p-10">
        <!-- Header -->
        <div class="flex items-center gap-4 mb-8">
          <div class="w-12 h-12 bg-red-500/10 border border-red-500/20 rounded-xl flex items-center justify-center">
            <Flag size={24} class="text-red-500" />
          </div>
          <div>
            <h3 class="text-xl font-bold text-white tracking-tight">Báo cáo vi phạm</h3>
            <p class="text-[10px] text-gray-400 mt-1 tracking-widest font-bold">Bảo vệ tính minh bạch của cộng đồng</p>
          </div>
        </div>

        <div class="space-y-6">
          <!-- Reason Selection -->
          <div class="grid grid-cols-2 gap-3">
            {#each reportReasons as r}
              <button 
                onclick={() => reason = r.label}
                class="flex items-center gap-3 p-4 rounded-xl border transition-all text-left group
                  {reason === r.label ? 'border-red-500 bg-red-500/5 text-white' : 'border-white/5 bg-white/[0.02] text-gray-400 hover:border-white/20 hover:text-gray-300'}"
              >
                <span class="text-xl">{r.icon}</span>
                <span class="text-[11px] font-bold tracking-wider">{r.label}</span>
              </button>
            {/each}
          </div>

          <!-- Details Input -->
          <div class="relative group">
            <div class="absolute -inset-0.5 bg-gradient-to-r from-red-500/0 to-orange-500/0 group-focus-within:from-red-500/20 group-focus-within:to-orange-500/20 rounded-xl transition duration-500"></div>
            <textarea 
              bind:value={details}
              placeholder="Cung cấp thêm chi tiết để chúng tôi xử lý nhanh hơn..."
              class="relative w-full h-32 bg-[#0a0a0a] border border-white/5 rounded-xl p-5 text-sm text-gray-200 placeholder:text-gray-600 focus:outline-none focus:border-red-500/50 transition-all resize-none"
            ></textarea>
          </div>

          <!-- Action -->
          <button 
            onclick={handleSubmit}
            disabled={!reason || isSubmitting}
            class="w-full group relative overflow-hidden py-5 bg-white text-black font-black text-xs tracking-[0.2em] rounded-xl transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:scale-100"
          >
            <div class="absolute inset-0 bg-gradient-to-r from-red-500 via-orange-500 to-red-500 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
            
            <div class="relative z-10 flex items-center justify-center gap-3 group-hover:text-white transition-colors duration-300">
              {#if isSubmitting}
                <Loader2 size={16} class="animate-spin" />
                Đang xử lý...
              {:else}
                <Send size={16} />
                GỬI BÁO CÁO NGAY
              {/if}
            </div>
          </button>
        </div>

        <div class="flex items-center justify-center gap-2 mt-8 opacity-60">
          <div class="w-1.5 h-1.5 bg-red-500 rounded-full animate-pulse"></div>
          <p class="text-[10px] text-gray-400 text-center font-bold tracking-widest ">
            osmo Intelligence // Đảm bảo mọi đánh giá đều trung thực
          </p>
        </div>
      </div>
    </div>
  </div>
{/if}

<style>
  div {
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }
</style>
