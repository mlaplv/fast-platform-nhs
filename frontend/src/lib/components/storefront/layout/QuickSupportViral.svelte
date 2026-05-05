<script lang="ts">
  /**
   * QUICK SUPPORT VIRAL MODAL - ELITE V2.2 SENIOR ARCHITECT VERSION
   * Root Fix: Physical Event Barrier + Pointer-Lock Transition
   * Aesthetics: Ultra-Sharp, Minimalist Technical (Refined)
   */
  import { fade, scale } from 'svelte/transition';
  import { onMount } from 'svelte';
  import { portal } from '$lib/core/actions/portal';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/zIndex';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';

  interface Props {
    isOpen: boolean;
    onClose: () => void;
  }

  let { isOpen, onClose }: Props = $props();

  // State & Resource Management
  const ui = getClientUi();
  let phone: string = $state('');
  let isSubmitting: boolean = $state(false);
  let showSuccess: boolean = $state(false);
  let visitorCount: number = $state(22);
  let isInputFocused: boolean = $state(false);

  onMount(() => {
    const interval = setInterval(() => {
      if (!isOpen) return;
      visitorCount = Math.floor(Math.random() * (45 - 18 + 1)) + 18;
    }, 10000);
    return () => clearInterval(interval);
  });

  /**
   * ARCHITECTURAL ROOT FIX: handleClose Isolation
   * Sử dụng onmousedown để đóng modal, tách biệt hoàn toàn với onmouseup/onclick.
   * Loại bỏ isClosing lock vá víu để UI phản hồi mượt mà không bị kẹt state.
   */
  function handleClose(e?: Event): void {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    
    onClose();
  }

  async function handleSubmit(e: SubmitEvent): Promise<void> {
    e.preventDefault();
    e.stopPropagation();
    
    if (phone.trim().length < 10 || isSubmitting) return;

    isSubmitting = true;
    try {
      const response = await fetch('/api/v1/client/support/urgent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          phone: phone.trim(),
          source_url: typeof window !== 'undefined' ? window.location.href : ''
        })
      });
      
      if (!response.ok) throw new Error('API Error');

      showSuccess = true;
      phone = '';
      ui.showToast('Yêu cầu khẩn cấp đã được gửi. Chuyên viên đang kết nối!', 'success');
      setTimeout(() => {
        if (showSuccess) {
          showSuccess = false;
          handleClose();
        }
      }, 2500);
    } catch (error: unknown) {
      console.error('[QuickSupport] Submission error:', error);
    } finally {
      isSubmitting = false;
    }
  }
</script>

{#if isOpen}
  <!-- 
    ROOT-CAUSE BARRIER: Toàn bộ container này đóng vai trò là một "bức tường" vật lý.
    Sử dụng pointer-events: auto để nó luôn hứng trọn các cú click ma (ghost clicks) 
    ngay cả khi đang mờ đi, không cho phép rò rỉ xuống Header.
  -->
  <div 
    use:portal
    class="fixed inset-0 flex items-center justify-center p-6 select-none"
    style:z-index={Z_INDEX_CLIENT.MODAL}
    style:pointer-events="auto"
    transition:fade={{ duration: 200 }}
    onmousedown={(e) => e.stopPropagation()}
    onmouseup={(e) => e.stopPropagation()}
    onclick={(e) => e.stopPropagation()}
  >
    <!-- Cinematic Backdrop (Non-blocking but event-consuming) -->
    <div 
      class="absolute inset-0 bg-black/80 backdrop-blur-[6px]"
      onmousedown={handleClose}
      aria-hidden="true"
      style:z-index={Z_INDEX_CLIENT.MODAL_OVERLAY}
    ></div>

    <!-- 
      MODAL CONTENT: Elite V2.2 Refined 
      - Tỉ lệ vàng, Typography kỹ thuật, viền siêu mảnh.
    -->
    <div 
      class="relative w-full max-w-[360px] bg-white shadow-[0_60px_120px_-20px_rgba(0,0,0,0.8)] border-t-[3px] border-luxury-copper flex flex-col overflow-hidden"
      style:z-index={Z_INDEX_CLIENT.MODAL}
      transition:scale={{ duration: 400, start: 0.99, opacity: 0 }}
      onmousedown={(e) => e.stopPropagation()}
      onclick={(e) => e.stopPropagation()}
    >
      <!-- Close Button (Sharp Aesthetic) -->
      <button 
        onmousedown={handleClose}
        class="absolute top-4 right-4 text-gray-300 hover:text-luxury-copper transition-all duration-300 z-20 p-2"
        aria-label="Close"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12" /></svg>
      </button>

      <!-- Elite Header: Technical Precision -->
      <header class="pt-10 pb-6 px-8 text-center bg-gray-50/30 border-b border-gray-100/50">
        <div class="flex items-center justify-center gap-2.5 mb-4">
            <div class="flex items-center gap-1.5 px-2 py-0.5 bg-red-500/5 border border-red-500/10">
                <span class="relative flex h-1.5 w-1.5">
                    <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                    <span class="relative inline-flex rounded-full h-1.5 w-1.5 bg-red-500"></span>
                </span>
                <span class="text-[8px] font-black text-red-600 uppercase tracking-[0.2em]">Ưu Tiên Tuyệt Đối</span>
            </div>
            <div class="h-px w-4 bg-gray-200"></div>
            <span class="text-[8px] font-black text-gray-400 uppercase tracking-[0.2em]">Hệ Thống V2.2</span>
        </div>

        <h2 class="text-xl font-black text-gray-900 tracking-[0.05em] uppercase italic leading-none mb-3">
            Hỗ Trợ <span class="text-luxury-copper">Khẩn Cấp</span>
        </h2>
        
        <p class="text-[10px] text-gray-400 font-bold tracking-tight uppercase">
            Helen Elite đang xử lý <span class="text-gray-900">{visitorCount} tín hiệu</span>. 
            Cam kết phản hồi trong <span class="text-luxury-copper font-black underline underline-offset-4 decoration-luxury-copper/20">30 giây</span>.
        </p>
      </header>

      <main class="p-8 space-y-6 bg-white">
        {#if !showSuccess}
          <form onsubmit={handleSubmit} class="space-y-6">
            <div class="group/input relative">
              <label for="support_phone" class="block text-[8px] font-black text-gray-400 uppercase tracking-[0.35em] mb-3 px-1 transition-colors {isInputFocused ? 'text-luxury-copper' : ''}">
                Đường Dây Kết Nối Trực Tiếp
              </label>
              
              <div class="relative">
                <input
                    id="support_phone"
                    type="tel"
                    bind:value={phone}
                    onfocus={() => isInputFocused = true}
                    onblur={() => isInputFocused = false}
                    placeholder="Nhập số điện thoại..."
                    class="w-full bg-white border border-gray-200 px-5 py-4 text-lg font-black text-gray-900 tracking-tight focus:border-luxury-copper focus:ring-1 focus:ring-luxury-copper/30 transition-all placeholder:text-gray-300 placeholder:font-medium outline-none"
                    disabled={isSubmitting}
                    autocomplete="tel"
                />
              </div>
            </div>

            <!-- Technical Button: Magnetic Sharp -->
            <button
              type="submit"
              class="group/btn relative w-full h-14 flex items-center justify-center overflow-hidden transition-all active:scale-[0.98] disabled:active:scale-100 {phone.length >= 10 ? 'bg-black' : 'bg-gray-100 cursor-not-allowed'}"
              disabled={isSubmitting || phone.length < 10}
            >
              <!-- Liquid Transition Layer -->
              {#if phone.length >= 10 && !isSubmitting}
                <div class="absolute inset-0 bg-luxury-copper translate-y-full group-hover/btn:translate-y-0 transition-transform duration-500 ease-out"></div>
              {/if}
              
              <div class="relative z-10 flex items-center justify-center gap-3">
                {#if isSubmitting}
                    <div class="w-4 h-4 border-[2px] border-gray-400 border-t-white rounded-full animate-spin"></div>
                    <span class="text-white text-[10px] font-black uppercase tracking-[0.4em]">Đang thiết lập...</span>
                {:else}
                    <span class="text-[10px] font-black uppercase tracking-[0.4em] transition-all {phone.length >= 10 ? 'text-white group-hover/btn:tracking-[0.5em]' : 'text-gray-400'}">Gửi yêu cầu khẩn cấp</span>
                    <svg class="w-4 h-4 transition-colors {phone.length >= 10 ? 'text-luxury-copper group-hover/btn:text-white' : 'text-gray-400'}" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                {/if}
              </div>
            </button>
          </form>
        {:else}
          <!-- Success State: Minimalist Precision -->
          <div in:fade={{ duration: 400 }} class="py-6 text-center space-y-5">
            <div class="w-14 h-14 bg-black text-luxury-copper flex items-center justify-center mx-auto border-[0.5px] border-luxury-copper/20 shadow-2xl">
              <svg class="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" /></svg>
            </div>
            <div class="space-y-2">
                <h3 class="text-lg font-black text-gray-900 uppercase tracking-tighter">Đã Bắt Tín Hiệu</h3>
                <p class="text-[10px] text-gray-500 font-bold uppercase tracking-widest leading-relaxed px-4">
                    Tín hiệu đã được tiếp nhận. Chuyên viên Elite sẽ gọi lại trong 30 giây.
                </p>
            </div>
          </div>
        {/if}
      </main>

      <!-- Viral Footer: Technical Metadata -->
      <footer class="bg-gray-950 py-4 px-8 flex items-center justify-between border-t border-white/5">
        <div class="flex items-center gap-3">
           <div class="flex -space-x-1.5">
             {#each [1, 2, 3] as _}
               <div class="w-4 h-4 border-[0.5px] border-white/10 bg-gray-900 grayscale opacity-40"></div>
             {/each}
           </div>
           <span class="text-[7px] font-black text-white/20 uppercase tracking-[0.4em]">Phiên bản V2.2.0</span>
        </div>
        <div class="flex flex-col items-end">
            <span class="text-[7px] font-black text-luxury-peach uppercase tracking-[0.2em] animate-pulse italic">Đường Truyền Mật</span>
        </div>
      </footer>
    </div>
  </div>
{/if}

<style>
  input:focus { outline: none; }
</style>
