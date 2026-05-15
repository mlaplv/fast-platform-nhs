<script lang="ts">
  import { fade, slide } from 'svelte/transition';
  import ShieldAlert from "@lucide/svelte/icons/shield-alert";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import Globe from "@lucide/svelte/icons/globe";
  import Target from "@lucide/svelte/icons/target";
  import Zap from "@lucide/svelte/icons/zap";
  import Search from "@lucide/svelte/icons/search";
  import ChevronLeft from "@lucide/svelte/icons/chevron-left";
  import ChevronRight from "@lucide/svelte/icons/chevron-right";

  let { 
    blacklistedIPs = [],
    unblockIP,
    manualIP = $bindable(''),
    isGlobalIP = $bindable(false),
    blockIP,
    campaigns = [],
    selectedCampaign = $bindable(null)
  } = $props();

  let searchQuery = $state('');
  let currentPage = $state(1);
  const itemsPerPage = 10;

  const filteredIPs = $derived(
    blacklistedIPs.filter(item => 
      item.ip.includes(searchQuery) || 
      (item.reason && item.reason.toLowerCase().includes(searchQuery.toLowerCase()))
    )
  );

  const paginatedIPs = $derived(
    filteredIPs.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage)
  );

  const totalPages = $derived(Math.ceil(filteredIPs.length / itemsPerPage));

  $effect(() => {
    if (searchQuery) currentPage = 1;
  });
</script>

<div class="grid grid-cols-1 md:grid-cols-12 gap-8 h-full" in:fade>
   <!-- CỘT TRÁI (8): DANH SÁCH ĐỐI TƯỢNG BỊ CHẶN -->
   <div class="col-span-12 md:col-span-8 bg-white/[0.02] border border-white/5 rounded-none p-8 flex flex-col shadow-2xl relative group overflow-hidden">
      <div class="absolute inset-0 bg-gradient-to-br from-rose-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-1000 pointer-events-none"></div>

      <div class="flex items-center justify-between mb-8 pb-5 border-b border-white/10 relative z-10">
         <div class="flex items-center gap-3">
            <div class="p-3 bg-rose-500/10 rounded-none border border-rose-500/20">
               <ShieldAlert size={20} class="text-rose-500" />
            </div>
          <div class="flex flex-col">
                <h3 class="text-sm font-black text-white tracking-[0.1em]">Danh sách đen</h3>
                <p class="text-[10px] text-slate-500 font-mono mt-1 tracking-tighter font-bold ">
                   TRUY VẤN DỮ LIỆU IP GIAN LẬN // CƠ SỞ DỮ LIỆU THỰC THI
                </p>
             </div>
          </div>
          
          <div class="flex items-center gap-4">
             <div class="relative w-48">
                <Search size={12} class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                <input 
                   type="text" 
                   bind:value={searchQuery}
                   placeholder="Tìm IP..."
                   class="w-full bg-white/5 border border-white/10 rounded-none py-1.5 pl-9 pr-3 text-[10px] text-white focus:border-rose-500/50 outline-none transition-all font-mono"
                />
             </div>
             <span class="text-[10px] font-mono text-slate-500 font-bold ">{filteredIPs.length} NODES_TERMINATED</span>
          </div>
       </div>

      <div class="flex-1 overflow-hidden flex flex-col border border-white/10 rounded-none bg-black/40 relative z-10 shadow-inner">
         <div class="grid grid-cols-4 px-6 py-4 text-[9px] text-slate-500 font-mono font-black tracking-widest text-left border-b border-white/10 bg-white/[0.03]">
            <span class="pl-2">Địa chỉ IP</span>
            <span>Lý do chặn</span>
            <span>Phạm vi</span>
            <span class="text-right pr-2">Thao tác</span>
         </div>
         <div class="flex-1 overflow-y-auto custom-scrollbar font-mono">
            {#each paginatedIPs as item}
               <div class="grid grid-cols-4 px-6 py-5 border-b border-white/[0.03] hover:bg-rose-500/[0.03] transition-all group/row" in:slide>
                  <span class="text-rose-500 font-black text-sm tracking-tighter group-hover/row:text-rose-400 transition-colors">{item.ip}</span>
                  <span class="text-slate-400 italic text-[11px] self-center truncate pr-4">{item.reason || 'Click Fraud Detected'}</span>
                  <div class="flex items-center gap-2 self-center">
                     {#if item.is_global}
                        <Globe size={12} class="text-cyan-400" />
                        <span class="text-[8px] text-cyan-400 font-black tracking-tighter ">Global Core</span>
                     {:else}
                        <Target size={12} class="text-amber-500" />
                        <span class="text-[8px] text-amber-500 font-black tracking-tighter ">Campaign Only</span>
                     {/if}
                  </div>
                  <div class="text-right self-center">
                     <button 
                        class="p-2 text-slate-600 hover:text-rose-500 hover:bg-rose-500/10 rounded-none transition-all active:scale-90"
                        onclick={() => unblockIP(item.ip)}
                        title="Gỡ khỏi danh sách đen"
                     >
                        <Trash2 size={16} />
                     </button>
                  </div>
               </div>
            {:else}
               <div class="h-full flex flex-col items-center justify-center gap-8 py-24 opacity-20">
                  <div class="relative">
                     <ShieldAlert size={80} class="text-slate-400" />
                     <div class="absolute inset-0 bg-slate-500/10 blur-[40px] rounded-none animate-pulse"></div>
                  </div>
                  <span class="text-[10px] tracking-[0.6em] font-black text-center ">NO_ACTIVE_THREATS_TERMINATED</span>
               </div>
            {/each}
         </div>

          <!-- PAGINATION -->
          {#if totalPages > 1}
             <div class="p-4 border-t border-white/10 bg-white/[0.02] flex justify-between items-center">
                <span class="text-[9px] font-mono text-slate-500 tracking-widest">Trang {currentPage}/{totalPages}</span>
                <div class="flex gap-2">
                   <button 
                      class="p-1.5 rounded-none bg-white/5 border border-white/10 text-slate-400 hover:text-white disabled:opacity-20"
                      disabled={currentPage === 1}
                      onclick={() => currentPage--}
                   >
                      <ChevronLeft size={14} />
                   </button>
                   <button 
                      class="p-1.5 rounded-none bg-white/5 border border-white/10 text-slate-400 hover:text-white disabled:opacity-20"
                      disabled={currentPage === totalPages}
                      onclick={() => currentPage++}
                   >
                      <ChevronRight size={14} />
                   </button>
                </div>
             </div>
          {/if}
       </div>
    </div>

   <!-- CỘT PHẢI (4): THIẾT LẬP LỆNH CHẶN THỦ CÔNG -->
    <div class="col-span-12 md:col-span-4 h-full relative">
       <div class="sticky top-0 bg-white/[0.03] border border-white/10 rounded-none p-8 shadow-2xl overflow-hidden h-fit group">
      <div class="absolute top-0 right-0 w-64 h-64 bg-amber-500/5 blur-[100px] rounded-none opacity-50 group-hover:opacity-100 transition-opacity"></div>
      
      <div class="flex items-center gap-3 mb-8 pb-5 border-b border-white/10 relative z-10">
         <div class="p-2 rounded-none bg-amber-500/10 border border-amber-500/20">
            <Zap size={18} class="text-amber-500" />
         </div>
         <h3 class="text-[10px] font-black tracking-widest text-amber-500 font-mono ">Điều phối lệnh chặn thủ công</h3>
      </div>

      <div class="flex flex-col gap-8 relative z-10">
         <div class="field">
            <label class="block text-[8px] text-slate-500 font-black mb-3 tracking-widest font-mono ">Địa chỉ IP mục tiêu</label>
            <input 
               type="text" 
               bind:value={manualIP}
               placeholder="Nhập địa chỉ IP..."
               class="w-full bg-black/40 border border-white/10 rounded-none p-4 text-sm font-mono text-white focus:border-amber-500/50 outline-none transition-all shadow-inner focus:bg-black/60"
            />
         </div>

         <div class="field">
            <div class="flex items-center justify-between p-4 bg-white/[0.02] border border-white/5 rounded-none">
               <div class="flex flex-col gap-1 flex-1">
                  <span class="text-[8px] text-slate-500 font-black tracking-widest font-mono ">Phạm vi thực thi</span>
                  <span class="text-[10px] {isGlobalIP ? 'text-cyan-400' : 'text-amber-500'} font-bold ">
                     {isGlobalIP ? 'TOÀN TÀI KHOẢN' : (selectedCampaign ? `CHIẾN DỊCH: ${selectedCampaign.name}` : 'CHƯA CHỌN CHIẾN DỊCH')}
                  </span>
               </div>
               <label class="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" bind:checked={isGlobalIP} class="sr-only peer" />
                  <div class="w-12 h-6 bg-white/5 border border-white/10 rounded-none peer peer-checked:bg-cyan-500/50 after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-slate-500 after:rounded-none after:h-5 after:w-5 after:transition-all peer-checked:after:translate-x-6 peer-checked:after:bg-cyan-400"></div>
               </label>
            </div>

            {#if !isGlobalIP}
               <div class="mt-4" in:slide>
                  <select 
                     bind:value={selectedCampaign} 
                     class="w-full bg-black/60 border border-white/10 rounded-none p-4 text-[11px] font-black text-white focus:border-amber-500/50 outline-none appearance-none transition-all shadow-inner "
                  >
                     <option value={null}>-- CHỌN CHIẾN DỊCH THỰC THI --</option>
                     {#each campaigns as c}
                        <option value={c} class="bg-[#0a0a0a] text-white ">{c.name}</option>
                     {/each}
                  </select>
               </div>
            {/if}
         </div>

         <button 
            class="w-full py-5 {isGlobalIP ? 'bg-gradient-to-r from-cyan-600 to-cyan-700' : 'bg-gradient-to-r from-amber-600 to-amber-700'} text-white font-black tracking-[0.2em] text-[11px] transition-all active:scale-[0.98] shadow-[0_10px_30px_rgba(0,0,0,0.3)] flex items-center justify-center gap-4 rounded-none group/btn border border-white/10 disabled:opacity-30 disabled:pointer-events-none "
            disabled={!manualIP || (!isGlobalIP && !selectedCampaign)}
            onclick={() => { if(manualIP) { blockIP(manualIP); manualIP = ''; } }}
         >
            <ShieldAlert size={18} class="group-hover:rotate-12 transition-transform" />
            <span>THỰC THI LỆNH CHẶN</span>
         </button>
      </div>

      <div class="mt-8 p-5 bg-black/40 border border-white/5 rounded-none shadow-inner">
         <p class="text-[9px] text-slate-500 leading-relaxed italic text-justify font-mono">
            <span class="text-amber-500 font-bold ">Mẹo:</span> Các địa chỉ IP bị chặn sẽ ngay lập tức được đồng bộ vào danh sách IP loại trừ của Google Ads. Dữ liệu sẽ có hiệu lực sau 2-5 phút.
         </p>
      </div>
   </div>
</div>
</div>
