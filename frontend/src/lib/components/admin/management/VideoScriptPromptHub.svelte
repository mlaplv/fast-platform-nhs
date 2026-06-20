<script lang="ts">
  import { fade, slide } from "svelte/transition";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import X from "@lucide/svelte/icons/x";
  import Copy from "@lucide/svelte/icons/copy";
  import Camera from "@lucide/svelte/icons/camera";
  import Sun from "@lucide/svelte/icons/sun";
  import RefreshCw from "@lucide/svelte/icons/refresh-cw";
  import Move from "@lucide/svelte/icons/move";
  import ChevronDown from "@lucide/svelte/icons/chevron-down";
  import type { VideoScript, VideoScene } from "$lib/types";
  import { useNanobot } from "$lib/state/nanobot.svelte";
  import AnimationPromptBuilder from "./AnimationPromptBuilder.svelte";

  const nanobot = useNanobot();

  interface Props {
    showPromptHub: boolean;
    activePromptTab:
      | "midjourney"
      | "runway"
      | "heygen"
      | "gemini"
      | "animation";
    activeScript: VideoScript | null;
    getMidjourneyPrompt: (scene: VideoScene, aspect: string) => string;
    getRunwayPrompt: (scene: VideoScene) => string;
    getGeminiPrompt: (scene: VideoScene) => string;
    getGeminiMasterPrompt: () => string;
    copyAllPrompts: (
      type: "midjourney" | "runway" | "heygen" | "gemini",
    ) => void;
    triggerAutoSave: () => void;
  }

  let {
    showPromptHub = $bindable(),
    activePromptTab = $bindable(),
    activeScript,
    getMidjourneyPrompt,
    getRunwayPrompt,
    getGeminiPrompt,
    getGeminiMasterPrompt,
    copyAllPrompts,
    triggerAutoSave,
  }: Props = $props();

  // Presets State
  let selectedCameraStyle = $state<
    "none" | "cinematic" | "studio" | "3d_render"
  >("none");
  let selectedLighting = $state<"none" | "volumetric" | "neon">("none");
  let arOverride = $state<"default" | "9:16" | "16:9" | "1:1">("default");
  let selectedCameraMovement = $state<
    "none" | "zoom_in" | "pan_left" | "dolly_zoom"
  >("none");

  // Dropdown active state
  let activeDropdown = $state<"camera" | "lighting" | "ar" | "movement" | null>(
    null,
  );

  function toggleDropdown(
    name: "camera" | "lighting" | "ar" | "movement",
    e: Event,
  ) {
    e.stopPropagation();
    activeDropdown = activeDropdown === name ? null : name;
  }

  function closeAllDropdowns() {
    activeDropdown = null;
  }

  // Dynamic Prompt Builders
  function buildMidjourneyPrompt(scene: VideoScene, aspect: string) {
    let base = getMidjourneyPrompt(scene, aspect);

    // Remove existing aspect ratio at the end if overridden
    if (arOverride !== "default") {
      base = base.replace(/--ar\s+[0-9]+:[0-9]+/g, "").trim();
    }

    // Append camera presets
    if (selectedCameraStyle === "cinematic") {
      base +=
        ", 35mm cinematic photograph, shallow depth of field, anamorphic lenses";
    } else if (selectedCameraStyle === "studio") {
      base +=
        ", commercial studio photography, high-end clean lighting, crisp product details";
    } else if (selectedCameraStyle === "3d_render") {
      base +=
        ", octane 3D product render, raytracing, unreal engine 5 style, hyper-detailed";
    }

    // Append lighting presets
    if (selectedLighting === "volumetric") {
      base += ", dramatic volumetric lighting, sunbeams";
    } else if (selectedLighting === "neon") {
      base += ", vibrant neon cyberpunk lighting, cinematic moody contrast";
    }

    // Append aspect ratio override
    if (arOverride !== "default") {
      base += ` --ar ${arOverride}`;
    }

    return base;
  }

  function buildRunwayPrompt(scene: VideoScene) {
    let base = getRunwayPrompt(scene);

    // Append camera movements
    if (selectedCameraMovement === "zoom_in") {
      base += ", slow continuous zoom in, macro details";
    } else if (selectedCameraMovement === "pan_left") {
      base += ", slow horizontal panning camera motion from right to left";
    } else if (selectedCameraMovement === "dolly_zoom") {
      base += ", dramatic vertigo effect dolly zoom camera movement";
    }

    return base;
  }

  // Copy helpers
  function copyPromptToClipboard(text: string, sceneNum: number) {
    navigator.clipboard.writeText(text);
    nanobot.showToast(`Đã sao chép prompt phân cảnh ${sceneNum}!`, "success");
  }

  function getCombinedVoiceover(): string {
    if (!activeScript || !activeScript.structured_script?.scenes) return "";
    return activeScript.structured_script.scenes
      .map((s) => (s.voiceover || "").trim())
      .filter(Boolean)
      .join(" ");
  }

  function copyAllModifiedPrompts() {
    if (!activeScript || !activeScript.structured_script?.scenes) return;
    const scenes = activeScript.structured_script.scenes;
    const aspect = activeScript.structured_script.aspect_ratio || "16:9";

    if (activePromptTab === "heygen") {
      const allVoiceover = getCombinedVoiceover();
      navigator.clipboard.writeText(allVoiceover);
      nanobot.showToast("Đã sao chép toàn bộ Voiceover liền mạch!", "success");
      return;
    }

    let allText = "";
    scenes.forEach((scene, idx) => {
      const promptText =
        activePromptTab === "midjourney"
          ? buildMidjourneyPrompt(scene, aspect)
          : activePromptTab === "runway"
            ? buildRunwayPrompt(scene)
            : activePromptTab === "gemini"
              ? getGeminiPrompt(scene)
              : scene.voiceover || "";
      allText += `Phân cảnh #${scene.scene_number || idx + 1}:\n${promptText}\n\n`;
    });

    navigator.clipboard.writeText(allText.trim());
    nanobot.showToast("Đã sao chép tất cả prompt tùy biến!", "success");
  }
</script>

<!-- AI Prompt Generator Hub Panel -->
{#if showPromptHub}
  <!-- Backdrop overlay -->
  <button
    type="button"
    onclick={() => {
      showPromptHub = false;
    }}
    class="fixed inset-0 z-40 bg-black/60 backdrop-blur-xs transition-opacity cursor-default border-0 p-0 m-0 w-full h-full text-left focus:outline-none"
    aria-label="Close panel"
  ></button>

  <!-- Floating Right Drawer -->
  <div
    class="fixed inset-y-0 right-0 z-50 w-full xl:w-[460px] h-full bg-[#050505] border-l border-[#151515] flex flex-col shadow-2xl overflow-hidden"
    transition:slide={{ axis: "x", duration: 250 }}
  >
    <!-- Drawer Header -->
    <div
      class="p-5 border-b border-gray-900 flex items-center justify-between bg-black/40"
    >
      <div class="flex items-center gap-2">
        <Sparkles class="w-5 h-5 text-cyan-400" />
        <div>
          <h3
            class="text-sm font-semibold text-gray-100 uppercase tracking-wider"
          >
            AI Prompt Bridge Center
          </h3>
          <p class="text-[10px] text-gray-500 font-mono mt-0.5">
            Xuất prompt chuẩn hóa cho các nền tảng AI Video & Image
          </p>
        </div>
      </div>
      <button
        onclick={() => {
          showPromptHub = false;
        }}
        class="p-1.5 hover:bg-gray-900 rounded-lg text-gray-400 hover:text-white transition-colors"
      >
        <X class="w-4 h-4" />
      </button>
    </div>

    <!-- Tabs & Copy All -->
    <div
      class="px-5 py-3 bg-[#0a0a0d] border-b border-gray-900 flex items-center justify-between"
    >
      <div class="flex flex-wrap gap-2">
        <button
          onclick={() => {
            activePromptTab = "midjourney";
          }}
          class="px-3 py-1.5 rounded-lg text-xs font-medium border transition-all
                   {activePromptTab === 'midjourney'
            ? 'bg-cyan-950/40 border-cyan-500/30 text-cyan-400 shadow-sm shadow-cyan-500/10'
            : 'border-transparent text-gray-400 hover:text-white'}"
        >
          Midjourney / Flux
        </button>
        <button
          onclick={() => {
            activePromptTab = "runway";
          }}
          class="px-3 py-1.5 rounded-lg text-xs font-medium border transition-all
                   {activePromptTab === 'runway'
            ? 'bg-purple-950/40 border-purple-500/30 text-purple-400 shadow-sm shadow-purple-500/10'
            : 'border-transparent text-gray-400 hover:text-white'}"
        >
          Runway Gen-3
        </button>
        <button
          onclick={() => {
            activePromptTab = "heygen";
          }}
          class="px-3 py-1.5 rounded-lg text-xs font-medium border transition-all
                   {activePromptTab === 'heygen'
            ? 'bg-pink-950/40 border-pink-500/30 text-pink-400 shadow-sm shadow-pink-500/10'
            : 'border-transparent text-gray-400 hover:text-white'}"
        >
          Thoại & Voiceover (TTS)
        </button>
        <button
          onclick={() => {
            activePromptTab = "gemini";
          }}
          class="px-3 py-1.5 rounded-lg text-xs font-medium border transition-all
                   {activePromptTab === 'gemini'
            ? 'bg-blue-950/40 border-blue-500/30 text-blue-400 shadow-sm shadow-blue-500/10'
            : 'border-transparent text-gray-400 hover:text-white'}"
        >
          Gemini Director
        </button>
        <button
          onclick={() => {
            activePromptTab = "animation";
          }}
          class="px-3 py-1.5 rounded-lg text-xs font-medium border transition-all
                   {activePromptTab === 'animation'
            ? 'bg-emerald-950/40 border-emerald-500/30 text-emerald-400 shadow-sm shadow-emerald-500/10'
            : 'border-transparent text-gray-400 hover:text-white'}"
        >
          Animation Pro
        </button>
      </div>

      <button
        onclick={copyAllModifiedPrompts}
        class="flex items-center gap-1.5 px-3 py-1.5 bg-gray-950 hover:bg-gray-900 text-xs text-gray-300 rounded-lg border border-gray-800 transition-all shrink-0"
      >
        <Copy class="w-3.5 h-3.5" />
        <span
          >{activePromptTab === "heygen"
            ? "Copy toàn bộ thoại"
            : "Sao chép tất cả"}</span
        >
      </button>
    </div>

    <!-- Presets Modifiers Panel -->
    {#if activePromptTab === "midjourney"}
      <div
        class="px-5 py-3.5 bg-[#0b0c10]/40 border-b border-gray-900/60 grid grid-cols-3 gap-3"
        transition:slide
      >
        <!-- Camera Style Preset -->
        <div class="space-y-1.5">
          <span
            class="flex items-center gap-1 text-[9px] font-mono text-gray-500 uppercase font-bold"
          >
            <Camera class="w-3 h-3 text-cyan-400" /> Phong cách chụp
          </span>
          <div class="relative">
            <button
              type="button"
              onclick={(e) => toggleDropdown("camera", e)}
              class="w-full bg-[#111115] hover:bg-[#18181f] border border-gray-850/80 hover:border-gray-750/90 rounded-lg px-2.5 py-1.5 text-[10px] text-gray-300 flex items-center justify-between transition-all focus:outline-none focus:ring-1 focus:ring-cyan-500/30"
            >
              <span class="truncate"
                >{selectedCameraStyle === "none"
                  ? "Mặc định kịch bản"
                  : selectedCameraStyle === "cinematic"
                    ? "Cinematic 35mm"
                    : selectedCameraStyle === "studio"
                      ? "Studio Commercial"
                      : "3D Octane Render"}</span
              >
              <ChevronDown
                class="w-3 h-3 text-gray-500 transition-transform duration-200 {activeDropdown ===
                'camera'
                  ? 'rotate-180 text-cyan-400'
                  : ''}"
              />
            </button>

            {#if activeDropdown === "camera"}
              <div
                transition:fade={{ duration: 100 }}
                class="absolute z-50 left-0 right-0 mt-1 bg-[#09090c]/98 backdrop-blur-md border border-gray-800/90 rounded-lg shadow-xl shadow-black/80 overflow-hidden py-1"
              >
                <button
                  type="button"
                  onclick={() => {
                    selectedCameraStyle = "none";
                    activeDropdown = null;
                  }}
                  class="w-full text-left px-3 py-1.5 text-[10px] transition-colors
                           {selectedCameraStyle === 'none'
                    ? 'bg-cyan-950/45 text-cyan-400 font-semibold'
                    : 'text-gray-400 hover:bg-white/5 hover:text-white'}"
                >
                  Mặc định kịch bản
                </button>
                <button
                  type="button"
                  onclick={() => {
                    selectedCameraStyle = "cinematic";
                    activeDropdown = null;
                  }}
                  class="w-full text-left px-3 py-1.5 text-[10px] transition-colors
                           {selectedCameraStyle === 'cinematic'
                    ? 'bg-cyan-950/45 text-cyan-400 font-semibold'
                    : 'text-gray-400 hover:bg-white/5 hover:text-white'}"
                >
                  Cinematic 35mm
                </button>
                <button
                  type="button"
                  onclick={() => {
                    selectedCameraStyle = "studio";
                    activeDropdown = null;
                  }}
                  class="w-full text-left px-3 py-1.5 text-[10px] transition-colors
                           {selectedCameraStyle === 'studio'
                    ? 'bg-cyan-950/45 text-cyan-400 font-semibold'
                    : 'text-gray-400 hover:bg-white/5 hover:text-white'}"
                >
                  Studio Commercial
                </button>
                <button
                  type="button"
                  onclick={() => {
                    selectedCameraStyle = "3d_render";
                    activeDropdown = null;
                  }}
                  class="w-full text-left px-3 py-1.5 text-[10px] transition-colors
                           {selectedCameraStyle === '3d_render'
                    ? 'bg-cyan-950/45 text-cyan-400 font-semibold'
                    : 'text-gray-400 hover:bg-white/5 hover:text-white'}"
                >
                  3D Octane Render
                </button>
              </div>
            {/if}
          </div>
        </div>

        <!-- Lighting Preset -->
        <div class="space-y-1.5">
          <span
            class="flex items-center gap-1 text-[9px] font-mono text-gray-500 uppercase font-bold"
          >
            <Sun class="w-3 h-3 text-cyan-400" /> Ánh sáng
          </span>
          <div class="relative">
            <button
              type="button"
              onclick={(e) => toggleDropdown("lighting", e)}
              class="w-full bg-[#111115] hover:bg-[#18181f] border border-gray-850/80 hover:border-gray-750/90 rounded-lg px-2.5 py-1.5 text-[10px] text-gray-300 flex items-center justify-between transition-all focus:outline-none focus:ring-1 focus:ring-cyan-500/30"
            >
              <span class="truncate"
                >{selectedLighting === "none"
                  ? "Mặc định kịch bản"
                  : selectedLighting === "volumetric"
                    ? "Volumetric (Luồng)"
                    : "Neon Cyberpunk"}</span
              >
              <ChevronDown
                class="w-3 h-3 text-gray-500 transition-transform duration-200 {activeDropdown ===
                'lighting'
                  ? 'rotate-180 text-cyan-400'
                  : ''}"
              />
            </button>

            {#if activeDropdown === "lighting"}
              <div
                transition:fade={{ duration: 100 }}
                class="absolute z-50 left-0 right-0 mt-1 bg-[#09090c]/98 backdrop-blur-md border border-gray-800/90 rounded-lg shadow-xl shadow-black/80 overflow-hidden py-1"
              >
                <button
                  type="button"
                  onclick={() => {
                    selectedLighting = "none";
                    activeDropdown = null;
                  }}
                  class="w-full text-left px-3 py-1.5 text-[10px] transition-colors
                           {selectedLighting === 'none'
                    ? 'bg-cyan-950/45 text-cyan-400 font-semibold'
                    : 'text-gray-400 hover:bg-white/5 hover:text-white'}"
                >
                  Mặc định kịch bản
                </button>
                <button
                  type="button"
                  onclick={() => {
                    selectedLighting = "volumetric";
                    activeDropdown = null;
                  }}
                  class="w-full text-left px-3 py-1.5 text-[10px] transition-colors
                           {selectedLighting === 'volumetric'
                    ? 'bg-cyan-950/45 text-cyan-400 font-semibold'
                    : 'text-gray-400 hover:bg-white/5 hover:text-white'}"
                >
                  Volumetric (Luồng sáng)
                </button>
                <button
                  type="button"
                  onclick={() => {
                    selectedLighting = "neon";
                    activeDropdown = null;
                  }}
                  class="w-full text-left px-3 py-1.5 text-[10px] transition-colors
                           {selectedLighting === 'neon'
                    ? 'bg-cyan-950/45 text-cyan-400 font-semibold'
                    : 'text-gray-400 hover:bg-white/5 hover:text-white'}"
                >
                  Neon Cyberpunk
                </button>
              </div>
            {/if}
          </div>
        </div>

        <!-- Aspect Ratio override -->
        <div class="space-y-1.5">
          <span
            class="flex items-center gap-1 text-[9px] font-mono text-gray-500 uppercase font-bold"
          >
            <RefreshCw class="w-3 h-3 text-cyan-400" /> Đè Khung hình
          </span>
          <div class="relative">
            <button
              type="button"
              onclick={(e) => toggleDropdown("ar", e)}
              class="w-full bg-[#111115] hover:bg-[#18181f] border border-gray-850/80 hover:border-gray-750/90 rounded-lg px-2.5 py-1.5 text-[10px] text-gray-300 flex items-center justify-between transition-all focus:outline-none focus:ring-1 focus:ring-cyan-500/30"
            >
              <span class="truncate"
                >{arOverride === "default"
                  ? "Dùng của kịch bản"
                  : arOverride === "9:16"
                    ? "Dọc (9:16)"
                    : arOverride === "16:9"
                      ? "Ngang (16:9)"
                      : "Vuông (1:1)"}</span
              >
              <ChevronDown
                class="w-3 h-3 text-gray-500 transition-transform duration-200 {activeDropdown ===
                'ar'
                  ? 'rotate-180 text-cyan-400'
                  : ''}"
              />
            </button>

            {#if activeDropdown === "ar"}
              <div
                transition:fade={{ duration: 100 }}
                class="absolute z-50 left-0 right-0 mt-1 bg-[#09090c]/98 backdrop-blur-md border border-gray-800/90 rounded-lg shadow-xl shadow-black/80 overflow-hidden py-1"
              >
                <button
                  type="button"
                  onclick={() => {
                    arOverride = "default";
                    activeDropdown = null;
                  }}
                  class="w-full text-left px-3 py-1.5 text-[10px] transition-colors
                           {arOverride === 'default'
                    ? 'bg-cyan-950/45 text-cyan-400 font-semibold'
                    : 'text-gray-400 hover:bg-white/5 hover:text-white'}"
                >
                  Dùng của kịch bản
                </button>
                <button
                  type="button"
                  onclick={() => {
                    arOverride = "9:16";
                    activeDropdown = null;
                  }}
                  class="w-full text-left px-3 py-1.5 text-[10px] transition-colors
                           {arOverride === '9:16'
                    ? 'bg-cyan-950/45 text-cyan-400 font-semibold'
                    : 'text-gray-400 hover:bg-white/5 hover:text-white'}"
                >
                  Dọc (9:16) - Shorts/TikTok
                </button>
                <button
                  type="button"
                  onclick={() => {
                    arOverride = "16:9";
                    activeDropdown = null;
                  }}
                  class="w-full text-left px-3 py-1.5 text-[10px] transition-colors
                           {arOverride === '16:9'
                    ? 'bg-cyan-950/45 text-cyan-400 font-semibold'
                    : 'text-gray-400 hover:bg-white/5 hover:text-white'}"
                >
                  Ngang (16:9) - Youtube
                </button>
                <button
                  type="button"
                  onclick={() => {
                    arOverride = "1:1";
                    activeDropdown = null;
                  }}
                  class="w-full text-left px-3 py-1.5 text-[10px] transition-colors
                           {arOverride === '1:1'
                    ? 'bg-cyan-950/45 text-cyan-400 font-semibold'
                    : 'text-gray-400 hover:bg-white/5 hover:text-white'}"
                >
                  Vuông (1:1)
                </button>
              </div>
            {/if}
          </div>
        </div>
      </div>
    {:else}
      {@const noneVal = undefined}
    {/if}

    {#if activePromptTab === "runway"}
      <div
        class="px-5 py-3.5 bg-[#0b0c10]/40 border-b border-gray-900/60"
        transition:slide
      >
        <!-- Camera Movement Preset -->
        <div class="space-y-1.5 max-w-xs">
          <span
            class="flex items-center gap-1 text-[9px] font-mono text-gray-500 uppercase font-bold"
          >
            <Move class="w-3 h-3 text-purple-400" /> Hiệu ứng máy quay (Runway Presets)
          </span>
          <div class="relative">
            <button
              type="button"
              onclick={(e) => toggleDropdown("movement", e)}
              class="w-full bg-[#111115] hover:bg-[#18181f] border border-gray-850/80 hover:border-gray-750/90 rounded-lg px-2.5 py-1.5 text-[10px] text-gray-300 flex items-center justify-between transition-all focus:outline-none focus:ring-1 focus:ring-purple-500/30"
            >
              <span class="truncate"
                >{selectedCameraMovement === "none"
                  ? "Mặc định kịch bản"
                  : selectedCameraMovement === "zoom_in"
                    ? "Slow Zoom In"
                    : selectedCameraMovement === "pan_left"
                      ? "Slow Pan Left"
                      : "Dolly Zoom Vertigo"}</span
              >
              <ChevronDown
                class="w-3 h-3 text-gray-500 transition-transform duration-200 {activeDropdown ===
                'movement'
                  ? 'rotate-180 text-purple-400'
                  : ''}"
              />
            </button>

            {#if activeDropdown === "movement"}
              <div
                transition:fade={{ duration: 100 }}
                class="absolute z-50 left-0 right-0 mt-1 bg-[#09090c]/98 backdrop-blur-md border border-gray-800/90 rounded-lg shadow-xl shadow-black/80 overflow-hidden py-1"
              >
                <button
                  type="button"
                  onclick={() => {
                    selectedCameraMovement = "none";
                    activeDropdown = null;
                  }}
                  class="w-full text-left px-3 py-1.5 text-[10px] transition-colors
                           {selectedCameraMovement === 'none'
                    ? 'bg-purple-950/45 text-purple-400 font-semibold'
                    : 'text-gray-400 hover:bg-white/5 hover:text-white'}"
                >
                  Mặc định kịch bản
                </button>
                <button
                  type="button"
                  onclick={() => {
                    selectedCameraMovement = "zoom_in";
                    activeDropdown = null;
                  }}
                  class="w-full text-left px-3 py-1.5 text-[10px] transition-colors
                           {selectedCameraMovement === 'zoom_in'
                    ? 'bg-purple-950/45 text-purple-400 font-semibold'
                    : 'text-gray-400 hover:bg-white/5 hover:text-white'}"
                >
                  Slow Zoom In (Cận cảnh chậm)
                </button>
                <button
                  type="button"
                  onclick={() => {
                    selectedCameraMovement = "pan_left";
                    activeDropdown = null;
                  }}
                  class="w-full text-left px-3 py-1.5 text-[10px] transition-colors
                           {selectedCameraMovement === 'pan_left'
                    ? 'bg-purple-950/45 text-purple-400 font-semibold'
                    : 'text-gray-400 hover:bg-white/5 hover:text-white'}"
                >
                  Slow Pan Left (Lia máy trái)
                </button>
                <button
                  type="button"
                  onclick={() => {
                    selectedCameraMovement = "dolly_zoom";
                    activeDropdown = null;
                  }}
                  class="w-full text-left px-3 py-1.5 text-[10px] transition-colors
                           {selectedCameraMovement === 'dolly_zoom'
                    ? 'bg-purple-950/45 text-purple-400 font-semibold'
                    : 'text-gray-400 hover:bg-white/5 hover:text-white'}"
                >
                  Dolly Zoom Vertigo (Hiệu ứng chóng mặt)
                </button>
              </div>
            {/if}
          </div>
        </div>
      </div>
    {:else}
      {@const noneVal = undefined}
    {/if}

    <!-- TIP Alert Box -->
    <div
      class="mx-5 mt-4 p-3 bg-amber-500/5 border border-amber-500/10 border-l-2 border-l-amber-500/50 rounded-r-lg space-y-1 relative"
      transition:slide
    >
      <div
        class="flex items-center gap-1.5 text-amber-400 font-semibold text-[10px] uppercase tracking-wider"
      >
        <Sparkles class="w-3.5 h-3.5 text-amber-400 animate-pulse" />
        <span>Mẹo sản xuất tối ưu (PRO TIP)</span>
      </div>
      <p class="text-[11px] text-gray-400 leading-relaxed font-sans">
        {#if activePromptTab === "midjourney"}
          Dùng prompt này để tạo ảnh sản phẩm có chất lượng điện ảnh cao trên
          Midjourney v6/Flux trước. Hãy tải ảnh sản phẩm thật của sếp lên làm
          ảnh tham chiếu (Character/Style Reference) để AI không tự ý đổi bao bì
          vỏ hộp.
        {:else if activePromptTab === "runway"}
          Hãy chọn chế độ <strong>Image-to-Video (Ảnh thành video)</strong>.
          Đính kèm ảnh sản phẩm tĩnh nét nhất đã tạo từ bước trước và dán prompt
          này vào để sinh chuyển động camera 4s mà không làm méo hay sai lệch
          nhãn mác.
        {:else if activePromptTab === "heygen"}
          Nhấp nút <strong>"Copy toàn bộ thoại"</strong> ở trên để sao chép văn bản
          thoại gộp sạch sẽ. Sếp dán thẳng vào CapCut để AI tự động thuyết minh bằng
          các giọng đọc tiếng Việt thịnh hành (như Thanh Vy, Chàng trai hoạt ngôn)
          chỉ trong 3 giây.
        {:else if activePromptTab === "gemini"}
          <strong>QUY TRÌNH LUYỆN & KHỚP CẢNH:</strong> B1: Gửi
          <strong>Master Prompt</strong>
          kèm ảnh sản phẩm thật lên trước để dạy Gemini nhớ website osmo.vn và thương
          hiệu sản phẩm. B2: Copy từng <strong>Phân cảnh lẻ</strong> bên dưới kèm
          ảnh sản phẩm thật gửi tiếp vào chính ô chat đó để AI sinh video chuyển
          động có tính liền mạch và chính xác.
        {/if}
      </p>
    </div>

    <!-- Prompts List -->
    <div class="flex-1 overflow-y-auto p-5 space-y-4 custom-scrollbar">
      {#if activePromptTab === "animation"}
        <AnimationPromptBuilder {activeScript} {triggerAutoSave} />
      {:else if activeScript && activeScript.structured_script?.scenes}
        {@const scenes = activeScript.structured_script.scenes}
        {#if activePromptTab === "gemini"}
          <!-- Master Prompt for Gemini Pro -->
          <div
            class="bg-blue-950/10 border border-blue-500/20 rounded-xl p-4 space-y-3 relative group"
          >
            <div
              class="flex items-center justify-between border-b border-blue-500/20 pb-2"
            >
              <span
                class="text-[10px] font-mono font-bold text-blue-400 uppercase"
                >Master Prompt cho Gemini Pro (Toàn bộ kịch bản)</span
              >
              <button
                onclick={() => {
                  navigator.clipboard.writeText(getGeminiMasterPrompt());
                  nanobot.showToast(
                    "Đã sao chép Master Prompt cho Gemini Pro!",
                    "success",
                  );
                }}
                class="p-1 text-blue-400 hover:text-blue-300 hover:bg-blue-500/10 rounded transition-all"
                title="Sao chép Master Prompt"
              >
                <Copy class="w-3.5 h-3.5" />
              </button>
            </div>
            <p class="text-[11px] text-gray-400 leading-relaxed font-sans">
              Dán câu lệnh tổng quát này vào Gemini Pro để nhận phân tích, tối
              ưu hoá nhịp độ và đạo diễn hình ảnh nâng cao cho toàn bộ kịch bản
              của sếp:
            </p>
            <pre
              class="text-xs text-blue-200 leading-relaxed font-mono whitespace-pre-wrap select-all bg-black/40 border border-blue-500/10 p-3 rounded-lg max-h-48 overflow-y-auto custom-scrollbar">{getGeminiMasterPrompt()}</pre>
          </div>
        {/if}

        {#if activePromptTab === "heygen"}
          <!-- Combined Voiceover for TTS Tools -->
          <div
            class="bg-pink-950/10 border border-pink-500/20 rounded-xl p-4 space-y-3 relative group"
          >
            <div
              class="flex items-center justify-between border-b border-pink-500/20 pb-2"
            >
              <span
                class="text-[10px] font-mono font-bold text-pink-400 uppercase"
                >Toàn bộ lời thoại liền mạch (Dùng cho CapCut / TTS)</span
              >
              <button
                onclick={() => {
                  navigator.clipboard.writeText(getCombinedVoiceover());
                  nanobot.showToast(
                    "Đã sao chép toàn bộ Voiceover liền mạch!",
                    "success",
                  );
                }}
                class="p-1 text-pink-400 hover:text-pink-300 hover:bg-pink-500/10 rounded transition-all"
                title="Sao chép toàn bộ lời thoại"
              >
                <Copy class="w-3.5 h-3.5" />
              </button>
            </div>
            <p class="text-[11px] text-gray-400 leading-relaxed font-sans">
              Đoạn văn gộp thoại của toàn bộ phân cảnh, có thể dán trực tiếp vào
              CapCut hoặc phần mềm đọc AI mà không bị lẫn tiêu đề phân cảnh:
            </p>
            <pre
              class="text-xs text-pink-200 leading-relaxed font-mono whitespace-pre-wrap select-all bg-black/40 border border-pink-500/10 p-3 rounded-lg max-h-48 overflow-y-auto custom-scrollbar">{getCombinedVoiceover()}</pre>
          </div>
        {/if}

        {#each scenes as scene, idx}
          {@const aspect =
            activeScript.structured_script.aspect_ratio || "16:9"}
          {@const currentAspect =
            arOverride === "default" ? aspect : arOverride}
          {@const promptText =
            activePromptTab === "midjourney"
              ? buildMidjourneyPrompt(scene, aspect)
              : activePromptTab === "runway"
                ? buildRunwayPrompt(scene)
                : activePromptTab === "gemini"
                  ? getGeminiPrompt(scene)
                  : scene.voiceover || ""}

          <div
            class="bg-[#0b0b0f] border border-gray-900 rounded-xl p-4 space-y-3 relative group"
          >
            <div
              class="flex items-center justify-between border-b border-gray-900/50 pb-2"
            >
              <span
                class="text-[10px] font-mono font-bold text-gray-400 uppercase"
                >Phân cảnh #{scene.scene_number || idx + 1}</span
              >
              <button
                onclick={() =>
                  copyPromptToClipboard(
                    promptText,
                    scene.scene_number || idx + 1,
                  )}
                class="p-1 text-gray-500 hover:text-cyan-400 hover:bg-cyan-500/10 rounded transition-all"
                title="Sao chép prompt này"
              >
                <Copy class="w-3.5 h-3.5" />
              </button>
            </div>

            <p
              class="text-xs text-gray-300 leading-relaxed font-mono whitespace-pre-wrap select-all bg-black/30 border border-gray-900/60 p-3 rounded-lg"
            >
              {promptText || "(Không có nội dung)"}
            </p>

            <div
              class="flex items-center justify-between text-[9px] text-gray-500 font-mono"
            >
              <span
                >Tỷ lệ: {activePromptTab === "midjourney"
                  ? currentAspect
                  : aspect}</span
              >
              <span>Thời lượng: {scene.duration} giây</span>
            </div>
          </div>
        {/each}
      {/if}
    </div>
  </div>
{/if}

<svelte:window onclick={closeAllDropdowns} />

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
