<script lang="ts">
  import { fade, slide } from 'svelte/transition';
  import ShieldAlert from "@lucide/svelte/icons/shield-alert";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import Globe from "@lucide/svelte/icons/globe";
  import Target from "@lucide/svelte/icons/target";
  import Zap from "@lucide/svelte/icons/zap";

  let { 
    blacklistedIPs = [],
    unblockIP,
    manualIP = $bindable(''),
    isGlobalIP = $bindable(false),
    blockIP
  } = $props();
</script>

<div class="grid grid-cols-12 gap-8 h-full" in:fade>
   <!-- CỘT TRÁI (8): DANH SÁCH ĐỐI TƯỢNG BỊ CHẶN -->
   <div class="col-span-8 bg-white/[0.02] border border-white/5 rounded-sm p-8 flex flex-col">
      <div class="flex items-center justify-between mb-8 pb-4 border-b border-white/5">
         <div class="flex items-center gap-3">
            <ShieldAlert size={18} class="text-ruby" />
            <h3 class="text-xs font-black uppercase tracking-[0.2em] text-ruby">DANH SÁCH ĐEN ĐANG HOẠT ĐỘNG</h3>
         </div>
         <span class="text-[10px] font-mono text-slate-500 uppercase">{blacklistedIPs.length} Đối tượng đã bị vô hiệu hóa</span>
      </div>

      <div class="flex-1 overflow-hidden flex flex-col border border-white/5 rounded-sm bg-black/40">
         <div class="grid grid-cols-4 bg-white/5 p-4 text-[10px] font-black uppercase tracking-widest text-slate-500">
            <span>Địa chỉ IP</span>
            <span>Lý do chặn</span>
            <span>Phạm vi</span>
            <span class="text-right">Thao tác</span>
         </div>
         <div class="flex-1 overflow-y-auto custom-scrollbar font-mono text-xs">
            {#each blacklistedIPs as item}
               <div class="grid grid-cols-4 p-5 border-b border-white/[0.02] hover:bg-ruby/5 transition-all group" in:slide>
                  <span class="text-ruby font-bold">{item.ip}</span>
                  <span class="text-slate-400 italic text-[11px]">{item.reason || 'Phát hiện Click ảo'}</span>
                  <div class="flex items-center gap-2">
                     {#if item.is_global}
                        <Globe size={12} class="text-cyan-400" />
                        <span class="text-[9px] text-cyan-400 font-black uppercase">Toàn tài khoản</span>
                     {:else}
                        <Target size={12} class="text-amber-500" />
                        <span class="text-[9px] text-amber-500 font-black uppercase">Theo chiến dịch</span>
                     {/if}
                  </div>
                  <div class="text-right">
                     <button 
                        class="text-slate-600 hover:text-ruby transition-all hover:scale-110"
                        onclick={() => unblockIP(item.ip)}
                        title="Gỡ khỏi danh sách đen"
                     >
                        <Trash2 size={16} />
                     </button>
                  </div>
               </div>
            {:else}
               <div class="h-full flex flex-col items-center justify-center gap-6 py-20 opacity-20">
                  <ShieldAlert size={64} />
                  <span class="text-[10px] uppercase tracking-[0.4em] font-black">Chưa có IP nào bị chặn trong hệ thống</span>
               </div>
            {/each}
         </div>
      </div>
   </div>

   <!-- CỘT PHẢI (4): THIẾT LẬP LỆNH CHẶN THỦ CÔNG -->
   <div class="col-span-4 bg-white/[0.03] border border-white/10 rounded-sm p-8 shadow-2xl relative overflow-hidden h-fit">
      <div class="absolute top-0 right-0 w-32 h-32 bg-ruby/5 blur-3xl rounded-full"></div>
      
      <div class="flex items-center gap-3 mb-8 pb-4 border-b border-white/10">
         <Zap size={18} class="text-amber-500" />
         <h3 class="text-xs font-black uppercase tracking-widest text-amber-500">ĐIỀU PHỐI LỆNH CHẶN</h3>
      </div>

      <div class="flex flex-col gap-6">
         <div class="field">
            <label class="block text-[9px] text-slate-500 font-black uppercase mb-3">Địa chỉ IP Mục tiêu</label>
            <input 
               type="text" 
               bind:value={manualIP}
               placeholder="Nhập IP (Ví dụ: 103.xxx.xxx.xxx)"
               class="w-full bg-black border border-white/10 p-4 text-sm font-mono text-white focus:border-ruby/50 outline-none transition-all"
            />
         </div>

         <div class="field">
            <div class="flex items-center justify-between mb-4">
               <span class="text-[9px] text-slate-500 font-black uppercase italic">Phạm vi: {isGlobalIP ? 'Toàn tài khoản' : 'Hiện tại'}</span>
               <label class="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" bind:checked={isGlobalIP} class="sr-only peer" />
                  <div class="w-11 h-6 bg-white/5 border border-white/10 rounded-full peer peer-checked:bg-ruby/50 after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-slate-500 after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:after:translate-x-full peer-checked:after:bg-ruby"></div>
               </label>
            </div>
         </div>

         <button 
            class="w-full py-5 bg-ruby text-white font-black tracking-[0.3em] text-[11px] hover:brightness-125 transition-all active:scale-95 shadow-xl flex items-center justify-center gap-3"
            onclick={() => { blockIP(manualIP); manualIP = ''; }}
         >
            <ShieldAlert size={16} />
            <span>THỰC THI LỆNH CHẶN</span>
         </button>
      </div>

      <div class="mt-8 p-4 bg-black/40 border border-white/5 rounded-sm">
         <p class="text-[9px] text-slate-500 leading-relaxed italic text-justify">
            * Các địa chỉ IP bị chặn sẽ ngay lập tức được đồng bộ vào danh sách IP loại trừ của Google Ads theo phạm vi Sếp đã chọn.
         </p>
      </div>
   </div>
</div>
