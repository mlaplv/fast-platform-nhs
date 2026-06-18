<script lang="ts">
  import { onMount } from "svelte";
  import Film from "@lucide/svelte/icons/film";
  import Clock from "@lucide/svelte/icons/clock";
  import ArrowUp from "@lucide/svelte/icons/arrow-up";
  import ArrowDown from "@lucide/svelte/icons/arrow-down";
  import Plus from "@lucide/svelte/icons/plus";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import Copy from "@lucide/svelte/icons/copy";
  import Check from "@lucide/svelte/icons/check";
  import AlertCircle from "@lucide/svelte/icons/alert-circle";
  
  // View mode icons verified in codebase
  import Layout from "@lucide/svelte/icons/layout";
  import LayoutGrid from "@lucide/svelte/icons/layout-grid";
  import List from "@lucide/svelte/icons/list";

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

  // Reactive state for layout mode & active scene selection
  let viewMode = $state<'split' | 'grid' | 'stack'>('split');
  let selectedSceneIdx = $state<number>(0);

  // Drag & drop state variables
  let draggedIdx = $state<number | null>(null);
  let dragHoverIdx = $state<number | null>(null);

  // Restore user preferences
  onMount(() => {
    const saved = localStorage.getItem("script_timeline_view_mode");
    if (saved === 'split' || saved === 'grid' || saved === 'stack') {
      viewMode = saved;
    }
  });

  function changeViewMode(mode: 'split' | 'grid' | 'stack') {
    viewMode = mode;
    localStorage.setItem("script_timeline_view_mode", mode);
  }

  // Safety guard: sync active scene index when total scenes count changes
  $effect(() => {
    const scenesCount = activeScript.structured_script?.scenes?.length || 0;
    if (scenesCount > 0 && selectedSceneIdx >= scenesCount) {
      selectedSceneIdx = scenesCount - 1;
    }
    if (selectedSceneIdx < 0) {
      selectedSceneIdx = 0;
    }
  });

  // HTML5 Drag & Drop handlers
  function handleDragStart(e: DragEvent, idx: number) {
    draggedIdx = idx;
    if (e.dataTransfer) {
      e.dataTransfer.effectAllowed = "move";
      e.dataTransfer.setData("text/plain", idx.toString());
    }
  }

  function handleDragOver(e: DragEvent, idx: number) {
    e.preventDefault();
    if (draggedIdx === null || draggedIdx === idx) return;
    dragHoverIdx = idx;
  }

  function handleDragLeave() {
    dragHoverIdx = null;
  }

  function handleDrop(e: DragEvent, targetIdx: number) {
    e.preventDefault();
    if (draggedIdx === null || draggedIdx === targetIdx) return;

    const list = [...activeScript.structured_script.scenes];
    const [draggedItem] = list.splice(draggedIdx, 1);
    list.splice(targetIdx, 0, draggedItem);

    // Recalculate sequential numbers
    list.forEach((scene, i) => {
      scene.scene_number = i + 1;
    });

    activeScript.structured_script.scenes = list;
    
    // Keep focus on the dropped scene
    selectedSceneIdx = targetIdx;
    
    triggerAutoSave();
    
    draggedIdx = null;
    dragHoverIdx = null;
  }

  function handleDragEnd() {
    draggedIdx = null;
    dragHoverIdx = null;
  }
</script>

<!-- Timeline Workspace Controls -->
{#if activeScript.structured_script?.scenes?.length > 0}
  {@const scenes = activeScript.structured_script.scenes}

  <!-- View Mode Switcher Toolbar -->
  <div class="flex items-center justify-between bg-[#080808] border border-[#151515] rounded-xl px-4 py-2 mb-4 shrink-0">
    <div class="flex items-center gap-2">
      <span class="text-[9px] font-mono text-gray-500 uppercase tracking-widest font-black">Chế độ xem timeline:</span>
    </div>
    <div class="flex items-center gap-1 bg-black/60 border border-gray-800 rounded-lg p-0.5">
      <button
        type="button"
        onclick={() => changeViewMode('split')}
        class="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-[9px] font-mono font-bold uppercase transition-all
               {viewMode === 'split' 
                 ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 shadow-sm shadow-cyan-500/5' 
                 : 'border border-transparent text-gray-500 hover:text-gray-300'}"
      >
        <Layout class="w-3.5 h-3.5" />
        <span>Chia đôi (Split Editor)</span>
      </button>
      
      <button
        type="button"
        onclick={() => changeViewMode('grid')}
        class="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-[9px] font-mono font-bold uppercase transition-all
               {viewMode === 'grid' 
                 ? 'bg-purple-500/10 text-purple-400 border border-purple-500/20 shadow-sm shadow-purple-500/5' 
                 : 'border border-transparent text-gray-500 hover:text-gray-300'}"
      >
        <LayoutGrid class="w-3.5 h-3.5" />
        <span>Bản vẽ (Storyboard Grid)</span>
      </button>
      
      <button
        type="button"
        onclick={() => changeViewMode('stack')}
        class="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-[9px] font-mono font-bold uppercase transition-all
               {viewMode === 'stack' 
                 ? 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20 shadow-sm shadow-yellow-500/5' 
                 : 'border border-transparent text-gray-500 hover:text-gray-300'}"
      >
        <List class="w-3.5 h-3.5" />
        <span>Danh sách cuộn (Classic Stack)</span>
      </button>
    </div>
  </div>

  <!-- ────────────────────────────────────────────────── -->
  <!-- 1. SPLIT VIEW (Master-Detail Editor) -->
  <!-- ────────────────────────────────────────────────── -->
  {#if viewMode === 'split'}
    <div class="grid grid-cols-1 xl:grid-cols-12 gap-5 items-start">
      
      <div class="xl:col-span-4 relative max-h-[600px] overflow-y-auto pr-1 custom-scrollbar scrollbar-none" style="scrollbar-width: none; -ms-overflow-style: none;">
        <div class="pl-9 relative z-10">
          {#each scenes as scene, idx}
            <div class="relative pb-4">
              <div class="relative flex items-center w-full">
                <!-- Timeline Segment Spine (Đoạn trục thời gian động nối tiếp) -->
                {#if idx === 0}
                  <!-- Cảnh đầu tiên: chỉ có đoạn dưới nối từ mốc tròn xuống đáy -->
                  <div class="absolute left-[-36px] w-8 flex justify-center top-1/2 bottom-[-16px] z-0">
                    <div class="w-[2px] h-full transition-all duration-300
                                {idx < selectedSceneIdx ? 'bg-cyan-500 shadow-[0_0_6px_rgba(6,182,212,0.4)]' : 'bg-gray-800'}"></div>
                  </div>
                {:else if idx === scenes.length - 1}
                  <!-- Cảnh cuối cùng: có đoạn trên nối từ đỉnh xuống mốc tròn -->
                  <div class="absolute left-[-36px] w-8 flex justify-center top-0 bottom-1/2 z-0">
                    <div class="w-[2px] h-full transition-all duration-300
                                {idx <= selectedSceneIdx ? 'bg-cyan-500 shadow-[0_0_6px_rgba(6,182,212,0.4)]' : 'bg-gray-800'}"></div>
                  </div>
                  <!-- Đoạn dưới đứt nét nối xuống nút Thêm phân cảnh mới -->
                  <div class="absolute left-[-36px] w-8 flex justify-center top-1/2 bottom-[-16px] z-0">
                    <div class="w-[2px] h-full bg-gray-800/40 border-dashed border-l border-gray-800"></div>
                  </div>
                {:else}
                  <!-- Cảnh ở giữa: chia làm 2 đoạn trên và dưới phân tách bởi mốc tròn -->
                  <!-- Đoạn trên: nối từ đỉnh xuống mốc tròn -->
                  <div class="absolute left-[-36px] w-8 flex justify-center top-0 bottom-1/2 z-0">
                    <div class="w-[2px] h-full transition-all duration-300
                                {idx <= selectedSceneIdx ? 'bg-cyan-500 shadow-[0_0_6px_rgba(6,182,212,0.4)]' : 'bg-gray-800'}"></div>
                  </div>
                  <!-- Đoạn dưới: nối từ mốc tròn xuống đáy -->
                  <div class="absolute left-[-36px] w-8 flex justify-center top-1/2 bottom-[-16px] z-0">
                    <div class="w-[2px] h-full transition-all duration-300
                                {idx < selectedSceneIdx ? 'bg-cyan-500 shadow-[0_0_6px_rgba(6,182,212,0.4)]' : 'bg-gray-800'}"></div>
                  </div>
                {/if}
                <!-- Timeline Node (Mốc tròn thời gian) -->
                <div class="absolute left-[-36px] w-8 flex justify-center top-1/2 -translate-y-1/2 z-20">
                  {#if selectedSceneIdx === idx}
                    <div class="w-3.5 h-3.5 rounded-full bg-cyan-400 border-[3px] border-[#020202] shadow-[0_0_8px_rgba(6,182,212,0.9)] transition-all duration-300"></div>
                  {:else}
                    <div class="w-2.5 h-2.5 rounded-full bg-[#161616] border-2 border-gray-700 hover:border-cyan-400/50 transition-all duration-300"></div>
                  {/if}
                </div>

              <!-- Card phân cảnh -->
              <div
                role="button"
                tabindex="0"
                draggable="true"
                ondragstart={(e) => handleDragStart(e, idx)}
                ondragover={(e) => handleDragOver(e, idx)}
                ondragleave={handleDragLeave}
                ondrop={(e) => handleDrop(e, idx)}
                ondragend={handleDragEnd}
                onclick={() => selectedSceneIdx = idx}
                onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); selectedSceneIdx = idx; } }}
                class="w-full text-left relative bg-[#070707]/90 border rounded-xl p-3.5 transition-all duration-200 block cursor-grab active:cursor-grabbing group
                       {selectedSceneIdx === idx 
                         ? 'border-cyan-500/50 bg-cyan-950/10 shadow-md shadow-cyan-500/5' 
                         : 'border-[#121212] hover:border-gray-800 hover:bg-[#0b0b0b]'}
                       {dragHoverIdx === idx ? 'border-dashed border-cyan-400 bg-cyan-950/20 scale-[0.98]' : ''}"
              >
                <!-- Scene Index & Duration Header -->
                <div class="flex items-center justify-between mb-2">
                  <div class="flex items-center gap-2">
                    <span class="text-[9px] font-mono font-bold uppercase tracking-widest
                                 {selectedSceneIdx === idx ? 'text-cyan-300' : 'text-gray-500'}">
                      PHÂN CẢNH #{scene.scene_number}
                    </span>
                  </div>
                  
                  <div class="flex items-center gap-1 bg-black/40 px-1.5 py-0.5 rounded border border-gray-900">
                    <Clock class="w-2.5 h-2.5 text-gray-500" />
                    <span class="text-[9px] font-mono font-bold text-cyan-300">{scene.duration}s</span>
                  </div>
                </div>

                <!-- Voiceover preview snippet -->
                <p class="text-[10px] text-gray-400 group-hover:text-gray-200 line-clamp-2 italic leading-relaxed font-sans">
                  {scene.voiceover || scene.visual_description || "(Không có nội dung thoại)"}
                </p>

                <!-- Quick operations inside sidebar -->
                <div class="mt-2.5 flex items-center justify-end gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    type="button"
                    onclick={(e) => { 
                      e.stopPropagation(); 
                      moveScene(idx, 'up'); 
                      if (selectedSceneIdx > 0) selectedSceneIdx--; 
                    }}
                    disabled={idx === 0}
                    class="p-0.5 hover:bg-[#151515] rounded text-gray-400 hover:text-white disabled:opacity-20 transition-all"
                    title="Di chuyển lên"
                  >
                    <ArrowUp class="w-3 h-3" />
                  </button>
                  <button
                    type="button"
                    onclick={(e) => { 
                      e.stopPropagation(); 
                      moveScene(idx, 'down'); 
                      if (selectedSceneIdx < scenes.length - 1) selectedSceneIdx++; 
                    }}
                    disabled={idx === scenes.length - 1}
                    class="p-0.5 hover:bg-[#151515] rounded text-gray-400 hover:text-white disabled:opacity-20 transition-all"
                    title="Di chuyển xuống"
                  >
                    <ArrowDown class="w-3 h-3" />
                  </button>
                  <button
                    type="button"
                    onclick={(e) => { 
                      e.stopPropagation(); 
                      deleteScene(idx); 
                      if (selectedSceneIdx >= scenes.length - 1 && selectedSceneIdx > 0) selectedSceneIdx--; 
                    }}
                    class="p-0.5 hover:bg-[#151515] rounded text-gray-400 hover:text-red-400 transition-all"
                    title="Xóa phân cảnh"
                  >
                    <Trash2 class="w-3 h-3" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        {/each}
          
          <!-- Add Scene Button -->
          <div class="relative pb-4">
            <div class="relative flex items-center w-full">
              <!-- Timeline Segment Spine cuối cùng nối từ đỉnh xuống mốc tròn thêm cảnh -->
              <div class="absolute left-[-36px] w-8 flex justify-center top-0 bottom-1/2 z-0">
                <div class="w-[2px] h-full bg-gray-800/40 border-dashed border-l border-gray-800"></div>
              </div>

              <!-- Timeline Plus Node (mốc tròn thêm cảnh) -->
              <div class="absolute left-[-36px] w-8 flex justify-center top-1/2 -translate-y-1/2 z-20">
                <div class="w-2.5 h-2.5 rounded-full bg-[#161616] border-2 border-dashed border-gray-700 flex items-center justify-center"></div>
              </div>
              
              <button
                type="button"
                onclick={() => { 
                  insertScene(scenes.length - 1); 
                  selectedSceneIdx = scenes.length; 
                }}
                class="w-full py-2.5 bg-dashed border border-dashed border-gray-800 hover:border-cyan-500/30 hover:bg-cyan-950/5 rounded-xl text-center text-[10px] font-mono text-gray-500 hover:text-cyan-400 transition-all flex items-center justify-center gap-1.5"
              >
                <Plus class="w-3.5 h-3.5" />
                <span>THÊM PHÂN CẢNH MỚI</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- RIGHT: Focus Active Scene Detailed Editor (8 columns) -->
      <div class="xl:col-span-8">
        {#if scenes[selectedSceneIdx]}
          {@const activeScene = scenes[selectedSceneIdx]}
          <div class="bg-[#050505] border border-[#151515] rounded-2xl p-5 space-y-4 shadow-xl relative overflow-hidden">
            <div class="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-cyan-500 to-purple-500"></div>
            
            <!-- Active Header -->
            <div class="flex items-center justify-between border-b border-gray-900 pb-3 mb-2">
              <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-lg bg-cyan-950/20 border border-cyan-500/20 flex items-center justify-center">
                  <Film class="w-4 h-4 text-cyan-400" />
                </div>
                <div>
                  <h3 class="text-xs font-mono font-black text-white uppercase tracking-wider">PHÂN CẢNH #{activeScene.scene_number}</h3>
                  <p class="text-[9px] font-mono text-gray-500 mt-0.5">Biên soạn nội dung visual prompt & lời thoại</p>
                </div>
              </div>

              <!-- Duration config -->
              <div class="flex items-center gap-2 bg-[#0c0c0c] border border-gray-800 rounded-xl px-3 py-1.5">
                <Clock class="w-3.5 h-3.5 text-yellow-500" />
                <span class="text-[10px] font-mono text-gray-400 uppercase">Thời lượng:</span>
                <input
                  type="number"
                  step="0.5"
                  min="1"
                  bind:value={activeScene.duration}
                  onchange={triggerAutoSave}
                  class="w-12 bg-black border border-gray-800 rounded-lg px-2 py-0.5 text-center text-cyan-400 text-xs font-mono font-bold focus:outline-none focus:border-cyan-500"
                />
                <span class="text-[10px] font-mono text-gray-500">giây</span>
              </div>
            </div>

            <!-- Visual Description Area -->
            <div class="space-y-1.5">
              <div class="flex items-center justify-between">
                <span class="text-[9px] font-mono text-pink-500 tracking-widest font-black uppercase">MÔ TẢ HÌNH ẢNH / VISUAL DESCRIPTION</span>
                <span class="text-[8px] font-mono text-gray-500">Sinh prompt Runway/MJ</span>
              </div>
              <textarea
                bind:value={activeScene.visual_description}
                oninput={triggerAutoSave}
                rows="4"
                class="w-full bg-[#080808] border border-gray-900 rounded-xl p-3 text-xs text-gray-200 focus:outline-none focus:border-cyan-500/40 focus:bg-[#0b0b0b] transition-all resize-none leading-relaxed font-sans shadow-inner"
                placeholder="Mô tả hành động của nhân vật, bối cảnh xung quanh, góc camera quay chậm..."
              ></textarea>
            </div>

            <!-- Voiceover Area -->
            <div class="space-y-1.5">
              <div class="flex items-center justify-between">
                <span class="text-[9px] font-mono text-cyan-400 tracking-widest font-black uppercase">LỜI THOẠI (VOICEOVER)</span>
                <span class="text-[8px] font-mono text-gray-500">Giữ tỷ lệ nói phù hợp với thời lượng</span>
              </div>
              <textarea
                bind:value={activeScene.voiceover}
                oninput={triggerAutoSave}
                rows="3"
                class="w-full bg-cyan-950/5 border border-cyan-500/10 rounded-xl p-3 text-xs text-cyan-100 font-medium focus:outline-none focus:border-cyan-500/40 focus:bg-cyan-950/10 transition-all resize-none leading-relaxed italic font-sans"
                placeholder="Lời thoại kịch bản sẽ thuyết minh..."
              ></textarea>
            </div>

            <!-- Camera & Editing Notes -->
            <div class="space-y-1.5">
              <span class="text-[9px] font-mono text-yellow-500/80 tracking-widest font-black uppercase block">GHI CHÚ RIÊNG PHÂN CẢNH</span>
              <input
                type="text"
                bind:value={activeScene.scene_notes}
                oninput={triggerAutoSave}
                class="w-full bg-[#080808] border border-gray-800 rounded-xl px-3 py-2 text-xs text-yellow-200/80 placeholder:text-gray-700 focus:outline-none focus:border-cyan-500/40 focus:bg-[#0b0b0b] transition-all"
                placeholder="Ví dụ: Zoom cận cảnh, lia máy slow-motion..."
              />
            </div>
            
            <!-- Detail Footer actions -->
            <div class="flex items-center justify-between pt-3.5 border-t border-gray-900 mt-5 text-[10px]">
              <span class="text-gray-500 font-mono">Đang soạn Phân cảnh {selectedSceneIdx + 1} / {scenes.length}</span>
              <div class="flex items-center gap-2">
                <button
                  type="button"
                  onclick={() => { 
                    insertScene(selectedSceneIdx); 
                    selectedSceneIdx++; 
                  }}
                  class="px-3 py-1.5 bg-gray-900 hover:bg-cyan-950/20 border border-gray-800 hover:border-cyan-500/30 text-gray-400 hover:text-cyan-400 rounded-lg transition-colors flex items-center gap-1 font-mono uppercase text-[9px] font-bold"
                >
                  <Plus class="w-3 h-3" />
                  <span>Chèn cảnh tiếp theo</span>
                </button>
              </div>
            </div>

          </div>
        {:else}
          <div class="border border-dashed border-gray-800 rounded-2xl p-12 text-center text-gray-500 font-mono text-xs">
            Vui lòng chọn một phân cảnh kịch bản ở danh sách bên trái để biên tập.
          </div>
        {/if}
      </div>

    </div>
  {/if}

  <!-- ────────────────────────────────────────────────── -->
  <!-- 2. STORYBOARD GRID VIEW -->
  <!-- ────────────────────────────────────────────────── -->
  {#if viewMode === 'grid'}
    <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      {#each scenes as scene, idx}
        <div 
          draggable="true"
          ondragstart={(e) => handleDragStart(e, idx)}
          ondragover={(e) => handleDragOver(e, idx)}
          ondragleave={handleDragLeave}
          ondrop={(e) => handleDrop(e, idx)}
          ondragend={handleDragEnd}
          class="bg-[#070707] border rounded-xl p-4 space-y-3 relative flex flex-col justify-between cursor-grab active:cursor-grabbing group transition-all duration-200
                 {dragHoverIdx === idx 
                   ? 'border-dashed border-purple-400 bg-purple-950/15 scale-[0.98]' 
                   : 'border-[#121212] hover:border-gray-800 focus-within:border-cyan-500/30'}"
        >
          <!-- Grid Scene Header -->
          <div class="flex items-center justify-between border-b border-gray-900 pb-2">
            <span class="text-[9px] font-mono font-bold text-cyan-300 uppercase">CẢNH #{scene.scene_number} ({scene.duration} giây)</span>
            <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
              <button 
                type="button"
                onclick={() => moveScene(idx, 'up')} 
                disabled={idx === 0} 
                class="p-0.5 hover:bg-[#151515] rounded text-gray-500 hover:text-white disabled:opacity-20"
              >
                <ArrowUp class="w-3 h-3" />
              </button>
              <button 
                type="button"
                onclick={() => moveScene(idx, 'down')} 
                disabled={idx === scenes.length - 1} 
                class="p-0.5 hover:bg-[#151515] rounded text-gray-500 hover:text-white disabled:opacity-20"
              >
                <ArrowDown class="w-3 h-3" />
              </button>
              <button 
                type="button"
                onclick={() => deleteScene(idx)} 
                class="p-0.5 hover:bg-[#151515] rounded text-gray-500 hover:text-red-400"
              >
                <Trash2 class="w-3 h-3" />
              </button>
            </div>
          </div>
          
          <!-- Textarea fields in Grid -->
          <div class="space-y-2.5 text-[10px]">
            <div>
              <span class="text-[7.5px] font-mono text-pink-500/80 uppercase font-black block mb-0.5">Mô tả Visual</span>
              <textarea
                bind:value={scene.visual_description}
                oninput={triggerAutoSave}
                rows="2"
                class="w-full bg-black/40 border border-gray-900 rounded p-2 text-gray-300 focus:outline-none focus:border-cyan-500/40 resize-none font-sans"
              ></textarea>
            </div>
            <div>
              <span class="text-[7.5px] font-mono text-cyan-400/80 uppercase font-black block mb-0.5">Lời thoại Voiceover</span>
              <textarea
                bind:value={scene.voiceover}
                oninput={triggerAutoSave}
                rows="2"
                class="w-full bg-cyan-950/5 border border-cyan-500/10 rounded p-2 text-cyan-100 focus:outline-none focus:border-cyan-500/40 resize-none italic font-sans"
              ></textarea>
            </div>
          </div>
          
          <!-- Edit detail quick action -->
          <button
            type="button"
            onclick={() => { 
              selectedSceneIdx = idx; 
              viewMode = 'split'; 
            }}
            class="w-full py-1 text-center bg-gray-900/60 hover:bg-cyan-950/20 border border-gray-800 hover:border-cyan-500/20 text-gray-400 hover:text-cyan-400 text-[8px] font-mono rounded uppercase tracking-wider transition-colors mt-2"
          >
            Mở trình soạn thảo chi tiết
          </button>
        </div>
      {/each}
    </div>
  {/if}

  <!-- ────────────────────────────────────────────────── -->
  <!-- 3. CLASSIC STACK VIEW (Optimized Scroll View) -->
  <!-- ────────────────────────────────────────────────── -->
  {#if viewMode === 'stack'}
    <div class="space-y-4">
      {#each scenes as scene, idx}
        <div 
          class="relative bg-[#070707] border border-[#121212] hover:border-gray-800 focus-within:border-cyan-500/30 focus-within:bg-cyan-950/5 rounded-xl p-4 transition-all duration-300"
        >
          <!-- Classic Header -->
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

            <!-- Controllers -->
            <div class="flex items-center gap-1.5">
              <button
                type="button"
                onclick={() => moveScene(idx, 'up')}
                disabled={idx === 0}
                class="p-1 hover:bg-[#151515] rounded text-gray-400 hover:text-white disabled:opacity-20 transition-all"
                title="Di chuyển lên"
              >
                <ArrowUp class="w-3.5 h-3.5" />
              </button>
              <button
                type="button"
                onclick={() => moveScene(idx, 'down')}
                disabled={idx === scenes.length - 1}
                class="p-1 hover:bg-[#151515] rounded text-gray-400 hover:text-white disabled:opacity-20 transition-all"
                title="Di chuyển xuống"
              >
                <ArrowDown class="w-3.5 h-3.5" />
              </button>
              <button
                type="button"
                onclick={() => insertScene(idx)}
                class="p-1 hover:bg-[#151515] rounded text-gray-400 hover:text-cyan-400 transition-all"
                title="Chèn phân cảnh sau"
              >
                <Plus class="w-3.5 h-3.5" />
              </button>
              <button
                type="button"
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
            <div class="lg:col-span-12 space-y-3">
              
              <!-- Visual description -->
              <div>
                <span class="text-[9px] font-mono text-pink-500 tracking-wider font-semibold uppercase block mb-1">MÔ TẢ HÌNH ẢNH / CẢNH QUAY</span>
                <textarea
                  bind:value={scene.visual_description}
                  oninput={triggerAutoSave}
                  rows="2"
                  class="w-full bg-[#0a0a0a] border border-gray-900 rounded-lg p-2.5 text-xs text-gray-200 focus:outline-none focus:border-cyan-500/40 focus:bg-[#0c0c0c] transition-all resize-none leading-relaxed font-sans"
                  placeholder="Mô tả hành động của diễn viên, bối cảnh, góc đặt camera..."
                ></textarea>
              </div>

              <!-- Voiceover -->
              <div>
                <div class="flex items-center justify-between mb-1">
                  <span class="text-[9px] font-mono text-cyan-400 tracking-wider font-semibold uppercase">LỜI THOẠI (VOICEOVER)</span>
                </div>
                <textarea
                  bind:value={scene.voiceover}
                  oninput={triggerAutoSave}
                  rows="2"
                  class="w-full bg-cyan-950/5 border border-cyan-500/10 rounded-lg p-2.5 text-xs text-cyan-100 font-medium focus:outline-none focus:border-cyan-500/40 focus:bg-cyan-950/10 transition-all resize-none leading-relaxed italic font-sans"
                  placeholder="Nội dung lời thuyết minh sẽ được đọc..."
                ></textarea>
              </div>

              <!-- Notes -->
              <div>
                <span class="text-[9px] font-mono text-yellow-500/80 tracking-wider block mb-1">GHI CHÚ RIÊNG PHÂN CẢNH</span>
                <input
                  type="text"
                  bind:value={scene.scene_notes}
                  oninput={triggerAutoSave}
                  class="w-full bg-[#0a0a0a] border border-gray-900 rounded-lg px-2.5 py-1.5 text-xs text-yellow-200/80 placeholder:text-gray-700 focus:outline-none focus:border-cyan-500/40 focus:bg-[#0c0c0c] transition-all"
                  placeholder="Ví dụ: Zoom cận cảnh vào sản phẩm, Lia máy slow-motion..."
                />
              </div>
            </div>
          </div>
        </div>
      {/each}
    </div>
  {/if}

{:else}
  <div class="text-center py-12 text-gray-600">
    <AlertCircle class="w-8 h-8 mx-auto opacity-35 text-red-500 mb-2" />
    <p class="text-[10px] font-mono">LỖI ĐỊNH DẠNG: Kịch bản không chứa phân cảnh cấu trúc.</p>
  </div>
{/if}

<style>
  /* Ẩn thanh scrollbar thô cứng trên trình duyệt */
  :global(.scrollbar-none::-webkit-scrollbar) {
    display: none;
  }
  :global(.scrollbar-none) {
    -ms-overflow-style: none;  /* IE and Edge */
    scrollbar-width: none;  /* Firefox */
  }
</style>
