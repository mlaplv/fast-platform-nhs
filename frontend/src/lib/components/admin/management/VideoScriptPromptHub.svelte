<script lang="ts">
  import { fade, slide } from "svelte/transition";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import X from "@lucide/svelte/icons/x";
  import Copy from "@lucide/svelte/icons/copy";
  import type { VideoScript, VideoScene } from "$lib/types";
  import { useNanobot } from "$lib/state/nanobot.svelte";

  const nanobot = useNanobot();

  interface Props {
    showPromptHub: boolean;
    activePromptTab: "midjourney" | "runway" | "heygen" | "gemini";
    activeScript: VideoScript | null;
    getMidjourneyPrompt: (scene: VideoScene, aspect: string) => string;
    getRunwayPrompt: (scene: VideoScene) => string;
    getGeminiPrompt: (scene: VideoScene) => string;
    getGeminiMasterPrompt: () => string;
    copyAllPrompts: (type: "midjourney" | "runway" | "heygen" | "gemini") => void;
  }

  let {
    showPromptHub = $bindable(),
    activePromptTab = $bindable(),
    activeScript,
    getMidjourneyPrompt,
    getRunwayPrompt,
    getGeminiPrompt,
    getGeminiMasterPrompt,
    copyAllPrompts
  }: Props = $props();
</script>

<!-- AI Prompt Generator Hub Drawer -->
{#if showPromptHub}
  <div class="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm" transition:fade={{ duration: 150 }}>
    <!-- Backdrop click to close -->
    <button class="absolute inset-0 cursor-default focus:outline-none" onclick={() => { showPromptHub = false; }}></button>
    
    <div 
      class="relative w-full max-w-2xl h-full bg-[#070709] border-l border-gray-900 shadow-2xl flex flex-col z-10"
      transition:slide={{ axis: 'x', duration: 250 }}
    >
      <!-- Drawer Header -->
      <div class="p-5 border-b border-gray-900 flex items-center justify-between bg-black/40">
        <div class="flex items-center gap-2">
          <Sparkles class="w-5 h-5 text-cyan-400" />
          <div>
            <h3 class="text-sm font-semibold text-gray-100 uppercase tracking-wider">AI Prompt Bridge Center</h3>
            <p class="text-[10px] text-gray-500 font-mono mt-0.5">Xuất prompt chuẩn hóa cho các nền tảng AI Video & Image</p>
          </div>
        </div>
        <button 
          onclick={() => { showPromptHub = false; }}
          class="p-1.5 hover:bg-gray-900 rounded-lg text-gray-400 hover:text-white transition-colors"
        >
          <X class="w-4 h-4" />
        </button>
      </div>

      <!-- Tabs & Copy All -->
      <div class="px-5 py-3 bg-[#0a0a0d] border-b border-gray-900 flex items-center justify-between">
        <div class="flex gap-2">
          <button 
            onclick={() => { activePromptTab = 'midjourney'; }}
            class="px-3 py-1.5 rounded-lg text-xs font-medium border transition-all
                   {activePromptTab === 'midjourney' 
                     ? 'bg-cyan-950/40 border-cyan-500/30 text-cyan-400 shadow-sm shadow-cyan-500/10' 
                     : 'border-transparent text-gray-400 hover:text-white'}"
          >
            Midjourney / Flux (Ảnh)
          </button>
          <button 
            onclick={() => { activePromptTab = 'runway'; }}
            class="px-3 py-1.5 rounded-lg text-xs font-medium border transition-all
                   {activePromptTab === 'runway' 
                     ? 'bg-purple-950/40 border-purple-500/30 text-purple-400 shadow-sm shadow-purple-500/10' 
                     : 'border-transparent text-gray-400 hover:text-white'}"
          >
            Runway Gen-3 (Video)
          </button>
          <button 
            onclick={() => { activePromptTab = 'heygen'; }}
            class="px-3 py-1.5 rounded-lg text-xs font-medium border transition-all
                   {activePromptTab === 'heygen' 
                     ? 'bg-pink-950/40 border-pink-500/30 text-pink-400 shadow-sm shadow-pink-500/10' 
                     : 'border-transparent text-gray-400 hover:text-white'}"
          >
            HeyGen (Lời thoại)
          </button>
          <button 
            onclick={() => { activePromptTab = 'gemini'; }}
            class="px-3 py-1.5 rounded-lg text-xs font-medium border transition-all
                   {activePromptTab === 'gemini' 
                     ? 'bg-blue-950/40 border-blue-500/30 text-blue-400 shadow-sm shadow-blue-500/10' 
                     : 'border-transparent text-gray-400 hover:text-white'}"
          >
            Gemini Pro (Đạo diễn)
          </button>
        </div>
        
        <button 
          onclick={() => copyAllPrompts(activePromptTab)}
          class="flex items-center gap-1.5 px-3 py-1.5 bg-gray-950 hover:bg-gray-900 text-xs text-gray-300 rounded-lg border border-gray-800 transition-all"
        >
          <Copy class="w-3.5 h-3.5" />
          <span>Sao chép tất cả</span>
        </button>
      </div>

      <!-- Prompts List -->
      <div class="flex-1 overflow-y-auto p-5 space-y-4 custom-scrollbar">
        {#if activeScript && activeScript.structured_script?.scenes}
          {@const scenes = activeScript.structured_script.scenes}
          {#if activePromptTab === 'gemini'}
            <!-- Master Prompt for Gemini Pro -->
            <div class="bg-blue-950/10 border border-blue-500/20 rounded-xl p-4 space-y-3 relative group">
              <div class="flex items-center justify-between border-b border-blue-500/20 pb-2">
                <span class="text-[10px] font-mono font-bold text-blue-400 uppercase">Master Prompt cho Gemini Pro (Toàn bộ kịch bản)</span>
                <button 
                  onclick={() => {
                    navigator.clipboard.writeText(getGeminiMasterPrompt());
                    nanobot.showToast("Đã sao chép Master Prompt cho Gemini Pro!", "success");
                  }}
                  class="p-1 text-blue-400 hover:text-blue-300 hover:bg-blue-500/10 rounded transition-all"
                  title="Sao chép Master Prompt"
                >
                  <Copy class="w-3.5 h-3.5" />
                </button>
              </div>
              <p class="text-[11px] text-gray-400 leading-relaxed font-sans">
                Dán câu lệnh tổng quát này vào Gemini Pro để nhận phân tích, tối ưu hoá nhịp độ và đạo diễn hình ảnh nâng cao cho toàn bộ kịch bản của sếp:
              </p>
              <pre class="text-xs text-blue-200 leading-relaxed font-mono whitespace-pre-wrap select-all bg-black/40 border border-blue-500/10 p-3 rounded-lg max-h-48 overflow-y-auto custom-scrollbar">{getGeminiMasterPrompt()}</pre>
            </div>
          {/if}

          {#each scenes as scene, idx}
            {@const aspect = activeScript.structured_script.aspect_ratio || "16:9"}
            {@const promptText = activePromptTab === 'midjourney' 
              ? getMidjourneyPrompt(scene, aspect)
              : activePromptTab === 'runway' 
                ? getRunwayPrompt(scene)
                : activePromptTab === 'gemini'
                  ? getGeminiPrompt(scene)
                  : (scene.voiceover || "")}
            
            <div class="bg-[#0b0b0f] border border-gray-900 rounded-xl p-4 space-y-3 relative group">
              <div class="flex items-center justify-between border-b border-gray-900/50 pb-2">
                <span class="text-[10px] font-mono font-bold text-gray-400 uppercase">Phân cảnh #{scene.scene_number || (idx + 1)}</span>
                <button 
                  onclick={() => {
                    navigator.clipboard.writeText(promptText);
                    nanobot.showToast(`Đã sao chép prompt phân cảnh ${scene.scene_number || (idx + 1)}!`, "success");
                  }}
                  class="p-1 text-gray-500 hover:text-cyan-400 hover:bg-cyan-500/10 rounded transition-all"
                  title="Sao chép prompt này"
                >
                  <Copy class="w-3.5 h-3.5" />
                </button>
              </div>
              
              <p class="text-xs text-gray-300 leading-relaxed font-mono whitespace-pre-wrap select-all bg-black/30 border border-gray-900/60 p-3 rounded-lg">
                {promptText || "(Không có nội dung)"}
              </p>
              
              <div class="flex items-center justify-between text-[9px] text-gray-500 font-mono">
                <span>Tỷ lệ: {aspect}</span>
                <span>Thời lượng: {scene.duration} giây</span>
              </div>
            </div>
          {/each}
        {/if}
      </div>
    </div>
  </div>
{/if}

<style>
  .custom-scrollbar::-webkit-scrollbar {
    width: 4px;
    height: 4px;
  }
  .custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 4px;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb:hover {
    background: rgba(6, 182, 212, 0.2);
  }
</style>
