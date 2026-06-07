<script lang="ts">
  import Target from "@lucide/svelte/icons/target";
  import Brain from "@lucide/svelte/icons/brain";

  let {
    fAd = $bindable(),
    aiGenerating = false,
    aiSuggestRSA,
    adSubmitting = false,
    submitAd,
    onBack,
    isEditingAd = false
  } = $props<{
    fAd: {
      final_url: string;
      display_path1: string;
      display_path2: string;
      headlines: string[];
      descriptions: string[];
      status: string;
    };
    aiGenerating?: boolean;
    aiSuggestRSA: (url: string) => void;
    adSubmitting?: boolean;
    submitAd: () => void;
    onBack: () => void;
    isEditingAd?: boolean;
  }>();

  // Derived filled counters
  let headlinesFilled = $derived(fAd?.headlines ? fAd.headlines.filter(h => h && h.trim()).length : 0);
  let descsFilled = $derived(fAd?.descriptions ? fAd.descriptions.filter(d => d && d.trim()).length : 0);
</script>

<div class="bg-white/[0.03] border border-white/10 p-8 shadow-2xl relative overflow-hidden group/form">
  <div class="absolute top-0 right-0 w-80 h-80 bg-cyan-500/5 blur-[100px] rounded-none pointer-events-none"></div>
  
  <div class="flex justify-between items-center mb-8 pb-6 border-b border-white/10 relative z-10">
    <div class="flex items-center gap-5">
      <div class="p-3 bg-emerald-400/10 rounded-none border border-emerald-400/20">
        <Target size={24} class="text-emerald-400" />
      </div>
      <div>
        <h4 class="text-lg font-black text-white tracking-wider font-mono">
          {isEditingAd ? 'Hiệu chỉnh Mẫu quảng cáo RSA' : 'Khởi tạo Mẫu quảng cáo RSA'}
        </h4>
        <p class="text-[10px] text-slate-500 font-mono mt-1 font-black">RSA (Responsive Search Ad) • Tiêu chuẩn tối ưu 2026</p>
      </div>
    </div>
    
    <div class="flex items-center gap-3">
      <button 
        type="button"
        class="px-5 py-2.5 bg-purple-600/10 border border-purple-500/30 text-purple-400 text-[10px] font-black tracking-wider hover:bg-purple-500 hover:text-white transition-all flex items-center gap-2 rounded-none group/ai"
        onclick={() => aiSuggestRSA(fAd.final_url)} 
        disabled={aiGenerating || !fAd.final_url}
        title="Tự động sinh tiêu đề, mô tả và display paths từ trang đích"
      >
        <Brain size={14} class="{aiGenerating ? 'animate-spin' : 'group-hover/ai:scale-110 transition-transform'}" /> 
        <span>Xohi AI gợi ý mẫu</span>
      </button>
    </div>
  </div>

  <div class="space-y-6 relative z-10">
    <!-- URL & Paths -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div class="md:col-span-2">
        <label class="block text-[9px] text-slate-400 font-black mb-2 tracking-widest font-mono">FINAL URL (Trang đích)</label>
        <input 
          type="text" 
          bind:value={fAd.final_url} 
          class="w-full bg-black/40 border border-white/10 rounded-none p-4 text-xs font-black text-white focus:border-cyan-400/50 outline-none transition-all" 
          placeholder="https://example.com/san-pham" 
        />
      </div>
      <div>
        <label class="block text-[9px] text-slate-400 font-black mb-2 tracking-widest font-mono">ĐƯỜNG DẪN HIỂN THỊ (Path 1 / Path 2)</label>
        <div class="flex items-center bg-black/40 border border-white/10 px-2 py-1">
          <span class="text-[10px] text-slate-600 font-mono select-none">/</span>
          <input 
            type="text" 
            bind:value={fAd.display_path1} 
            maxlength="15"
            class="w-full bg-transparent border-none p-2 text-xs font-mono font-black text-white outline-none focus:text-cyan-400" 
            placeholder="path1" 
          />
          <span class="text-[10px] text-slate-600 font-mono select-none">/</span>
          <input 
            type="text" 
            bind:value={fAd.display_path2} 
            maxlength="15"
            class="w-full bg-transparent border-none p-2 text-xs font-mono font-black text-white outline-none focus:text-cyan-400" 
            placeholder="path2" 
          />
        </div>
      </div>
    </div>

    <!-- Headlines -->
    <div>
      <div class="flex justify-between items-center mb-3">
        <label class="text-[9px] text-slate-400 font-black tracking-widest font-mono">DÒNG TIÊU ĐỀ (Tối đa 15 tiêu đề - Dài tối đa 30 ký tự)</label>
        <span class="text-[9px] font-mono font-black {headlinesFilled >= 12 ? 'text-emerald-400' : 'text-yellow-500'}">
          Đã điền: {headlinesFilled}/15 (Tối thiểu 12 tiêu đề)
        </span>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        {#each Array(15) as _, i}
          <div class="relative flex items-center bg-black/30 border border-white/5 focus-within:border-cyan-400/30 transition-all">
            <span class="pl-3 text-[9px] font-mono text-slate-600 font-black select-none">#{i+1}</span>
            <input 
              type="text" 
              bind:value={fAd.headlines[i]} 
              maxlength="30"
              class="w-full bg-transparent border-none p-3 pl-2 text-xs font-black text-white outline-none" 
              placeholder="Tiêu đề hấp dẫn..." 
            />
            <span class="pr-3 text-[8px] font-mono text-slate-600 select-none">
              {(fAd.headlines[i] || '').length}/30
            </span>
          </div>
        {/each}
      </div>
    </div>

    <!-- Descriptions -->
    <div>
      <div class="flex justify-between items-center mb-3">
        <label class="text-[9px] text-slate-400 font-black tracking-widest font-mono">NỘI DUNG MÔ TẢ (Tối đa 4 mô tả - Dài tối đa 90 ký tự)</label>
        <span class="text-[9px] font-mono font-black {descsFilled >= 4 ? 'text-emerald-400' : 'text-yellow-500'}">
          Đã điền: {descsFilled}/4
        </span>
      </div>
      <div class="space-y-3">
        {#each Array(4) as _, i}
          <div class="relative flex items-center bg-black/30 border border-white/5 focus-within:border-cyan-400/30 transition-all">
            <span class="pl-4 text-[9px] font-mono text-slate-600 font-black select-none">Mô tả #{i+1}</span>
            <input 
              type="text" 
              bind:value={fAd.descriptions[i]} 
              maxlength="90"
              class="w-full bg-transparent border-none p-4 pl-3 text-xs font-black text-white outline-none" 
              placeholder="Mô tả chi tiết về sản phẩm, dịch vụ hoặc ưu đãi..." 
            />
            <span class="pr-4 text-[8px] font-mono text-slate-600 select-none">
              {(fAd.descriptions[i] || '').length}/90
            </span>
          </div>
        {/each}
      </div>
    </div>

    <!-- Status Select -->
    <div class="flex justify-between items-center pt-4 border-t border-white/10">
      <div class="flex items-center gap-4">
        <label class="text-[9px] text-slate-400 font-black tracking-widest font-mono">TRẠNG THÁI KHỞI CHẠY</label>
        <select 
          bind:value={fAd.status} 
          class="bg-black border border-white/10 text-xs text-white p-2 font-mono font-black outline-none"
        >
          <option value="ENABLED">ĐANG CHẠY (ENABLED)</option>
          <option value="PAUSED">TẠM DỪNG (PAUSED)</option>
        </select>
      </div>

      <div class="flex items-center gap-4">
        <button 
          type="button"
          class="px-6 py-3 bg-white/5 border border-white/10 text-white text-[10px] font-black tracking-widest hover:bg-white/10 transition-all"
          onclick={onBack}
        >
          QUAY LẠI
        </button>
        <button 
          type="button"
          class="px-10 py-3 bg-emerald-600 hover:bg-emerald-500 text-white text-[10px] font-black tracking-widest transition-all shadow-lg shadow-emerald-950/20 active:scale-95"
          onclick={submitAd}
          disabled={adSubmitting}
        >
          {adSubmitting ? 'ĐANG XUẤT BẢN...' : 'XUẤT BẢN QUẢNG CÁO'}
        </button>
      </div>
    </div>
  </div>
</div>
