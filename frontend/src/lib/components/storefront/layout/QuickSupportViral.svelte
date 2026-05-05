<script lang="ts" context="module">
  /**
   * CONSTANTS & STATIC DATA (Dọn dẹp bộ nhớ, không khởi tạo lại khi component re-render)
   */
  const SIMULATED_NAMES = ['Chị Lan', 'Anh Tuấn', 'Chị Mai', 'Anh Hùng', 'Chị Vy', 'Anh Minh', 'Chị Hạnh'];
  
  const INITIAL_ACTIONS = [
    { id: 1, text: 'Chị Hạnh vừa được tư vấn thành công', time: '2 phút trước' },
    { id: 2, text: 'Anh Minh đang kết nối với Helen...', time: 'Vừa xong' }
  ];
</script>

<script lang="ts">
  import { fade, fly, scale } from 'svelte/transition';
  import { onMount } from 'svelte';

  interface Props {
    isOpen: boolean;
    onClose: () => void;
  }

  let { isOpen, onClose }: Props = $props();

  /**
   * STATE MANAGEMENT (Svelte 5 Runes)
   */
  let phone = $state('');
  let isSubmitting = $state(false);
  let showSuccess = $state(false);
  let visitorCount = $state(15);
  let recentActions = $state([...INITIAL_ACTIONS]);

  /**
   * FOMO LOGIC ENGINE
   * Đảm bảo Dispose ngay khi xong để bảo vệ 2GB RAM (R00/Resource Discipline)
   */
  onMount(() => {
    const interval = setInterval(() => {
      if (!isOpen) return; // Chỉ chạy logic khi modal đang mở

      const newAction = {
        id: Date.now(),
        text: `${SIMULATED_NAMES[Math.floor(Math.random() * SIMULATED_NAMES.length)]} vừa gửi yêu cầu hỗ trợ`,
        time: 'Vừa xong'
      };
      
      recentActions = [newAction, ...recentActions.slice(0, 2)];
      visitorCount = Math.floor(Math.random() * (35 - 12 + 1)) + 12;
    }, 7000);

    return () => clearInterval(interval);
  });

  /**
   * ACTIONS
   */
  async function handleSubmit(e: SubmitEvent) {
    e.preventDefault();
    const cleanPhone = phone.trim();
    if (!cleanPhone || cleanPhone.length < 10) return;

    isSubmitting = true;
    
    try {
      // Giả lập gửi thông tin hỗ trợ khẩn cấp (Elite response < 200ms logic simulation)
      await new Promise(resolve => setTimeout(resolve, 1200));
      
      showSuccess = true;
      phone = '';

      // Tự động đóng modal sau khi thành công
      setTimeout(() => {
        if (showSuccess) {
          showSuccess = false;
          onClose();
        }
      }, 3000);
    } catch (error) {
      console.error('Support form error:', error);
    } finally {
      isSubmitting = false;
    }
  }

  function handleBackdropClick(e: MouseEvent) {
    if (e.target === e.currentTarget) onClose();
  }
</script>

{#if isOpen}
  <div 
    class="fixed inset-0 z-[var(--z-modal)] flex items-center justify-center p-4"
    transition:fade={{ duration: 150 }}
  >
    <!-- Liquid Glass Backdrop -->
    <div 
      class="absolute inset-0 bg-black/60 backdrop-blur-[12px] transition-all"
      onclick={handleBackdropClick}
      aria-hidden="true"
    ></div>

    <!-- Modal Content: Sharp Aesthetic (No rounded corners) -->
    <div 
      class="relative w-full max-w-md bg-white shadow-[0_30px_70px_rgba(0,0,0,0.5)] border-t-[4px] border-luxury-copper overflow-hidden"
      transition:scale={{ duration: 300, start: 0.95, opacity: 0 }}
    >
      <!-- Close Trigger -->
      <button 
        onclick={onClose}
        class="absolute top-4 right-4 text-gray-400 hover:text-luxury-copper transition-all z-10 p-2"
        aria-label="Close modal"
      >
        <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12" /></svg>
      </button>

      <!-- Viral Branding Header -->
      <header class="relative bg-gray-50/80 p-8 text-center border-b border-gray-100">
        <div class="absolute top-4 left-6 flex items-center gap-2">
          <div class="relative flex h-2 w-2">
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
            <span class="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
          </div>
          <span class="text-[9px] font-black text-red-500 uppercase tracking-[0.2em]">Live Support</span>
        </div>

        <h2 class="text-2xl font-black text-gray-900 uppercase tracking-tighter mb-1 italic">
          Hỗ Trợ <span class="text-luxury-copper">Khẩn Cấp</span>
        </h2>
        <p class="text-[12px] text-gray-500 font-medium tracking-tight">
          Đang có <span class="text-gray-900 font-bold">{visitorCount} khách hàng</span> đang được kết nối.<br/>
          Phản hồi trung bình: <span class="text-luxury-copper font-black">30 GIÂY</span>.
        </p>
      </header>

      <main class="p-8">
        {#if !showSuccess}
          <form onsubmit={handleSubmit} class="space-y-5">
            <div class="relative">
              <label for="support_phone" class="block text-[10px] font-black text-gray-400 uppercase tracking-[0.2em] mb-2 px-1">
                Số điện thoại của bạn
              </label>
              <input
                id="support_phone"
                type="tel"
                bind:value={phone}
                placeholder="09xx xxx xxx"
                class="w-full bg-gray-50 border-2 border-gray-100 px-5 py-4 text-xl font-bold focus:border-luxury-copper focus:bg-white focus:ring-0 transition-all placeholder:text-gray-200"
                disabled={isSubmitting}
                autocomplete="tel"
                autofocus
              />
            </div>

            <button
              type="submit"
              class="w-full bg-gradient-to-r from-luxury-copper via-luxury-peach to-luxury-copper bg-[length:200%_auto] hover:bg-right transition-all duration-700 text-white font-black py-5 uppercase tracking-[0.25em] shadow-xl shadow-luxury-copper/20 flex items-center justify-center gap-3 active:scale-[0.97] disabled:opacity-50"
              disabled={isSubmitting || phone.length < 10}
            >
              {#if isSubmitting}
                <div class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                ĐANG KẾT NỐI...
              {:else}
                GỬI YÊU CẦU NGAY
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
              {/if}
            </button>
          </form>

          <!-- Real-time Activity Feed -->
          <section class="mt-8 pt-6 border-t border-gray-50">
            <h4 class="text-[9px] font-black text-gray-300 uppercase tracking-[0.2em] mb-4">Hoạt động mới nhất</h4>
            <div class="space-y-3">
              {#each recentActions as action (action.id)}
                <div 
                  in:fly={{ y: 8, duration: 400 }}
                  class="flex items-center justify-between text-[11px] font-medium animate-in fade-in slide-in-from-bottom-1"
                >
                  <span class="text-gray-600 flex items-center gap-2">
                    <span class="w-1 h-1 bg-luxury-copper/40"></span>
                    {action.text}
                  </span>
                  <span class="text-gray-400 italic text-[9px]">{action.time}</span>
                </div>
              {/each}
            </div>
          </section>
        {:else}
          <!-- Success State -->
          <div 
            in:fly={{ y: 20, duration: 500 }}
            class="py-12 text-center space-y-4"
          >
            <div class="w-20 h-20 bg-green-50 text-green-500 flex items-center justify-center mx-auto mb-6">
              <svg class="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" /></svg>
            </div>
            <h3 class="text-xl font-black text-gray-900 uppercase tracking-tighter">Gửi thành công!</h3>
            <p class="text-[13px] text-gray-500 font-medium px-4">Đội ngũ Helen đã nhận thông báo và sẽ gọi lại cho bạn trong ít giây tới.</p>
          </div>
        {/if}
      </main>

      <!-- Viral Security Footer -->
      <footer class="bg-gray-900 py-3 px-8 flex items-center justify-between border-t border-white/5">
        <div class="flex items-center gap-3">
           <div class="flex -space-x-2">
             {#each [1, 2, 3] as _}
               <div class="w-5 h-5 rounded-full border-2 border-gray-900 bg-gray-800 flex items-center justify-center overflow-hidden">
                 <div class="w-full h-full bg-gradient-to-br from-gray-700 to-gray-900"></div>
               </div>
             {/each}
           </div>
           <span class="text-[8px] font-black text-gray-500 uppercase tracking-widest">Helen Elite Team (24/7)</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="text-[9px] font-black text-luxury-peach uppercase animate-pulse">Phòng trực: Sẵn sàng</span>
        </div>
      </footer>
    </div>
  </div>
{/if}

<style>
  /* Loại bỏ focus ring mặc định của trình duyệt */
  input:focus {
    outline: none;
  }

  /* Custom transition for shimmer if needed */
  :global(.animate-in) {
    animation-duration: 0.5s;
  }
</style>
