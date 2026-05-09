<script lang="ts">
  import { portal } from '$lib/core/actions/portal';
  import { fade, fly, slide } from 'svelte/transition';
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import { getCartStore } from '$lib/state/commerce/cart.svelte.ts';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/zIndex';
  import ViralDatePicker from './ViralDatePicker.svelte';
  import X from "@lucide/svelte/icons/x";
  import GiftIcon from "@lucide/svelte/icons/gift";
  import Clock from "@lucide/svelte/icons/clock";
  import Send from "@lucide/svelte/icons/send";
  import ChevronDown from "@lucide/svelte/icons/chevron-down";
  import MessageSquare from "@lucide/svelte/icons/message-square";

  // 🚀 ELITE HYBRID INTERFACE
  let { 
    isOpen = $bindable<boolean | undefined>(undefined),
    onClose
  } = $props();

  const shopStore = getShopStore();
  const cartStore = getCartStore();
  const activeStore = $derived(shopStore || cartStore);
  const showModal = $derived(isOpen !== undefined ? isOpen : activeStore?.isGiftModalOpen);

  // Progressive Disclosure State
  let isMessageExpanded = $state(false);
  let isScheduleExpanded = $state(false);
  let selectedQuickType = $state<'now' | 'tomorrow' | 'weekend' | null>(null);

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

  let form = $state({
    senderName: '',
    senderPhone: '',
    message: '',
    packaging: 'PREMIUM_GIFT_BOX',
    scheduledAt: '',
    recurringType: 'none',
    recurringMetadata: {
        daysOfWeek: [] as number[],
        dayOfMonth: 1
    }
  });

  function formatDateForInput(date: Date) {
    const tzoffset = date.getTimezoneOffset() * 60000;
    return new Date(date.getTime() - tzoffset).toISOString().slice(0, 16);
  }

  function setQuickSchedule(type: 'now' | 'tomorrow' | 'weekend') {
    selectedQuickType = type;
    const d = new Date();
    if (type === 'now') {
      // Just set current time
    } else if (type === 'tomorrow') {
      d.setDate(d.getDate() + 1);
      d.setHours(9, 0, 0, 0);
    } else if (type === 'weekend') {
      const day = d.getDay();
      const diff = 6 - day + (day === 6 ? 7 : 0);
      d.setDate(d.getDate() + diff);
      d.setHours(10, 0, 0, 0);
    }
    form.scheduledAt = formatDateForInput(d);
  }

  $effect(() => {
    if (showModal && activeStore?.giftInfo) {
      form.senderName = activeStore.giftInfo.sender_name || '';
      form.senderPhone = activeStore.giftInfo.sender_phone || '';
      form.message = activeStore.giftInfo.message || '';
      form.packaging = activeStore.giftInfo.packaging || 'PREMIUM_GIFT_BOX';
      form.scheduledAt = activeStore.giftInfo.scheduled_at || '';
      form.recurringType = activeStore.giftInfo.recurring_type || 'none';
      form.recurringMetadata = activeStore.giftInfo.recurring_metadata || { daysOfWeek: [], dayOfMonth: 1 };
      
      if (form.message) isMessageExpanded = true;
      if (form.scheduledAt || form.recurringType !== 'none') isScheduleExpanded = true;
    }
  });

  function close() {
    if (isOpen !== undefined) isOpen = false;
    if (onClose) onClose();
    activeStore?.toggleGiftModal(false);
  }

  function save() {
    if (!activeStore) {
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
</script>

{#if showModal}
  <div 
    use:portal 
    style:z-index={Z_INDEX_CLIENT.MODAL + 50} 
    class="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-end justify-center"
    in:fade={{ duration: 300 }}
    out:fade={{ duration: 250 }}
    onclick={(e) => e.target === e.currentTarget && close()}
  >
    <!-- Optimized Luxury Drawer -->
    <div 
      class="mobile-gift-drawer w-full max-h-[92vh] flex flex-col rounded-t-[40px] overflow-hidden bg-white"
      in:fly={{ y: '100%', duration: 400, opacity: 1 }}
      out:fly={{ y: '100%', duration: 300, opacity: 1 }}
    >
      <!-- Drag Handle -->
      <div class="flex justify-center p-4">
        <div class="w-10 h-1.5 bg-gray-200 rounded-full"></div>
      </div>

      <!-- Header -->
      <div class="px-8 pb-4 flex items-center justify-between">
        <div class="flex items-center gap-4">
            <div class="w-12 h-12 rounded-2xl bg-[#C18F7E] flex items-center justify-center shadow-lg shadow-[#C18F7E]/20">
                <GiftIcon size={24} class="text-white" />
            </div>
            <div>
                <h3 class="text-xl font-bold text-gray-900 tracking-tight italic">Quà Tặng Elite</h3>
                <p class="text-[10px] font-black text-[#C18F7E] uppercase tracking-[0.3em] leading-none mt-1">osmo Premium Protocol</p>
            </div>
        </div>
        <button onclick={close} class="w-10 h-10 flex items-center justify-center bg-gray-100 rounded-full text-gray-400">
            <X size={18} />
        </button>
      </div>

      <!-- Content Area -->
      <div class="flex-1 overflow-y-auto px-8 pt-4 pb-40 custom-scrollbar relative">
        <div class="space-y-8">
            <!-- Basic Fields -->
            <div class="grid grid-cols-1 gap-4">
                <div class="field-wrap-elite">
                    <input type="text" bind:value={form.senderName} placeholder=" " class="field-input-elite" id="opt-name" />
                    <label for="opt-name" class="field-label-elite">Tên người tặng</label>
                </div>
                <div class="field-wrap-elite">
                    <input type="tel" bind:value={form.senderPhone} placeholder=" " class="field-input-elite" id="opt-phone" />
                    <label for="opt-phone" class="field-label-elite">Số điện thoại</label>
                </div>
            </div>

            <!-- Section: Message -->
            <div class="divider-elite"></div>
            <div class="collapsible-section">
                <button 
                    onclick={() => isMessageExpanded = !isMessageExpanded}
                    class="flex items-center justify-between w-full py-2 text-sm font-bold text-gray-800 uppercase tracking-widest"
                >
                    <div class="flex items-center gap-3">
                        <MessageSquare size={16} class="text-[#C18F7E]" />
                        <span>Lời nhắn yêu thương</span>
                    </div>
                    <ChevronDown size={18} class="transition-transform duration-300 {isMessageExpanded ? 'rotate-180' : ''} text-gray-300" />
                </button>
                
                {#if isMessageExpanded}
                    <div transition:slide class="space-y-5 pb-6 pt-4">
                        <div class="flex flex-wrap gap-2 overflow-x-auto no-scrollbar pb-1">
                            {#each giftPresets as preset}
                                <button 
                                    type="button"
                                    class="pill-btn-elite {form.message === preset.text ? 'active' : ''}"
                                    onclick={() => form.message = preset.text}
                                >
                                    {preset.label}
                                </button>
                            {/each}
                        </div>

                        <div class="field-wrap-elite">
                            <textarea bind:value={form.message} placeholder=" " class="field-input-elite h-32 pt-7" id="opt-msg"></textarea>
                            <label for="opt-msg" class="field-label-elite">Nội dung chi tiết...</label>
                        </div>

                        {#if form.message}
                            <div class="gift-preview-card" in:fade>
                                <p class="preview-text">"{form.message}"</p>
                                <div class="preview-footer">Elite Gifting by osmo</div>
                            </div>
                        {/if}
                    </div>
                {/if}
            </div>

            <!-- Section: Schedule -->
            <div class="divider-elite"></div>
            <div class="collapsible-section">
                <button 
                    onclick={() => isScheduleExpanded = !isScheduleExpanded}
                    class="flex items-center justify-between w-full py-2 text-sm font-bold text-gray-800 uppercase tracking-widest"
                >
                    <div class="flex items-center gap-3">
                        <Clock size={16} class="text-[#C18F7E]" />
                        <span>Hẹn giờ giao hàng</span>
                    </div>
                    <ChevronDown size={18} class="transition-transform duration-300 {isScheduleExpanded ? 'rotate-180' : ''} text-gray-300" />
                </button>

                {#if isScheduleExpanded}
                    <div transition:slide class="space-y-6 pb-6 pt-4">
                        <div class="flex gap-2">
                            <button 
                                onclick={() => setQuickSchedule('now')} 
                                class="pill-btn-elite !rounded-2xl px-6 {selectedQuickType === 'now' ? 'active' : ''}"
                            >
                                🚀 Giao ngay
                            </button>
                            <button 
                                onclick={() => setQuickSchedule('tomorrow')} 
                                class="pill-btn-elite !rounded-2xl px-6 {selectedQuickType === 'tomorrow' ? 'active' : ''}"
                            >
                                🌅 Sáng mai
                            </button>
                        </div>

                        <div class="datepicker-elite">
                            <ViralDatePicker bind:value={form.scheduledAt} onSelect={() => selectedQuickType = null} />
                        </div>

                        <div class="space-y-4">
                            <span class="text-[11px] font-black text-gray-400 uppercase tracking-widest block px-1">Tần suất lặp lại</span>
                            <div class="flex flex-wrap gap-2">
                                {#each repeatOptions as opt}
                                    <button 
                                        type="button" 
                                        class="repeat-btn-elite {form.recurringType === opt.value ? 'active' : ''}"
                                        onclick={() => form.recurringType = opt.value}
                                    >
                                        {opt.label}
                                    </button>
                                {/each}
                            </div>
                        </div>
                    </div>
                {/if}
            </div>
        </div>
      </div>

      <!-- Floating CTA with Mask to Prevent Overlap -->
      <div class="cta-floating-container">
        <!-- Liquid Glass Mask Overlay -->
        <div class="cta-mask"></div>
        
        <button 
            onclick={save}
            disabled={!form.senderName || !form.senderPhone}
            class="cta-elite-final"
        >
            <div class="flex items-center justify-center gap-3">
                <Send size={18} />
                <span class="text-xs font-bold tracking-widest">Xác nhận gửi quà</span>
            </div>
            <div class="cta-shimmer"></div>
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  @reference "../../../../routes/layout.css";

  .mobile-gift-drawer {
    box-shadow: 0 -20px 40px rgba(0, 0, 0, 0.08);
  }

  .divider-elite {
    @apply h-px w-full bg-gray-100;
  }

  /* Luxury Light Input */
  .field-wrap-elite {
    @apply relative flex flex-col;
  }
  .field-input-elite {
    @apply w-full bg-[#F9F9F9] border border-gray-200 px-5 pt-7 pb-3 text-gray-900 font-bold outline-none transition-all;
    border-radius: 20px;
    font-size: 16px;
  }
  .field-input-elite:focus {
    @apply border-[#C18F7E] bg-white shadow-xl shadow-[#C18F7E]/5;
  }
  .field-label-elite {
    @apply absolute left-5 top-3 text-[10px] font-black uppercase text-gray-400 tracking-wider pointer-events-none transition-all;
  }
  .field-input-elite:focus + .field-label-elite {
    @apply text-[#C18F7E];
  }

  .pill-btn-elite {
    @apply px-4 py-2.5 rounded-full border border-gray-200 bg-white text-[11px] font-bold text-gray-500 transition-all;
  }
  .pill-btn-elite.active {
    @apply border-[#C18F7E] bg-[#C18F7E]/10 text-[#C18F7E] shadow-md shadow-[#C18F7E]/10;
  }

  .datepicker-elite {
    @apply rounded-[28px] overflow-hidden border border-gray-100 shadow-sm;
  }

  .repeat-btn-elite {
    @apply px-4 py-2 rounded-xl border border-gray-100 text-[10px] font-bold text-gray-400 transition-all;
  }
  .repeat-btn-elite.active {
    @apply border-[#C18F7E] text-[#C18F7E] bg-[#C18F7E]/5;
  }

  .gift-preview-card {
    @apply p-8 bg-gray-50 border border-dashed border-gray-200 rounded-[32px] text-center;
  }
  .preview-text {
    @apply text-[17px] text-gray-800 font-medium italic leading-relaxed;
    font-family: 'Times New Roman', serif;
  }
  .preview-footer {
    @apply text-[9px] font-black text-[#C18F7E] uppercase mt-6 tracking-[0.3em] opacity-60;
  }

  /* 💎 ULTIMATE CTA POSITIONING & STYLE */
  .cta-floating-container {
    @apply absolute bottom-0 left-0 w-full p-8 pb-10 z-30 pointer-events-none;
  }
  .cta-mask {
    @apply absolute inset-0 -top-20 pointer-events-none;
    background: linear-gradient(to top, #FFFFFF 60%, transparent 100%);
  }

  .cta-elite-final {
    @apply relative w-full h-16 rounded-[24px] text-white font-black shadow-2xl pointer-events-auto overflow-hidden transition-all active:scale-95 disabled:opacity-40 disabled:grayscale;
    background: linear-gradient(135deg, #C18F7E 0%, #A07465 100%);
    box-shadow: 0 15px 35px -10px rgba(193, 143, 126, 0.5);
  }

  .cta-shimmer {
    @apply absolute inset-0 -translate-x-full;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
    animation: shimmer 3s infinite;
  }

  @keyframes shimmer {
    100% { transform: translateX(100%); }
  }

  .no-scrollbar::-webkit-scrollbar { display: none; }
  .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
  .custom-scrollbar::-webkit-scrollbar { width: 3px; }
  .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(0, 0, 0, 0.05); border-radius: 10px; }
</style>
