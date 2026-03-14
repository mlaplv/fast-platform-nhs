<script lang="ts">
  let { wordCount, charCount, isFocused, readTime }: {
    wordCount: number;
    charCount: number;
    isFocused: boolean;
    readTime: string;
  } = $props();
</script>

<div class="flex items-center gap-4 px-4 py-1.5 bg-white/[0.02] border-t border-white/5 text-[10px] text-white/30 font-mono shrink-0">
  <span>📄 {wordCount} từ</span>
  <span>🔤 {charCount} ký tự</span>
  <span class="ml-auto text-blue-500/50">{readTime}</span>
  <div class="w-1.5 h-1.5 rounded-full {isFocused ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]' : 'bg-white/20'} transition-colors ml-2" title={isFocused ? 'Đang soạn thảo...' : 'Đang tạm dừng'}></div>
</div>
