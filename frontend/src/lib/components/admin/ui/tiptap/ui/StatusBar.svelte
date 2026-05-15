<script lang="ts">
  import FileText from "@lucide/svelte/icons/file-text";
  import Type from "@lucide/svelte/icons/type";
  import Clock from "@lucide/svelte/icons/clock";

  let { wordCount, charCount, isFocused, readTime }: {
    wordCount: number;
    charCount: number;
    isFocused: boolean;
    readTime: string;
  } = $props();
</script>

<div class="flex items-center gap-6 px-6 py-2.5 bg-black/20 border-t border-white/5 text-[9px] font-black tracking-[0.2em] text-white/20 shrink-0 shadow-2xl">
  <div class="flex items-center gap-2">
    <FileText size={10} class="text-white/10" />
    <span>{wordCount} Words</span>
  </div>
  <div class="flex items-center gap-2">
    <Type size={10} class="text-white/10" />
    <span>{charCount} Chars</span>
  </div>
  
  <div class="ml-auto flex items-center gap-3">
    <div class="flex items-center gap-2 bg-white/5 px-3 py-1 rounded-full border border-white/5">
      <Clock size={10} class="text-cyan-500/40" />
      <span class="text-cyan-500/60 lowercase italic tracking-tight">{readTime}</span>
    </div>
    
    <div class="flex items-center gap-2 ml-2">
      <span class="text-[8px] {isFocused ? 'text-cyan-400 opacity-100' : 'text-white/10 opacity-50'} transition-all duration-500">
        {isFocused ? 'Neural_Focus_Active' : 'Standby_Mode'}
      </span>
      <div class="w-1.5 h-1.5 rounded-full {isFocused ? 'bg-cyan-500 shadow-[0_0_12px_rgba(6,182,212,1)]' : 'bg-white/10'} transition-all duration-700"></div>
    </div>
  </div>
</div>
