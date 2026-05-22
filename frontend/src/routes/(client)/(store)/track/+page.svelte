<script lang="ts">
  import { fade, fly, scale } from 'svelte/transition';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/zIndex';
  import { apiClient } from '$lib/utils/apiClient';
  import { goto } from '$app/navigation';
  import TrackMobile from '$lib/components/mobile/sections/TrackMobile.svelte';
  import Search from "@lucide/svelte/icons/search";
  import ArrowLeft from "@lucide/svelte/icons/arrow-left";

  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import TikTokShopLoading from '$lib/components/storefront/product/TikTokShopLoading.svelte';
  import SeoHead from '$lib/components/storefront/seo/SeoHead.svelte';


  let { data } = $props<{ data: { isMobile: boolean } }>();
  const clientUi = getClientUi();

  // Elite V2.2: Sync layout with track context
  $effect.pre(() => {
    if (clientUi.isDetermined && clientUi.isMobile) {
      clientUi.isHeaderHidden = true;
      clientUi.isFooterHidden = true;
    } else if (clientUi.isDetermined) {
      clientUi.isHeaderHidden = false;
      clientUi.isFooterHidden = false;
    }
    return () => {
      clientUi.isHeaderHidden = false;
      clientUi.isFooterHidden = false;
    };
  });

  let orderId = $state('');
  let phone = $state('');
  let isSubmitting = $state(false);

  async function handleTrack() {
    if (!orderId || !phone) {
        clientUi.showToast("Vui lòng điền đủ Mã đơn và Số điện thoại", "error");
        return;
    }

    isSubmitting = true;
    try {
        const res = await apiClient.get<import('$lib/types').OrderDetail>(`/api/v1/client/orders/${orderId.trim()}`, { params: { phone: phone.trim() } });
        if (res) {
            clientUi.showToast("Đã tìm thấy đơn hàng! Đang chuyển hướng...", "success");
            const cleanPhone = phone.trim();
            setTimeout(() => goto(`/checkout/success/${orderId.trim()}?phone=${cleanPhone}&lookup=1`), 1000);
        }
    } catch (e: unknown) {
        const err = e as { message?: string };
        clientUi.showToast(err.message || "Không tìm thấy đơn hàng hoặc thông tin không khớp", "error");
    } finally {
        isSubmitting = false;
    }
  }
</script>

<SeoHead 
  title="Tra cứu đơn hàng | {clientUi.settings?.basic_info?.site_name || clientUi.settings?.site_name || 'SmartShop'}" 
  description="Theo dõi trạng thái và lịch trình đơn hàng của bạn"
  robots="noindex, nofollow"
/>

{#if !clientUi.isDetermined}
  <TikTokShopLoading variant="grid" />
{:else if clientUi.isMobile}
  <TrackMobile bind:orderId bind:phone {isSubmitting} onTrack={handleTrack} />
{:else}
  <div class="min-h-[calc(100vh-140px)] bg-[#fafafa] text-slate-900 flex flex-col items-center justify-center p-6 relative overflow-hidden font-sans">
    
    <div 
      in:fly={{ y: 20, duration: 800 }}
      class="w-full max-w-md bg-white p-10 shadow-2xl border-t-4 border-sky-500 relative" style:z-index={Z_INDEX_CLIENT.SURFACE}
    >
      <!-- Header Section -->
      <div class="text-center mb-10">
        <div class="w-20 h-20 bg-sky-50 text-sky-500 rounded-full flex items-center justify-center mx-auto border border-sky-100 mb-6">
           <Search size={32} class="relative" />
        </div>
        
        <h1 class="text-2xl font-black tracking-tighter italic leading-tight mb-2 text-slate-900">
          TRA CỨU ĐƠN
        </h1>
        <p class="text-[10px] font-bold text-slate-400 tracking-widest">Kiểm tra trạng thái & lịch trình</p>
      </div>

      <!-- Tracking Form -->
      <div class="space-y-4">
        <input 
            type="text" 
            bind:value={orderId}
            placeholder="MÃ ĐƠN HÀNG (VD: 6CC...)"
            class="w-full px-6 py-4 bg-slate-50 border-2 border-slate-100 focus:border-sky-500 focus:bg-white outline-none text-slate-900 font-black text-left text-sm placeholder:text-slate-400 transition-all rounded-none"
            spellcheck="false"
        />

        <input 
            type="tel" 
            bind:value={phone}
            placeholder="SỐ ĐIỆN THOẠI ĐẶT HÀNG"
            class="w-full px-6 py-4 bg-slate-50 border-2 border-slate-100 focus:border-sky-500 focus:bg-white outline-none text-slate-900 font-black text-left text-sm placeholder:text-slate-400 transition-all rounded-none"
            onkeydown={(e) => e.key === 'Enter' && handleTrack()}
            spellcheck="false"
        />

        <button 
          onclick={handleTrack}
          disabled={isSubmitting}
          class="w-full !mt-6 py-4 bg-slate-900 hover:bg-sky-500 text-white font-black disabled:opacity-50 transition-all active:scale-95 text-xs tracking-[0.3em] italic"
        >
          <div class="relative flex items-center justify-center gap-2">
            {#if isSubmitting}
              <div class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
              <span>ĐANG GIẢI MÃ...</span>
            {:else}
              <span>KIỂM TRA TRẠNG THÁI →</span>
            {/if}
          </div>
        </button>
      </div>

      <div class="mt-8 text-center">
         <p class="text-[9px] text-slate-400 font-bold tracking-widest italic pt-4 border-t border-slate-100">
           AN TOÀN • BẢO MẬT • RIÊNG TƯ
         </p>
      </div>
    </div>

    <a 
      href="/" 
      class="mt-10 group flex items-center gap-2 text-[10px] font-black text-slate-400 hover:text-slate-900 transition-colors tracking-[0.3em] bg-white px-6 py-3 shadow-sm border border-slate-100"
    >
      <ArrowLeft size={14} class="group-hover:-translate-x-1 transition-transform" />
      <span>Quay lại CỬA HÀNG</span>
    </a>
  </div>
{/if}

<style>
  input {
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }
</style>
