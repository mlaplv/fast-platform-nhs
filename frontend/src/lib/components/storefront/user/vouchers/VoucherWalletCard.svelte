<script lang="ts">
  import { Ticket, Sparkles, Clock, Info } from 'lucide-svelte';
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
  class="voucher-wallet-card relative w-full h-[100px] flex bg-white border border-stone-100 rounded-xl overflow-hidden shadow-sm hover:shadow-md transition-all group"
  in:scale={{ duration: 400, start: 0.98 }}
>
  <!-- 🎫 LEFT STUB (COLORFUL) -->
  <div class="w-[80px] md:w-[100px] h-full flex flex-col items-center justify-center relative border-r border-dashed border-stone-100/50 {isShipping ? 'bg-gradient-to-br from-blue-500 to-indigo-600' : 'bg-gradient-to-br from-luxury-sakura to-luxury-copper'}">
    <!-- 🟢 TikTok Notches -->
    <div class="absolute -left-1.5 top-1/2 -translate-y-1/2 w-3 h-3 rounded-full bg-[#f9f8f6] z-10"></div>
    <div class="absolute -right-1.5 top-1/2 -translate-y-1/2 w-3 h-3 rounded-full bg-[#f9f8f6] z-10 border-l border-stone-100/10"></div>

    <div class="relative z-10 flex flex-col items-center gap-1.5">
       <div class="w-10 h-10 rounded-full bg-white/20 backdrop-blur-md flex items-center justify-center border border-white/30 text-white shadow-inner">
          <Ticket size={20} class="drop-shadow-sm" />
       </div>
       <span class="text-[8px] font-black text-white/80 uppercase tracking-[0.2em]">{voucher.category}</span>
    </div>
    
    <!-- Decorative sparkles -->
    <Sparkles size={12} class="absolute top-2 left-2 text-white/20 animate-pulse" />
  </div>

  <!-- 📄 MAIN CONTENT -->
  <div class="flex-1 p-4 flex flex-col justify-between min-w-0 bg-white">
    <div class="space-y-1">
      <div class="flex items-center justify-between gap-2">
         <h3 class="text-sm md:text-base font-black text-stone-900 truncate uppercase tracking-tight">{mainLabel}</h3>
         {#if voucher.is_default}
           <span class="px-1.5 py-0.5 bg-emerald-50 text-emerald-600 text-[8px] font-black uppercase rounded-[4px] border border-emerald-100 animate-pulse">Mặc định</span>
         {/if}
      </div>
      <p class="text-[10px] md:text-[11px] font-bold text-stone-500 uppercase tracking-wide truncate">{subLabel}</p>
    </div>

    <!-- 📊 USAGE STATS -->
    <div class="space-y-2">
       <div class="flex items-center justify-between text-[8px] font-black uppercase tracking-widest text-stone-400">
          <span>Đã dùng: {voucher.used_count.toLocaleString()}</span>
          {#if voucher.usage_limit}
            <span>Hạn mức: {voucher.usage_limit.toLocaleString()}</span>
          {/if}
       </div>
       
       {#if voucher.usage_limit}
         <div class="h-1 w-full bg-stone-50 rounded-full overflow-hidden border border-stone-100/50">
            <div 
              class="h-full {usagePercent > 80 ? 'bg-red-400' : 'bg-luxury-copper'} transition-all duration-1000" 
              style="width: {usagePercent}%"
            ></div>
         </div>
       {/if}
    </div>
  </div>

  <!-- 💡 ACTION / INFO -->
  <div class="w-[60px] md:w-[80px] h-full flex flex-col items-center justify-center bg-stone-50/50 border-l border-stone-50">
     <button class="flex flex-col items-center gap-1 group/btn">
        <div class="w-8 h-8 rounded-full bg-white border border-stone-200 flex items-center justify-center text-stone-400 group-hover/btn:text-luxury-copper group-hover/btn:border-luxury-copper transition-all active:scale-90">
           <Info size={16} />
        </div>
        <span class="text-[8px] font-black text-stone-400 group-hover/btn:text-luxury-copper uppercase tracking-tighter">Chi tiết</span>
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
