<script lang="ts">
  import Film from "@lucide/svelte/icons/film";
  import Clock from "@lucide/svelte/icons/clock";
  import ArrowUp from "@lucide/svelte/icons/arrow-up";
  import ArrowDown from "@lucide/svelte/icons/arrow-down";
  import Plus from "@lucide/svelte/icons/plus";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import Download from "@lucide/svelte/icons/download";
  import Upload from "@lucide/svelte/icons/upload";
  import Image from "@lucide/svelte/icons/image";
  import Link from "@lucide/svelte/icons/link";
  import Copy from "@lucide/svelte/icons/copy";
  import Check from "@lucide/svelte/icons/check";
  import AlertCircle from "@lucide/svelte/icons/alert-circle";
  import type { VideoScript, VideoScene } from "$lib/types";

  interface Props {
    activeScript: VideoScript;
    activeSceneIdx: number | null;
    generatingImageMap: Record<number, boolean>;
    copiedTextMap: Record<number, boolean>;
    triggerAutoSave: () => void;
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
    activeSceneIdx,
    generatingImageMap,
    copiedTextMap,
    triggerAutoSave,
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

<!-- Storyblock Timeline container -->
{#if activeScript.structured_script?.scenes?.length > 0}
  {@const scenes = activeScript.structured_script.scenes}
  <div class="space-y-4">
    {#each scenes as scene, idx}
      <div 
        class="relative bg-[#070707] border rounded-xl p-4 transition-all duration-300
               {activeSceneIdx === idx 
                 ? 'border-cyan-500/60 bg-cyan-950/5 shadow-md shadow-cyan-500/5' 
                 : 'border-[#121212] hover:border-gray-800'}"
      >
        <!-- Storyblock Header info & controllers -->
        <div class="flex items-center justify-between border-b border-gray-900 pb-2 mb-3">
          <div class="flex items-center gap-2.5">
            <Film class="w-3.5 h-3.5 text-cyan-400" />
            <span class="text-[10px] font-mono font-bold text-cyan-300 uppercase">PHÂN CẢNH #{scene.scene_number}</span>
            <span class="text-gray-700">|</span>
            
            <div class="flex items-center gap-1 text-[10px]">
              <Clock class="w-3 h-3 text-gray-500" />
              <input
                type="number"
                step="0.5"
                min="1"
                bind:value={scene.duration}
                onchange={triggerAutoSave}
                class="w-12 bg-black border border-gray-800 rounded px-1.5 py-0.5 text-center text-cyan-300 text-[10px] font-mono focus:outline-none focus:border-cyan-500/40"
              />
              <span class="text-gray-500">giây</span>
            </div>
          </div>

          <!-- Control buttons -->
          <div class="flex items-center gap-1.5">
            <button
              onclick={() => moveScene(idx, 'up')}
              disabled={idx === 0}
              class="p-1 hover:bg-[#151515] rounded text-gray-400 hover:text-white disabled:opacity-20 transition-all"
              title="Di chuyển lên"
            >
              <ArrowUp class="w-3.5 h-3.5" />
            </button>
            <button
              onclick={() => moveScene(idx, 'down')}
              disabled={idx === scenes.length - 1}
              class="p-1 hover:bg-[#151515] rounded text-gray-400 hover:text-white disabled:opacity-20 transition-all"
              title="Di chuyển xuống"
            >
              <ArrowDown class="w-3.5 h-3.5" />
            </button>
            <button
              onclick={() => insertScene(idx)}
              class="p-1 hover:bg-[#151515] rounded text-gray-400 hover:text-cyan-400 transition-all"
              title="Chèn phân cảnh sau"
            >
              <Plus class="w-3.5 h-3.5" />
            </button>
            <button
              onclick={() => deleteScene(idx)}
              class="p-1 hover:bg-[#151515] rounded text-gray-400 hover:text-red-400 transition-all"
              title="Xóa phân cảnh này"
            >
              <Trash2 class="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-12 gap-4">
          <!-- Inputs Panel (Left) -->
          <div class="lg:col-span-8 space-y-3.5">
            
            <!-- Visual Description input -->
            <div>
              <span class="text-[9px] font-mono text-pink-500 tracking-wider font-semibold uppercase block mb-1">MÔ TẢ HÌNH ẢNH / CẢNH QUAY</span>
              <textarea
                bind:value={scene.visual_description}
                oninput={triggerAutoSave}
                rows="2"
                class="w-full bg-[#0a0a0a] border border-gray-900 rounded-lg p-2.5 text-xs text-gray-200 focus:outline-none focus:border-cyan-500/40 focus:bg-[#0c0c0c] transition-all resize-none leading-relaxed"
                placeholder="Mô tả hành động của diễn viên, bối cảnh, góc đặt camera..."
              ></textarea>
            </div>

            <!-- Voiceover script input -->
            <div>
              <div class="flex items-center justify-between mb-1">
                <span class="text-[9px] font-mono text-cyan-400 tracking-wider font-semibold uppercase">LỜI THOẠI (VOICEOVER)</span>
                <button
                  type="button"
                  onclick={() => downloadSceneAudio(scene)}
                  class="flex items-center gap-1 text-[9px] font-mono text-cyan-500 hover:text-cyan-400 transition-colors bg-cyan-950/20 hover:bg-cyan-500/10 border border-cyan-500/20 rounded px-1.5 py-0.5"
                  title="Tải giọng đọc phân cảnh này dưới dạng file MP3"
                >
                  <Download class="w-2.5 h-2.5" />
                  <span>Tải voice MP3</span>
                </button>
              </div>
              <textarea
                bind:value={scene.voiceover}
                oninput={triggerAutoSave}
                rows="2"
                class="w-full bg-cyan-950/5 border border-cyan-500/10 rounded-lg p-2.5 text-xs text-cyan-100 font-medium focus:outline-none focus:border-cyan-500/40 focus:bg-cyan-950/10 transition-all resize-none leading-relaxed italic"
                placeholder="Nội dung lời thuyết minh sẽ được đọc ở phân cảnh này..."
              ></textarea>
            </div>

            <!-- SFX and Scene-level notes -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <span class="text-[9px] font-mono text-purple-400 tracking-wider block mb-1">ÂM THANH / SFX / NHẠC NỀN</span>
                <input
                  type="text"
                  bind:value={scene.audio_cue}
                  oninput={triggerAutoSave}
                  class="w-full bg-[#0a0a0a] border border-gray-900 rounded-lg px-2.5 py-1.5 text-xs text-purple-300 placeholder:text-gray-700 focus:outline-none focus:border-cyan-500/40 focus:bg-[#0c0c0c] transition-all"
                  placeholder="Nhạc nền lofi, SFX tiếng chuông..."
                />
              </div>
              <div>
                <span class="text-[9px] font-mono text-yellow-500/80 tracking-wider block mb-1">GHI CHÚ RIÊNG PHÂN CẢNH</span>
                <input
                  type="text"
                  bind:value={scene.scene_notes}
                  oninput={triggerAutoSave}
                  class="w-full bg-[#0a0a0a] border border-gray-900 rounded-lg px-2.5 py-1.5 text-xs text-yellow-200/80 placeholder:text-gray-700 focus:outline-none focus:border-cyan-500/40 focus:bg-[#0c0c0c] transition-all"
                  placeholder="Zoom cận cảnh vào sản phẩm..."
                />
              </div>
            </div>
          </div>

          <!-- Storyboard Media Slot (Right) -->
          <div class="lg:col-span-4 flex flex-col justify-between border-t lg:border-t-0 lg:border-l border-gray-900 pt-3 lg:pt-0 lg:pl-4">
            <div class="space-y-2.5">
              <span class="text-[9px] font-mono text-gray-500 tracking-wider font-semibold uppercase block">STORYBOARD MEDIA SLOT</span>

              <!-- Media Slot placeholder / display -->
              <div class="relative w-full aspect-video rounded-lg border border-gray-900 bg-black/40 overflow-hidden flex flex-col items-center justify-center group/media">
                {#if scene.image_url}
                  <img
                    src={scene.image_url}
                    alt="Storyboard Scene #{scene.scene_number}"
                    class="w-full h-full object-cover"
                  />
                  <!-- Hover controls overlay -->
                  <div class="absolute inset-0 bg-black/80 opacity-0 group-hover/media:opacity-100 flex flex-col items-center justify-center gap-1.5 transition-all p-2">
                    <div class="flex gap-1.5">
                      <label class="p-1.5 bg-gray-900/90 hover:bg-cyan-500 hover:text-black rounded text-gray-300 transition-all cursor-pointer" title="Tải ảnh mới lên">
                        <Upload class="w-3.5 h-3.5" />
                        <input type="file" accept="image/*" class="hidden" onchange={(e) => handleImageUpload(e, idx)} />
                      </label>
                      <button
                        onclick={() => openMediaLibrary(idx)}
                        class="p-1.5 bg-gray-900/90 hover:bg-cyan-500 hover:text-black rounded text-gray-300 transition-all"
                        title="Chọn từ thư viện"
                      >
                        <Image class="w-3.5 h-3.5" />
                      </button>
                    </div>
                    <button
                      onclick={() => {
                        scene.image_url = '';
                        triggerAutoSave();
                      }}
                      class="text-[9px] text-red-400 hover:text-red-300 underline font-mono mt-1"
                    >
                      XÓA ẢNH KHỎI CẢNH
                    </button>
                  </div>
                {:else if generatingImageMap[idx]}
                  <div class="flex flex-col items-center justify-center gap-2">
                    <div class="w-6 h-6 border-2 border-cyan-500/10 border-t-cyan-400 rounded-full animate-spin"></div>
                    <span class="text-[9px] font-mono text-cyan-400/60 uppercase">DRAFTING...</span>
                  </div>
                {:else}
                  <!-- Action slots when image empty -->
                  <div class="text-center p-3">
                    <Image class="w-6 h-6 text-gray-600 mx-auto mb-1.5 opacity-55" />
                    <div class="flex flex-wrap items-center justify-center gap-1.5">
                      <button
                        onclick={() => generateAiImage(idx)}
                        class="px-2 py-1 bg-cyan-950/30 hover:bg-cyan-500/20 border border-cyan-500/20 text-[9px] font-mono text-cyan-400 rounded transition-colors"
                      >
                        Sinh ảnh AI
                      </button>
                      
                      <label class="px-2 py-1 bg-[#111] hover:bg-gray-800 border border-gray-800 text-[9px] font-mono text-gray-300 rounded cursor-pointer transition-colors">
                        Tải lên
                        <input type="file" accept="image/*" class="hidden" onchange={(e) => handleImageUpload(e, idx)} />
                      </label>
                      
                      <button
                        onclick={() => openMediaLibrary(idx)}
                        class="p-1 bg-[#111] hover:bg-gray-800 border border-gray-800 text-[9px] font-mono text-gray-300 rounded transition-colors"
                        title="Chọn từ thư viện"
                      >
                        Thư viện
                      </button>
                      
                      <button
                        onclick={() => pasteImageUrl(idx)}
                        class="p-1 bg-[#111] hover:bg-gray-800 border border-gray-800 text-[9px] font-mono text-gray-300 rounded transition-colors"
                        title="Dán link ảnh"
                      >
                        <Link class="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                {/if}
              </div>
            </div>

            <!-- AI Image Prompt Edit -->
            <div class="mt-2.5">
              <span class="text-[8px] font-mono text-gray-500 tracking-wider uppercase block mb-1">PROMPT TIẾNG ANH (AI RENDER)</span>
              <div class="relative">
                <textarea
                  bind:value={scene.image_prompt}
                  oninput={triggerAutoSave}
                  rows="2"
                  class="w-full bg-black/40 border border-gray-900 rounded-lg p-2 text-[10px] text-gray-400 font-mono focus:outline-none focus:border-cyan-500/40 focus:bg-[#0c0c0c] transition-all resize-none leading-normal"
                  placeholder="Prompt sinh ảnh Midjourney/Stable Diffusion..."
                ></textarea>
                
                <button
                  onclick={() => copyPrompt(scene.image_prompt || "", idx)}
                  class="absolute right-2 bottom-2 p-1 hover:bg-white/5 rounded text-gray-500 hover:text-white transition-colors"
                  title="Sao chép prompt"
                >
                  {#if copiedTextMap[idx]}
                    <Check class="w-3.5 h-3.5 text-emerald-400" />
                  {:else}
                    <Copy class="w-3.5 h-3.5" />
                  {/if}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    {/each}
  </div>
{:else}
  <div class="text-center py-12 text-gray-600">
    <AlertCircle class="w-8 h-8 mx-auto opacity-35 text-red-500 mb-2" />
    <p class="text-[10px] font-mono">LỖI ĐỊNH DẠNG: Kịch bản không chứa phân cảnh cấu trúc.</p>
  </div>
{/if}
