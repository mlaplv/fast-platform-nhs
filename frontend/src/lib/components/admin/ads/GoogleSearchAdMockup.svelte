<script lang="ts">
  let {
    final_url = '',
    display_path1 = '',
    display_path2 = '',
    headlines = [],
    descriptions = []
  } = $props<{
    final_url?: string;
    display_path1?: string;
    display_path2?: string;
    headlines?: string[];
    descriptions?: string[];
  }>();

  // Helper to get domain name
  const getDomain = (url: string) => {
    if (!url) return 'your-domain.com';
    try {
      return url.replace(/^https?:\/\//, '').split('/')[0];
    } catch {
      return 'your-domain.com';
    }
  };
</script>

<div class="bg-[#171717] border border-white/5 p-6 rounded-none shadow-xl">
  <div class="flex items-center justify-between mb-4 pb-2 border-b border-white/5">
    <span class="text-[9px] text-slate-500 font-mono font-black tracking-wider uppercase">Google Search Preview (Real-time)</span>
    <div class="flex gap-1.5">
      <span class="w-2 h-2 rounded-full bg-red-500/30"></span>
      <span class="w-2 h-2 rounded-full bg-yellow-500/30"></span>
      <span class="w-2 h-2 rounded-full bg-green-500/30"></span>
    </div>
  </div>
  
  <!-- Google Result Card -->
  <div class="bg-white text-black p-5 rounded-lg shadow-md font-sans text-sm">
    <div class="flex items-center gap-2 text-xs text-slate-600 mb-1">
      <span class="font-bold text-black text-[11px] bg-slate-100 px-1.5 py-0.5 rounded">Tài trợ</span>
      <span class="text-slate-400 select-none">•</span>
      <span class="hover:underline cursor-pointer truncate max-w-[200px] text-slate-700 text-left">
        {getDomain(final_url)}
        {#if display_path1}
          <span class="text-slate-500"> &gt; {display_path1}</span>
        {/if}
        {#if display_path2}
          <span class="text-slate-500"> &gt; {display_path2}</span>
        {/if}
      </span>
    </div>
    
    <!-- Title (Blue Link) -->
    <h4 class="text-blue-800 text-lg hover:underline cursor-pointer font-medium leading-tight mb-1 tracking-normal text-left">
      {#if headlines && headlines.filter(h => h && h.trim()).length > 0}
        {headlines.filter(h => h && h.trim()).slice(0, 3).join(' | ')}
      {:else}
        Nhập tiêu đề hoặc bấm gợi ý AI...
      {/if}
    </h4>

    <!-- Description (Grey text) -->
    <p class="text-slate-700 text-xs leading-relaxed text-left">
      {#if descriptions && descriptions.filter(d => d && d.trim()).length > 0}
        {descriptions.filter(d => d && d.trim()).slice(0, 2).join(' ')}
      {:else}
        Nhập mô tả sản phẩm ở cột bên trái...
      {/if}
    </p>
  </div>
</div>
