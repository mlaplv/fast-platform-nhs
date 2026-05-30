<script lang="ts">
  import { fade, fly, scale } from 'svelte/transition';
  import Search from "@lucide/svelte/icons/search";
  import Phone from "@lucide/svelte/icons/phone";
  import Hash from "@lucide/svelte/icons/hash";
  import ArrowLeft from "@lucide/svelte/icons/arrow-left";
  import Loader2 from "@lucide/svelte/icons/loader-2";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import Navigation from "@lucide/svelte/icons/navigation";
  import { onMount } from 'svelte';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/zIndex';
  import { useNanobot } from '$lib/state/nanobot.svelte';
  const nanobot = useNanobot();

  let { orderId = $bindable(), phone = $bindable(), isSubmitting, onTrack } = $props<{ 
    orderId: string, 
    phone: string, 
    isSubmitting: boolean,
    onTrack: () => void 
  }>();

  onMount(() => {
    if (orderId === undefined) orderId = '';
    if (phone === undefined) phone = '';
    const originalHideFooter = nanobot.ui.hideFooter;
    nanobot.ui.hideFooter = true;
    return () => {
      nanobot.ui.hideFooter = originalHideFooter;
    };
  });

  $effect(() => {
    if (typeof document !== 'undefined') {
      const originalOverflow = document.body.style.overflow;
      document.body.style.overflow = 'hidden';
      return () => {
        document.body.style.overflow = originalOverflow;
      };
    }
  });
</script>

<div class="fixed inset-0 bg-[#0a0a0a] text-white overflow-hidden flex flex-col items-center justify-center p-6">
  <!-- Radar Background Animation -->
  <div class="absolute top-[20%] left-1/2 -translate-x-1/2 w-[300px] h-[300px]">
    <div class="absolute inset-0 border border-sky-500/20 rounded-full animate-[ping_3s_linear_infinite]"></div>
    <div class="absolute inset-0 border border-sky-500/10 rounded-full animate-[ping_3s_linear_infinite_1s]"></div>
    <div class="absolute inset-0 border border-sky-500/5 rounded-full animate-[ping_3s_linear_infinite_2s]"></div>
    <div class="absolute inset-0 bg-sky-500/5 blur-[80px] rounded-full"></div>
  </div>

  <div class="relative w-full max-w-sm flex flex-col items-center z-surface">
    <!-- Header Icon -->
    <div in:scale={{ duration: 600, start: 0.5 }} class="w-24 h-24 bg-sky-500/20 text-sky-400 rounded-full flex items-center justify-center mb-10 border border-sky-500/30 relative">
      <div class="absolute inset-0 bg-sky-400/20 rounded-full blur-2xl {isSubmitting ? 'animate-pulse' : ''}"></div>
      <Search class="w-10 h-10 relative z-surface" strokeWidth={2.5} />
      {#if isSubmitting}
        <div class="absolute inset-0 border-2 border-sky-400 border-t-transparent rounded-full animate-spin"></div>
      {/if}
    </div>

    <!-- Title Group -->
    <div class="text-center mb-12">
      <h2 in:fly={{ y: 20, duration: 600, delay: 200 }} class="text-3xl font-black italic tracking-tighter mb-2">TRA CỨU ĐƠN</h2>
      <div in:fade={{ delay: 400 }} class="flex items-center justify-center gap-2">
         <span class="w-1.5 h-1.5 bg-sky-500 rounded-full animate-pulse"></span>
         <p class="text-white/40 text-[9px] tracking-[0.4em] font-bold italic">Elite Radar Tracking V2.2</p>
      </div>
    </div>

    <!-- Input Stack -->
    <div in:fly={{ y: 30, duration: 800, delay: 600 }} class="w-full space-y-5 mb-10">
      <!-- Order ID Input -->
      <div class="relative group">
        <div class="absolute left-6 top-1/2 -translate-y-1/2 text-white/20 group-focus-within:text-sky-400 transition-colors">
          <Hash class="w-5 h-5" />
        </div>
        <input 
          type="text" 
          bind:value={orderId}
          placeholder="MÃ ĐƠN HÀNG (UUID)"
          class="w-full pl-16 pr-6 py-5 bg-white/[0.03] border border-white/10 focus:border-sky-500/50 rounded-full outline-none text-white font-black text-sm placeholder:text-white/10 tracking-widest transition-all"
        />
      </div>

      <!-- Phone Input -->
      <div class="relative group">
        <div class="absolute left-6 top-1/2 -translate-y-1/2 text-white/20 group-focus-within:text-sky-400 transition-colors">
          <Phone class="w-5 h-5" />
        </div>
        <input 
          type="tel" 
          bind:value={phone}
          placeholder="SỐ ĐIỆN THOẠI"
          class="w-full pl-16 pr-6 py-5 bg-white/[0.03] border border-white/10 focus:border-sky-500/50 rounded-full outline-none text-white font-black text-lg placeholder:text-white/10 tracking-[0.2em] transition-all"
        />
      </div>
    </div>

    <!-- Action Button -->
    <button 
      onclick={onTrack}
      disabled={isSubmitting}
      class="w-full py-5 text-white font-black text-base tracking-widest rounded-full btn-primary-viral active:scale-95 transition-all overflow-hidden relative group disabled:opacity-50"
    >
        <span class="relative z-surface flex items-center justify-center gap-3">
          {#if isSubmitting}
            <Loader2 class="w-5 h-5 animate-spin" /> ĐANG TÌM KIẾM
          {:else}
            KIỂM TRA TRẠNG THÁI <Navigation class="w-4 h-4 fill-current" />
          {/if}
        </span>
        <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000"></div>
    </button>

    <!-- Help Context -->
    <div in:fade={{ delay: 1000 }} class="mt-8 text-center flex flex-col items-center gap-4">
      <p class="text-[9px] text-white/20 font-black tracking-[0.2em] leading-relaxed max-w-[200px]">
        Quý khách vui lòng nhập đúng thông tin để bảo mật dữ liệu đơn hàng
      </p>
      
      <a 
        href="/" 
        class="flex items-center gap-2 text-[10px] font-black text-sky-400 tracking-widest hover:text-sky-300 transition- colors pt-4"
      >
        <ArrowLeft class="w-3 h-3" /> Quay lại CỬA HÀNG
      </a>
    </div>
  </div>

  <!-- Decorative Sparkles -->
  <div class="fixed top-10 right-10 text-sky-500/20 animate-pulse">
    <Sparkles class="w-8 h-8" />
  </div>
</div>

<style lang="postcss">
  :global(body) {
    background-color: #0a0a0a;
  }
</style>

