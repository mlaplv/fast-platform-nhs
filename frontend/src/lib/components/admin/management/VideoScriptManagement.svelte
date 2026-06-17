<script lang="ts">
  import { fade } from "svelte/transition";
  import { untrack, onDestroy } from "svelte";
  import Image from "@lucide/svelte/icons/image";
  import X from "@lucide/svelte/icons/x";

  import type { BaseWidgetProps, VideoScript, VideoScriptStyle, VideoScene, Article, MediaAsset } from "$lib/types";
  import { useNanobot } from "$lib/state/nanobot.svelte";
  const nanobot = useNanobot();
  import { apiClient } from "$lib/utils/apiClient";
  // Subcomponents
  import ScriptList from "./ScriptList.svelte";
  import ScriptEditorWorkspace from "./ScriptEditorWorkspace.svelte";
  import VideoScriptGenerator from "./VideoScriptGenerator.svelte";

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

  // Step-wise generation states
  let generatorStep = $state<1 | 2>(1);
  let isAnalyzing = $state(false);
  let competitorAnalysis = $state<{
    competitor_weaknesses: string[];
    our_strengths: string[];
    core_message: string;
  } | null>(null);


  // AI Prompt Hub states
  let showPromptHub = $state(false);
  let activePromptTab = $state<"midjourney" | "runway" | "heygen" | "gemini">("midjourney");

  // Evaluation States
  let isEvaluating = $state(false);
  let isOptimizing = $state(false);

  async function handleEvaluate() {
    const script = activeScript;
    if (!script) return;
    isEvaluating = true;
    try {
      const res = await apiClient.post<{ data: any }>(
        `/api/v1/video/script/${script.id}/evaluate`
      );
      if (res.data) {
        if (!script.structured_script) {
          script.structured_script = {} as any;
        }
        script.structured_script.evaluation = res.data;
        const idx = scripts.findIndex(s => s.id === script.id);
        if (idx !== -1) {
          scripts[idx] = JSON.parse(JSON.stringify(script));
        }
        if (activeScript && activeScript.id === script.id) {
          activeScript = JSON.parse(JSON.stringify(script));
        }
        nanobot.addLog("[SYS] Đánh giá kịch bản AI thành công!", "Nanobot-System");
        nanobot.showToast("Đánh giá kịch bản thành công!", "success");
      }
    } catch (error) {
      const msg = error instanceof Error ? error.message : String(error);
      nanobot.addLog(`[SYS] Lỗi khi đánh giá kịch bản: ${msg}`, "Nanobot-System");
      nanobot.showToast(`Lỗi khi đánh giá: ${msg}`, "error");
    } finally {
      isEvaluating = false;
    }
  }

  async function handleOptimize() {
    const script = activeScript;
    if (!script) return;
    isOptimizing = true;
    try {
      const res = await apiClient.post<{ data: VideoScript }>(
        `/api/v1/video/script/${script.id}/optimize`
      );
      if (res.data) {
        activeScript = res.data;
        const idx = scripts.findIndex(s => s.id === script.id);
        if (idx !== -1) {
          scripts[idx] = res.data;
        }
        nanobot.addLog("[SYS] Tối ưu hóa kịch bản AI thành công!", "Nanobot-System");
        nanobot.showToast("Tự động sửa lỗi kịch bản thành công!", "success");
      }
    } catch (error) {
      const msg = error instanceof Error ? error.message : String(error);
      nanobot.addLog(`[SYS] Lỗi khi tối ưu hóa kịch bản: ${msg}`, "Nanobot-System");
      nanobot.showToast(`Lỗi khi tối ưu hóa: ${msg}`, "error");
    } finally {
      isOptimizing = false;
    }
  }

  function getMidjourneyPrompt(scene: VideoScene, aspect: string) {
    const desc = scene.visual_description || "";
    const notes = scene.scene_notes || "";
    const ar = aspect === "9:16" ? "9:16" : "16:9";
    return `A high-fidelity commercial cinematography storyboard slot. ${desc}. ${notes}. Clean look, photorealistic, 8k resolution, cinematic lighting, commercial grade, strictly reference the attached product image and brand logo for visual consistency, do not alter or fabricate packaging or brand design --ar ${ar} --style raw --v 6.0`;
  }

  function getRunwayPrompt(scene: VideoScene) {
    const desc = scene.visual_description || "";
    const notes = scene.scene_notes || "";
    return `Cinematic, hyper-realistic video. ${desc}. Camera motion: ${notes}. Smooth transition, high dynamic range, photorealistic commercial styling, 8k, strictly adhere to the attached product design and brand logo, no variations.`;
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

LƯU Ý THƯƠNG HIỆU QUAN TRỌNG:
* Bắt buộc phải tham chiếu và sử dụng chính xác thiết kế bao bì của sản phẩm và logo thương hiệu được đính kèm ở đầu tin nhắn này làm mẫu tham chiếu trực quan.
* Tuyệt đối không tự ý thay đổi màu sắc, nhãn mác, kiểu dáng chai lọ/tuýp sản phẩm hoặc thiết kế logo thương hiệu để tránh sai lệch nhận diện.

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
    text += `LƯU Ý THƯƠNG HIỆU QUAN TRỌNG:\n`;
    text += `* Bắt buộc phải tham chiếu và sử dụng chính xác thiết kế bao bì của sản phẩm và logo thương hiệu được đính kèm ở đầu tin nhắn này làm mẫu tham chiếu trực quan.\n`;
    text += `* Tuyệt đối không tự ý thay đổi màu sắc, nhãn mác, kiểu dáng chai lọ/tuýp sản phẩm hoặc thiết kế logo thương hiệu để tránh sai lệch nhận diện.\n\n`;
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
      });
    } else {
      activeScript = null;
    }
  });

  // Debounced auto-save trigger
  function triggerAutoSave() {
    const script = activeScript;
    if (!script) return;
    saveStatus = "Saving...";
    clearTimeout(saveTimeout);
    saveTimeout = setTimeout(async () => {
      try {
        const total = script.structured_script.scenes.reduce((sum, s) => sum + (Number(s.duration) || 0), 0);
        script.structured_script.total_duration = Math.round(total * 10) / 10;

        const res = await apiClient.patch<{ data: VideoScript }>(
          `/api/v1/video/script/${script.id}`,
          {
            title: script.title,
            structured_script: script.structured_script
          }
        );
        const idx = scripts.findIndex(s => s.id === script.id);
        if (idx !== -1) {
          scripts[idx] = res.data;
        }
        if (activeScript && activeScript.id === script.id) {
          activeScript = res.data;
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

  // Step 1: Analyze competitors and strengths
  async function handleAnalyze() {
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

    isAnalyzing = true;
    try {
      const res = await apiClient.post<{ data: { competitor_weaknesses: string[], our_strengths: string[], core_message: string } }>(
        "/api/v1/video/script/analyze-competitors",
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
      competitorAnalysis = res.data;
      generatorStep = 2;
      nanobot.showToast("Phân tích đối thủ & USP hoàn tất!", "success");
    } catch (error: unknown) {
      const msg = error instanceof Error ? error.message : String(error);
      nanobot.showToast(`Lỗi phân tích đối thủ: ${msg}`, "error");
    } finally {
      isAnalyzing = false;
    }
  }

  // Step 2: Generate Script
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
    genStep = 2; // Bỏ qua step 1 (đã phân tích)

    try {
      const res = await apiClient.post<{ message: string; data: VideoScript }>(
        "/api/v1/video/script/generate",
        {
          source_type: sourceType,
          product_id: sourceType === "product" ? selectedProductId : null,
          article_id: sourceType === "article" ? selectedArticleId : null,
          description: sourceType === "custom" ? customDescription : null,
          style_id: selectedStyleId,
          aspect_ratio: aspectRatio,
          target_duration: targetDuration,
          competitor_analysis: competitorAnalysis
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
    onOpenDrawer={() => {
      isDrawerOpen = true;
      generatorStep = 1;
      competitorAnalysis = null;
    }}
  />

  <ScriptEditorWorkspace
    activeScript={activeScript}
    saveStatus={saveStatus}
    copiedTextMap={copiedTextMap}
    bind:showPromptHub={showPromptHub}
    bind:activePromptTab={activePromptTab}
    triggerAutoSave={triggerAutoSave}
    downloadMarkdown={downloadMarkdown}
    handleDelete={handleDelete}
    moveScene={moveScene}
    insertScene={insertScene}
    deleteScene={deleteScene}
    copyPrompt={copyPrompt}
    getMidjourneyPrompt={getMidjourneyPrompt}
    getRunwayPrompt={getRunwayPrompt}
    getGeminiPrompt={getGeminiPrompt}
    getGeminiMasterPrompt={getGeminiMasterPrompt}
    copyAllPrompts={copyAllPrompts}
    isEvaluating={isEvaluating}
    isOptimizing={isOptimizing}
    onEvaluate={handleEvaluate}
    onOptimize={handleOptimize}
  />

</div>

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
  bind:generatorStep={generatorStep}
  isAnalyzing={isAnalyzing}
  bind:competitorAnalysis={competitorAnalysis}
  handleAnalyze={handleAnalyze}
/>
