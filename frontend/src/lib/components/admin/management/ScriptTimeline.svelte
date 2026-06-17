<script lang="ts">
  import Film from "@lucide/svelte/icons/film";
  import Clock from "@lucide/svelte/icons/clock";
  import ArrowUp from "@lucide/svelte/icons/arrow-up";
  import ArrowDown from "@lucide/svelte/icons/arrow-down";
  import Plus from "@lucide/svelte/icons/plus";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import Copy from "@lucide/svelte/icons/copy";
  import Check from "@lucide/svelte/icons/check";
  import AlertCircle from "@lucide/svelte/icons/alert-circle";
  import type { VideoScript, VideoScene } from "$lib/types";

  interface Props {
    activeScript: VideoScript;
    copiedTextMap: Record<number, boolean>;
    triggerAutoSave: () => void;
    moveScene: (idx: number, direction: 'up' | 'down') => void;
    insertScene: (idx: number) => void;
    deleteScene: (idx: number) => void;
    copyPrompt: (text: string, index: number) => void;
  }

  let {
    activeScript,
    copiedTextMap,
    triggerAutoSave,
    moveScene,
    insertScene,
    deleteScene,
    copyPrompt
  }: Props = $props();
</script>

<!-- Storyblock Timeline container -->
{#if activeScript.structured_script?.scenes?.length > 0}
  {@const scenes = activeScript.structured_script.scenes}
  <div class="space-y-4">
    {#each scenes as scene, idx}
      <div 
        class="relative bg-[#070707] border border-[#121212] hover:border-gray-800 focus-within:border-cyan-500/30 focus-within:bg-cyan-950/5 rounded-xl p-4 transition-all duration-300"
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
          <!-- Inputs Panel (Left) - Expanded to Full Width -->
          <div class="lg:col-span-12 space-y-3.5">
            
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
              </div>
              <textarea
                bind:value={scene.voiceover}
                oninput={triggerAutoSave}
                rows="2"
                class="w-full bg-cyan-950/5 border border-cyan-500/10 rounded-lg p-2.5 text-xs text-cyan-100 font-medium focus:outline-none focus:border-cyan-500/40 focus:bg-cyan-950/10 transition-all resize-none leading-relaxed italic"
                placeholder="Nội dung lời thuyết minh sẽ được đọc ở phân cảnh này..."
              ></textarea>
            </div>

            <!-- Scene-level notes -->
            <div>
              <span class="text-[9px] font-mono text-yellow-500/80 tracking-wider block mb-1">GHI CHÚ RIÊNG PHÂN CẢNH (CHUYỂN ĐỘNG CAMERA & DIỄN XUẤT)</span>
              <input
                type="text"
                bind:value={scene.scene_notes}
                oninput={triggerAutoSave}
                class="w-full bg-[#0a0a0a] border border-gray-900 rounded-lg px-2.5 py-1.5 text-xs text-yellow-200/80 placeholder:text-gray-700 focus:outline-none focus:border-cyan-500/40 focus:bg-[#0c0c0c] transition-all"
                placeholder="Ví dụ: Zoom cận cảnh vào sản phẩm, Lia máy góc rộng..."
              />
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
