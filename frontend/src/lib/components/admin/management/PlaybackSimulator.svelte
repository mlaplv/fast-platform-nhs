<script lang="ts">
  import Play from "@lucide/svelte/icons/play";
  import Square from "@lucide/svelte/icons/square";
  import Volume2 from "@lucide/svelte/icons/volume-2";
  import RefreshCw from "@lucide/svelte/icons/refresh-cw";
  import Download from "@lucide/svelte/icons/download";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import type { VideoScript } from "$lib/types";

  interface Props {
    isPlaying: boolean;
    ttsEnabled: boolean;
    selectedVoice: string;
    isPreloadingAudio: boolean;
    activeSceneIdx: number | null;
    playbackTime: number;
    activeScript: VideoScript;
    startPlayback: () => void;
    stopPlayback: () => void;
    downloadMarkdown: (script: VideoScript) => void;
    handleDelete: (id: string, title: string) => void;
  }

  let {
    isPlaying = $bindable(),
    ttsEnabled = $bindable(),
    selectedVoice = $bindable(),
    isPreloadingAudio,
    activeSceneIdx,
    playbackTime,
    activeScript,
    startPlayback,
    stopPlayback,
    downloadMarkdown,
    handleDelete
  }: Props = $props();
</script>

<!-- Playback Simulator controls -->
<div class="flex flex-wrap items-center gap-2 shrink-0">
  <div class="flex items-center gap-1 bg-black border border-gray-800 rounded-lg p-1">
    {#if isPlaying}
      <button
        onclick={stopPlayback}
        class="flex items-center justify-center p-1.5 bg-red-950/40 text-red-400 hover:bg-red-500/20 rounded transition-colors"
        title="Dừng giả lập"
      >
        <Square class="w-3.5 h-3.5 fill-current" />
      </button>
    {:else}
      <button
        onclick={startPlayback}
        class="flex items-center justify-center p-1.5 bg-cyan-950/40 text-cyan-400 hover:bg-cyan-500/20 rounded transition-colors"
        title="Chạy thử kịch bản"
      >
        <Play class="w-3.5 h-3.5 fill-current" />
      </button>
    {/if}
    
    <button
      onclick={() => { ttsEnabled = !ttsEnabled; }}
      class="flex items-center justify-center p-1.5 rounded transition-colors
             {ttsEnabled ? 'bg-purple-950/40 text-purple-400 border border-purple-500/20' : 'text-gray-500 hover:text-gray-300'}"
      title="Đọc thử giọng nói Việt (TTS)"
    >
      <Volume2 class="w-3.5 h-3.5" />
    </button>

    {#if ttsEnabled}
      <select
        bind:value={selectedVoice}
        class="bg-[#0b0c10] border border-purple-500/25 rounded px-2 py-0.5 text-[10px] text-purple-400 outline-none focus:border-purple-500 transition-all font-mono"
      >
        <option value="vi-VN-HoaiMyNeural">Hoài Mỹ (Nữ - Bắc - TikTok)</option>
        <option value="vi-VN-NamMinhNeural">Nam Minh (Nam - Bắc - Reviewer)</option>
      </select>
    {/if}

    {#if isPreloadingAudio}
      <span class="flex items-center gap-1 text-[10px] text-yellow-500 font-mono px-2 animate-pulse">
        <RefreshCw class="w-3 h-3 animate-spin text-yellow-500" />
        <span>Đang tải audio...</span>
      </span>
    {/if}

    {#if isPlaying}
      <div class="px-2 py-0.5 text-[10px] font-mono text-cyan-400 bg-cyan-950/20 rounded border border-cyan-500/20 flex items-center gap-1">
        <span>SCENE #{activeSceneIdx! + 1}</span>
        <span>•</span>
        <span>{playbackTime}s</span>
      </div>
    {/if}
  </div>

  <button
    onclick={() => downloadMarkdown(activeScript)}
    class="flex items-center gap-1.5 px-3 py-1.5 bg-cyan-950/30 hover:bg-cyan-500/20 border border-cyan-500/30 rounded text-[11px] font-mono tracking-wide text-cyan-400 transition-colors"
  >
    <Download class="w-3.5 h-3.5" />
    <span>EXPORT MD</span>
  </button>
  
  <button
    onclick={() => handleDelete(activeScript.id, activeScript.title)}
    class="p-2 bg-red-950/20 hover:bg-red-500/20 border border-red-500/30 rounded text-red-400 transition-colors"
    title="Xóa kịch bản"
  >
    <Trash2 class="w-3.5 h-3.5" />
  </button>
</div>
