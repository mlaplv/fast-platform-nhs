<script lang="ts">
  import { fade, slide } from 'svelte/transition';
  import ShieldAlert from "@lucide/svelte/icons/shield-alert";
  import Activity from "@lucide/svelte/icons/activity";

  let { 
    summary = null,
    isBlacklisted,
    blockIP
  } = $props();
</script>

<div class="grid grid-cols-12 gap-8 h-full" in:fade>
   <!-- BIỂU ĐỒ TẦN SUẤT -->
   <div class="col-span-8 bg-white/[0.02] border border-white/5 rounded-sm p-8 flex flex-col">
      <div class="flex items-center gap-3 mb-8 pb-4 border-b border-white/5">
         <Activity size={18} class="text-cyan-400" />
         <h3 class="text-xs font-black uppercase tracking-[0.2em] text-slate-400">PHÂN TÍCH TẦN SUẤT TRUY CẬP NGHI VẤN (24 GIỜ)</h3>
      </div>
      
      <div class="flex-1 flex items-end gap-3 min-h-[350px] px-4 pb-4">
         {#each summary?.hourly_breakdown || [] as h}
            <div class="flex-1 flex flex-col items-center gap-4 h-full group">
               <div class="w-full bg-white/5 rounded-t-sm flex items-end h-full relative overflow-hidden">
                  <div 
                    class="w-full bg-gradient-to-t from-ruby/40 to-ruby hover:from-cyan-400 hover:to-cyan-500 transition-all duration-700 shadow-[0_0_15px_rgba(255,62,94,0.2)] group-hover:shadow-[0_0_20px_rgba(0,243,255,0.4)]" 
                    style="height: {Math.max(h.fraud_rate * 100, 2)}%"
                  ></div>
               </div>
               <span class="text-[10px] text-slate-600 font-mono group-hover:text-cyan-400 transition-colors">{new Date(h.hour).getHours()} Giờ</span>
            </div>
         {:else}
            <div class="w-full h-full flex items-center justify-center text-[10px] uppercase tracking-widest text-slate-700 font-black animate-pulse">
               ĐANG QUÉT TÍN HIỆU MÔI TRƯỜNG...
            </div>
         {/each}
      </div>
   </div>

   <!-- DANH SÁCH IP -->
   <div class="col-span-4 bg-white/[0.02] border border-white/5 rounded-sm p-8 flex flex-col">
      <div class="flex items-center gap-3 mb-8 pb-4 border-b border-white/5">
         <ShieldAlert size={18} class="text-ruby" />
         <h3 class="text-xs font-black uppercase tracking-[0.2em] text-ruby/80">MỤC TIÊU NGUY CƠ CAO</h3>
      </div>

      <div class="flex-1 overflow-y-auto custom-scrollbar flex flex-col gap-3 pr-2">
         {#each summary?.top_offending_ips || [] as item}
            <div class="bg-black/40 border border-white/5 p-4 flex justify-between items-center group hover:border-ruby/30 transition-all" in:slide>
               <div class="flex flex-col gap-1">
                  <span class="text-xs font-black font-mono text-ruby/90 tracking-tighter">{item.ip}</span>
                  <span class="text-[9px] text-slate-600 font-bold uppercase">{item.click_count} Lượt vi phạm</span>
               </div>
               {#if isBlacklisted(item.ip)}
                  <div class="px-3 py-1 bg-emerald-500/10 border border-emerald-500/30 text-emerald-500 text-[8px] font-black uppercase tracking-widest">ĐÃ CHẶN</div>
               {:else}
                  <button 
                     class="px-4 py-2 bg-ruby text-white text-[9px] font-black uppercase tracking-widest hover:brightness-125 transition-all active:scale-95 shadow-[0_4px_15px_rgba(255,62,94,0.2)]"
                     onclick={() => blockIP(item.ip)}
                  >
                     CHẶN NGAY
                  </button>
               {/if}
            </div>
         {:else}
            <div class="h-full flex items-center justify-center text-[10px] uppercase text-slate-700 italic">Không phát hiện mục tiêu nghi vấn.</div>
         {/each}
      </div>
   </div>
</div>
