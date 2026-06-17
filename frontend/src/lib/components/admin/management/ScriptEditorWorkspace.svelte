<script lang="ts">
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import ShoppingBag from "@lucide/svelte/icons/shopping-bag";
  import Palette from "@lucide/svelte/icons/palette";
  import User from "@lucide/svelte/icons/user";
  import Clock from "@lucide/svelte/icons/clock";
  import FileText from "@lucide/svelte/icons/file-text";
  import Eye from "@lucide/svelte/icons/eye";
  import type { VideoScript, VideoScene } from "$lib/types";

  import PlaybackSimulator from "./PlaybackSimulator.svelte";
  import CompetitiveIntel from "./CompetitiveIntel.svelte";
  import ScriptTimeline from "./ScriptTimeline.svelte";

  interface Props {
    activeScript: VideoScript | null;
    saveStatus: string;
    isPlaying: boolean;
    ttsEnabled: boolean;
    selectedVoice: string;
    isPreloadingAudio: boolean;
    activeSceneIdx: number | null;
    playbackTime: number;
    generatingImageMap: Record<number, boolean>;
    copiedTextMap: Record<number, boolean>;
    showPromptHub: boolean;
    triggerAutoSave: () => void;
    startPlayback: () => void;
    stopPlayback: () => void;
    downloadMarkdown: (script: VideoScript) => void;
    handleDelete: (id: string, title: string) => void;
    moveScene: (idx: number, direction: 'up' | 'down') => void;
    insertScene: (idx: number) => void;
    deleteScene: (idx: number) => void;
    downloadSceneAudio: (scene: VideoScene) => void;
    handleImageUpload: (e: Event, sceneIdx: number) => void;
    openMediaLibrary: (sceneIdx: number) => void;
    generateAiImage: (sceneIdx: number) => void;
    pasteImageUrl: (sceneIdx: number) => void;
    copyPrompt: (text: string, index: number) => void;
  }

  let {
    activeScript,
    saveStatus,
    isPlaying = $bindable(),
    ttsEnabled = $bindable(),
    selectedVoice = $bindable(),
    isPreloadingAudio,
    activeSceneIdx,
    playbackTime,
    generatingImageMap,
    copiedTextMap,
    showPromptHub = $bindable(),
    triggerAutoSave,
    startPlayback,
    stopPlayback,
    downloadMarkdown,
    handleDelete,
    moveScene,
    insertScene,
    deleteScene,
    downloadSceneAudio,
    handleImageUpload,
    openMediaLibrary,
    generateAiImage,
    pasteImageUrl,
    copyPrompt
  }: Props = $props();
</script>

<!-- RIGHT COLUMN: Detail Pro Editor Workspace -->
<div class="flex-1 flex flex-col h-full bg-[#020202] overflow-hidden">
  {#if !activeScript}
    <div class="flex-1 flex flex-col items-center justify-center gap-4 text-gray-500 p-8">
      <div class="w-16 h-16 rounded-2xl bg-cyan-950/10 border border-cyan-500/20 flex items-center justify-center relative group">
        <div class="absolute inset-0 rounded-2xl bg-cyan-500/10 blur-md opacity-50 group-hover:opacity-100 transition-opacity"></div>
        <Sparkles class="w-6 h-6 text-cyan-400 animate-pulse" />
      </div>
      <div class="text-center">
        <h3 class="text-xs font-bold tracking-widest text-cyan-400 uppercase">PRO SCRIPTS ENGINE IDLE</h3>
        <p class="text-[10px] text-gray-600 mt-1 max-w-xs leading-relaxed">
          Chọn kịch bản ở thanh menu bên trái hoặc click "Tạo mới" để bắt đầu thiết kế kịch bản tiếp thị chuyên nghiệp.
        </p>
      </div>
    </div>
  {:else}
    <!-- Detail Workspace Header -->
    <div class="p-4 border-b border-[#151515] bg-[#050505] flex flex-col xl:flex-row xl:items-center justify-between gap-4 shrink-0">
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-3">
          <input
            type="text"
            bind:value={activeScript.title}
            oninput={triggerAutoSave}
            class="bg-transparent text-sm font-semibold text-white tracking-wide border-b border-transparent hover:border-gray-800 focus:border-cyan-500 focus:outline-none py-0.5 w-full max-w-xl transition-all"
            placeholder="Nhập tiêu đề kịch bản..."
          />
          
          <!-- Auto-save neon status dot -->
          <div class="flex items-center gap-1.5 shrink-0 px-2 py-0.5 rounded bg-[#111] border border-gray-800">
            <span class="w-1.5 h-1.5 rounded-full 
                         {saveStatus === 'Saved' 
                           ? 'bg-cyan-400 shadow-sm shadow-cyan-400' 
                           : saveStatus === 'Saving...' 
                             ? 'bg-yellow-400 animate-pulse' 
                             : 'bg-red-500 animate-ping'}"
            ></span>
            <span class="text-[9px] font-mono text-gray-400 uppercase tracking-wide">{saveStatus}</span>
          </div>
        </div>

        <div class="mt-2.5 flex flex-wrap items-center gap-2 text-[10px] text-gray-400">
          <span class="flex items-center gap-1 bg-[#111] px-2 py-0.5 rounded border border-gray-800">
            <ShoppingBag class="w-3 h-3 text-pink-500" />
            <span>Sản phẩm: <strong class="text-gray-200">{activeScript.product_name}</strong></span>
          </span>
          <span class="flex items-center gap-1 bg-[#111] px-2 py-0.5 rounded border border-gray-800">
            <Palette class="w-3 h-3 text-cyan-400" />
            <span>Style: <strong class="text-gray-200">{activeScript.style_name}</strong></span>
          </span>
          <span class="flex items-center gap-1 bg-[#111] px-2 py-0.5 rounded border border-gray-800">
            <User class="w-3 h-3 text-purple-400" />
            <span>Đối tượng: <strong class="text-gray-200">{activeScript.structured_script?.target_audience || "Mọi người"}</strong></span>
          </span>
          <span class="flex items-center gap-1 bg-[#111] px-2 py-0.5 rounded border border-gray-800">
            <Clock class="w-3 h-3 text-yellow-400" />
            <span>Tổng thời lượng: <strong class="text-gray-200">{activeScript.structured_script?.total_duration || 0}s</strong></span>
          </span>
        </div>
      </div>

      <PlaybackSimulator
        bind:isPlaying={isPlaying}
        bind:ttsEnabled={ttsEnabled}
        bind:selectedVoice={selectedVoice}
        isPreloadingAudio={isPreloadingAudio}
        activeSceneIdx={activeSceneIdx}
        playbackTime={playbackTime}
        activeScript={activeScript}
        startPlayback={startPlayback}
        stopPlayback={stopPlayback}
        downloadMarkdown={downloadMarkdown}
        handleDelete={handleDelete}
      />
    </div>

    <!-- Main Workspace Editor Panel -->
    <div class="flex-1 overflow-y-auto p-4 md:p-6 space-y-6 custom-scrollbar bg-[#020202]">
      
      <CompetitiveIntel activeScript={activeScript} />

      <!-- Script-level Notes section -->
      {#if activeScript.structured_script}
        <div class="bg-[#080808] border border-[#151515] rounded-xl p-4 space-y-2">
          <div class="flex items-center gap-2 border-b border-gray-900 pb-2">
            <FileText class="w-4 h-4 text-cyan-400" />
            <span class="text-[10px] font-mono font-bold tracking-widest text-gray-400 uppercase">GHI CHÚ ĐẠO DIỄN / ĐỊNH HƯỚNG CHUNG</span>
          </div>
          <textarea
            bind:value={activeScript.structured_script.notes}
            oninput={triggerAutoSave}
            placeholder="Viết ghi chú chung về tone giọng đọc, tông màu video, chỉ dẫn dựng phim cho cả dự án tại đây..."
            rows="2"
            class="w-full bg-transparent border-0 resize-none text-xs text-gray-300 placeholder:text-gray-600 focus:outline-none focus:ring-0 leading-relaxed font-sans"
          ></textarea>
        </div>
      {/if}

      <!-- AI Prompt Hub Bento Card -->
      <div class="grid grid-cols-1 gap-4">
        <!-- Trung tâm AI Generative Prompt -->
        <div class="bg-[#0b0c10]/60 border border-purple-500/20 rounded-xl p-5 relative overflow-hidden group">
          <div class="absolute -right-10 -bottom-10 w-32 h-32 bg-purple-500/5 rounded-full blur-2xl group-hover:bg-purple-500/10 transition-all duration-500"></div>
          
          <div class="flex items-center justify-between border-b border-gray-900/60 pb-3 mb-4">
            <div class="flex items-center gap-2">
              <Sparkles class="w-4 h-4 text-purple-400" />
              <span class="text-[10px] font-mono font-bold tracking-widest text-purple-400 uppercase">AI GENERATIVE PROMPT HUB</span>
            </div>
            <span class="text-[9px] font-mono bg-purple-900/20 text-purple-400 px-2 py-0.5 rounded border border-purple-500/20 animate-pulse">GENERATIVE PIXEL</span>
          </div>
          
          <div class="space-y-4 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <p class="text-[11px] text-gray-400 leading-relaxed font-sans md:max-w-2xl">
              Trích xuất hàng loạt các câu lệnh (prompts) tối ưu riêng cho từng nền tảng AI Video (Runway, Sora) và AI Image (Midjourney, Flux) để tạo ra thước phim điện ảnh cao cấp dựa trên kịch bản chi tiết này.
            </p>
            
            <button 
              onclick={() => { showPromptHub = true; }}
              class="flex-shrink-0 flex items-center justify-center gap-2 py-2.5 px-6 bg-gradient-to-r from-purple-700 to-pink-700 hover:from-purple-600 hover:to-pink-600 text-white rounded-lg font-semibold text-xs border border-purple-400/20 transition-all shadow-md shadow-purple-500/10 hover:shadow-purple-500/25 active:scale-[0.98]"
            >
              <Eye class="w-3.5 h-3.5" />
              <span>XEM & SAO CHÉP AI PROMPT BATCH</span>
            </button>
          </div>
        </div>
      </div>

      <ScriptTimeline
        activeScript={activeScript}
        activeSceneIdx={activeSceneIdx}
        generatingImageMap={generatingImageMap}
        copiedTextMap={copiedTextMap}
        triggerAutoSave={triggerAutoSave}
        moveScene={moveScene}
        insertScene={insertScene}
        deleteScene={deleteScene}
        downloadSceneAudio={downloadSceneAudio}
        handleImageUpload={handleImageUpload}
        openMediaLibrary={openMediaLibrary}
        generateAiImage={generateAiImage}
        pasteImageUrl={pasteImageUrl}
        copyPrompt={copyPrompt}
      />
    </div>
  {/if}
</div>
