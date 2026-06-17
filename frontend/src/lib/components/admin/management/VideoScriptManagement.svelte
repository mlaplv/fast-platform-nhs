<script lang="ts">
  import { fade } from "svelte/transition";
  import { untrack, onDestroy } from "svelte";
  import Image from "@lucide/svelte/icons/image";
  import X from "@lucide/svelte/icons/x";

  import type { BaseWidgetProps, VideoScript, VideoScriptStyle, VideoScene, Article, MediaAsset } from "$lib/types";
  import { useNanobot } from "$lib/state/nanobot.svelte";
  const nanobot = useNanobot();
  import { apiClient } from "$lib/utils/apiClient";
  import FileManager from "$lib/components/media/FileManager.svelte";

  // Subcomponents
  import ScriptList from "./ScriptList.svelte";
  import ScriptEditorWorkspace from "./ScriptEditorWorkspace.svelte";
  import VideoScriptGenerator from "./VideoScriptGenerator.svelte";
  import VideoScriptPromptHub from "./VideoScriptPromptHub.svelte";

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
  let articles = $state<Article[]>([]);
  
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
  let selectedArticleId = $state("");
  let customDescription = $state("");
  let sourceType = $state<"product" | "article" | "custom">("product");
  let targetDuration = $state<number>(30);
  let aspectRatio = $state<string>("9:16");

  // Media Library state
  let mediaLibrary = $state<MediaAsset[]>([]);
  let showLibraryModalIdx = $state<number | null>(null);

  // Playback Timeline simulator state
  let isPlaying = $state(false);
  let playbackInterval: ReturnType<typeof setInterval>;
  let selectedVoice = $state("vi-VN-HoaiMyNeural");
  let ttsEnabled = $state(true);
  let activeSceneIdx = $state<number | null>(null);
  let playbackTime = $state(0);

  // AI Prompt Hub states
  let showPromptHub = $state(false);
  let activePromptTab = $state<"midjourney" | "runway" | "heygen" | "gemini">("midjourney");

  function getMidjourneyPrompt(scene: VideoScene, aspect: string) {
    const desc = scene.visual_description || "";
    const notes = scene.scene_notes || "";
    const ar = aspect === "9:16" ? "9:16" : "16:9";
    return `A high-fidelity commercial cinematography storyboard slot. ${desc}. ${notes}. Clean look, photorealistic, 8k resolution, cinematic lighting, commercial grade --ar ${ar} --style raw --v 6.0`;
  }

  function getRunwayPrompt(scene: VideoScene) {
    const desc = scene.visual_description || "";
    const notes = scene.scene_notes || "";
    return `Cinematic, hyper-realistic video. ${desc}. Camera motion: ${notes}. Smooth transition, high dynamic range, photorealistic commercial styling, 8k.`;
  }

  function getGeminiPrompt(scene: VideoScene) {
    const desc = scene.visual_description || "";
    const notes = scene.scene_notes || "";
    const voice = scene.voiceover || "";
    return `[LỆNH TẠO VIDEO TRỰC TIẾP] Hãy sử dụng công cụ tạo video (Imagen Video / Vids / Google Video generator) tích hợp của bạn để sinh ra video trực tiếp cho phân cảnh sau:
- Mô tả hình ảnh (Visual Description): ${desc}
- Lời thoại (Voiceover): ${voice}
- Chuyển động camera & Ghi chú: ${notes}
- Phong cách: Điện ảnh thương mại, độ phân giải 8K, ánh sáng chuyên nghiệp.

YÊU CẦU: Thực thi ngay lệnh sinh video cho phân cảnh này dựa trên mô tả trên.`;
  }

  function getGeminiMasterPrompt() {
    if (!activeScript || !activeScript.structured_script?.scenes) return "";
    let text = `[LỆNH ĐIỀU HÀNH ĐẠO DIỄN - TẠO DỰ ÁN VIDEO TOÀN BỘ KỊCH BẢN]\n`;
    text += `Bạn là Đạo diễn Video AI kiêm Trợ lý sinh video của Google. Dưới đây là kịch bản marketing chi tiết cho sản phẩm "${activeScript.title || 'sản phẩm'}":\n\n`;
    activeScript.structured_script.scenes.forEach((scene: VideoScene, idx: number) => {
      const num = scene.scene_number || (idx + 1);
      text += `Phân cảnh #${num}:\n`;
      text += `- Mô tả hình ảnh: ${scene.visual_description || ""}\n`;
      text += `- Lời thoại: ${scene.voiceover || ""}\n`;
      text += `- Ghi chú & Chuyển động: ${scene.scene_notes || ""}\n\n`;
    });
    text += `YÊU CẦU THỰC THI:\n`;
    text += `1. Hãy kích hoạt ngay chức năng sinh video tích hợp (Imagen/Google Vids) để tạo các đoạn video phân cảnh trực tiếp.\n`;
    text += `2. Cung cấp các mô tả video đầu ra, đồng thời đưa ra các chỉ dẫn cụ thể về nhịp độ để tối ưu hóa việc xuất bản dự án video.`;
    return text;
  }

  function copyAllPrompts(type: "midjourney" | "runway" | "heygen" | "gemini") {
    if (!activeScript || !activeScript.structured_script?.scenes) return;
    const aspect = activeScript.structured_script.aspect_ratio || "16:9";
    let text = "";
    
    if (type === "gemini") {
      text = getGeminiMasterPrompt();
    } else {
      activeScript.structured_script.scenes.forEach((scene: VideoScene, idx: number) => {
        const num = scene.scene_number || (idx + 1);
        if (type === "midjourney") {
          text += `Scene #${num} Midjourney Prompt:\n${getMidjourneyPrompt(scene, aspect)}\n\n`;
        } else if (type === "runway") {
          text += `Scene #${num} Runway Prompt:\n${getRunwayPrompt(scene)}\n\n`;
        } else if (type === "heygen") {
          text += `Scene #${num} Voiceover:\n${scene.voiceover || ""}\n\n`;
        }
      });
    }
    
    navigator.clipboard.writeText(text.trim());
    nanobot.showToast("Đã sao chép tất cả prompt vào clipboard!", "success");
  }

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
        const total = activeScript.structured_script.scenes.reduce((sum, s) => sum + (Number(s.duration) || 0), 0);
        activeScript.structured_script.total_duration = Math.round(total * 10) / 10;

        const res = await apiClient.patch<{ data: VideoScript }>(
          `/api/v1/video/script/${activeScript.id}`,
          {
            title: activeScript.title,
            structured_script: activeScript.structured_script
          }
        );
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

  // Load Styles, Products & Articles
  async function loadMetadata() {
    try {
      const styleRes = await apiClient.get<{ data: VideoScriptStyle[] }>("/api/v1/video/styles");
      styles = styleRes.data || [];

      const prodRes = await apiClient.get<{ data: Product[] }>("/api/v1/products?limit=100");
      products = prodRes.data || [];

      const articleRes = await apiClient.get<{ data: Article[] }>("/api/v1/articles?limit=100");
      articles = articleRes.data || [];

      if (styles.length > 0) selectedStyleId = styles[0].id;
      if (products.length > 0) selectedProductId = products[0].id;
      if (articles.length > 0) selectedArticleId = articles[0].id;
    } catch (e) {
      console.warn("Failed to load metadata options", e);
    }
  }

  // Load Media Library
  async function loadMediaLibrary() {
    try {
      const res = await apiClient.get<{ data: MediaAsset[] }>("/api/v1/media?limit=24");
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
    
    if (!selectedStyleId) {
      nanobot.showToast("Vui lòng chọn phong cách kịch bản!", "warning");
      return;
    }
    
    if (sourceType === "product" && !selectedProductId) {
      nanobot.showToast("Vui lòng chọn sản phẩm tiêu điểm!", "warning");
      return;
    }
    
    if (sourceType === "article" && !selectedArticleId) {
      nanobot.showToast("Vui lòng chọn bài viết nguồn!", "warning");
      return;
    }
    
    if (sourceType === "custom" && !customDescription.trim()) {
      nanobot.showToast("Vui lòng nhập mô tả ý tưởng!", "warning");
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
          source_type: sourceType,
          product_id: sourceType === "product" ? selectedProductId : null,
          article_id: sourceType === "article" ? selectedArticleId : null,
          description: sourceType === "custom" ? customDescription : null,
          style_id: selectedStyleId,
          aspect_ratio: aspectRatio,
          target_duration: targetDuration
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
    const token = typeof window !== 'undefined' ? (localStorage.getItem("admin_token") || sessionStorage.getItem("admin_token") || "") : "";
    const url = `/api/v1/video/script/${script.id}/export?Authorization=Bearer ${token}`;
    
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
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      nanobot.showToast(`Lỗi tải ảnh: ${msg}`, "error");
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
      await new Promise(r => setTimeout(r, 2200));
      const sig = Math.floor(Math.random() * 10000);
      scene.image_url = `https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=600&auto=format&fit=crop&sig=${sig}`;
      triggerAutoSave();
      nanobot.showToast("Đã tạo ảnh phác họa AI thành công!", "success");
    } catch (err: unknown) {
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

  // High-fidelity Vietnamese Edge TTS voiceover prefetch & play engine
  let currentAudio: HTMLAudioElement | null = null;
  let currentAudioUrl: string | null = null;
  let sceneAudioCache = new Map<number, string>(); // scene_number -> blobUrl
  let isPreloadingAudio = $state(false);

  async function preloadScriptAudio() {
    if (typeof window === "undefined" || !activeScript?.structured_script?.scenes?.length) return;
    
    isPreloadingAudio = true;
    const scenes = activeScript.structured_script.scenes;
    const voiceToLoad = selectedVoice;
    
    sceneAudioCache.forEach(url => URL.revokeObjectURL(url));
    sceneAudioCache.clear();
    
    for (const scene of scenes) {
      if (!scene.voiceover) continue;
      if (selectedVoice !== voiceToLoad) break;
      
      const url = `/api/v1/client/tts/stream?text=${encodeURIComponent(scene.voiceover)}&voice=${voiceToLoad}`;
      try {
        const response = await fetch(url);
        if (response.ok) {
          const blob = await response.blob();
          if (blob.size > 0 && !blob.type.includes("json")) {
            const blobUrl = URL.createObjectURL(blob);
            sceneAudioCache.set(scene.scene_number, blobUrl);
          }
        }
      } catch (e) {
        console.warn(`[TTS Preload] Không thể tải trước âm thanh cho phân cảnh ${scene.scene_number}:`, e);
      }
    }
    isPreloadingAudio = false;
  }

  $effect(() => {
    if (activeScript && selectedVoice) {
      preloadScriptAudio();
    }
  });

  onDestroy(() => {
    sceneAudioCache.forEach(url => URL.revokeObjectURL(url));
  });

  async function speakVoiceover(sceneNumber: number, text: string) {
    if (typeof window === "undefined") return;
    if (currentAudio) {
      currentAudio.pause();
      currentAudio = null;
    }
    if (currentAudioUrl) {
      const isFromCache = Array.from(sceneAudioCache.values()).includes(currentAudioUrl);
      if (!isFromCache) {
        URL.revokeObjectURL(currentAudioUrl);
      }
      currentAudioUrl = null;
    }
    
    if (sceneAudioCache.has(sceneNumber)) {
      currentAudioUrl = sceneAudioCache.get(sceneNumber)!;
      currentAudio = new Audio(currentAudioUrl);
      currentAudio.play().catch(e => {
        console.warn("[TTS] Lỗi phát âm thanh từ bộ đệm:", e);
      });
      return;
    }
    
    const url = `/api/v1/client/tts/stream?text=${encodeURIComponent(text)}&voice=${selectedVoice}`;
    try {
      const response = await fetch(url);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const blob = await response.blob();
      
      if (blob.size > 0 && !blob.type.includes("json")) {
        currentAudioUrl = URL.createObjectURL(blob);
        currentAudio = new Audio(currentAudioUrl);
        currentAudio.play().catch(e => {
          console.warn("[TTS] Lỗi phát âm thanh tự phát:", e);
        });
      }
    } catch (e) {
      console.warn("[TTS] Không thể lấy dữ liệu âm thanh:", e);
    }
  }

  // Playback Simulator core
  function startPlayback() {
    if (!activeScript?.structured_script?.scenes?.length) return;
    isPlaying = true;
    activeSceneIdx = 0;
    let elapsed = 0;
    let sceneStart = 0;

    if (ttsEnabled) {
      speakVoiceover(activeScript.structured_script.scenes[0].scene_number, activeScript.structured_script.scenes[0].voiceover);
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
            speakVoiceover(activeScript.structured_script.scenes[activeSceneIdx!].scene_number, activeScript.structured_script.scenes[activeSceneIdx!].voiceover);
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
    if (currentAudioUrl) {
      const isFromCache = Array.from(sceneAudioCache.values()).includes(currentAudioUrl);
      if (!isFromCache) {
        URL.revokeObjectURL(currentAudioUrl);
      }
      currentAudioUrl = null;
    }
    if (typeof window !== "undefined" && window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
  }

  function downloadSceneAudio(scene: VideoScene) {
    if (!scene.voiceover) {
      nanobot.showToast("Không có lời thoại để tải!", "warning");
      return;
    }
    const url = `/api/v1/client/tts/stream?text=${encodeURIComponent(scene.voiceover)}&voice=${selectedVoice}`;
    
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
  
  <ScriptList
    scripts={scripts}
    isLoading={isLoading}
    bind:selectedScriptId={selectedScriptId}
    bind:searchInput={searchInput}
    bind:currentPage={currentPage}
    pageSize={pageSize}
    totalScripts={totalScripts}
    totalPages={totalPages}
    onSearchInput={handleSearchInput}
    onRefresh={loadScripts}
    onOpenDrawer={() => { isDrawerOpen = true; }}
  />

  <ScriptEditorWorkspace
    activeScript={activeScript}
    saveStatus={saveStatus}
    bind:isPlaying={isPlaying}
    bind:ttsEnabled={ttsEnabled}
    bind:selectedVoice={selectedVoice}
    isPreloadingAudio={isPreloadingAudio}
    activeSceneIdx={activeSceneIdx}
    playbackTime={playbackTime}
    generatingImageMap={generatingImageMap}
    copiedTextMap={copiedTextMap}
    bind:showPromptHub={showPromptHub}
    triggerAutoSave={triggerAutoSave}
    startPlayback={startPlayback}
    stopPlayback={stopPlayback}
    downloadMarkdown={downloadMarkdown}
    handleDelete={handleDelete}
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

<!-- MODAL: System Media Library selector -->
{#if showLibraryModalIdx !== null}
  <div class="fixed inset-0 z-[120] flex items-center justify-center bg-black/80 backdrop-blur-xs p-4" transition:fade={{ duration: 150 }}>
    <div class="bg-[#080808] border border-gray-800 rounded-xl w-full max-w-5xl h-[85vh] flex flex-col overflow-hidden shadow-2xl">
      <!-- Modal Header -->
      <div class="p-4 border-b border-gray-900 flex items-center justify-between bg-black/40">
        <div class="flex items-center gap-2">
          <Image class="w-4 h-4 text-cyan-400" />
          <h3 class="text-xs font-bold tracking-widest text-white uppercase">HỆ THỐNG THƯ VIỆN ĐA PHƯƠNG TIỆN</h3>
        </div>
        <button
          onclick={() => { showLibraryModalIdx = null; }}
          class="p-1.5 hover:bg-gray-900 rounded text-gray-400 hover:text-white transition-colors"
        >
          <X class="w-4 h-4" />
        </button>
      </div>

      <!-- Professional FileManager component -->
      <div class="flex-1 overflow-hidden">
        <FileManager
          onSelect={(asset) => selectFromLibrary(showLibraryModalIdx!, asset.url)}
        />
      </div>
    </div>
  </div>
{/if}

<VideoScriptGenerator
  bind:isDrawerOpen={isDrawerOpen}
  isGenerating={isGenerating}
  genStep={genStep}
  bind:sourceType={sourceType}
  products={products}
  bind:selectedProductId={selectedProductId}
  articles={articles}
  bind:selectedArticleId={selectedArticleId}
  bind:customDescription={customDescription}
  bind:aspectRatio={aspectRatio}
  bind:targetDuration={targetDuration}
  styles={styles}
  bind:selectedStyleId={selectedStyleId}
  handleGenerate={handleGenerate}
/>

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
