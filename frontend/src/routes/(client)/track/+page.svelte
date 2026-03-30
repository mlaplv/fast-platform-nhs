<script lang="ts">
  import { fade, fly, scale } from 'svelte/transition';
  import { apiClient } from '$lib/utils/apiClient';
  import { goto } from '$app/navigation';
  import TrackMobile from '$lib/components/mobile/sections/TrackMobile.svelte';

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
        const res = await apiClient.get<any>(`/api/v1/client/orders/${orderId.trim()}`, { params: { phone: phone.trim() } });
        if (res) {
            showToast("Đã tìm thấy đơn hàng! Đang chuyển hướng...");
            const cleanPhone = phone.trim();
            setTimeout(() => goto(`/checkout/success/${orderId.trim()}?phone=${cleanPhone}&lookup=1`), 1000);
        }
    } catch (e: any) {
        showToast(e.message || "Không tìm thấy đơn hàng hoặc thông tin không khớp", "error");
    } finally {
        isSubmitting = false;
    }
  }
</script>

<svelte:head>
  <title>Tra cứu đơn hàng | Nhà Thuốc Hồng Sơn</title>
</svelte:head>

{#if data.isMobile}
  <TrackMobile bind:orderId bind:phone {isSubmitting} onTrack={handleTrack} />
{:else}
  <div class="min-h-screen bg-slate-950 text-white flex flex-col items-center justify-center p-6 relative overflow-hidden">
    <!-- Elite Glass Background! -->
    <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-sky-500/10 rounded-full blur-[100px] pointer-events-none"></div>

    <div 
      in:fly={{ y: 20, duration: 800 }}
      class="w-full max-w-md bg-white/5 border border-white/10 backdrop-blur-3xl rounded-[3rem] p-10 md:p-12 shadow-2xl relative z-10"
    >
      <div class="text-center mb-10">
        <div class="w-20 h-20 bg-sky-500/10 text-sky-400 rounded-full flex items-center justify-center mx-auto mb-6 border border-sky-500/20 shadow-[0_0_30px_rgba(14,165,233,0.1)]">
          <svg class="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
        </div>
        <h1 class="text-3xl font-black tracking-tighter uppercase italic leading-none mb-2">Tra cứu đơn</h1>
        <p class="text-slate-500 text-[10px] font-black uppercase tracking-[0.3em] italic">Elite Order Tracking V2.2</p>
      </div>

      <div class="space-y-6">
        <div class="space-y-2">
          <label class="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-4">Mã đơn hàng (UUID):</label>
          <input 
            type="text" 
            bind:value={orderId}
            placeholder="Ví dụ: 6cc3ad08..."
            class="w-full px-6 py-4 bg-white/[0.03] border-2 border-white/5 focus:border-sky-500/50 focus:bg-white/[0.05] rounded-[1.5rem] outline-none text-white font-bold text-sm uppercase placeholder:text-slate-700 transition-all"
          />
        </div>

        <div class="space-y-2">
          <label class="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-4">Số điện thoại:</label>
          <input 
            type="tel" 
            bind:value={phone}
            placeholder="Nhập Số điện thoại..."
            class="w-full px-6 py-4 bg-white/[0.03] border-2 border-white/5 focus:border-sky-500/50 focus:bg-white/[0.05] rounded-[1.5rem] outline-none text-white font-black text-lg placeholder:text-slate-700 tracking-wider transition-all"
          />
        </div>

        <button 
          onclick={handleTrack}
          disabled={isSubmitting}
          class="w-full py-5 bg-sky-500 hover:bg-sky-400 text-white font-black rounded-full transition-all active:scale-95 shadow-xl shadow-sky-500/20 uppercase tracking-tighter italic text-lg mt-4 disabled:opacity-50 disabled:pointer-events-none"
        >
          {isSubmitting ? 'ĐANG TRA CỨU...' : 'KIỂM TRA TRẠNG THÁI →'}
        </button>
      </div>

      <p class="mt-10 text-[9px] text-slate-600 text-center font-bold uppercase tracking-widest leading-relaxed">
        Quý khách vui lòng nhập đúng thông tin để bảo mật dữ liệu đơn hàng
      </p>
    </div>

    <a 
      href="/" 
      class="mt-8 text-[10px] font-black text-slate-500 hover:text-white transition-colors uppercase tracking-[0.3em]"
    >
      ← QUAY LẠI CỬA HÀNG
    </a>
  </div>
{/if}

<!-- Elite Toast System! -->
<div class="fixed bottom-8 right-8 z-[2000] flex flex-col gap-3 pointer-events-none">
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
