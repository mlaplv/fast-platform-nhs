<script lang="ts">
    import Ticket from "@lucide/svelte/icons/ticket";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import Clock from "@lucide/svelte/icons/clock";
  import Info from "@lucide/svelte/icons/info";
  import { formatCurrency } from '$lib/utils/format';
  import type { Voucher } from '$lib/types/commerce/checkout';
  import { fade, scale } from 'svelte/transition';

  let { voucher } = $props<{ voucher: Voucher }>();

  const isShipping = $derived(voucher.type === 'SHIPPING');
  const usagePercent = $derived(voucher.usage_limit ? Math.min(100, (voucher.used_count / voucher.usage_limit) * 100) : 0);
  
  // Logic hiển thị label chính
  const mainLabel = $derived(
    voucher.type === 'PERCENT' ? `GIẢM ${voucher.value}%` :
    voucher.type === 'FIXED' ? `GIẢM ${formatCurrency(voucher.value)}` :
    'FREESHIP'
  );

  const subLabel = $derived(
    voucher.min_spend > 0 ? `Đơn tối thiểu ${formatCurrency(voucher.min_spend)}` : 'Mọi đơn hàng'
  );
</script>

<div 
  class="voucher-wallet-card relative w-full h-[110px] flex bg-white border border-stone-100 rounded-2xl overflow-hidden shadow-[0_10px_30px_rgba(0,0,0,0.02)] hover:shadow-[0_20px_40px_rgba(0,0,0,0.04)] transition-all group"
  in:scale={{ duration: 400, start: 0.98 }}
>
  <!-- 🎫 LEFT STUB (PREMIUM METALLIC GRADIENT) -->
  <div class="w-[90px] md:w-[110px] h-full flex flex-col items-center justify-center relative border-r border-dashed border-stone-200/50 {isShipping ? 'bg-stone-800' : 'bg-luxury-copper'}">
    <!-- 🟢 Perforated Ticket Notches -->
    <div class="absolute -left-2 top-1/2 -translate-y-1/2 w-4 h-4 rounded-full bg-[#f9f8f6] z-10 border border-stone-100"></div>
    <div class="absolute -right-2 top-1/2 -translate-y-1/2 w-4 h-4 rounded-full bg-[#f9f8f6] z-10 border border-stone-100"></div>

    <div class="relative z-10 flex flex-col items-center gap-2">
       <div class="w-11 h-11 rounded-full bg-white/10 backdrop-blur-md flex items-center justify-center border border-white/20 text-white shadow-xl group-hover:scale-110 transition-transform duration-500">
          <Ticket size={22} class="drop-shadow-lg" strokeWidth={1.5} />
       </div>
       <span class="text-[8px] font-black text-white/50 tracking-[0.3em] font-mono">{voucher.category}</span>
    </div>
    
    <!-- Premium Shimmer -->
    <div class="absolute inset-0 bg-gradient-to-tr from-transparent via-white/5 to-transparent animate-shimmer opacity-0 group-hover:opacity-100 transition-opacity"></div>
  </div>

  <!-- 📄 MAIN CONTENT (CLEAN & BREATHABLE) -->
  <div class="flex-1 p-5 flex flex-col justify-between min-w-0 bg-white">
    <div class="space-y-1.5">
      <div class="flex items-center justify-between gap-2">
         <h3 class="text-sm md:text-base font-serif italic text-stone-800 truncate tracking-wide">{mainLabel}</h3>
         {#if voucher.is_default}
           <span class="px-2 py-0.5 bg-stone-800 text-white text-[8px] font-black rounded-full border border-stone-800 shadow-lg shadow-stone-800/10">ELITE</span>
         {/if}
      </div>
      <p class="text-[10px] md:text-[11px] font-black text-stone-400 tracking-widest truncate">{subLabel}</p>
    </div>

    <!-- 📊 USAGE STATS (MINIMALIST) -->
    <div class="space-y-2">
       <div class="flex items-center justify-between text-[8px] font-black tracking-[0.2em] text-stone-300">
          <span>PROGRESS: {usagePercent.toFixed(0)}%</span>
          {#if voucher.usage_limit}
            <span class="flex items-center gap-1"><Clock size={8} /> {voucher.usage_limit - voucher.used_count} Lượt còn lại</span>
          {/if}
       </div>
       
       {#if voucher.usage_limit}
         <div class="h-1 w-full bg-stone-50 rounded-full overflow-hidden">
            <div 
              class="h-full bg-stone-800 transition-all duration-1000 ease-out" 
              style="width: {usagePercent}%"
            ></div>
         </div>
       {/if}
    </div>
  </div>

  <!-- 💡 ACTION SECTION (GLASS BUTTON) -->
  <div class="w-[70px] md:w-[90px] h-full flex flex-col items-center justify-center bg-stone-50/30 border-l border-stone-50">
     <button class="flex flex-col items-center gap-1.5 group/btn">
        <div class="w-9 h-9 rounded-full bg-white border border-stone-100 flex items-center justify-center text-stone-300 group-hover/btn:text-luxury-copper group-hover/btn:border-luxury-copper group-hover/btn:shadow-lg transition-all active:scale-90">
           <Info size={18} />
        </div>
        <span class="text-[8px] font-black text-stone-400 group-hover/btn:text-stone-800 tracking-widest transition-colors font-mono">DETAIL</span>
     </button>
  </div>
</div>

<style>
  .voucher-wallet-card {
    transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  }
  .voucher-wallet-card:hover {
    transform: translateY(-2px);
  }
  :global(.text-luxury-sakura) { color: #ffb7c5; }
  :global(.from-luxury-sakura) { --tw-gradient-from: #ffb7c5; }
  :global(.to-luxury-copper) { --tw-gradient-to: #c5a059; }
</style>
