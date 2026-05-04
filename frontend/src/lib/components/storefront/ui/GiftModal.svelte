<script lang="ts">
  import { portal } from '$lib/core/actions/portal';
  import { fade, fly, scale } from 'svelte/transition';
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import { getCartStore } from '$lib/state/commerce/cart.svelte.ts';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/zIndex';
  import ViralDatePicker from './ViralDatePicker.svelte';

  // 🚀 ELITE HYBRID INTERFACE (Context-First, Prop-Fallback)
  let { 
    isOpen = $bindable<boolean | undefined>(undefined),
    onClose
  } = $props();

  const shopStore = getShopStore();
  const cartStore = getCartStore();

  // Smart Discovery: Which store are we syncing with?
  const activeStore = $derived(shopStore || cartStore);
  
  // Visibility Logic: Store-controlled OR Prop-controlled
  const showModal = $derived(isOpen !== undefined ? isOpen : activeStore?.isGiftModalOpen);

  const giftPresets = [
    { label: "Sinh nhật", text: "Chúc mừng sinh nhật! Chúc bạn luôn xinh đẹp và hạnh phúc rạng ngời. ❤️" },
    { label: "Tặng Vợ", text: "Tặng vợ yêu món quà bất ngờ. Cảm ơn em đã luôn đồng hành cùng anh! 😘" },
    { label: "Kỷ niệm", text: "Mừng ngày kỷ niệm của chúng ta. Yêu em nhiều hơn mỗi ngày. 🥂" },
    { label: "Xin lỗi", text: "Đừng giận anh nữa nhé, món quà nhỏ thay lời muốn nói. 💐" }
  ];

  const repeatOptions = [
    { value: "none", label: "Không lặp lại" },
    { value: "daily", label: "Hàng ngày" },
    { value: "weekly", label: "Hàng tuần" },
    { value: "monthly", label: "Hàng tháng" },
    { value: "yearly", label: "Hàng năm" }
  ];

  // Initialize local state from active store
  let form = $state({
    senderName: '',
    senderPhone: '',
    message: '',
    packaging: 'PREMIUM_GIFT_BOX',
    scheduledAt: '',
    recurringType: 'none',
    recurringMetadata: {
        daysOfWeek: [] as number[], // 0-6
        dayOfMonth: 1
    }
  });

  // Helper: Format Date for local datetime-local input
  function formatDateForInput(date: Date) {
    const tzoffset = date.getTimezoneOffset() * 60000;
    return new Date(date.getTime() - tzoffset).toISOString().slice(0, 16);
  }

  function setQuickSchedule(type: 'now' | 'tomorrow' | 'weekend') {
    const d = new Date();
    if (type === 'now') {
      // Just set current time
    } else if (type === 'tomorrow') {
      d.setDate(d.getDate() + 1);
      d.setHours(9, 0, 0, 0);
    } else if (type === 'weekend') {
      const day = d.getDay();
      const diff = 6 - day + (day === 6 ? 7 : 0); // Saturday
      d.setDate(d.getDate() + diff);
      d.setHours(10, 0, 0, 0);
    }
    form.scheduledAt = formatDateForInput(d);
  }

  // Re-sync local form when activeStore or showModal changes
  $effect(() => {
    if (showModal && activeStore?.giftInfo) {
      form.senderName = activeStore.giftInfo.sender_name || '';
      form.senderPhone = activeStore.giftInfo.sender_phone || '';
      form.message = activeStore.giftInfo.message || '';
      form.packaging = activeStore.giftInfo.packaging || 'PREMIUM_GIFT_BOX';
      form.scheduledAt = activeStore.giftInfo.scheduled_at || '';
      form.recurringType = activeStore.giftInfo.recurring_type || 'none';
      form.recurringMetadata = activeStore.giftInfo.recurring_metadata || { daysOfWeek: [], dayOfMonth: 1 };
    }
  });

  function close() {
    if (isOpen !== undefined) isOpen = false;
    if (onClose) onClose();
    activeStore?.toggleGiftModal(false);
  }

  function save() {
    if (!activeStore) {
        // If no store, we just rely on props/events (not implemented here, but could be)
        close();
        return;
    }
    
    if (!form.senderName || !form.senderPhone) return;

    activeStore.setGiftInfo({
        sender_name: form.senderName,
        sender_phone: form.senderPhone,
        message: form.message,
        packaging: form.packaging,
        scheduled_at: form.scheduledAt || undefined,
        recurring_type: form.recurringType,
        recurring_metadata: form.recurringType !== 'none' ? form.recurringMetadata : undefined
    });
    
    close();
  }

  function handleBackdropClick(e: MouseEvent) {
    if (e.target === e.currentTarget) close();
  }
</script>

{#if showModal}
  <div 
    use:portal 
    style:z-index={Z_INDEX_CLIENT.MODAL + 10} 
    class="fixed inset-0 flex items-center justify-center p-4 bg-slate-950/90 backdrop-blur-xl" 
    in:fade={{ duration: 300 }} 
    out:fade={{ duration: 200 }}
    onclick={handleBackdropClick}
  >
    <!-- Modal Container -->
    <div 
        class="viral-modal w-full max-w-lg overflow-hidden relative" 
        in:fly={{ y: 50, duration: 500, opacity: 0 }}
        out:scale={{ start: 1, end: 0.95, opacity: 0 }}
    >
      <!-- Decorative Glows -->
      <div class="modal-glow-bg"></div>

      <!-- Header -->
      <div class="flex items-center justify-between p-6 pb-2 relative z-10">
        <div>
          <h3 class="text-xl font-black text-white uppercase italic tracking-wider flex items-center gap-2">
            <span class="text-2xl">🎁</span> BẠN LÀ NGƯỜI TẶNG QUÀ?
          </h3>
          <p class="text-[10px] text-pink-400 font-bold uppercase tracking-widest mt-1 opacity-80">Elite Viral Sender Information</p>
        </div>
        <button onclick={close} class="text-slate-400 hover:text-white transition-all transform hover:rotate-90">
          <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12" /></svg>
        </button>
      </div>

      <!-- Scrollable Content -->
      <div class="p-6 pt-4 space-y-6 max-h-[70vh] overflow-y-auto custom-scrollbar relative z-10">
        <!-- Recipient Info Grid -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="field-wrap-viral">
            <input type="text" bind:value={form.senderName} placeholder=" " class="field-input-viral" id="v-name" />
            <label for="v-name" class="field-label-viral">Tên của bạn (Để in thiệp)</label>
          </div>
          <div class="field-wrap-viral">
            <input type="tel" bind:value={form.senderPhone} placeholder=" " class="field-input-viral" id="v-phone" />
            <label for="v-phone" class="field-label-viral">SĐT của bạn (Để nhận xác nhận)</label>
          </div>
        </div>

        <!-- Preset Messages -->
        <div class="space-y-2">
            <span class="text-[9px] font-black uppercase text-pink-500/80 tracking-widest ml-1">Chọn mẫu lời nhắn nhanh</span>
            <div class="flex flex-wrap gap-2">
              {#each giftPresets as preset}
                <button 
                  type="button" 
                  class="preset-pill {form.message === preset.text ? 'preset-active' : ''}"
                  onclick={() => form.message = preset.text}
                >
                  {preset.label}
                </button>
              {/each}
            </div>
        </div>

        <!-- Message Area -->
        <div class="field-wrap-viral">
          <textarea bind:value={form.message} placeholder=" " class="field-input-viral h-28" id="v-msg"></textarea>
          <label for="v-msg" class="field-label-viral">Lời nhắn gửi yêu thương...</label>
        </div>

        <!-- Message Preview Card -->
        {#if form.message}
            <div class="message-preview-card" in:fade>
                <div class="preview-sticker">Elite Premium</div>
                <p class="preview-text">{form.message}</p>
                <div class="preview-footer">Gói quà bởi osmo</div>
            </div>
        {/if}

        <div class="divider"></div>

        <!-- Scheduling Section -->
        <div class="space-y-6">
          <div class="flex items-center gap-2 mb-2">
            <span class="text-[10px] font-black uppercase text-sky-400 tracking-widest">Hẹn giờ & Lặp lại (Đặc quyền)</span>
            <div class="h-px flex-1 bg-white/5"></div>
          </div>

          <div class="space-y-6">
            <!-- Date Picker -->
            <div class="space-y-4">
              <div class="flex flex-wrap gap-2">
                <button 
                    type="button" 
                    onclick={() => setQuickSchedule('now')} 
                    class="preset-pill !border-sky-500/30 hover:!border-sky-500 {form.scheduledAt === formatDateForInput(new Date()) ? 'preset-active' : ''}"
                >
                    🚀 Giao ngay
                </button>
                <button 
                    type="button" 
                    onclick={() => setQuickSchedule('tomorrow')} 
                    class="preset-pill !border-sky-500/30 hover:!border-sky-500"
                >
                    🌅 Sáng mai
                </button>
                <button 
                    type="button" 
                    onclick={() => setQuickSchedule('weekend')} 
                    class="preset-pill !border-sky-500/30 hover:!border-sky-500"
                >
                    📅 Cuối tuần
                </button>
              </div>

              <!-- 🚀 ELITE DATE PICKER -->
              <ViralDatePicker bind:value={form.scheduledAt} />
            </div>

            <!-- Repeat Selection -->
            <div class="space-y-4">
                <div class="flex items-center justify-between px-1">
                    <span class="text-[9px] font-black uppercase text-slate-500 tracking-widest">Tần suất lặp lại</span>
                    {#if form.recurringType !== 'none'}
                        <span class="text-[8px] font-bold text-sky-400 bg-sky-500/10 px-2 py-0.5 rounded uppercase animate-pulse">Đang kích hoạt</span>
                    {/if}
                </div>
                
                <div class="flex flex-wrap gap-2">
                  {#each repeatOptions as opt}
                    <button 
                      type="button" 
                      class="preset-pill {form.recurringType === opt.value ? 'preset-active !border-sky-500 !bg-sky-500/10 !text-sky-400' : ''}"
                      onclick={() => form.recurringType = opt.value}
                    >
                      {opt.label}
                    </button>
                  {/each}
                </div>

                <!-- 🛠️ RECURRING DETAILS -->
                {#if form.recurringType === 'weekly'}
                    <div class="detail-panel" in:fly={{ y: 10 }}>
                        <span class="text-[8px] font-black text-slate-500 uppercase mb-2 block">Chọn ngày trong tuần</span>
                        <div class="flex gap-2">
                            {#each ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7'] as day, i}
                                <button 
                                    type="button"
                                    class="w-10 h-10 rounded-full border border-white/10 text-[10px] font-black transition-all {form.recurringMetadata.daysOfWeek.includes(i) ? 'bg-pink-500 border-pink-500 text-white shadow-lg' : 'text-slate-500 hover:bg-white/5'}"
                                    onclick={() => {
                                        if (form.recurringMetadata.daysOfWeek.includes(i)) {
                                            form.recurringMetadata.daysOfWeek = form.recurringMetadata.daysOfWeek.filter(d => d !== i);
                                        } else {
                                            form.recurringMetadata.daysOfWeek = [...form.recurringMetadata.daysOfWeek, i];
                                        }
                                    }}
                                >
                                    {day}
                                </button>
                            {/each}
                        </div>
                    </div>
                {:else if form.recurringType === 'monthly'}
                    <div class="detail-panel" in:fly={{ y: 10 }}>
                        <span class="text-[8px] font-black text-slate-500 uppercase mb-3 block">Chọn ngày trong tháng</span>
                        <div class="grid grid-cols-7 gap-1">
                            {#each Array.from({length: 31}, (_, i) => i + 1) as d}
                                <button 
                                    type="button"
                                    class="h-8 rounded md:rounded-lg text-[10px] font-bold transition-all {form.recurringMetadata.dayOfMonth === d ? 'bg-sky-500 text-white' : 'bg-white/5 text-slate-400 hover:bg-white/10'}"
                                    onclick={() => form.recurringMetadata.dayOfMonth = d}
                                >
                                    {d}
                                </button>
                            {/each}
                        </div>
                    </div>
                {/if}
            </div>
          </div>
        </div>
      </div>

      <!-- Action Footer -->
      <div class="p-6 bg-white/5 border-t border-white/5 flex items-center justify-between relative z-10">
        <button 
            onclick={close} 
            class="px-6 py-3 text-slate-400 font-bold uppercase text-[10px] tracking-widest hover:text-white transition-colors"
        >
            HỦY BỎ
        </button>
        <button 
            onclick={save} 
            disabled={!form.senderName || !form.senderPhone}
            class="save-btn-viral"
        >
            XÁC NHẬN GỬI QUÀ
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  @reference "../../../../routes/layout.css";

  .viral-modal {
    background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 20px;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
  }

  .modal-glow-bg {
    position: absolute;
    inset: 0;
    background: radial-gradient(circle at top right, rgba(236, 72, 153, 0.1), transparent 50%),
                radial-gradient(circle at bottom left, rgba(56, 189, 248, 0.1), transparent 50%);
    pointer-events: none;
  }

  /* Viral Fields Styling */
  .field-wrap-viral {
    @apply relative flex flex-col;
  }
  .field-input-viral {
    @apply w-full bg-white/5 border border-white/10 px-4 pt-6 pb-2 text-white font-bold outline-none transition-all;
    border-radius: 12px;
    color-scheme: dark; /* 🚀 Forces native pickers to use dark theme */
  }
  .field-input-viral:focus {
    @apply border-sky-500 bg-sky-500/5 ring-4 ring-sky-500/10;
  }
  .field-label-viral {
    @apply absolute left-4 top-2 text-[10px] font-black uppercase text-slate-500 tracking-wider pointer-events-none transition-all;
  }
  .field-input-viral:focus + .field-label-viral {
    @apply text-sky-400;
  }

  /* Preset Pills */
  .preset-pill {
    @apply px-3 py-1.5 rounded-full border border-white/10 text-[10px] font-bold text-slate-400 transition-all hover:bg-white/5 hover:text-white;
  }
  .preset-active {
    @apply border-pink-500 bg-pink-500/10 text-pink-400 shadow-[0_0_15px_rgba(236,72,153,0.3)];
  }

  /* Preview Card */
  .message-preview-card {
    @apply relative p-6 bg-white/5 border border-dashed border-white/20 rounded-xl mt-4 overflow-hidden;
    background: repeating-linear-gradient(45deg, rgba(255,255,255,0.01), rgba(255,255,255,0.01) 10px, transparent 10px, transparent 20px);
  }
  .preview-sticker {
    @apply absolute -top-1 -right-4 px-6 py-1 bg-amber-500 text-black text-[8px] font-black uppercase tracking-tighter rotate-12 shadow-lg;
  }
  .preview-text {
    @apply text-sm text-slate-200 font-medium leading-relaxed italic;
  }
  .preview-footer {
    @apply text-[8px] font-black text-slate-600 uppercase mt-4 text-right;
  }

  .divider {
    @apply h-px w-full bg-gradient-to-r from-transparent via-white/10 to-transparent;
  }

  .save-btn-viral {
    @apply px-8 py-3 bg-gradient-to-r from-sky-500 to-indigo-600 text-white font-black uppercase text-[11px] tracking-widest shadow-xl transition-all hover:scale-105 active:scale-95 disabled:opacity-50 disabled:grayscale;
    border-radius: 12px;
  }

  .custom-scrollbar::-webkit-scrollbar {
    width: 4px;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 10px;
  }

  .detail-panel {
    @apply p-4 bg-white/5 border border-white/5 rounded-2xl;
  }
</style>