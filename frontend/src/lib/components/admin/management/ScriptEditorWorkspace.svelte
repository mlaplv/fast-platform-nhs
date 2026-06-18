<script lang="ts">
  import { slide, fade } from "svelte/transition";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import ShoppingBag from "@lucide/svelte/icons/shopping-bag";
  import Palette from "@lucide/svelte/icons/palette";
  import User from "@lucide/svelte/icons/user";
  import Clock from "@lucide/svelte/icons/clock";
  import FileText from "@lucide/svelte/icons/file-text";
  import Eye from "@lucide/svelte/icons/eye";
  import Download from "@lucide/svelte/icons/download";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import ChevronLeft from "@lucide/svelte/icons/chevron-left";
  import ChevronRight from "@lucide/svelte/icons/chevron-right";
  import type { VideoScript, VideoScene } from "$lib/types";

  import CompetitiveIntel from "./CompetitiveIntel.svelte";
  import LandingPageMatchCard from "./LandingPageMatchCard.svelte";
  import ScriptTimeline from "./ScriptTimeline.svelte";
  import VideoScriptPromptHub from "./VideoScriptPromptHub.svelte";
  import ScriptEvaluationCard from "./ScriptEvaluationCard.svelte";

  interface Props {
    activeScript: VideoScript | null;
    saveStatus: string;
    copiedTextMap: Record<number, boolean>;
    showPromptHub: boolean;
    activePromptTab: "midjourney" | "runway" | "heygen" | "gemini";
    activeWorkspaceTab: 'intel' | 'match' | 'eval' | null;
    triggerAutoSave: () => void;
    downloadMarkdown: (script: VideoScript) => void;
    handleDelete: (id: string, title: string) => void;
    moveScene: (idx: number, direction: 'up' | 'down') => void;
    insertScene: (idx: number) => void;
    deleteScene: (idx: number) => void;
    copyPrompt: (text: string, index: number) => void;
    getMidjourneyPrompt: (scene: VideoScene, aspect: string) => string;
    getRunwayPrompt: (scene: VideoScene) => string;
    getGeminiPrompt: (scene: VideoScene) => string;
    getGeminiMasterPrompt: () => string;
    copyAllPrompts: (type: "midjourney" | "runway" | "heygen" | "gemini") => void;
    isEvaluating: boolean;
    isOptimizing: boolean;
    onEvaluate: () => Promise<void>;
    onForceEvaluate: () => Promise<void>;
    onOptimize: (focusCriterion?: string) => Promise<void>;
    isScriptModified: boolean;
    isSidebarOpen: boolean;
    toggleSidebar: () => void;
  }

  let {
    activeScript,
    saveStatus,
    copiedTextMap,
    showPromptHub = $bindable(),
    activePromptTab = $bindable(),
    activeWorkspaceTab = $bindable<'intel' | 'match' | 'eval' | null>('intel'),
    triggerAutoSave,
    downloadMarkdown,
    handleDelete,
    moveScene,
    insertScene,
    deleteScene,
    copyPrompt,
    getMidjourneyPrompt,
    getRunwayPrompt,
    getGeminiPrompt,
    getGeminiMasterPrompt,
    copyAllPrompts,
    isEvaluating,
    isOptimizing,
    onEvaluate,
    onForceEvaluate,
    onOptimize,
    isScriptModified,
    isSidebarOpen,
    toggleSidebar
  }: Props = $props();

  // activeWorkspaceTab giờ được bind từ parent nên xóa local state
</script>

<!-- RIGHT COLUMN: Detail Pro Editor Workspace -->
<div class="flex-1 flex flex-row h-full bg-[#020202] overflow-hidden">
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
    <!-- Main editor body -->
    <div class="flex-1 flex flex-col h-full overflow-hidden">
      <!-- Detail Workspace Header -->
      <div class="p-4 border-b border-[#151515] bg-[#050505] flex flex-col xl:flex-row xl:items-center justify-between gap-4 shrink-0">
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-3">
            <!-- Toggle Sidebar Button -->
            <button
              type="button"
              onclick={toggleSidebar}
              class="flex items-center justify-center w-7 h-7 rounded bg-[#111] hover:bg-[#161616] border border-gray-800 text-gray-400 hover:text-white transition-all shrink-0"
              title={isSidebarOpen ? "Đóng danh sách kịch bản" : "Mở danh sách kịch bản"}
            >
              {#if isSidebarOpen}
                <ChevronLeft class="w-4 h-4" />
              {:else}
                <ChevronRight class="w-4 h-4" />
              {/if}
            </button>

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

            <!-- Prompt Hub Toggle Button -->
            <button
              onclick={() => { showPromptHub = !showPromptHub; }}
              class="flex items-center gap-1.5 px-3 py-1 rounded bg-[#16161a] hover:bg-purple-900/25 border border-purple-500/20 text-purple-400 hover:text-purple-300 font-mono text-[9px] font-bold uppercase transition-all"
            >
              <Sparkles class="w-3.5 h-3.5 text-purple-400" />
              <span>{showPromptHub ? 'Đóng Prompt' : 'Mở Prompt'}</span>
            </button>
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

        <div class="flex items-center gap-2">
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
      </div>

      <!-- Main Workspace Editor Panel -->
      <div class="flex-1 overflow-y-auto p-4 md:p-6 space-y-6 custom-scrollbar bg-[#020202]">
        
        <!-- Unified Inspiration & CRO Workspace Tabs -->
        <div class="bg-[#080808] border border-[#151515] rounded-xl overflow-hidden">
          <!-- Tab Bar -->
          <div class="flex items-center justify-between px-3 py-2 bg-[#0a0a0a] border-b border-[#151515]">
            <div class="flex items-center gap-2">
              <button
                type="button"
                onclick={() => { activeWorkspaceTab = 'intel'; }}
                class="px-3 py-1.5 text-[9px] font-mono font-bold uppercase tracking-wider transition-all rounded-lg flex items-center gap-1.5 border
                       {activeWorkspaceTab === 'intel'
                         ? 'bg-[#121212] border-yellow-500/20 text-yellow-500 shadow-sm shadow-yellow-500/5'
                         : 'border-transparent text-gray-500 hover:text-gray-300'}"
              >
                <Sparkles class="w-3.5 h-3.5 {activeWorkspaceTab === 'intel' ? 'text-yellow-500' : 'text-gray-500'}" />
                <span>Phân tích đối thủ</span>
              </button>
              
              <button
                type="button"
                onclick={() => { activeWorkspaceTab = 'match'; }}
                class="px-3 py-1.5 text-[9px] font-mono font-bold uppercase tracking-wider transition-all rounded-lg flex items-center gap-1.5 border
                       {activeWorkspaceTab === 'match'
                         ? 'bg-[#121212] border-cyan-500/20 text-cyan-400 shadow-sm shadow-cyan-500/5'
                         : 'border-transparent text-gray-500 hover:text-gray-300'}"
              >
                <FileText class="w-3.5 h-3.5 {activeWorkspaceTab === 'match' ? 'text-cyan-400' : 'text-gray-500'}" />
                <span>Tối ưu Landing Page</span>
              </button>

              <button
                type="button"
                onclick={() => { activeWorkspaceTab = 'eval'; }}
                class="px-3 py-1.5 text-[9px] font-mono font-bold uppercase tracking-wider transition-all rounded-lg flex items-center gap-1.5 border
                       {activeWorkspaceTab === 'eval'
                         ? 'bg-[#121212] border-purple-500/20 text-purple-400 shadow-sm shadow-purple-500/5'
                         : 'border-transparent text-gray-500 hover:text-gray-300'}"
              >
                <Sparkles class="w-3.5 h-3.5 {activeWorkspaceTab === 'eval' ? 'text-purple-400' : 'text-gray-500'}" />
                <span>Đánh giá & Tối ưu AI</span>
              </button>
            </div>
            
            <button
              type="button"
              onclick={() => { activeWorkspaceTab = activeWorkspaceTab ? null : 'intel'; }}
              class="px-3 py-1.5 text-[9px] font-mono text-gray-500 hover:text-gray-300 uppercase transition-colors"
            >
              {activeWorkspaceTab ? 'Thu gọn' : 'Mở rộng'}
            </button>
          </div>

          <!-- Tab Content -->
          {#if activeWorkspaceTab}
            <div class="p-4 bg-black/20" transition:slide>
              {#if activeWorkspaceTab === 'intel'}
                <div transition:fade={{ duration: 150 }}>
                  <CompetitiveIntel activeScript={activeScript} />
                </div>
              {:else if activeWorkspaceTab === 'match'}
                <div transition:fade={{ duration: 150 }}>
                  <LandingPageMatchCard activeScript={activeScript} />
                </div>
              {:else if activeWorkspaceTab === 'eval'}
                <div transition:fade={{ duration: 150 }}>
                  {#if activeScript}
                    <ScriptEvaluationCard
                      activeScript={activeScript}
                      isEvaluating={isEvaluating}
                      isOptimizing={isOptimizing}
                      onEvaluate={onEvaluate}
                      onForceEvaluate={onForceEvaluate}
                      onOptimize={onOptimize}
                      isScriptModified={isScriptModified}
                    />
                  {/if}
                </div>
              {/if}
            </div>
          {/if}
        </div>

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

        <ScriptTimeline
          activeScript={activeScript}
          copiedTextMap={copiedTextMap}
          triggerAutoSave={triggerAutoSave}
          moveScene={moveScene}
          insertScene={insertScene}
          deleteScene={deleteScene}
          copyPrompt={copyPrompt}
        />
      </div>
    </div>

    <!-- SIDE-BY-SIDE PROMPT HUB PANEL -->
    <VideoScriptPromptHub
      bind:showPromptHub={showPromptHub}
      bind:activePromptTab={activePromptTab}
      activeScript={activeScript}
      getMidjourneyPrompt={getMidjourneyPrompt}
      getRunwayPrompt={getRunwayPrompt}
      getGeminiPrompt={getGeminiPrompt}
      getGeminiMasterPrompt={getGeminiMasterPrompt}
      copyAllPrompts={copyAllPrompts}
    />
  {/if}
</div>
