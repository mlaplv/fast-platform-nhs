<script lang="ts">
  import { fade, slide } from 'svelte/transition';
  import ShieldAlert from "@lucide/svelte/icons/shield-alert";
  import Activity from "@lucide/svelte/icons/activity";

  let { 
    summary = null,
    isBlacklisted,
    blockIP,
    periodLabel = ''
  } = $props();
</script>

<div class="grid grid-cols-1 md:grid-cols-12 gap-6" in:fade>
   <!-- Biểu đồ tần suất -->
   <div class="col-span-12 md:col-span-8 bg-white/[0.02] border border-white/5 rounded-none p-6 flex flex-col shadow-2xl relative group overflow-hidden">
      <div class="absolute inset-0 bg-gradient-to-br from-cyan-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-1000 pointer-events-none"></div>
      
      <div class="flex items-center gap-3 mb-8 pb-5 border-b border-white/5 relative z-10">
         <div class="p-2 rounded-none bg-cyan-500/10 border border-cyan-500/20">
            <Activity size={18} class="text-cyan-400" />
         </div>
         <h3 class="text-[10px] font-black tracking-[0.2em] text-slate-400 font-mono ">Phân tích xu hướng gian lận ({periodLabel})</h3>
      </div>
      
      <div class="mt-6">
         {#if summary?.hourly_breakdown?.length > 0}
            <div class="flex flex-col gap-6">
               <div class="relative w-full aspect-[21/9] min-h-[200px] flex">
               <!-- Y-Axis Labels -->
               <div class="w-10 h-full flex flex-col justify-between text-[8px] text-slate-500 font-mono pb-2">
                  <span>100%</span>
                  <span>75%</span>
                  <span>50%</span>
                  <span>25%</span>
                  <span>0%</span>
               </div>
               
               <div class="flex-1 relative h-full border-l border-b border-white/5">
                  <svg class="w-full h-full overflow-visible" viewBox="0 0 1000 300" preserveAspectRatio="none">
                     <defs>
                        <linearGradient id="lineGradient" x1="0" y1="0" x2="1" y2="0">
                           <stop offset="0%" stop-color="#ff3e5e" />
                           <stop offset="100%" stop-color="#00f3ff" />
                        </linearGradient>
                        <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
                           <stop offset="0%" stop-color="#ff3e5e" stop-opacity="0.3" />
                           <stop offset="100%" stop-color="#ff3e5e" stop-opacity="0" />
                        </linearGradient>
                     </defs>

                     <!-- Grid -->
                     {#each [0, 0.25, 0.5, 0.75, 1] as p}
                        <line x1="0" y1={300 - (p * 300)} x2="1000" y2={300 - (p * 300)} stroke="white" stroke-opacity="0.03" stroke-width="1" />
                     {/each}

                     <!-- Area Fill (Smooth) -->
                     <path 
                        d="M 0 300 
                           {(() => {
                              const points = summary.hourly_breakdown.map((h, i) => ({
                                 x: (i / Math.max(summary.hourly_breakdown.length - 1, 1)) * 1000,
                                 y: 300 - (h.fraud_rate * 300)
                              }));
                              if (points.length < 2) return "";
                              let d = `L ${points[0].x} ${points[0].y}`;
                              for (let i = 0; i < points.length - 1; i++) {
                                 const p0 = points[i];
                                 const p1 = points[i + 1];
                                 const cp1x = p0.x + (p1.x - p0.x) / 1.5;
                                 d += ` C ${cp1x} ${p0.y}, ${cp1x} ${p1.y}, ${p1.x} ${p1.y}`;
                              }
                              return d;
                           })()} 
                           L 1000 300 Z"
                        fill="url(#areaGradient)"
                     />

                     <!-- Main Line (Smooth) -->
                     <path 
                        d="{(() => {
                           const points = summary.hourly_breakdown.map((h, i) => ({
                              x: (i / Math.max(summary.hourly_breakdown.length - 1, 1)) * 1000,
                              y: 300 - (h.fraud_rate * 300)
                           }));
                           if (points.length < 1) return "";
                           let d = `M ${points[0].x} ${points[0].y}`;
                           for (let i = 0; i < points.length - 1; i++) {
                              const p0 = points[i];
                              const p1 = points[i + 1];
                              const cp1x = p0.x + (p1.x - p0.x) / 1.5;
                              d += ` C ${cp1x} ${p0.y}, ${cp1x} ${p1.y}, ${p1.x} ${p1.y}`;
                           }
                           return d;
                        })()}"
                        fill="none"
                        stroke="url(#lineGradient)"
                        stroke-width="2"
                        stroke-linecap="round"
                        class="transition-all duration-700"
                     />

                     <!-- Hover Tooltip Line & Points -->
                     {#each summary.hourly_breakdown as h, i}
                        <g class="group/point">
                           <line 
                              x1={(i / Math.max(summary.hourly_breakdown.length - 1, 1)) * 1000} y1="0" 
                              x2={(i / Math.max(summary.hourly_breakdown.length - 1, 1)) * 1000} y2="300" 
                              stroke="white" stroke-opacity="0" class="group-hover/point:stroke-opacity-10 transition-opacity" stroke-dasharray="4" 
                           />
                           <circle 
                              cx={(i / Math.max(summary.hourly_breakdown.length - 1, 1)) * 1000} 
                              cy={300 - (h.fraud_rate * 300)} 
                              r="4" 
                              fill="#ff3e5e" 
                              class="opacity-0 group-hover/point:opacity-100 transition-opacity"
                           />
                           <rect 
                              x={(i / Math.max(summary.hourly_breakdown.length - 1, 1)) * 1000 - 20} 
                              y="0" width="40" height="300" 
                              fill="transparent" 
                              class="cursor-crosshair"
                           >
                              <title>{new Date(h.hour).getHours()}h: {(h.fraud_rate * 100).toFixed(1)}%</title>
                           </rect>
                        </g>
                     {/each}
                  </svg>
               </div>
            </div>
         </div>
            
            <!-- X-Axis Labels -->
            <div class="flex justify-between px-12 mt-4">
               {#each summary.hourly_breakdown.filter((_, i) => i % (Math.ceil(summary.hourly_breakdown.length / 6)) === 0) as h}
                  <span class="text-[8px] text-slate-500 font-mono font-bold">{new Date(h.hour).getHours()}h</span>
               {/each}
            </div>
         {:else}
            <div class="min-h-[300px] flex flex-col items-center justify-center gap-4 text-[10px] tracking-[0.4em] text-slate-700 font-black relative overflow-hidden">
               <div class="absolute inset-0 flex items-center justify-center">
                  <div class="w-64 h-64 bg-cyan-500/5 rounded-none blur-[100px] animate-pulse"></div>
               </div>
               <Activity size={32} class="animate-pulse" />
               <span class="relative z-10">Đang quét tín hiệu môi trường...</span>
            </div>
         {/if}
      </div>
   </div>

    <!-- Danh sách IP -->
    <div class="col-span-12 md:col-span-4 bg-white/[0.02] border border-white/5 rounded-none p-6 flex flex-col shadow-2xl relative group overflow-hidden h-fit">
       <div class="absolute inset-0 bg-gradient-to-br from-rose-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-1000 pointer-events-none"></div>

       <div class="flex items-center gap-3 mb-8 pb-5 border-b border-white/5 relative z-10">
          <div class="p-2 rounded-none bg-rose-500/10 border border-rose-500/20">
             <ShieldAlert size={18} class="text-rose-500" />
          </div>
          <h3 class="text-[10px] font-black tracking-[0.2em] text-rose-500/80 font-mono ">Mục tiêu nguy cơ cao</h3>
       </div>

       <div class="max-h-[400px] overflow-y-auto custom-scrollbar flex flex-col gap-4 pr-2 relative z-10">
          {#each summary?.top_offending_ips || [] as item}
             <div class="bg-black/40 border border-white/10 p-5 rounded-none flex justify-between items-center group/item hover:border-rose-500/40 transition-all hover:bg-rose-500/[0.03]" in:slide>
               <div class="flex flex-col gap-1.5">
                  <span class="text-sm font-black font-mono text-rose-500 tracking-tighter group-hover/item:text-rose-400 transition-colors">{item.ip}</span>
                  <div class="flex items-center gap-2">
                     <span class="w-1.5 h-1.5 rounded-none bg-rose-500 animate-pulse"></span>
                     <span class="text-[9px] text-slate-500 font-mono font-bold">{item.click_count} lượt vi phạm</span>
                  </div>
               </div>
                {#if isBlacklisted(item.ip)}
                   <div class="px-3 py-1.5 bg-emerald-500/10 border border-emerald-500/30 text-emerald-500 text-[8px] font-mono font-black tracking-widest rounded-none shadow-inner">Đã khóa</div>
                {:else}
                   <button 
                      class="px-5 py-2.5 bg-gradient-to-r from-rose-600 to-rose-700 text-white text-[9px] font-black tracking-widest hover:from-rose-500 hover:to-rose-600 transition-all active:scale-[0.98] shadow-xl rounded-none border border-white/10 "
                      onclick={() => blockIP(item.ip)}
                   >
                      Chặn IP
                   </button>
                {/if}
            </div>
         {:else}
            <div class="h-full flex flex-col items-center justify-center text-[10px] text-slate-700 font-mono gap-4 py-20">
               <ShieldAlert size={32} class="opacity-20" />
               <span class="tracking-widest">Không phát hiện mục tiêu nghi vấn.</span>
            </div>
         {/each}
      </div>
   </div>
</div>
