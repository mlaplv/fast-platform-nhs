<script lang="ts">
  import { fade, fly, scale } from 'svelte/transition';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/zIndex';
  import { apiClient } from '$lib/utils/apiClient';
  import { goto } from '$app/navigation';
  import TrackMobile from '$lib/components/mobile/sections/TrackMobile.svelte';
  import Search from 'lucide-svelte/icons/search';
  import Hash from 'lucide-svelte/icons/hash';
  import Phone from 'lucide-svelte/icons/phone';
  import ArrowRight from 'lucide-svelte/icons/arrow-right';
  import ArrowLeft from 'lucide-svelte/icons/arrow-left';

  let { data } = $props<{ data: { isMobile: boolean } }>();

  let orderId = $state('');
  let phone = $state('');
  let isSubmitting = $state(false);

  // Elite V2.2 Toast System!
  let toasts = $state<{id: number, type: 'success' | 'error', message: string}[]>([]);
  let toastId = 0;

  function showToast(message: string, type: 'success' | 'error' = 'success') {
    const id = toastId++;
    toasts.push({ id, type, message });
    setTimeout(() => {
        const idx = toasts.findIndex(t => t.id === id);
        if (idx !== -1) toasts.splice(idx, 1);
    }, 4000);
  }

  async function handleTrack() {
    if (!orderId || !phone) {
        showToast("Vui lòng điền đủ Mã đơn và Số điện thoại", "error");
        return;
    }

    isSubmitting = true;
    try {
        // Try to fetch order with phone verification!
        const res = await apiClient.get<import('$lib/types').OrderDetail>(`/api/v1/client/orders/${orderId.trim()}`, { params: { phone: phone.trim() } });
        if (res) {
            showToast("Đã tìm thấy đơn hàng! Đang chuyển hướng...");
            const cleanPhone = phone.trim();
            setTimeout(() => goto(`/checkout/success/${orderId.trim()}?phone=${cleanPhone}&lookup=1`), 1000);
        }
    } catch (e: unknown) {
        const err = e as { message?: string };
        showToast(err.message || "Không tìm thấy đơn hàng hoặc thông tin không khớp", "error");
    } finally {
        isSubmitting = false;
    }
  }
</script>

<svelte:head>
  <title>Tra cứu đơn hàng</title>
  <meta name="description" content="Theo dõi trạng thái đơn hàng" />
  <meta name="robots" content="noindex, nofollow" />
</svelte:head>

{#if data.isMobile}
  <TrackMobile bind:orderId bind:phone {isSubmitting} onTrack={handleTrack} />
{:else}
  <div class="min-h-screen bg-[#020617] text-white flex flex-col items-center justify-center p-6 relative overflow-hidden font-sans">
    <!-- Liquid Glass Ambient Background -->
    <div class="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-blue-600/10 rounded-full blur-[120px] pointer-events-none animate-pulse"></div>
    <div class="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] bg-sky-500/10 rounded-full blur-[100px] pointer-events-none animate-pulse" style:animation-delay="2s"></div>

    <div 
      in:fly={{ y: 30, duration: 1000, easing: (t) => t * (2 - t) }}
      class="w-full max-w-md bg-white/[0.03] border border-white/10 backdrop-blur-3xl rounded-[3rem] p-12 shadow-[0_30px_100px_rgba(0,0,0,0.6)] relative glass-card" style:z-index={Z_INDEX_CLIENT.SURFACE}
    >
      <!-- Header Section -->
      <div class="text-center mb-12">
        <div class="relative w-24 h-24 mx-auto mb-8">
          <div class="absolute inset-0 bg-sky-500/20 rounded-full blur-2xl animate-pulse"></div>
          <div class="relative w-full h-full bg-slate-900 border border-white/10 rounded-full flex items-center justify-center shadow-inner overflow-hidden">
             <div class="absolute inset-0 bg-gradient-to-tr from-sky-500/10 to-transparent"></div>
             <Search size={32} class="text-sky-400 relative" style:z-index={Z_INDEX_CLIENT.SURFACE} />
          </div>
        </div>
        
        <h1 class="text-4xl font-black tracking-tighter uppercase italic leading-none mb-3 text-white">
          Tra cứu đơn
        </h1>
        <div class="flex items-center justify-center gap-2">
           <div class="h-px w-8 bg-gradient-to-r from-transparent to-sky-500/50"></div>
           <p class="text-[9px] font-black text-sky-500 uppercase tracking-[0.4em] italic">Elite Tracking Mode</p>
           <div class="h-px w-8 bg-gradient-to-l from-transparent to-sky-500/50"></div>
        </div>
      </div>

      <!-- Tracking Form -->
      <div class="space-y-8">
        <!-- Input Group: Order ID -->
        <div class="relative group">
          <div class="absolute left-6 top-1/2 -translate-y-1/2 text-slate-500 transition-colors group-focus-within:text-sky-400" style:z-index={Z_INDEX_CLIENT.SURFACE}>
             <Hash size={18} />
          </div>
          <input 
            type="text" 
            id="orderId"
            bind:value={orderId}
            placeholder=" "
            class="peer w-full pl-14 pr-6 py-5 bg-white/[0.02] border border-white/10 focus:border-sky-500/50 rounded-2xl outline-none text-white font-bold text-sm uppercase transition-all focus:bg-white/[0.05] focus:shadow-[0_0_20px_rgba(14,165,233,0.1)]"
          />
          <label 
            for="orderId"
            class="absolute left-14 top-1/2 -translate-y-1/2 text-[10px] font-black text-slate-500 uppercase tracking-widest pointer-events-none transition-all duration-300 peer-focus:-top-2 peer-focus:left-6 peer-focus:text-sky-500 peer-[:not(:placeholder-shown)]:-top-2 peer-[:not(:placeholder-shown)]:left-6 peer-[:not(:placeholder-shown)]:text-sky-500 bg-[#020617] px-2 rounded-sm"
          >
            Mã đơn hàng (6CC...)
          </label>
        </div>

        <!-- Input Group: Phone -->
        <div class="relative group">
          <div class="absolute left-6 top-1/2 -translate-y-1/2 text-slate-500 transition-colors group-focus-within:text-sky-400" style:z-index={Z_INDEX_CLIENT.SURFACE}>
             <Phone size={18} />
          </div>
          <input 
            type="tel" 
            id="phone"
            bind:value={phone}
            placeholder=" "
            class="peer w-full pl-14 pr-6 py-5 bg-white/[0.02] border border-white/10 focus:border-sky-500/50 rounded-2xl outline-none text-white font-black text-lg transition-all focus:bg-white/[0.05] focus:shadow-[0_0_20px_rgba(14,165,233,0.1)]"
          />
          <label 
            for="phone"
            class="absolute left-14 top-1/2 -translate-y-1/2 text-[10px] font-black text-slate-500 uppercase tracking-widest pointer-events-none transition-all duration-300 peer-focus:-top-2 peer-focus:left-6 peer-focus:text-sky-500 peer-[:not(:placeholder-shown)]:-top-2 peer-[:not(:placeholder-shown)]:left-6 peer-[:not(:placeholder-shown)]:text-sky-500 bg-[#020617] px-2 rounded-sm"
          >
            Số điện thoại nhận hàng
          </label>
        </div>

        <!-- Action Button -->
        <button 
          onclick={handleTrack}
          disabled={isSubmitting}
          class="group relative w-full py-5 bg-gradient-to-r from-blue-600 to-sky-500 hover:from-blue-500 hover:to-sky-400 text-white font-black rounded-2xl transition-all active:scale-[0.98] shadow-2xl shadow-blue-500/20 uppercase tracking-widest italic text-sm mt-4 disabled:opacity-50 overflow-hidden"
        >
          <div class="absolute inset-0 bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity"></div>
          <div class="relative flex items-center justify-center gap-3" style:z-index={Z_INDEX_CLIENT.SURFACE}>
            {#if isSubmitting}
              <div class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
              <span>Đang giải mã...</span>
            {:else}
              <span>Kiểm tra trạng thái</span>
              <ArrowRight size={18} class="group-hover:translate-x-1 transition-transform" />
            {/if}
          </div>
        </button>
      </div>

      <div class="mt-12 text-center">
         <p class="text-[8px] text-slate-600 font-bold uppercase tracking-[0.3em] leading-relaxed max-w-[200px] mx-auto italic">
           Dữ liệu được bảo mật bởi<br/>hệ thống Elite Security V2.2
         </p>
      </div>
    </div>

    <!-- Footer Action -->
    <a 
      href="/" 
      class="mt-12 group flex items-center gap-3 text-[10px] font-black text-slate-600 hover:text-sky-400 transition-all uppercase tracking-[0.4em]"
    >
      <ArrowLeft size={14} class="group-hover:-translate-x-1 transition-transform" />
      <span>Quay lại cửa hàng</span>
    </a>
  </div>
{/if}

<!-- Elite Toast System! -->
<div class="fixed bottom-8 right-8 flex flex-col gap-3 pointer-events-none" style:z-index={Z_INDEX_CLIENT.TOAST}>
  {#each toasts as toast (toast.id)}
    <div 
      in:fly={{ x: 50, duration: 400 }}
      out:fade
      class="px-6 py-4 rounded-2xl shadow-2xl backdrop-blur-xl border {toast.type === 'success' ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' : 'bg-red-500/10 border-red-500/30 text-red-400'} flex items-center gap-3 pointer-events-auto"
    >
      <div class="w-2 h-2 rounded-full {toast.type === 'success' ? 'bg-emerald-400' : 'bg-red-400'} animate-pulse"></div>
      <span class="text-xs font-black uppercase tracking-widest italic">{toast.message}</span>
    </div>
  {/each}
</div>

<style>
  .glass-card {
    border: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    backdrop-filter: blur(40px);
    animation: glass-reveal 1.2s cubic-bezier(0.2, 0.8, 0.2, 1);
  }

  @keyframes glass-reveal {
    from { opacity: 0; transform: translateY(20px); filter: blur(10px); }
    to { opacity: 1; transform: translateY(0); filter: blur(0); }
  }

  /* Smooth Label Transition (Zero-JS) */
  input:focus + label,
  input:not(:placeholder-shown) + label {
    transform: translateY(-2.8rem) scale(0.9);
    padding: 0 0.5rem;
    color: #38bdf8; /* sky-400 */
    background: #020617; /* Matches body bg */
    border-radius: 4px;
    z-index: var(--z-overlay);
  }

  input {
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  /* Premium Button Lift */
  button:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 15px 40px rgba(37, 99, 235, 0.4);
  }
</style>
