<script lang="ts">
  import { fade } from "svelte/transition";
  import { untrack, onDestroy, onMount } from "svelte";
  import Image from "@lucide/svelte/icons/image";
  import X from "@lucide/svelte/icons/x";

  import type {
    BaseWidgetProps,
    VideoScript,
    VideoScriptStyle,
    VideoScene,
    Article,
    MediaAsset,
    VideoScriptEvaluation,
  } from "$lib/types";
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
  let selectedScript = $derived(
    scripts.find((s) => s.id === selectedScriptId) || null,
  );
  let activeScript = $state<VideoScript | null>(null);
  let copiedTextMap = $state<Record<number, boolean>>({});

  // Sidebar toggle state
  let isSidebarOpen = $state(true);

  onMount(() => {
    const saved = localStorage.getItem("script_management_sidebar_open");
    if (saved !== null) {
      isSidebarOpen = saved === "true";
    }
  });

  function toggleSidebar() {
    isSidebarOpen = !isSidebarOpen;
    localStorage.setItem(
      "script_management_sidebar_open",
      isSidebarOpen.toString(),
    );
  }

  // Auto-save State
  let saveStatus = $state<"Saved" | "Saving..." | "Error saving">("Saved");
  let saveTimeout: ReturnType<typeof setTimeout>;

  // Drawer / Form State
  let isDrawerOpen = $state(false);
  let selectedProductId = $state("");
  let selectedStyleId = $state("");
  let selectedArticleId = $state("");
  let customDescription = $state("");
  let extraRequirements = $state("");
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
  let activePromptTab = $state<
    "midjourney" | "runway" | "heygen" | "gemini" | "animation"
  >("midjourney");
  let activeWorkspaceTab = $state<"intel" | "match" | "eval" | null>("intel");

  // Evaluation States
  let isEvaluating = $state(false);
  let isOptimizing = $state(false);

  // Fingerprint of script contents to detect changes since last evaluation
  let lastEvaluatedFingerprint = $state<string>("");

  function getScriptContentFingerprint(script: VideoScript | null): string {
    if (!script || !script.structured_script) return "";
    const data = {
      title: script.title,
      style_name: script.style_name,
      target_audience: script.structured_script.target_audience,
      target_duration: script.structured_script.target_duration,
      scenes: (script.structured_script.scenes || []).map((s: VideoScene) => ({
        scene_number: s.scene_number,
        duration: s.duration,
        visual_description: s.visual_description,
        voiceover: s.voiceover,
        scene_notes: s.scene_notes,
      })),
      notes: script.structured_script.notes,
    };
    return JSON.stringify(data);
  }

  let isScriptModified = $derived(
    activeScript
      ? getScriptContentFingerprint(activeScript) !== lastEvaluatedFingerprint
      : false,
  );

  // forceEvaluate=true: bypass guard khi user chủ động nhấn "Đánh giá lại"
  async function handleEvaluate(forceEvaluate = false) {
    const script = activeScript;
    if (!script) return;

    // Safety check: Chỉ chặn khi KHÔNG phải force và đã có kết quả mới nhất
    if (!forceEvaluate) {
      const currentFingerprint = getScriptContentFingerprint(script);
      if (
        script.structured_script?.evaluation &&
        currentFingerprint === lastEvaluatedFingerprint
      ) {
        nanobot.showToast(
          "Kịch bản chưa có thay đổi nào so với lần đánh giá trước. Nhấn 'Đánh giá lại' để bắt buộc chạy lại!",
          "info",
        );
        return;
      }
    }

    isEvaluating = true;
    try {
      const res = await apiClient.post<{ data: VideoScriptEvaluation }>(
        `/api/v1/video/script/${script.id}/evaluate`,
      );
      if (res.data) {
        if (!script.structured_script) {
          script.structured_script = {} as VideoScript["structured_script"];
        }
        script.structured_script.evaluation = res.data;
        const idx = scripts.findIndex((s) => s.id === script.id);
        if (idx !== -1) {
          scripts[idx] = JSON.parse(JSON.stringify(script));
        }
        if (activeScript && activeScript.id === script.id) {
          activeScript = JSON.parse(JSON.stringify(script));
          // Cập nhật fingerprint sau đánh giá
          lastEvaluatedFingerprint = getScriptContentFingerprint(activeScript);
        }
        nanobot.addLog(
          "[SYS] Đánh giá kịch bản AI thành công!",
          "Nanobot-System",
        );
        nanobot.showToast("Đánh giá kịch bản thành công!", "success");
      }
    } catch (error) {
      const msg = error instanceof Error ? error.message : String(error);
      nanobot.addLog(
        `[SYS] Lỗi khi đánh giá kịch bản: ${msg}`,
        "Nanobot-System",
      );
      nanobot.showToast(`Lỗi khi đánh giá: ${msg}`, "error");
    } finally {
      isEvaluating = false;
    }
  }

  async function handleOptimize(focusCriterion?: string | unknown) {
    const script = activeScript;
    if (!script) return;
    isOptimizing = true;
    try {
      let url = `/api/v1/video/script/${script.id}/optimize`;
      // Chỉ gán focus_criterion nếu nó là chuỗi thực sự (không phải PointerEvent từ Svelte event handler)
      let focus: string | null = null;
      if (typeof focusCriterion === "string" && focusCriterion.trim() !== "") {
        focus = focusCriterion;
        url += `?focus_criterion=${encodeURIComponent(focus)}`;
      }
      const res = await apiClient.post<{ data: VideoScript }>(url);
      if (res.data) {
        activeScript = res.data;
        const idx = scripts.findIndex((s) => s.id === script.id);
        if (idx !== -1) {
          scripts[idx] = res.data;
        }
        // Cập nhật fingerprint sau optimize (backend đã tự đánh giá lại)
        lastEvaluatedFingerprint = getScriptContentFingerprint(activeScript);
        nanobot.addLog(
          "[SYS] Tối ưu hóa kịch bản AI thành công!",
          "Nanobot-System",
        );
        if (focus) {
          nanobot.showToast(
            `Đã tối ưu tập trung riêng tiêu chí "${focus}" thành công!`,
            "success",
          );
        } else {
          nanobot.showToast(
            "Tự động sửa lỗi & đánh giá lại thành công! Xem kết quả tab Đánh giá.",
            "success",
          );
        }
        // Tự động switch sang tab eval để user thấy điểm mới
        activeWorkspaceTab = "eval";
      }
    } catch (error) {
      const msg = error instanceof Error ? error.message : String(error);
      nanobot.addLog(
        `[SYS] Lỗi khi tối ưu hóa kịch bản: ${msg}`,
        "Nanobot-System",
      );
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
    return `Cinematic, hyper-realistic video. ${desc}. Camera motion: ${notes}. Smooth transition, high dynamic range, photorealistic commercial styling, 8k, image-to-video mode using the uploaded reference image, strictly maintain visual consistency for the product packaging and character model without any variations.`;
  }

  function getGeminiPrompt(scene: VideoScene) {
    const desc = scene.visual_description || "";
    const notes = scene.scene_notes || "";
    const voice = scene.voiceover || "";
    const prodName =
      activeScript?.product_name || activeScript?.title || "sản phẩm";
    const num = scene.scene_number || 1;
    return `[LỆNH TẠO VIDEO PHÂN CẢNH #${num} - NHẤT QUÁN THƯƠNG HIỆU & LIỀN MẠCH]
(Lưu ý: Sếp hãy đính kèm ảnh sản phẩm thực tế hoặc ảnh nhân vật mẫu của phân cảnh này vào cùng lượt gửi để làm tham chiếu)

Đây là Phân cảnh #${num} trong chuỗi video marketing của sản phẩm "${prodName}".
Yêu cầu sinh video chuyển động trực tiếp từ ảnh đính kèm theo mô tả:
- Phân cảnh số: #${num}
- Thương hiệu / Sản phẩm: ${prodName}
- Website chính thức: osmo.vn (Thương hiệu Miccosmo Việt Nam)
- Mô tả hình ảnh (Visual Description): ${desc}
- Lời thoại (Voiceover): ${voice}
- Chuyển động camera & Ghi chú: ${notes}
- Phong cách: Điện ảnh thương mại, độ phân giải 8K, ánh sáng chuyên nghiệp.

QUY TẮC LIỀN MẠCH & BẢO TOÀN THƯƠNG HIỆU BẮT BUỘC:
1. BẢO TOÀN THƯƠNG HIỆU: Giữ logo, nhãn mác và thiết kế bao bì của sản phẩm trong ảnh đính kèm hoàn toàn tĩnh và sắc nét. Tuyệt đối không làm méo mó chữ viết hay tự ý thay đổi màu sắc chai/lọ.
2. TÍNH LIỀN MẠCH (CONTINUITY): Đối chiếu với tông màu ánh sáng (color grading), bối cảnh xung quanh và gương mặt/mái tóc/trang phục của nhân vật nữ ở các phân cảnh trước trong lịch sử chat để đảm bảo tính liên tục tuyệt đối, tránh bị lệch mặt hay lệch màu khi ghép thành phim hoàn chỉnh.
3. KHÔNG TỰ VẼ ĐỒ HỌA: Tuyệt đối KHÔNG tự vẽ thêm các nút bấm CTA (như Mua ngay, Giảm cân), mã QR, hay chữ khuyến mãi đè lên video. Các yếu tố này sẽ được xử lý ở khâu hậu kỳ.

YÊU CẦU: Thực thi ngay lệnh sinh video chuyển động cho Phân cảnh #${num} dựa trên ảnh đính kèm và lịch sử huấn luyện của dự án.`;
  }

  function getGeminiMasterPrompt() {
    if (!activeScript || !activeScript.structured_script?.scenes) return "";

    const analysis = activeScript.structured_script.competitor_analysis;
    const strengths = analysis?.our_strengths
      ? analysis.our_strengths.join(", ")
      : "";
    const coreMsg = analysis?.core_message ? analysis.core_message : "";
    const prodName =
      activeScript.product_name || activeScript.title || "sản phẩm";

    let text = `[LỆNH ĐIỀU HÀNH ĐẠO DIỄN - THIẾT LẬP DỰ ÁN TOÀN BỘ KỊCH BẢN]\n`;
    text += `Bạn là Đạo diễn Video AI kiêm Trợ lý sinh video của Google. Dưới đây là thông tin nền tảng thương hiệu và sản phẩm của dự án:\n`;
    text += `- Thương hiệu / Sản phẩm: ${prodName}\n`;
    text += `- Tên kịch bản: ${activeScript.title || "marketing"}\n`;
    text += `- Website chính thức: osmo.vn (Thương hiệu Miccosmo Việt Nam)\n`;
    text += `- Khách hàng mục tiêu: ${activeScript.structured_script.target_audience || "Khách hàng có nhu cầu chăm sóc da/sức khoẻ"}\n`;
    if (strengths) text += `- Ưu thế vượt trội của ta (USP): ${strengths}\n`;
    if (coreMsg) text += `- Thông điệp cốt lõi: ${coreMsg}\n`;
    text += `\n`;
    text += `DƯỚI ĐÂY LÀ CHI TIẾT TỪNG PHÂN CẢNH KỊCH BẢN:\n\n`;

    activeScript.structured_script.scenes.forEach(
      (scene: VideoScene, idx: number) => {
        const num = scene.scene_number || idx + 1;
        text += `Phân cảnh #${num} (Video Độc Lập):\n`;
        text += `- Mô tả hình ảnh: ${scene.visual_description || ""}\n`;
        text += `- Lời thoại: ${scene.voiceover || ""}\n`;
        text += `- Ghi chú & Chuyển động: ${scene.scene_notes || ""}\n\n`;
      },
    );

    text += `HƯỚNG DẪN ĐẠO DIỄN QUAN TRỌNG ĐỂ TRÁNH LỖI NHIỄM CHÉO (CROSS-CONTAMINATION) & CHỈ CHỈNH BỐI CẢNH:\n`;
    text += `* Mỗi phân cảnh là một video 4s - 6s HOÀN TOÀN ĐỘC LẬP. Tuyệt đối KHÔNG lấy các chi tiết đồ họa, chữ viết, mã QR, hoặc nút CTA của phân cảnh sau vẽ đè lên phân cảnh trước.\n`;
    text += `* TUYỆT ĐỐI KHÔNG vẽ trực tiếp mã QR, nút bấm mua hàng, hay chữ quảng cáo lên video. Các phần này chỉ là ghi chú sản xuất để chèn ở khâu hậu kỳ.\n`;
    text += `* Sử dụng chính xác thiết kế bao bì của sản phẩm và logo thương hiệu từ ảnh đính kèm làm mẫu tham chiếu trực quan. Giữ logo và nhãn sản phẩm tĩnh, không biến đổi nhãn mác.\n`;
    text += `* Duy trì tính nhất quán về gương mặt nhân vật nữ, chất kem dưỡng và mẫu vỏ hộp qua các phân cảnh.\n\n`;
    text += `⚠️ YÊU CẦU THỰC THI QUAN TRỌNG (HÃY ĐỌC KỸ):\n`;
    text += `1. Đây là BƯỚC THIẾT LẬP DỰ ÁN. Bạn chỉ được phép ghi nhớ toàn bộ thông tin nền tảng thương hiệu và kịch bản này để định hình bối cảnh cho dự án.\n`;
    text += `2. TUYỆT ĐỐI KHÔNG TỰ Ý SINH VIDEO HOẶC CHẠY BẤT KỲ PHÂN CẢNH NÀO NGAY BÂY GIỜ.\n`;
    text += `3. Hãy trả lời ngắn gọn: "Tôi đã ghi nhớ toàn bộ dự án [Tên sản phẩm]. Hãy gửi ảnh kèm lệnh của từng Phân cảnh cụ thể, tôi sẽ thực hiện sinh video tương ứng." và dừng lại để đợi lệnh tiếp theo của tôi.`;
    return text;
  }

  function copyAllPrompts(type: "midjourney" | "runway" | "heygen" | "gemini") {
    if (!activeScript || !activeScript.structured_script?.scenes) return;
    const aspect = activeScript.structured_script.aspect_ratio || "16:9";
    let text = "";

    if (type === "gemini") {
      text = getGeminiMasterPrompt();
    } else {
      activeScript.structured_script.scenes.forEach(
        (scene: VideoScene, idx: number) => {
          const num = scene.scene_number || idx + 1;
          if (type === "midjourney") {
            text += `Scene #${num} Midjourney Prompt:\n${getMidjourneyPrompt(scene, aspect)}\n\n`;
          } else if (type === "runway") {
            text += `Scene #${num} Runway Prompt:\n${getRunwayPrompt(scene)}\n\n`;
          } else if (type === "heygen") {
            text += `Scene #${num} Voiceover:\n${scene.voiceover || ""}\n\n`;
          }
        },
      );
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
        if (activeScript && activeScript.structured_script?.evaluation) {
          lastEvaluatedFingerprint = getScriptContentFingerprint(activeScript);
        } else {
          lastEvaluatedFingerprint = "";
        }
      });
    } else {
      activeScript = null;
      lastEvaluatedFingerprint = "";
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
        const total = script.structured_script.scenes.reduce(
          (sum, s) => sum + (Number(s.duration) || 0),
          0,
        );
        script.structured_script.total_duration = Math.round(total * 10) / 10;

        const res = await apiClient.patch<{ data: VideoScript }>(
          `/api/v1/video/script/${script.id}`,
          {
            title: script.title,
            structured_script: script.structured_script,
          },
        );
        const idx = scripts.findIndex((s) => s.id === script.id);
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
        nanobot.addLog(
          `[SYS] Script auto-save failed: ${msg}`,
          "Nanobot-System",
        );
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
        `/api/v1/video/scripts?${params.toString()}`,
      );
      scripts = res.data;
      totalScripts = res.total;

      if (scripts.length > 0 && !selectedScriptId) {
        selectedScriptId = scripts[0].id;
      }
    } catch (error: unknown) {
      const msg = error instanceof Error ? error.message : String(error);
      nanobot.addLog(
        `[SYS] Video scripts load failed: ${msg}`,
        "Nanobot-System",
      );
      scripts = [];
      totalScripts = 0;
    } finally {
      isLoading = false;
    }
  }

  // Load Styles
  async function loadMetadata() {
    try {
      const styleRes = await apiClient.get<{ data: VideoScriptStyle[] }>(
        "/api/v1/video/styles",
      );
      styles = styleRes.data || [];

      if (styles.length > 0) selectedStyleId = styles[0].id;
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
        await apiClient.delete(
          `/api/v1/video/script/${encodeURIComponent(id)}`,
        );
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
      const res = await apiClient.post<{
        data: {
          competitor_weaknesses: string[];
          our_strengths: string[];
          core_message: string;
        };
      }>("/api/v1/video/script/analyze-competitors", {
        source_type: sourceType,
        product_id: sourceType === "product" ? selectedProductId : null,
        article_id: sourceType === "article" ? selectedArticleId : null,
        description: sourceType === "custom" ? customDescription : null,
        style_id: selectedStyleId,
        aspect_ratio: aspectRatio,
        target_duration: targetDuration,
        extra_requirements: extraRequirements.trim() || null,
      });
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
          competitor_analysis: competitorAnalysis,
          extra_requirements: extraRequirements.trim() || null,
        },
      );

      genStep = 3;
      await new Promise((r) => setTimeout(r, 600));

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
    const token =
      typeof window !== "undefined"
        ? localStorage.getItem("admin_token") ||
          sessionStorage.getItem("admin_token") ||
          ""
        : "";
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
  function moveScene(idx: number, direction: "up" | "down") {
    if (!activeScript) return;
    const scenes = activeScript.structured_script.scenes;
    const targetIdx = direction === "up" ? idx - 1 : idx + 1;
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
      visual_description:
        "Máy quay lia cận cảnh sản phẩm đặt trên bệ đỡ xoay tròn, ánh sáng dịu nhẹ tập trung vào bao bì thương hiệu.",
      voiceover: "Chất lượng vượt trội đi kèm thiết kế tinh tế từng đường nét.",
      scene_notes: "Chú ý quay slow-motion 60fps để tạo cảm giác cao cấp.",
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
      nanobot.showToast(
        "Kịch bản video phải duy trì ít nhất 1 phân cảnh!",
        "warning",
      );
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

<div
  class="w-full h-full flex flex-col md:flex-row bg-[#020202] text-gray-200 overflow-hidden font-sans"
>
  {#if isSidebarOpen}
    <div
      transition:fade={{ duration: 150 }}
      class="w-full md:w-[360px] shrink-0 border-r border-[#121212] flex flex-col h-full"
    >
      <ScriptList
        {scripts}
        {isLoading}
        bind:selectedScriptId
        bind:searchInput
        bind:currentPage
        {pageSize}
        {totalScripts}
        {totalPages}
        onSearchInput={handleSearchInput}
        onRefresh={loadScripts}
        onOpenDrawer={() => {
          isDrawerOpen = true;
          generatorStep = 1;
          competitorAnalysis = null;
        }}
      />
    </div>
  {/if}

  <ScriptEditorWorkspace
    {activeScript}
    {saveStatus}
    {copiedTextMap}
    bind:showPromptHub
    bind:activePromptTab
    {triggerAutoSave}
    {downloadMarkdown}
    {handleDelete}
    {moveScene}
    {insertScene}
    {deleteScene}
    {copyPrompt}
    {getMidjourneyPrompt}
    {getRunwayPrompt}
    {getGeminiPrompt}
    {getGeminiMasterPrompt}
    {copyAllPrompts}
    {isEvaluating}
    {isOptimizing}
    onEvaluate={handleEvaluate}
    onForceEvaluate={() => handleEvaluate(true)}
    onOptimize={handleOptimize}
    {isScriptModified}
    bind:activeWorkspaceTab
    {isSidebarOpen}
    {toggleSidebar}
  />
</div>

<VideoScriptGenerator
  bind:isDrawerOpen
  {isGenerating}
  {genStep}
  bind:sourceType
  bind:selectedProductId
  bind:selectedArticleId
  bind:customDescription
  bind:extraRequirements
  bind:aspectRatio
  bind:targetDuration
  {styles}
  bind:selectedStyleId
  {handleGenerate}
  bind:generatorStep
  {isAnalyzing}
  bind:competitorAnalysis
  {handleAnalyze}
/>
