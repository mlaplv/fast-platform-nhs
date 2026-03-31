<script lang="ts">
  import { onMount, untrack } from "svelte";
  import MissionControlShell from "$lib/components/admin/ui/MissionControlShell.svelte";
  import Globe from "lucide-svelte/icons/globe";
  import ExternalLink from "lucide-svelte/icons/external-link";
  import Shield from "lucide-svelte/icons/shield";
  import Type from "lucide-svelte/icons/type";
  import { Z_INDEX_ADMIN } from "$lib/core/constants/z_index_admin";

  interface LinkData {
    url: string;
    title?: string;
    target?: string | null;
    rel?: string | null;
  }

  let { 
    show = $bindable(), 
    currentData = { url: '', title: '', target: null, rel: null },
    onApply
  }: {
    show: boolean;
    currentData: LinkData;
    onApply: (data: LinkData) => void;
  } = $props();

  let linkUrl = $state('');
  let linkTitle = $state('');
  let isTargetBlank = $state(false);
  let isNoFollow = $state(false);
  
  $effect(() => {
    if (show) {
      untrack(() => {
        linkUrl = currentData.url || '';
        linkTitle = currentData.title || '';
        isTargetBlank = currentData.target === '_blank';
        isNoFollow = !!currentData.rel?.includes('nofollow');
      });
    }
  });

  function handleApply() {
    onApply({
      url: linkUrl.trim(),
      title: linkTitle.trim(),
      target: isTargetBlank ? '_blank' : null,
      rel: isNoFollow ? 'nofollow noopener noreferrer' : null
    });
    show = false;
  }
</script>

<MissionControlShell
  title="LINK_COMMAND_CENTER"
  node="SEO_OPTIMIZER_v2"
  protocol="HYPERLINK_CONTROL"
  isOpen={show}
  onClose={() => show = false}
  headerIcon={Globe}
  maxWidth="max-w-xl"
  height="h-auto"
  zIndex={Z_INDEX_ADMIN.MODAL}
  backdropClass="bg-black/90 backdrop-blur-xl"
>
  <div class="px-8 py-8 flex flex-col gap-6">
    
    <!-- SECTION 1: CORE DATA -->
    <div class="grid grid-cols-1 gap-5">
      <!-- URL Input -->
      <div class="field-group">
        <label class="field-label">
          <Globe size={10} class="text-cyan-400/50" />
          Target URL / Destination
        </label>
        <div class="relative">
          <input
            type="url"
            placeholder="https://example.com/target-page"
            bind:value={linkUrl}
            onkeydown={(e) => e.key === 'Enter' && handleApply()}
            class="field-input font-mono text-xs text-cyan-400 !bg-black/40 !border-white/5 focus:!border-cyan-500/50"
          />
          <div class="field-line"></div>
        </div>
      </div>

      <!-- Title/Alt Input -->
      <div class="field-group">
        <label class="field-label">
          <Type size={10} class="text-cyan-400/50" />
          Link Title (SEO ALT Text)
        </label>
        <div class="relative">
          <input
            type="text"
            placeholder="Descriptive text for SEO..."
            bind:value={linkTitle}
            onkeydown={(e) => e.key === 'Enter' && handleApply()}
            class="field-input text-xs text-white/80 !bg-black/40 !border-white/5 focus:!border-cyan-500/50"
          />
          <div class="field-line"></div>
        </div>
        <p class="text-[8px] text-white/10 italic">Tooltip hiển thị khi di chuột và giúp Crawler hiểu ngữ cảnh.</p>
      </div>
    </div>

    <!-- SECTION 2: ATTRIBUTES -->
    <div class="flex flex-wrap gap-4 pt-2 border-t border-white/5">
      <!-- Target Blank -->
      <button 
        onclick={() => isTargetBlank = !isTargetBlank}
        class="flex-1 min-w-[140px] flex items-center justify-between px-4 py-3 rounded-xl border transition-all
          {isTargetBlank ? 'bg-cyan-500/10 border-cyan-500/40 text-cyan-400' : 'bg-white/[0.02] border-white/5 text-white/20'}"
      >
        <div class="flex items-center gap-3">
          <ExternalLink size={14} />
          <span class="text-[10px] font-black uppercase tracking-widest">New Tab</span>
        </div>
        <div class="w-2 h-2 rounded-full {isTargetBlank ? 'bg-cyan-500 animate-pulse' : 'bg-white/10'}"></div>
      </button>

      <!-- No Follow -->
      <button 
        onclick={() => isNoFollow = !isNoFollow}
        class="flex-1 min-w-[140px] flex items-center justify-between px-4 py-3 rounded-xl border transition-all
          {isNoFollow ? 'bg-orange-500/10 border-orange-500/40 text-orange-400' : 'bg-white/[0.02] border-white/5 text-white/20'}"
      >
        <div class="flex items-center gap-3">
          <Shield size={14} />
          <span class="text-[10px] font-black uppercase tracking-widest">No Follow</span>
        </div>
        <div class="w-2 h-2 rounded-full {isNoFollow ? 'bg-orange-500 animate-pulse' : 'bg-white/10'}"></div>
      </button>
    </div>

    <!-- ACTION BUTTONS -->
    <div class="flex gap-4 mt-4 pt-4 border-t border-white/5 justify-end">
      <button 
        onclick={() => show = false} 
        class="px-6 py-2.5 text-[10px] font-black uppercase tracking-[0.2em] text-white/20 hover:text-white transition-colors cursor-pointer"
      >Discard</button>
      <button 
        onclick={handleApply} 
        class="px-10 py-2.5 bg-gradient-to-r from-cyan-500 to-blue-600 text-black text-[10px] font-black uppercase tracking-[0.25em] rounded-xl hover:brightness-110 active:scale-95 transition-all cursor-pointer box-shadow-cyan"
      >Inject Link</button>
    </div>
  </div>
</MissionControlShell>

<style>
  @reference "tailwindcss";

  .box-shadow-cyan {
    box-shadow: 0 0 20px rgba(6, 182, 212, 0.2);
  }

  .field-group {
    @apply flex flex-col gap-2.5;
  }

  .field-label {
    @apply flex items-center gap-2 text-[9px] font-black text-white/30 uppercase tracking-[0.2em];
  }

  .field-input {
    @apply w-full bg-transparent border-b border-white/10 px-0 py-2 outline-none transition-all;
  }

  .field-line {
    @apply absolute bottom-0 left-0 w-0 h-px bg-cyan-400 transition-all duration-500;
  }

  .field-input:focus + .field-line {
    @apply w-full;
  }
</style>
