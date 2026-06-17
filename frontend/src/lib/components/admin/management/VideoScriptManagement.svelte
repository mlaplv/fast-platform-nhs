<script lang="ts">
  import { fade, slide } from "svelte/transition";
  import { untrack, onDestroy } from "svelte";
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
  import Terminal from "@lucide/svelte/icons/terminal";
  import ExternalLink from "@lucide/svelte/icons/external-link";
  import Eye from "@lucide/svelte/icons/eye";

  import type { BaseWidgetProps, VideoScript, VideoScriptStyle, VideoScene, Article, MediaAsset } from "$lib/types";
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
  let articles = $state<Article[]>([]);
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

  // Clypra & AI Prompt states
  let isClypraLoading = $state(false);
  let isDownloadingZip = $state(false);
  let showPromptHub = $state(false);
  let activePromptTab = $state<"midjourney" | "runway" | "heygen" | "gemini">("midjourney");

  async function openInClypra() {
    if (!activeScript) return;
    isClypraLoading = true;
    try {
      const res = await apiClient.post<{ data: { launched: boolean } }>(
        `/api/v1/video/script/${activeScript.id}/clypra/open?voice=${selectedVoice}`
      );
      if (res.data && res.data.data?.launched) {
        nanobot.showToast("Đã xuất timeline và khởi chạy Clypra Editor!", "success");
      } else {
        nanobot.showToast("Đã lưu project.json, hãy mở Clypra thủ công để chỉnh sửa.", "warning");
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      nanobot.showToast(`Lỗi kết nối Clypra: ${msg}`, "error");
    } finally {
      isClypraLoading = false;
    }
  }

  async function downloadClypraZip() {
    if (!activeScript) return;
    isDownloadingZip = true;
    try {
      const token = sessionStorage.getItem("admin_token") || 
        document.cookie.split("; ").find(row => row.startsWith("admin_token="))?.split("=")[1] || 
        null;
        
      const response = await fetch(`/api/v1/video/script/${activeScript.id}/clypra/download?voice=${selectedVoice}`, {
        headers: {
          ...(token ? { "Authorization": `Bearer ${token}` } : {})
        }
      });
      
      if (!response.ok) {
        throw new Error("Không thể tải xuống file dự án. Vui lòng kiểm tra lại kết nối.");
      }
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `clypra_project_${activeScript.id}.zip`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();
      nanobot.showToast("Tải dự án Clypra ZIP thành công!", "success");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      nanobot.showToast(`Lỗi tải file: ${msg}`, "error");
    } finally {
      isDownloadingZip = false;
    }
  }

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
      // Giai đoạn 1: Gọi phân tích Google Search & Đối thủ
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
      // Simulate high quality render latency
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

  // High-fidelity Vietnamese Edge TTS voiceover prefetch & play engine
  let currentAudio: HTMLAudioElement | null = null;
  let currentAudioUrl: string | null = null;
  let sceneAudioCache = new Map<number, string>(); // scene_number -> blobUrl
  let isPreloadingAudio = $state(false);

  async function preloadScriptAudio() {
    if (typeof window === "undefined" || !activeScript?.structured_script?.scenes?.length) return;
    
    isPreloadingAudio = true;
    const apiBase = window.location.origin;
    const scenes = activeScript.structured_script.scenes;
    const voiceToLoad = selectedVoice;
    
    // Thu hồi toàn bộ Object URLs cũ để tránh rò rỉ bộ nhớ
    sceneAudioCache.forEach(url => URL.revokeObjectURL(url));
    sceneAudioCache.clear();
    
    // Tải trước nối tiếp để không làm nghẽn băng thông và tránh rate limit của Microsoft
    for (const scene of scenes) {
      if (!scene.voiceover) continue;
      
      // Kiểm tra nếu người dùng đã chuyển kịch bản hoặc giọng đọc khác trong lúc đang tải
      if (selectedVoice !== voiceToLoad) break;
      
      const url = `${apiBase}/api/v1/client/tts/stream?text=${encodeURIComponent(scene.voiceover)}&voice=${voiceToLoad}`;
      try {
        const response = await fetch(url);
        if (response.ok) {
          const blob = await response.blob();
          // Bảo vệ nếu blob rỗng hoặc lỗi JSON trả về từ server
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

  // Tự động tải trước âm thanh khi người dùng mở kịch bản hoặc chuyển giọng nói khác
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
      // Chỉ thu hồi đường dẫn động, giữ nguyên cache tĩnh tải trước
      const isFromCache = Array.from(sceneAudioCache.values()).includes(currentAudioUrl);
      if (!isFromCache) {
        URL.revokeObjectURL(currentAudioUrl);
      }
      currentAudioUrl = null;
    }
    
    // 1. Kiểm tra trong bộ nhớ đệm tải trước (Instant Playback - Triệt tiêu giật lag)
    if (sceneAudioCache.has(sceneNumber)) {
      currentAudioUrl = sceneAudioCache.get(sceneNumber)!;
      currentAudio = new Audio(currentAudioUrl);
      currentAudio.play().catch(e => {
        console.warn("[TTS] Lỗi phát âm thanh từ bộ đệm:", e);
      });
      return;
    }
    
    // 2. Chế độ Fallback tải trực tiếp nếu chưa kịp nạp vào bộ đệm
    const apiBase = window.location.origin;
    const url = `${apiBase}/api/v1/client/tts/stream?text=${encodeURIComponent(text)}&voice=${selectedVoice}`;
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
        
        {#if activeScript.structured_script?.competitor_analysis}
          <!-- Competitive Intelligence Panel -->
          <div class="bg-[#050608] border border-cyan-950 rounded-xl p-4 space-y-3 relative overflow-hidden group">
            <div class="absolute -right-10 -bottom-10 w-24 h-24 bg-cyan-500/5 rounded-full blur-xl"></div>
            <div class="flex items-center justify-between border-b border-cyan-900/20 pb-2">
              <div class="flex items-center gap-2">
                <Sparkles class="w-4 h-4 text-cyan-400" />
                <span class="text-[10px] font-mono font-bold tracking-widest text-cyan-400 uppercase">PHÂN TÍCH ĐỐI THỦ & CHIẾN LƯỢC PHẢN BIỆN (USP)</span>
              </div>
              {#if activeScript.structured_script?.aspect_ratio}
                <span class="text-[9px] font-mono bg-cyan-950 text-cyan-400 px-2 py-0.5 rounded border border-cyan-500/20 font-bold">
                  Khung hình: {activeScript.structured_script.aspect_ratio === '9:16' ? 'Dọc (9:16)' : activeScript.structured_script.aspect_ratio === '16:9' ? 'Ngang (16:9)' : activeScript.structured_script.aspect_ratio}
                </span>
              {/if}
            </div>

            <!-- Core message banner -->
            {#if activeScript.structured_script.competitor_analysis.core_message}
              <div class="bg-cyan-950/20 border border-cyan-500/25 rounded-lg p-2.5">
                <p class="text-[9px] font-mono text-cyan-400 uppercase tracking-wider font-bold mb-1">Thông điệp truyền thông cốt lõi:</p>
                <p class="text-xs text-gray-200 leading-relaxed font-semibold italic">
                  "{activeScript.structured_script.competitor_analysis.core_message}"
                </p>
              </div>
            {/if}

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
              <!-- Competitor Weaknesses -->
              <div class="space-y-1.5">
                <span class="text-[9px] font-mono text-red-400/80 uppercase tracking-wider font-bold block">▼ Điểm yếu lớn của đối thủ:</span>
                <ul class="space-y-1 text-[11px] text-gray-400 leading-relaxed list-disc list-inside">
                  {#each activeScript.structured_script.competitor_analysis.competitor_weaknesses || [] as weakness}
                    <li>{weakness}</li>
                  {/each}
                </ul>
              </div>

              <!-- Our Strengths / USP -->
              <div class="space-y-1.5">
                <span class="text-[9px] font-mono text-emerald-400/80 uppercase tracking-wider font-bold block">▲ Điểm mạnh/USP của chúng ta:</span>
                <ul class="space-y-1 text-[11px] text-gray-400 leading-relaxed list-disc list-inside">
                  {#each activeScript.structured_script.competitor_analysis.our_strengths || [] as strength}
                    <li>{strength}</li>
                  {/each}
                </ul>
              </div>
            </div>
          </div>
        {/if}

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

        <!-- Cầu nối Video Editor & AI Prompt Hub Bento Card -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <!-- Cầu nối Clypra Studio -->
          <div class="bg-[#0b0c10]/60 border border-cyan-500/20 rounded-xl p-5 relative overflow-hidden group">
            <div class="absolute -right-10 -bottom-10 w-32 h-32 bg-cyan-500/5 rounded-full blur-2xl group-hover:bg-cyan-500/10 transition-all duration-500"></div>
            
            <div class="flex items-center justify-between border-b border-gray-900/60 pb-3 mb-4">
              <div class="flex items-center gap-2">
                <Film class="w-4 h-4 text-cyan-400" />
                <span class="text-[10px] font-mono font-bold tracking-widest text-cyan-400 uppercase">CLYPRA EDITOR STUDIO</span>
              </div>
              <span class="text-[9px] font-mono bg-cyan-900/20 text-cyan-400 px-2 py-0.5 rounded border border-cyan-500/20">LOCAL PRODUCTION</span>
            </div>
            
            <div class="space-y-4">
              <p class="text-[11px] text-gray-400 leading-relaxed font-sans">
                Đóng gói toàn bộ phân cảnh thành Timeline Project chuẩn Clypra (tự động ghép ảnh storyboard, sinh giọng đọc TTS, chèn phụ đề) và mở trình chỉnh sửa Clypra chỉ với 1 click.
              </p>
              
              <div class="grid grid-cols-2 gap-3">
                <button 
                  onclick={openInClypra}
                  disabled={isClypraLoading || isDownloadingZip}
                  class="flex items-center justify-center gap-1.5 py-2 px-2 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 disabled:from-gray-800 disabled:to-gray-800 text-white rounded-lg font-semibold text-[11px] border border-cyan-400/20 transition-all shadow-md shadow-cyan-500/10 hover:shadow-cyan-500/25 active:scale-[0.98]"
                >
                  {#if isClypraLoading}
                    <span class="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                    <span>MỞ...</span>
                  {:else}
                    <ExternalLink class="w-3.5 h-3.5" />
                    <span>MỞ TRỰC TIẾP</span>
                  {/if}
                </button>

                <button 
                  onclick={downloadClypraZip}
                  disabled={isClypraLoading || isDownloadingZip}
                  class="flex items-center justify-center gap-1.5 py-2 px-2 bg-gradient-to-r from-teal-600 to-cyan-600 hover:from-teal-500 hover:to-cyan-500 disabled:from-gray-800 disabled:to-gray-800 text-white rounded-lg font-semibold text-[11px] border border-teal-400/20 transition-all shadow-md shadow-teal-500/10 hover:shadow-teal-500/25 active:scale-[0.98]"
                >
                  {#if isDownloadingZip}
                    <span class="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                    <span>TẢI...</span>
                  {:else}
                    <Download class="w-3.5 h-3.5" />
                    <span>TẢI ZIP DỰ ÁN</span>
                  {/if}
                </button>
              </div>
            </div>
          </div>

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
            
            <div class="space-y-4">
              <p class="text-[11px] text-gray-400 leading-relaxed font-sans">
                Trích xuất hàng loạt các câu lệnh (prompts) tối ưu riêng cho từng nền tảng AI Video (Runway, Sora) và AI Image (Midjourney, Flux) để tạo ra thước phim điện ảnh cao cấp.
              </p>
              
              <button 
                onclick={() => showPromptHub = true}
                class="w-full flex items-center justify-center gap-2 py-2.5 bg-gradient-to-r from-purple-700 to-pink-700 hover:from-purple-600 hover:to-pink-600 text-white rounded-lg font-semibold text-xs border border-purple-400/20 transition-all shadow-md shadow-purple-500/10 hover:shadow-purple-500/25 active:scale-[0.98]"
              >
                <Eye class="w-3.5 h-3.5" />
                <span>XEM & SAO CHÉP AI PROMPT BATCH</span>
              </button>
            </div>
          </div>
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
                  Google Search & Phân tích phản biện đối thủ...
                </span>
              </div>
              <div class="flex items-center gap-3 text-xs">
                <span class="w-4 h-4 rounded-full border border-cyan-500/30 flex items-center justify-center text-[9px] font-mono
                             {genStep >= 2 ? 'bg-cyan-950 text-cyan-400 border-cyan-500' : 'text-gray-600 border-gray-800'}">
                  2
                </span>
                <span class={genStep === 2 ? 'text-cyan-400 font-semibold animate-pulse' : genStep > 2 ? 'text-gray-400' : 'text-gray-600'}>
                  AI Core thiết lập kịch bản phân cảnh & USP...
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
            <!-- Source Type selection -->
            <div class="space-y-2">
              <label class="text-[10px] font-mono tracking-wider text-gray-400 uppercase">NGUỒN DỮ LIỆU ĐẦU VÀO</label>
              <div class="grid grid-cols-3 gap-2 p-1 bg-[#111] rounded-lg border border-gray-800">
                <button
                  type="button"
                  onclick={() => sourceType = "product"}
                  class="py-1 text-[11px] rounded transition-all font-semibold
                         {sourceType === 'product' ? 'bg-cyan-950 text-cyan-400 border border-cyan-500/20' : 'text-gray-400 hover:text-white'}"
                >
                  Sản phẩm
                </button>
                <button
                  type="button"
                  onclick={() => sourceType = "article"}
                  class="py-1 text-[11px] rounded transition-all font-semibold
                         {sourceType === 'article' ? 'bg-cyan-950 text-cyan-400 border border-cyan-500/20' : 'text-gray-400 hover:text-white'}"
                >
                  Bài viết
                </button>
                <button
                  type="button"
                  onclick={() => sourceType = "custom"}
                  class="py-1 text-[11px] rounded transition-all font-semibold
                         {sourceType === 'custom' ? 'bg-cyan-950 text-cyan-400 border border-cyan-500/20' : 'text-gray-400 hover:text-white'}"
                >
                  Nhập tay
                </button>
              </div>
            </div>

            <!-- Dynamic Input Area based on source type -->
            {#if sourceType === "product"}
              <div class="space-y-2">
                <label for="product-select" class="text-[10px] font-mono tracking-wider text-gray-400 uppercase">CHỌN SẢN PHẨM TIÊU ĐIỂM</label>
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
                  Hệ thống tự động phân tích ưu điểm sản phẩm để làm chất liệu viết kịch bản.
                </p>
              </div>
            {:else if sourceType === "article"}
              <div class="space-y-2">
                <label for="article-select" class="text-[10px] font-mono tracking-wider text-gray-400 uppercase">CHỌN BÀI VIẾT LÀM NGUỒN</label>
                <select
                  id="article-select"
                  bind:value={selectedArticleId}
                  class="w-full bg-[#111] border border-gray-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500"
                >
                  {#if articles.length === 0}
                    <option value="">Không tìm thấy bài viết nào</option>
                  {:else}
                    {#each articles as art}
                      <option value={art.id}>{art.title}</option>
                    {/each}
                  {/if}
                </select>
                <p class="text-[9px] font-mono text-gray-500 leading-normal">
                  Chuyển hóa nội dung bài viết tin tức/chia sẻ thành kịch bản phân cảnh video sinh động.
                </p>
              </div>
            {:else}
              <div class="space-y-2">
                <label for="custom-desc" class="text-[10px] font-mono tracking-wider text-gray-400 uppercase">MÔ TẢ CHI TIẾT Ý TƯỞNG</label>
                <textarea
                  id="custom-desc"
                  bind:value={customDescription}
                  rows="3"
                  placeholder="Nhập ý tưởng video, mô tả sản phẩm dịch vụ, hoặc điểm nổi bật bạn muốn quảng cáo..."
                  class="w-full bg-[#111] border border-gray-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500 resize-none leading-relaxed"
                ></textarea>
                <p class="text-[9px] font-mono text-gray-500 leading-normal">
                  Viết bất kỳ ý tưởng thô nào của bạn, AI sẽ xây dựng thành kịch bản chuyên nghiệp.
                </p>
              </div>
            {/if}

            <!-- Settings Grid: Aspect Ratio & Duration -->
            <div class="grid grid-cols-2 gap-4">
              <!-- Aspect Ratio -->
              <div class="space-y-2">
                <label for="aspect-ratio-select" class="text-[10px] font-mono tracking-wider text-gray-400 uppercase">KHUNG HÌNH (THIẾT BỊ)</label>
                <select
                  id="aspect-ratio-select"
                  bind:value={aspectRatio}
                  class="w-full bg-[#111] border border-gray-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500"
                >
                  <option value="9:16">Dọc (9:16) - TikTok/Reels</option>
                  <option value="16:9">Ngang (16:9) - YouTube/PC</option>
                  <option value="1:1">Vuông (1:1) - Instagram</option>
                </select>
              </div>

              <!-- Duration -->
              <div class="space-y-2">
                <label for="duration-select" class="text-[10px] font-mono tracking-wider text-gray-400 uppercase">THỜI LƯỢNG MỤC TIÊU</label>
                <select
                  id="duration-select"
                  bind:value={targetDuration}
                  class="w-full bg-[#111] border border-gray-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500"
                >
                  <option value={15}>15 giây (Cực ngắn)</option>
                  <option value={30}>30 giây (Tiêu chuẩn)</option>
                  <option value={60}>60 giây (Chi tiết)</option>
                  <option value={90}>90 giây (Kể chuyện)</option>
                </select>
              </div>
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
            </div>

            <!-- Style instruction details panel -->
            {#if styles.find(s => s.id === selectedStyleId)}
              {@const currentStyle = styles.find(s => s.id === selectedStyleId)!}
              <div class="bg-[#0c0c0c] border border-cyan-500/10 rounded-lg p-3 space-y-2">
                <span class="text-[9px] font-mono text-cyan-400 font-bold uppercase tracking-widest block font-sans">CHI TIẾT PHONG CÁCH</span>
                <div class="text-[10px] space-y-1 text-gray-400 leading-relaxed font-sans">
                  <p><strong>Cấu trúc Hook:</strong> <span class="text-gray-300 italic">{currentStyle.hook_template}</span></p>
                  <p class="line-clamp-2"><strong>Chỉ dẫn:</strong> {currentStyle.style_instruction}</p>
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

<!-- AI Prompt Generator Hub Drawer -->
{#if showPromptHub}
  <div class="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm" transition:fade={{ duration: 150 }}>
    <!-- Backdrop click to close -->
    <button class="absolute inset-0 cursor-default focus:outline-none" onclick={() => showPromptHub = false}></button>
    
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
          onclick={() => showPromptHub = false}
          class="p-1.5 hover:bg-gray-900 rounded-lg text-gray-400 hover:text-white transition-colors"
        >
          <X class="w-4 h-4" />
        </button>
      </div>

      <!-- Tabs & Copy All -->
      <div class="px-5 py-3 bg-[#0a0a0d] border-b border-gray-900 flex items-center justify-between">
        <div class="flex gap-2">
          <button 
            onclick={() => activePromptTab = 'midjourney'}
            class="px-3 py-1.5 rounded-lg text-xs font-medium border transition-all
                   {activePromptTab === 'midjourney' 
                     ? 'bg-cyan-950/40 border-cyan-500/30 text-cyan-400 shadow-sm shadow-cyan-500/10' 
                     : 'border-transparent text-gray-400 hover:text-white'}"
          >
            Midjourney / Flux (Ảnh)
          </button>
          <button 
            onclick={() => activePromptTab = 'runway'}
            class="px-3 py-1.5 rounded-lg text-xs font-medium border transition-all
                   {activePromptTab === 'runway' 
                     ? 'bg-purple-950/40 border-purple-500/30 text-purple-400 shadow-sm shadow-purple-500/10' 
                     : 'border-transparent text-gray-400 hover:text-white'}"
          >
            Runway Gen-3 (Video)
          </button>
          <button 
            onclick={() => activePromptTab = 'heygen'}
            class="px-3 py-1.5 rounded-lg text-xs font-medium border transition-all
                   {activePromptTab === 'heygen' 
                     ? 'bg-pink-950/40 border-pink-500/30 text-pink-400 shadow-sm shadow-pink-500/10' 
                     : 'border-transparent text-gray-400 hover:text-white'}"
          >
            HeyGen (Lời thoại)
          </button>
          <button 
            onclick={() => activePromptTab = 'gemini'}
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

          {#each activeScript.structured_script.scenes as scene, idx}
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
                    nanobot.showToast(`Đã sao chép prompt phân cảnh ${scene.scene_number}!`, "success");
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
