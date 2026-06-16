<script lang="ts">
  import { fade, slide } from "svelte/transition";
  import { untrack } from "svelte";
  import Video from "@lucide/svelte/icons/video";
  import Search from "@lucide/svelte/icons/search";
  import Plus from "@lucide/svelte/icons/plus";
  import RefreshCw from "@lucide/svelte/icons/refresh-cw";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import Download from "@lucide/svelte/icons/download";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import Clock from "@lucide/svelte/icons/clock";
  import User from "@lucide/svelte/icons/user";
  import Copy from "@lucide/svelte/icons/copy";
  import Check from "@lucide/svelte/icons/check";
  import AlertCircle from "@lucide/svelte/icons/alert-circle";
  import ChevronRight from "@lucide/svelte/icons/chevron-right";
  import Film from "@lucide/svelte/icons/film";
  import ShoppingBag from "@lucide/svelte/icons/shopping-bag";
  import Palette from "@lucide/svelte/icons/palette";
  import X from "@lucide/svelte/icons/x";
  import ArrowUp from "@lucide/svelte/icons/arrow-up";
  import ArrowDown from "@lucide/svelte/icons/arrow-down";
  import Play from "@lucide/svelte/icons/play";
  import Square from "@lucide/svelte/icons/square";
  import Volume2 from "@lucide/svelte/icons/volume-2";
  import Image from "@lucide/svelte/icons/image";
  import Link from "@lucide/svelte/icons/link";
  import FileText from "@lucide/svelte/icons/file-text";
  import Upload from "@lucide/svelte/icons/upload";

  import type { BaseWidgetProps, VideoScript, VideoScriptStyle } from "$lib/types";
  import { useNanobot } from "$lib/state/nanobot.svelte";
  const nanobot = useNanobot();
  import { apiClient } from "$lib/utils/apiClient";
  import OrderPagination from "./OrderPagination.svelte";
  import FileManager from "$lib/components/media/FileManager.svelte";

  // Product interface for selection
  interface Product {
    id: string;
    name: string;
    slug: string;
  }

  let { data = {} } = $props<BaseWidgetProps>();

  // State definitions
  let scripts = $state<VideoScript[]>([]);
  let styles = $state<VideoScriptStyle[]>([]);
  let products = $state<Product[]>([]);
  
  let totalScripts = $state(0);
  let isLoading = $state(true);
  let isGenerating = $state(false);
  let genStep = $state(0); // 0: Idle, 1: resolving product, 2: generating script, 3: finishing

  // Filters & Pagination
  let searchInput = $state("");
  let searchTerm = $state("");
  let currentPage = $state(1);
  let pageSize = $state(8);

  // Selection & Active workspace state
  let selectedScriptId = $state<string | null>(null);
  let selectedScript = $derived(scripts.find(s => s.id === selectedScriptId) || null);
  let activeScript = $state<VideoScript | null>(null);
  let copiedTextMap = $state<Record<number, boolean>>({});

  // Auto-save State
  let saveStatus = $state<"Saved" | "Saving..." | "Error saving">("Saved");
  let saveTimeout: ReturnType<typeof setTimeout>;

  // Drawer / Form State
  let isDrawerOpen = $state(false);
  let selectedProductId = $state("");
  let selectedStyleId = $state("");

  // Media Library state
  let mediaLibrary = $state<any[]>([]);
  let showLibraryModalIdx = $state<number | null>(null);

  // Playback Timeline simulator state
  let isPlaying = $state(false);
  let activeSceneIdx = $state<number | null>(null);
  let playbackTime = $state(0);
  let ttsEnabled = $state(true);
  let selectedVoice = $state("vi-VN-HoaiMyNeural");
  let playbackInterval: ReturnType<typeof setInterval>;

  // Deep copy selected script to active copy
  $effect(() => {
    if (selectedScript) {
      untrack(() => {
        activeScript = JSON.parse(JSON.stringify(selectedScript));
        saveStatus = "Saved";
        stopPlayback();
      });
    } else {
      activeScript = null;
    }
  });

  // Debounced auto-save trigger
  function triggerAutoSave() {
    if (!activeScript) return;
    saveStatus = "Saving...";
    clearTimeout(saveTimeout);
    saveTimeout = setTimeout(async () => {
      try {
        // Recalculate total duration
        const total = activeScript.structured_script.scenes.reduce((sum, s) => sum + (Number(s.duration) || 0), 0);
        activeScript.structured_script.total_duration = Math.round(total * 10) / 10;

        const res = await apiClient.patch<{ data: VideoScript }>(
          `/api/v1/video/script/${activeScript.id}`,
          {
            title: activeScript.title,
            structured_script: activeScript.structured_script
          }
        );
        // Sync to scripts list
        const idx = scripts.findIndex(s => s.id === activeScript.id);
        if (idx !== -1) {
          scripts[idx] = res.data;
        }
        saveStatus = "Saved";
      } catch (error: unknown) {
        saveStatus = "Error saving";
        const msg = error instanceof Error ? error.message : String(error);
        nanobot.addLog(`[SYS] Script auto-save failed: ${msg}`, "Nanobot-System");
      }
    }, 1000);
  }

  // Load Scripts
  async function loadScripts() {
    isLoading = true;
    try {
      const offset = (currentPage - 1) * pageSize;
      const params = new URLSearchParams({
        limit: pageSize.toString(),
        offset: offset.toString(),
      });
      if (searchTerm) params.append("search", searchTerm);

      const res = await apiClient.get<{ data: VideoScript[]; total: number }>(
        `/api/v1/video/scripts?${params.toString()}`
      );
      scripts = res.data;
      totalScripts = res.total;

      // Select first script by default if none selected
      if (scripts.length > 0 && !selectedScriptId) {
        selectedScriptId = scripts[0].id;
      }
    } catch (error: unknown) {
      const msg = error instanceof Error ? error.message : String(error);
      nanobot.addLog(`[SYS] Video scripts load failed: ${msg}`, "Nanobot-System");
      scripts = [];
      totalScripts = 0;
    } finally {
      isLoading = false;
    }
  }

  // Load Styles & Products
  async function loadMetadata() {
    try {
      const styleRes = await apiClient.get<{ data: VideoScriptStyle[] }>("/api/v1/video/styles");
      styles = styleRes.data || [];

      const prodRes = await apiClient.get<{ data: Product[] }>("/api/v1/products?limit=100");
      products = prodRes.data || [];

      if (styles.length > 0) selectedStyleId = styles[0].id;
      if (products.length > 0) selectedProductId = products[0].id;
    } catch (e) {
      console.warn("Failed to load metadata options", e);
    }
  }

  // Load Media Library
  async function loadMediaLibrary() {
    try {
      const res = await apiClient.get<{ data: any[] }>("/api/v1/media?limit=24");
      mediaLibrary = res.data || [];
    } catch (e) {
      console.warn("Failed to load media library", e);
    }
  }

  // Command-driven activation
  $effect(() => {
    if (data?.action === "CREATE") {
      untrack(() => {
        isDrawerOpen = true;
      });
    }
  });

  // Reload when page/search changes
  $effect(() => {
    loadScripts();
  });

  // Initial load
  $effect(() => {
    loadMetadata();
    loadMediaLibrary();
  });

  // Debounced Search
  let searchTimer: ReturnType<typeof setTimeout> | undefined;
  function handleSearchInput(e: Event) {
    const val = (e.target as HTMLInputElement).value;
    searchInput = val;
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
      searchTerm = val;
      currentPage = 1;
    }, 500);
  }

  // Delete script
  async function handleDelete(id: string, title: string) {
    const confirm = await nanobot.showConfirm({
      title: "XÁC NHẬN XOÁ KỊCH BẢN",
      message: `Bạn có chắc chắn muốn xoá kịch bản "${title}"? Hành động này không thể hoàn tác.`,
      confirmLabel: "XOÁ NGAY",
      cancelLabel: "Hủy bỏ",
    });
    if (confirm) {
      try {
        await apiClient.delete(`/api/v1/video/script/${encodeURIComponent(id)}`);
        nanobot.showToast("Đã xóa kịch bản thành công!", "success");
        if (selectedScriptId === id) {
          selectedScriptId = null;
        }
        loadScripts();
      } catch (error: unknown) {
        const msg = error instanceof Error ? error.message : String(error);
        nanobot.showToast(msg, "error");
      }
    }
  }

  // Generate Script
  async function handleGenerate(e: Event) {
    e.preventDefault();
    if (!selectedProductId || !selectedStyleId) {
      nanobot.showToast("Vui lòng chọn đầy đủ sản phẩm và phong cách!", "warning");
      return;
    }

    isGenerating = true;
    genStep = 1;

    try {
      await new Promise(r => setTimeout(r, 800));
      genStep = 2;

      const res = await apiClient.post<{ message: string; data: VideoScript }>(
        "/api/v1/video/script/generate",
        {
          product_id: selectedProductId,
          style_id: selectedStyleId
        }
      );

      genStep = 3;
      await new Promise(r => setTimeout(r, 600));

      nanobot.showToast("Đã sinh kịch bản video thành công!", "success");
      isDrawerOpen = false;
      selectedScriptId = res.data.id;
      loadScripts();
    } catch (error: unknown) {
      const msg = error instanceof Error ? error.message : String(error);
      nanobot.showToast(`Lỗi sinh kịch bản: ${msg}`, "error");
    } finally {
      isGenerating = false;
      genStep = 0;
    }
  }

  // Copy Image Prompt
  async function copyPrompt(text: string, index: number) {
    try {
      await navigator.clipboard.writeText(text);
      copiedTextMap[index] = true;
      setTimeout(() => {
        copiedTextMap[index] = false;
      }, 2000);
      nanobot.showToast(`Đã sao chép prompt phân cảnh ${index + 1}`, "success");
    } catch (e) {
      nanobot.showToast("Không thể sao chép tự động", "error");
    }
  }

  // Download Markdown file
  function downloadMarkdown(script: VideoScript) {
    const apiBase = typeof window !== 'undefined' ? window.location.origin : '';
    const token = typeof window !== 'undefined' ? (localStorage.getItem("admin_token") || sessionStorage.getItem("admin_token") || "") : "";
    const url = `${apiBase}/api/v1/video/script/${script.id}/export?Authorization=Bearer ${token}`;
    
    const link = document.createElement("a");
    link.href = url;
    link.download = `script_${script.id}.md`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    nanobot.showToast("Đang tải xuống kịch bản...", "info");
  }

  // Image Upload handler
  async function handleImageUpload(e: Event, sceneIdx: number) {
    const input = e.target as HTMLInputElement;
    if (!input.files?.length || !activeScript) return;
    const file = input.files[0];
    const formData = new FormData();
    formData.append("data", file);
    
    try {
      nanobot.showToast("Đang tải ảnh lên...", "info");
      const res = await apiClient.upload<{ data: { file_path: string } }>(
        "/api/v1/media",
        formData
      );
      activeScript.structured_script.scenes[sceneIdx].image_url = res.data.file_path;
      triggerAutoSave();
      nanobot.showToast("Tải ảnh lên thành công!", "success");
      loadMediaLibrary();
    } catch (err: any) {
      nanobot.showToast(`Lỗi tải ảnh: ${err.message || String(err)}`, "error");
    }
  }

  // AI Image generator simulation
  let generatingImageMap = $state<Record<number, boolean>>({});
  async function generateAiImage(sceneIdx: number) {
    if (!activeScript) return;
    const scene = activeScript.structured_script.scenes[sceneIdx];
    if (!scene.image_prompt) {
      nanobot.showToast("Phân cảnh này chưa có Prompt hình ảnh!", "warning");
      return;
    }

    generatingImageMap[sceneIdx] = true;
    try {
      nanobot.showToast("AI đang phác họa hình ảnh phân cảnh...", "info");
      // Simulate high quality render latency
      await new Promise(r => setTimeout(r, 2200));
      const sig = Math.floor(Math.random() * 10000);
      scene.image_url = `https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=600&auto=format&fit=crop&sig=${sig}`;
      triggerAutoSave();
      nanobot.showToast("Đã tạo ảnh phác họa AI thành công!", "success");
    } catch (err: any) {
      nanobot.showToast("Lỗi sinh ảnh AI", "error");
    } finally {
      generatingImageMap[sceneIdx] = false;
    }
  }

  // Paste Image URL direct
  function pasteImageUrl(sceneIdx: number) {
    const url = prompt("Nhập hoặc dán URL hình ảnh:");
    if (url && activeScript) {
      activeScript.structured_script.scenes[sceneIdx].image_url = url;
      triggerAutoSave();
      nanobot.showToast("Đã liên kết URL ảnh phân cảnh!", "success");
    }
  }

  // Choose from system media library
  function openMediaLibrary(sceneIdx: number) {
    showLibraryModalIdx = sceneIdx;
  }

  function selectFromLibrary(sceneIdx: number, url: string) {
    if (activeScript) {
      activeScript.structured_script.scenes[sceneIdx].image_url = url;
      showLibraryModalIdx = null;
      triggerAutoSave();
      nanobot.showToast("Đã chọn ảnh từ thư viện!", "success");
    }
  }

  // Scene Operations: Move Up / Down
  function moveScene(idx: number, direction: 'up' | 'down') {
    if (!activeScript) return;
    const scenes = activeScript.structured_script.scenes;
    const targetIdx = direction === 'up' ? idx - 1 : idx + 1;
    if (targetIdx < 0 || targetIdx >= scenes.length) return;
    
    const temp = scenes[idx];
    scenes[idx] = scenes[targetIdx];
    scenes[targetIdx] = temp;
    
    // Reset index
    scenes.forEach((s, i) => {
      s.scene_number = i + 1;
    });
    
    triggerAutoSave();
  }

  // Scene Operations: Insert Scene
  function insertScene(idx: number) {
    if (!activeScript) return;
    const scenes = activeScript.structured_script.scenes;
    const newScene = {
      scene_number: idx + 2,
      duration: 3.0,
      visual_description: "Máy quay lia cận cảnh sản phẩm đặt trên bệ đỡ xoay tròn, ánh sáng dịu nhẹ tập trung vào bao bì thương hiệu.",
      voiceover: "Chất lượng vượt trội đi kèm thiết kế tinh tế từng đường nét.",
      audio_cue: "SFX tiếng kim loại click nhẹ, âm nhạc dâng trào nhẹ nhàng",
      image_prompt: "Cinematic close-up of cosmetics bottle on a rotating pedestal, luxury studio lighting, 8k resolution",
      scene_notes: "Chú ý quay slow-motion 60fps để tạo cảm giác cao cấp."
    };
    
    scenes.splice(idx + 1, 0, newScene);
    scenes.forEach((s, i) => {
      s.scene_number = i + 1;
    });
    
    triggerAutoSave();
    nanobot.showToast("Đã chèn thêm phân cảnh mới!", "success");
  }

  // Scene Operations: Delete Scene
  function deleteScene(idx: number) {
    if (!activeScript) return;
    const scenes = activeScript.structured_script.scenes;
    if (scenes.length <= 1) {
      nanobot.showToast("Kịch bản video phải duy trì ít nhất 1 phân cảnh!", "warning");
      return;
    }
    scenes.splice(idx, 1);
    scenes.forEach((s, i) => {
      s.scene_number = i + 1;
    });
    triggerAutoSave();
    nanobot.showToast("Đã xóa phân cảnh!", "info");
  }

  // High-fidelity Vietnamese Edge TTS voiceover preview helper
  let currentAudio: HTMLAudioElement | null = null;
  function speakVoiceover(text: string) {
    if (typeof window === "undefined") return;
    if (currentAudio) {
      currentAudio.pause();
      currentAudio = null;
    }
    
    // Tận dụng API Client TTS công khai đã tích hợp sẵn trên backend (chạy trên port 8000 được Caddy định tuyến)
    const apiBase = window.location.origin;
    const url = `${apiBase}/api/v1/client/tts/stream?text=${encodeURIComponent(text)}&voice=${selectedVoice}`;
    currentAudio = new Audio(url);
    currentAudio.play().catch(e => {
      console.warn("[TTS] Lỗi phát âm thanh hoặc bị trình duyệt chặn tự phát:", e);
    });
  }

  // Playback Simulator core
  function startPlayback() {
    if (!activeScript?.structured_script?.scenes?.length) return;
    isPlaying = true;
    activeSceneIdx = 0;
    let elapsed = 0;
    let sceneStart = 0;

    if (ttsEnabled) {
      speakVoiceover(activeScript.structured_script.scenes[0].voiceover);
    }

    playbackInterval = setInterval(() => {
      if (!activeScript) return stopPlayback();
      const currentScene = activeScript.structured_script.scenes[activeSceneIdx!];
      if (!currentScene) return stopPlayback();

      elapsed += 0.1;
      playbackTime = Math.round(elapsed * 10) / 10;

      if (elapsed >= sceneStart + currentScene.duration) {
        if (activeSceneIdx! + 1 < activeScript.structured_script.scenes.length) {
          sceneStart += currentScene.duration;
          activeSceneIdx!++;
          if (ttsEnabled) {
            speakVoiceover(activeScript.structured_script.scenes[activeSceneIdx!].voiceover);
          }
        } else {
          stopPlayback();
        }
      }
    }, 100);
  }

  function stopPlayback() {
    isPlaying = false;
    activeSceneIdx = null;
    playbackTime = 0;
    clearInterval(playbackInterval);
    if (currentAudio) {
      currentAudio.pause();
      currentAudio = null;
    }
    if (typeof window !== "undefined" && window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
  }

  function downloadSceneAudio(scene: any) {
    if (!scene.voiceover) {
      nanobot.showToast("Không có lời thoại để tải!", "warning");
      return;
    }
    const apiBase = window.location.origin;
    const url = `${apiBase}/api/v1/client/tts/stream?text=${encodeURIComponent(scene.voiceover)}&voice=${selectedVoice}`;
    
    const a = document.createElement("a");
    a.href = url;
    const safeTitle = (activeScript?.title || "kich_ban").toLowerCase()
      .replace(/[^a-z0-9\s]/g, "")
      .replace(/\s+/g, "_");
    a.download = `${safeTitle}_scene_${scene.scene_number}.mp3`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    nanobot.showToast(`Đang tải giọng đọc Phân Cảnh ${scene.scene_number}...`, "success");
  }

  let totalPages = $derived(Math.max(1, Math.ceil(totalScripts / pageSize)));
</script>

<div class="w-full h-full flex flex-col md:flex-row bg-[#020202] text-gray-200 overflow-hidden font-sans">
  
  <!-- LEFT COLUMN: Scripts List & Filters -->
  <div class="w-full md:w-[360px] shrink-0 border-r border-[#151515] flex flex-col h-full bg-[#050505]">
    
    <!-- Header Toolbar -->
    <div class="p-4 border-b border-[#151515] flex items-center justify-between gap-3 bg-[#080808]">
      <div class="relative flex-1">
        <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-500" />
        <input
          type="text"
          placeholder="Tìm kịch bản..."
          class="w-full bg-[#111] border border-gray-800 rounded-md pl-9 pr-4 py-1.5 text-xs text-cyan-100 placeholder:text-gray-600 focus:outline-none focus:border-cyan-500/40 focus:bg-[#151515] transition-all"
          value={searchInput}
          oninput={handleSearchInput}
        />
      </div>
      
      <button
        onclick={loadScripts}
        class="p-2 bg-[#111] hover:bg-[#1a1a1a] border border-gray-800 rounded-md text-gray-400 hover:text-cyan-400 transition-colors"
        title="Tải lại danh sách"
      >
        <RefreshCw class="w-3.5 h-3.5" />
      </button>

      <button
        onclick={() => isDrawerOpen = true}
        class="flex items-center gap-1 px-3 py-1.5 bg-gradient-to-r from-pink-500 to-cyan-500 text-black text-xs font-semibold rounded-md hover:opacity-90 shadow-md shadow-cyan-500/10 transition-all shrink-0"
      >
        <Plus class="w-3.5 h-3.5 stroke-[3]" />
        <span>Tạo mới</span>
      </button>
    </div>

    <!-- Scripts Bento List -->
    <div class="flex-1 overflow-y-auto custom-scrollbar p-3 space-y-2">
      {#if isLoading}
        <div class="h-full flex flex-col items-center justify-center gap-3 py-12">
          <div class="w-8 h-8 border-2 border-cyan-500/10 border-t-cyan-400 rounded-full animate-spin"></div>
          <span class="text-[10px] font-mono text-cyan-400/50 tracking-wider">LOADING_SCRIPTS...</span>
        </div>
      {:else if scripts.length === 0}
        <div class="h-full flex flex-col items-center justify-center gap-3 text-gray-600 py-16">
          <Video class="w-10 h-10 opacity-20" />
          <span class="text-[10px] font-mono tracking-widest uppercase">Chưa có kịch bản nào</span>
        </div>
      {:else}
        {#each scripts as script (script.id)}
          <!-- svelte-ignore a11y_click_events_have_key_events -->
          <!-- svelte-ignore a11y_no_static_element_interactions -->
          <div
            onclick={() => selectedScriptId = script.id}
            class="group relative p-3 rounded-lg border transition-all cursor-pointer select-none
                   {selectedScriptId === script.id 
                     ? 'bg-cyan-950/20 border-cyan-500/40 shadow-sm shadow-cyan-500/5' 
                     : 'bg-[#0b0b0b] border-[#151515] hover:border-gray-800'}"
          >
            {#if selectedScriptId === script.id}
              <div class="absolute left-0 top-0 bottom-0 w-[3px] bg-cyan-500 rounded-l-md"></div>
            {/if}

            <div class="flex items-start justify-between gap-2">
              <h3 class="text-xs font-medium text-gray-200 line-clamp-2 leading-relaxed transition-colors group-hover:text-cyan-300">
                {script.title}
              </h3>
              
              <span class="text-[9px] px-1.5 py-0.5 rounded shrink-0 font-bold border tracking-wider
                           {script.style_platform === 'TikTok' 
                             ? 'bg-black text-white border-white/20' 
                             : 'bg-red-950/20 text-red-400 border-red-500/20'}">
                {script.style_platform || "Video"}
              </span>
            </div>

            <div class="mt-2.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-[10px] text-gray-500">
              <span class="flex items-center gap-1">
                <ShoppingBag class="w-3 h-3 text-pink-500/50" />
                <span class="truncate max-w-[100px]">{script.product_name || "Sản phẩm"}</span>
              </span>
              <span class="flex items-center gap-1">
                <Clock class="w-3 h-3 text-cyan-500/50" />
                <span>{script.structured_script?.total_duration || 0}s</span>
              </span>
              <span class="ml-auto text-gray-600 text-[9px] font-mono">
                {new Date(script.created_at).toLocaleDateString("vi-VN")}
              </span>
            </div>
          </div>
        {/each}
      {/if}
    </div>

    <!-- Pagination footer -->
    <div class="border-t border-[#151515] bg-[#070707] shrink-0">
      <OrderPagination
        bind:currentPage
        totalPages={totalPages}
        pageSize={pageSize}
        totalItems={totalScripts}
      />
    </div>
  </div>

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

        <!-- Detail Action Toolbar -->
        <div class="flex flex-wrap items-center gap-2 shrink-0">
          
          <!-- Playback Simulator controls -->
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
              onclick={() => ttsEnabled = !ttsEnabled}
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

            {#if isPlaying}
              <div class="px-2 py-0.5 text-[10px] font-mono text-cyan-400 bg-cyan-950/20 rounded border border-cyan-500/20 flex items-center gap-1">
                <span>SCENE #{activeSceneIdx! + 1}</span>
                <span>•</span>
                <span>{playbackTime}s</span>
              </div>
            {/if}
          </div>

          <button
            onclick={() => downloadMarkdown(activeScript!)}
            class="flex items-center gap-1.5 px-3 py-1.5 bg-cyan-950/30 hover:bg-cyan-500/20 border border-cyan-500/30 rounded text-[11px] font-mono tracking-wide text-cyan-400 transition-colors"
          >
            <Download class="w-3.5 h-3.5" />
            <span>EXPORT MD</span>
          </button>
          
          <button
            onclick={() => handleDelete(activeScript!.id, activeScript!.title)}
            class="p-2 bg-red-950/20 hover:bg-red-500/20 border border-red-500/30 rounded text-red-400 transition-colors"
            title="Xóa kịch bản"
          >
            <Trash2 class="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      <!-- Main Workspace Editor Panel -->
      <div class="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-6 bg-gradient-to-b from-[#020202] to-[#040404]">
        
        <!-- Script-level Notes section -->
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

        <!-- Storyblock Timeline container -->
        {#if activeScript.structured_script?.scenes?.length > 0}
          <div class="space-y-4">
            {#each activeScript.structured_script.scenes as scene, idx}
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
                      disabled={idx === activeScript!.structured_script.scenes.length - 1}
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
      </div>
    {/if}
  </div>

</div>

<!-- DRAWER: Generate Script Form -->
{#if isDrawerOpen}
  <!-- svelte-ignore a11y_click_events_have_key_events -->
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div
    class="fixed inset-0 bg-black/80 backdrop-blur-xs flex items-center justify-end z-[110]"
    transition:fade={{ duration: 200 }}
    onclick={() => !isGenerating && (isDrawerOpen = false)}
  >
    <!-- Drawer panel -->
    <div
      class="w-full max-w-md h-full bg-[#080808] border-l border-gray-800 p-6 flex flex-col justify-between"
      transition:slide={{ direction: 'right', duration: 250 }}
      onclick={(e) => e.stopPropagation()}
    >
      <div>
        <!-- Drawer Header -->
        <div class="flex items-center justify-between pb-4 border-b border-gray-900 mb-6">
          <div class="flex items-center gap-2">
            <Sparkles class="w-4 h-4 text-cyan-400" />
            <h3 class="text-sm font-bold text-white tracking-widest uppercase">SINH KỊCH BẢN VIDEO</h3>
          </div>
          <button
            onclick={() => isDrawerOpen = false}
            disabled={isGenerating}
            class="p-1.5 hover:bg-white/5 rounded text-gray-400 hover:text-white transition-colors"
          >
            <X class="w-4 h-4" />
          </button>
        </div>

        {#if isGenerating}
          <!-- Generating Status Loading Screen -->
          <div class="py-12 flex flex-col items-center justify-center gap-6">
            <div class="relative w-16 h-16 flex items-center justify-center">
              <div class="absolute inset-0 rounded-full border border-cyan-500/20 border-t-cyan-400 animate-spin"></div>
              <Video class="w-6 h-6 text-cyan-400 animate-pulse" />
            </div>

            <div class="w-full space-y-3 mt-4">
              <div class="flex items-center gap-3 text-xs">
                <span class="w-4 h-4 rounded-full border border-cyan-500/30 flex items-center justify-center text-[9px] font-mono
                             {genStep >= 1 ? 'bg-cyan-950 text-cyan-400 border-cyan-500' : 'text-gray-600 border-gray-800'}">
                  1
                </span>
                <span class={genStep === 1 ? 'text-cyan-400 font-semibold' : genStep > 1 ? 'text-gray-400' : 'text-gray-600'}>
                  Phân tích thông tin và công dụng sản phẩm...
                </span>
              </div>
              <div class="flex items-center gap-3 text-xs">
                <span class="w-4 h-4 rounded-full border border-cyan-500/30 flex items-center justify-center text-[9px] font-mono
                             {genStep >= 2 ? 'bg-cyan-950 text-cyan-400 border-cyan-500' : 'text-gray-600 border-gray-800'}">
                  2
                </span>
                <span class={genStep === 2 ? 'text-cyan-400 font-semibold animate-pulse' : genStep > 2 ? 'text-gray-400' : 'text-gray-600'}>
                  AI Core thiết lập phân cảnh & lời thoại...
                </span>
              </div>
              <div class="flex items-center gap-3 text-xs">
                <span class="w-4 h-4 rounded-full border border-cyan-500/30 flex items-center justify-center text-[9px] font-mono
                             {genStep >= 3 ? 'bg-cyan-950 text-cyan-400 border-cyan-500' : 'text-gray-600 border-gray-800'}">
                  3
                </span>
                <span class={genStep === 3 ? 'text-cyan-400 font-semibold' : 'text-gray-600'}>
                  Hoàn thiện và đồng bộ hóa cơ sở dữ liệu...
                </span>
              </div>
            </div>
            
            <p class="text-[9px] font-mono text-gray-500 tracking-wider text-center mt-6">
              Vui lòng không đóng cửa sổ. AI đang tính toán...
            </p>
          </div>
        {:else}
          <!-- Creation Form -->
          <form onsubmit={handleGenerate} class="space-y-5">
            <!-- Product selection -->
            <div class="space-y-2">
              <label for="product-select" class="text-[10px] font-mono tracking-wider text-gray-400 uppercase">SẢN PHẨM TIÊU ĐIỂM</label>
              <select
                id="product-select"
                bind:value={selectedProductId}
                class="w-full bg-[#111] border border-gray-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500"
              >
                {#if products.length === 0}
                  <option value="">Không tìm thấy sản phẩm nào</option>
                {:else}
                  {#each products as prod}
                    <option value={prod.id}>{prod.name} (SKU/Slug: {prod.slug})</option>
                  {/each}
                {/if}
              </select>
              <p class="text-[9px] font-mono text-gray-500 leading-normal">
                Kịch bản sẽ tự động trích xuất đặc tính nổi bật, cách dùng và tệp khách hàng từ sản phẩm được chọn.
              </p>
            </div>

            <!-- Style selection -->
            <div class="space-y-2">
              <label for="style-select" class="text-[10px] font-mono tracking-wider text-gray-400 uppercase">PHONG CÁCH / XU HƯỚNG VIDEO</label>
              <select
                id="style-select"
                bind:value={selectedStyleId}
                class="w-full bg-[#111] border border-gray-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500"
              >
                {#if styles.length === 0}
                  <option value="">Không tìm thấy phong cách nào</option>
                {:else}
                  {#each styles as style}
                    <option value={style.id}>[{style.platform}] {style.name}</option>
                  {/each}
                {/if}
              </select>
              <p class="text-[9px] font-mono text-gray-500 leading-normal">
                Style định dạng nhịp độ video, cách kể chuyện (storytelling) và cấu trúc Hook 3 giây đầu tiên.
              </p>
            </div>

            <!-- Style instruction details panel -->
            {#if styles.find(s => s.id === selectedStyleId)}
              {@const currentStyle = styles.find(s => s.id === selectedStyleId)!}
              <div class="bg-[#0c0c0c] border border-cyan-500/10 rounded-lg p-3 space-y-2 mt-4">
                <span class="text-[9px] font-mono text-cyan-400 font-bold uppercase tracking-widest block">CHI TIẾT PHONG CÁCH</span>
                <div class="text-[10px] space-y-1 text-gray-400 leading-relaxed">
                  <p><strong>Nền tảng:</strong> <span class="text-white">{currentStyle.platform}</span></p>
                  <p><strong>Cấu trúc Hook:</strong> <span class="text-gray-300 italic">{currentStyle.hook_template}</span></p>
                  <p class="line-clamp-3"><strong>Chi tiết:</strong> {currentStyle.style_instruction}</p>
                </div>
              </div>
            {/if}
          </form>
        {/if}
      </div>

      <!-- Footer Buttons -->
      {#if !isGenerating}
        <div class="flex items-center gap-3 border-t border-gray-900 pt-4 mt-6">
          <button
            onclick={() => isDrawerOpen = false}
            class="flex-1 py-2 bg-gray-900 hover:bg-gray-800 text-gray-300 text-xs font-semibold rounded-lg border border-gray-800 transition-colors"
          >
            Hủy bỏ
          </button>
          <button
            onclick={handleGenerate}
            class="flex-1 py-2 bg-gradient-to-r from-pink-500 to-cyan-500 text-black text-xs font-bold rounded-lg hover:opacity-90 shadow-md shadow-cyan-500/10 transition-all"
          >
            Bắt đầu sinh AI
          </button>
        </div>
      {/if}
    </div>
  </div>
{/if}

<!-- MODAL: System Media Library selector -->
{#if showLibraryModalIdx !== null}
  <div
    class="fixed inset-0 bg-black/80 backdrop-blur-xs flex items-center justify-center z-[120] p-4"
    transition:fade={{ duration: 150 }}
  >
    <div class="bg-[#0c0e14] border border-gray-850 rounded-xl w-full max-w-5xl h-[85vh] flex flex-col p-5 overflow-hidden shadow-2xl">
      <div class="flex items-center justify-between border-b border-gray-900 pb-3 mb-4">
        <div class="flex items-center gap-2">
          <Image class="w-4 h-4 text-cyan-400" />
          <h3 class="text-sm font-bold text-white uppercase tracking-wider">CHỌN ẢNH TỪ THƯ VIỆN HỆ THỐNG</h3>
        </div>
        <button
          onclick={() => showLibraryModalIdx = null}
          class="p-1 hover:bg-white/5 rounded text-gray-400 hover:text-white transition-colors"
        >
          <X class="w-4 h-4" />
        </button>
      </div>

      <!-- Professional FileManager component -->
      <div class="flex-1 overflow-hidden rounded-lg border border-gray-800 bg-black relative">
        <FileManager
          mode="pick"
          onSelect={(assets) => {
            if (assets && assets.length > 0) {
              const asset = assets[0];
              const url = asset.file_path || `/uploads/${asset.id}.webp`;
              selectFromLibrary(showLibraryModalIdx!, url);
            }
          }}
          onPickConfirm={(assets) => {
            if (assets && assets.length > 0) {
              const asset = assets[0];
              const url = asset.file_path || `/uploads/${asset.id}.webp`;
              selectFromLibrary(showLibraryModalIdx!, url);
            }
          }}
          onPickClose={() => showLibraryModalIdx = null}
        />
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
