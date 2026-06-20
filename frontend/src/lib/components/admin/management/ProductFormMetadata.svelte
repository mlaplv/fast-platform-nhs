<script lang="ts">
  import { onMount } from "svelte";
  import Layout from "@lucide/svelte/icons/layout";
  import Zap from "@lucide/svelte/icons/zap";
  import MessageSquare from "@lucide/svelte/icons/message-square";
  import Microscope from "@lucide/svelte/icons/microscope";
  import HelpCircle from "@lucide/svelte/icons/help-circle";
  import Plus from "@lucide/svelte/icons/plus";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import Tag from "@lucide/svelte/icons/tag";
  import RefreshCw from "@lucide/svelte/icons/refresh-cw";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import Beaker from "@lucide/svelte/icons/beaker";
  import Star from "@lucide/svelte/icons/star";
  import Share2 from "@lucide/svelte/icons/share-2";
  import Heart from "@lucide/svelte/icons/heart";
  import Clock from "@lucide/svelte/icons/clock";
  import Ticket from "@lucide/svelte/icons/ticket";
  import Shield from "@lucide/svelte/icons/shield";
  import type { ProductFormState, ProductMetadata } from "$lib/types";
  import { useNanobot } from "$lib/state/nanobot.svelte";
  import { apiClient } from "$lib/utils/apiClient";
  import { getIngredientIcon } from "$lib/utils/product";
  import SemanticEditor from "$lib/components/admin/ui/SemanticEditor.svelte";

  const nanobot = useNanobot();

  let { formState = $bindable(), onOpenVault } = $props<{
    formState: ProductFormState;
    onOpenVault?: (field: string) => void;
  }>();

  let isScanning = $state(false);

  async function scanComplianceImage() {
    if (!formState.metadata.notification_doc) {
      nanobot.showToast(
        "Vui lòng chọn hoặc nhập URL ảnh phiếu công bố trước khi quét.",
        "error",
      );
      return;
    }

    isScanning = true;
    try {
      nanobot.showToast("AI đang phân tích ảnh phiếu công bố...", "info");
      const response = await apiClient.post("/admin/compliance/scan-image", {
        image_url: formState.metadata.notification_doc,
      });

      if (response.success && response.data) {
        formState.metadata.notification_no =
          response.data.notification_no || formState.metadata.notification_no;
        formState.metadata.notification_date =
          response.data.notification_date ||
          formState.metadata.notification_date;
        formState.metadata.authority =
          response.data.authority || formState.metadata.authority;
        nanobot.showToast("Đã tự động điền thông tin từ ảnh!", "success");
      } else {
        nanobot.showToast(
          "Không thể trích xuất dữ liệu. Vui lòng kiểm tra lại chất lượng ảnh.",
          "error",
        );
      }
    } catch (err) {
      console.error("AI Scan Error:", err);
      nanobot.showToast("Lỗi hệ thống khi quét ảnh.", "error");
    } finally {
      isScanning = false;
    }
  }

  onMount(() => {
    if (!formState.metadata) {
      formState.metadata = { landing_type: "standard" };
    }
    if (!formState.metadata.landing_type) {
      formState.metadata.landing_type = "standard";
    }
  });

  /** Viral Intelligence: Auto-suggest icons for ingredients */
  const viralIcons = [
    { icon: "💧", label: "Cấp ẩm / HA" },
    { icon: "🍋", label: "Vitamin C / Làm sáng" },
    { icon: "🛡️", label: "Niacinamide / Bảo vệ" },
    { icon: "🌙", label: "Retinol / Tái tạo" },
    { icon: "🌿", label: "Trà xanh / Thảo mộc" },
    { icon: "🧬", label: "Collagen / Ceramide" },
    { icon: "✨", label: "Sáng da / Glow" },
    { icon: "☀️", label: "Chống nắng / SPF" },
    { icon: "🧪", label: "Acid / AHA / BHA" },
    { icon: "🌱", label: "Rau má / Cica" },
    { icon: "🍎", label: "Lựu / Chống oxy hóa" },
    { icon: "🌹", label: "Hoa hồng / Dịu nhẹ" },
    { icon: "🍯", label: "Mật ong / Sát khuẩn" },
    { icon: "🫗", label: "Dầu dưỡng / Olive" },
    { icon: "🌑", label: "Than hoạt tính / Đất sét" },
    { icon: "🪵", label: "Cam thảo / Rễ cây" },
    { icon: "🧴", label: "Lotion / Dưỡng thể" },
    { icon: "🩹", label: "Phục hồi / Cấp cứu" },
    { icon: "🧼", label: "Làm sạch / Cleanser" },
    { icon: "💊", label: "Dược mỹ phẩm / Đặc trị" },
  ];
  let activeIconPicker = $state<number | null>(null);

  $effect(() => {
    if (formState.metadata.featured_ingredients) {
      formState.metadata.featured_ingredients.forEach((item) => {
        if (item.name && (!item.icon || item.icon === "🧬")) {
          const smartIcon = getIngredientIcon(item.name);
          if (smartIcon !== "🧬") {
            item.icon = smartIcon;
          }
        }
      });
    }
  });

  const landingTypes = [
    {
      value: "standard",
      label: "Tiêu chuẩn (E-commerce)",
      desc: "Giao diện truyền thống",
    },
    {
      value: "stealth",
      label: "Phễu chuyển đổi (Stealth)",
      desc: "Tối ưu chuyển đổi nhanh (CPA)",
    },
    {
      value: "tiktok",
      label: "Phong cách TikTok",
      desc: "Trải nghiệm video như TikTok",
    },
  ];

  // ─── Auto-detect video duration ─────────────────────────────────
  let isDetectingDuration = $state(false);
  let detectError = $state<string | null>(null);

  function isVideoFile(url: string): boolean {
    if (!url) return false;
    const clean = url.split("?")[0].toLowerCase();
    return /\.(mp4|webm|mov|ogg|ogv|avi|mkv)$/.test(clean);
  }

  function detectVideoDuration(url: string): Promise<number | null> {
    return new Promise((resolve) => {
      if (!url || !isVideoFile(url)) {
        resolve(null);
        return;
      }
      const v = document.createElement("video");
      v.preload = "metadata";
      v.src = url;
      v.onloadedmetadata = () => {
        const dur = isFinite(v.duration)
          ? Math.round(v.duration * 10) / 10
          : null;
        v.src = "";
        resolve(dur);
      };
      v.onerror = () => {
        v.src = "";
        resolve(null);
      };
      setTimeout(() => {
        v.src = "";
        resolve(null);
      }, 8000);
    });
  }

  async function autoDetectEndTime(url?: string) {
    const target = url ?? formState.metadata?.video_url;
    if (!target || !isVideoFile(target)) return;
    isDetectingDuration = true;
    detectError = null;
    try {
      const dur = await detectVideoDuration(target);
      if (dur !== null) {
        formState.metadata.video_end_time = dur;
        formState.metadata.video_start_time =
          formState.metadata.video_start_time ?? 0;
      } else {
        detectError = "Không đọc được thời lượng";
      }
    } finally {
      isDetectingDuration = false;
    }
  }

  // ─── FAQ Management (GEO 2026) ──────────────────────────────────
  function addFaq() {
    if (!formState.metadata.faqs) formState.metadata.faqs = [];
    formState.metadata.faqs.push({ question: "", answer: "" });
  }

  function removeFaq(index: number) {
    if (!formState.metadata.faqs) return;
    formState.metadata.faqs.splice(index, 1);
  }

  // ─── Featured Ingredients Management ────────────────────────────
  function addFeaturedIngredient() {
    if (!formState.metadata.featured_ingredients)
      formState.metadata.featured_ingredients = [];
    formState.metadata.featured_ingredients.push({
      name: "",
      benefit: "",
      icon: "",
    });
  }

  function removeFeaturedIngredient(index: number) {
    if (!formState.metadata.featured_ingredients) return;
    formState.metadata.featured_ingredients.splice(index, 1);
  }

  let isSuggestingFaqs = $state(false);

  async function handleAiSuggestFaqs() {
    if (!formState.name) {
      nanobot.showToast(
        "Vui lòng nhập tên sản phẩm trước khi gọi XOHI.",
        "warning",
      );
      return;
    }
    isSuggestingFaqs = true;
    try {
      const res = await apiClient.post<{
        data: { question: string; answer: string }[];
      }>("/api/v1/products/faq-suggest", {
        name: formState.name,
        description: formState.description || "",
      });
      if (res && res.data && Array.isArray(res.data) && res.data.length > 0) {
        if (!formState.metadata.faqs) formState.metadata.faqs = [];
        formState.metadata.faqs.push(...res.data);
        nanobot.showToast(
          "XOHI đã tự động tạo thành công bộ câu hỏi FAQ.",
          "success",
        );
      } else {
        nanobot.showToast(
          "XOHI không thể tạo thêm câu hỏi. Vui lòng thử lại.",
          "error",
        );
      }
    } catch (e) {
      console.error("XOHI FAQ Suggestion failed:", e);
      nanobot.showToast("Lỗi kết nối tới hệ thống AI XOHI.", "error");
    } finally {
      isSuggestingFaqs = false;
    }
  }

  let isSuggestingIngredients = $state(false);

  async function handleAiSuggestIngredients() {
    if (!formState.metadata.ingredients || !formState.metadata.ingredients.trim()) {
      nanobot.showToast(
        "Vui lòng nhập bảng thành phần trước khi gọi XOHI.",
        "warning",
      );
      return;
    }
    isSuggestingIngredients = true;
    try {
      const res = await apiClient.post<{
        data: { name: string; benefit: string; icon: string }[];
      }>("/api/v1/products/ingredients-suggest", {
        name: formState.name || "",
        ingredients: formState.metadata.ingredients,
      });
      if (res && res.data && Array.isArray(res.data) && res.data.length > 0) {
        formState.metadata.featured_ingredients = res.data.map((item) => ({
          name: item.name,
          benefit: item.benefit,
          icon: item.icon || getIngredientIcon(item.name)
        }));
        nanobot.showToast(
          "XOHI đã tự động tạo thành công 4 thành phần nổi bật.",
          "success",
        );
      } else {
        nanobot.showToast(
          "XOHI không thể trích xuất thành phần. Vui lòng kiểm tra lại bảng thành phần.",
          "error",
        );
      }
    } catch (e) {
      console.error("XOHI Ingredients Suggestion failed:", e);
      nanobot.showToast("Lỗi kết nối tới hệ thống AI XOHI.", "error");
    } finally {
      isSuggestingIngredients = false;
    }
  }

  let isSuggestingSemantic = $state(false);

  async function handleAiSuggestSemantic() {
    if (!formState.name) {
      nanobot.showToast(
        "Vui lòng nhập tên sản phẩm trước khi gọi XOHI.",
        "warning",
      );
      return;
    }
    isSuggestingSemantic = true;
    try {
      const res = await apiClient.post<{
        data: string;
      }>("/api/v1/products/semantic-suggest", {
        name: formState.name,
        description: formState.description || "",
        seo_description: formState.seoDescription || "",
      });
      if (res && res.data) {
        formState.metadata.desc_semantic = res.data;
        nanobot.showToast(
          "XOHI đã tối ưu hóa tóm tắt SGE Semantic thành công!",
          "success",
        );
      } else {
        nanobot.showToast(
          "XOHI không thể tạo tóm tắt. Vui lòng kiểm tra mô tả sản phẩm.",
          "error",
        );
      }
    } catch (e) {
      console.error("XOHI Semantic Suggestion failed:", e);
      nanobot.showToast("Lỗi kết nối tới hệ thống AI XOHI.", "error");
    } finally {
      isSuggestingSemantic = false;
    }
  }

  let isSuggestingIngredientsGrouped = $state(false);

  async function handleAiSuggestIngredientsGrouped() {
    if (!formState.metadata.ingredients || !formState.metadata.ingredients.trim()) {
      nanobot.showToast(
        "Vui lòng nhập bảng thành phần đầy đủ trước khi gọi XOHI phân nhóm.",
        "warning",
      );
      return;
    }
    isSuggestingIngredientsGrouped = true;
    try {
      const res = await apiClient.post<{
        data: { group: string; priority: number; items: string[] }[];
      }>("/api/v1/products/ingredients-grouped", {
        ingredients: formState.metadata.ingredients,
      });
      if (res && res.data && Array.isArray(res.data) && res.data.length > 0) {
        formState.metadata.ingredients_groups = res.data;
        
        // Cập nhật lại text thô trong bảng thành phần theo thứ tự độ ưu tiên giảm dần
        const reordered = res.data
          .map(grp => grp.items.join(", "))
          .filter(Boolean)
          .join(", ");
        if (reordered) {
          formState.metadata.ingredients = reordered;
        }

        nanobot.showToast(
          "XOHI đã phân nhóm và sắp xếp lại bảng thành phần gốc theo độ ưu tiên thành công!",
          "success",
        );
      } else {
        nanobot.showToast(
          "XOHI không thể phân nhóm thành phần. Vui lòng kiểm tra lại bảng thành phần.",
          "error",
        );
      }
    } catch (e) {
      console.error("XOHI Ingredients Grouping failed:", e);
      nanobot.showToast("Lỗi kết nối tới hệ thống AI XOHI.", "error");
    } finally {
      isSuggestingIngredientsGrouped = false;
    }
  }


  function toggleSharePromo() {
    if (!formState.metadata.share_promotion) {
      formState.metadata.share_promotion = {
        enabled: true,
        voucher_id: "",
      };
    } else {
      formState.metadata.share_promotion.enabled =
        !formState.metadata.share_promotion.enabled;
    }
  }
</script>

<div class="flex flex-col gap-6">
  <!-- LANDING TYPE SELECTOR -->
  <div class="flex flex-col gap-3">
    <div
      class="flex items-center gap-2 text-[9px] font-black text-white/25 tracking-[0.25em]"
    >
      <Layout size={11} class="text-amber-400/60" />
      Loại hình trang đích (Landing Type)
    </div>

    <div class="grid grid-cols-3 gap-2">
      {#each landingTypes as type}
        <button
          type="button"
          onclick={() =>
            (formState.metadata.landing_type =
              type.value as ProductMetadata["landing_type"])}
          class="flex flex-col gap-1 p-3 rounded-xl border transition-all text-left {formState
            .metadata.landing_type === type.value
            ? 'bg-amber-500/10 border-amber-500/50'
            : 'bg-white/5 border-white/5 hover:border-white/10'}"
        >
          <span
            class="text-[10px] font-bold {formState.metadata.landing_type ===
            type.value
              ? 'text-amber-400'
              : 'text-white/60'}">{type.label}</span
          >
          <span class="text-[8px] text-white/30 leading-tight">{type.desc}</span
          >
        </button>
      {/each}
    </div>
  </div>

  <!-- CONTEXTUAL FIELDS -->
  <div
    class="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 rounded-2xl bg-white/[0.02] border border-white/5"
  >
    <!-- Scarcity Timer (Stealth/TikTok) -->
    {#if formState.metadata.landing_type !== "standard"}
      <div class="flex flex-col gap-1.5">
        <label
          class="text-[9px] font-bold text-white/40 tracking-wider"
          >Thời gian khan hiếm (Giây)</label
        >
        <input
          type="number"
          bind:value={formState.metadata.scarcity_seconds}
          placeholder="600"
          class="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-[11px] text-white focus:outline-none focus:border-amber-500/50 transition-colors"
        />
      </div>
    {/if}

    <!-- Video URL (Desktop) -->
    <div class="flex flex-col gap-1.5">
      <label class="text-[9px] font-bold text-white/40 tracking-wider"
        >Video URL Desktop (TikTok/YouTube/Nội bộ)</label
      >
      <input
        type="text"
        bind:value={formState.metadata.video_url}
        onchange={() => {
          const url = formState.metadata.video_url;
          if (url && isVideoFile(url)) {
            autoDetectEndTime(url);
          }
        }}
        placeholder="/uploads/video/desktop.mp4"
        class="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-[11px] text-white focus:outline-none focus:border-amber-500/50 transition-colors"
      />
    </div>

    <!-- Video URL (Mobile) -->
    <div class="flex flex-col gap-1.5">
      <label class="text-[9px] font-bold text-white/40 tracking-wider"
        >Video URL Mobile (TikTok/YouTube/Nội bộ)</label
      >
      <input
        type="text"
        bind:value={formState.metadata.mobile_video_url}
        onchange={() => {
          const url = formState.metadata.mobile_video_url;
          if (url && isVideoFile(url)) {
            autoDetectEndTime(url);
          }
        }}
        placeholder="/uploads/video/mobile.mp4"
        class="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-[11px] text-white focus:outline-none focus:border-amber-500/50 transition-colors"
      />
    </div>

    <!-- VIDEO PLAYBACK CONTROLS -->
    <div
      class="md:col-span-2 flex flex-col gap-2 p-3 rounded-xl bg-amber-500/[0.04] border border-amber-500/15"
    >
      <div class="flex items-center justify-between mb-1">
        <div class="flex items-center gap-1.5">
          <Clock size={10} class="text-amber-400/70" />
          <span
            class="text-[9px] font-black text-amber-400/60 tracking-[0.25em]"
            >Cắt ghép Video</span
          >
        </div>
        {#if isDetectingDuration}
          <div class="flex items-center gap-1.5 text-amber-400/60">
            <RefreshCw size={10} class="animate-spin" />
            <span class="text-[8px] font-mono">Phân tích...</span>
          </div>
        {/if}
      </div>
      <div class="grid grid-cols-2 gap-3">
        <div class="flex flex-col gap-1">
          <label
            class="text-[8px] font-bold text-white/30 tracking-wider"
            >Bắt đầu (s)</label
          >
          <input
            type="number"
            bind:value={formState.metadata.video_start_time}
            class="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-[11px] text-amber-300 font-mono focus:outline-none focus:border-amber-500/50 transition-colors"
          />
        </div>
        <div class="flex flex-col gap-1">
          <label
            class="text-[8px] font-bold text-white/30 tracking-wider"
            >Kết thúc (s)</label
          >
          <input
            type="number"
            bind:value={formState.metadata.video_end_time}
            class="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-[11px] text-amber-300 font-mono focus:outline-none focus:border-amber-500/50 transition-colors"
          />
        </div>
      </div>
    </div>
  </div>

  <!-- R00 Compliance: UI Labels -->
  <div class="flex flex-col gap-4">
    <div
      class="flex items-center gap-2 text-[9px] font-black text-white/25 tracking-[0.25em]"
    >
      <Zap size={11} class="text-amber-400/60" />
      Cấu hình R00 (UI Strings)
    </div>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div class="flex flex-col gap-1.5">
        <label
          class="text-[9px] font-bold text-white/40 tracking-wider"
          >Text Loading Sync</label
        >
        <input
          type="text"
          bind:value={formState.metadata.sync_loading_text}
          placeholder="Đang phân tích dữ liệu AI..."
          class="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-[11px] text-white focus:outline-none focus:border-amber-500/50 transition-colors"
        />
      </div>
      <div class="flex flex-col gap-1.5">
        <label
          class="text-[9px] font-bold text-white/40 tracking-wider"
          >Tên Website (SEO)</label
        >
        <input
          type="text"
          bind:value={formState.metadata.seo_site_name}
          placeholder="SmartShop.vn"
          class="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-[11px] text-white focus:outline-none focus:border-amber-500/50 transition-colors"
        />
      </div>
    </div>
  </div>

  <!-- VIRAL & ENGAGEMENT SECTION -->
  <div class="flex flex-col gap-4">
    <div
      class="flex items-center gap-2 text-[9px] font-black text-white/25 tracking-[0.25em]"
    >
      <Share2 size={11} class="text-pink-400/60" />
      Lan truyền & Tương tác
    </div>

    <div
      class="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 rounded-2xl bg-white/[0.02] border border-white/5"
    >
      <!-- Flash Sale End Time -->
      <div class="flex flex-col gap-1.5">
        <div class="flex items-center justify-between">
          <label
            class="text-[9px] font-bold text-white/40 tracking-wider"
            >Flash Sale kết thúc</label
          >
          <label class="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              bind:checked={formState.metadata.is_flash_sale}
              class="sr-only peer"
            />
            <div
              class="w-7 h-4 bg-white/10 rounded-full peer peer-checked:bg-pink-500 transition-all relative after:content-[''] after:absolute after:top-0.5 after:left-0.5 after:bg-white after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:after:translate-x-3"
            ></div>
          </label>
        </div>
        <input
          type="datetime-local"
          bind:value={formState.metadata.flash_sale_end}
          class="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-[11px] text-white focus:outline-none focus:border-pink-500/50 transition-colors"
        />
      </div>

      <!-- Social Proof Boost -->
      <div class="flex flex-col gap-1.5">
        <label
          class="text-[9px] font-bold text-white/40 tracking-wider"
          >Social Proof Boost</label
        >
        <div class="grid grid-cols-2 gap-3">
          <div class="relative">
            <input
              type="number"
              bind:value={formState.metadata.likes}
              class="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-[11px] text-white pl-8"
            />
            <Heart
              size={12}
              class="absolute left-2.5 top-1/2 -translate-y-1/2 text-pink-500/50"
            />
          </div>
          <div class="relative">
            <input
              type="number"
              bind:value={formState.metadata.share_count}
              class="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-[11px] text-white pl-8"
            />
            <Share2
              size={12}
              class="absolute left-2.5 top-1/2 -translate-y-1/2 text-pink-500/50"
            />
          </div>
        </div>
      </div>

      <!-- SHARE TO UNLOCK PROMOTION -->
      <div
        class="md:col-span-2 mt-2 p-4 rounded-xl bg-pink-500/[0.03] border border-pink-500/15"
      >
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-2">
            <Ticket size={14} class="text-pink-400" />
            <span
              class="text-[10px] font-black text-white/80 tracking-widest"
              >Share-to-Unlock</span
            >
          </div>
          <button
            type="button"
            onclick={toggleSharePromo}
            class="px-3 py-1.5 rounded-lg text-[9px] font-black tracking-wider transition-all {formState
              .metadata.share_promotion?.enabled
              ? 'bg-pink-500/20 text-pink-400 border border-pink-500/30'
              : 'bg-white/5 text-white/30 border border-white/10'}"
          >
            {formState.metadata.share_promotion?.enabled ? "BẬT" : "TẮT"}
          </button>
        </div>

        {#if formState.metadata.share_promotion?.enabled}
          <div class="flex flex-col gap-1.5">
            <label
              class="text-[9px] font-bold text-white/40 tracking-wider"
              >ID Voucher / Chiến dịch</label
            >
            <input
              type="text"
              bind:value={formState.metadata.share_promotion.voucher_id}
              placeholder="VD: OSMO50K"
              class="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-[11px] text-white focus:outline-none focus:border-pink-500/50 transition-colors font-mono"
            />
            <p class="text-[8px] text-pink-400/60 mt-1">
              Hệ thống tự tải cấu hình từ Voucher này.
            </p>
          </div>
        {/if}
      </div>
    </div>
  </div>

  <!-- GEO 2026: Product FAQs -->
  <div class="flex flex-col gap-4">
    <div class="flex items-center justify-between">
      <div
        class="flex items-center gap-2 text-[9px] font-black text-white/25 tracking-[0.25em]"
      >
        <HelpCircle size={11} class="text-amber-400/60" />
        Hỏi đáp (FAQ)
      </div>
      <div class="flex items-center gap-2">
        <button
          type="button"
          onclick={handleAiSuggestFaqs}
          class="px-3 py-1.5 rounded-lg bg-blue-500/10 border border-blue-500/30 text-blue-400 text-[9px] font-black tracking-wider"
          >XOHI AUTO</button
        >
        <button
          type="button"
          onclick={addFaq}
          class="px-3 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400 text-[9px] font-black tracking-wider"
          >Thêm tay</button
        >
      </div>
    </div>

    {#if formState.metadata.faqs && formState.metadata.faqs.length > 0}
      <div class="flex flex-col gap-3">
        {#each formState.metadata.faqs as faq, i}
          <div
            class="flex flex-col gap-2 p-3 rounded-xl bg-white/[0.02] border border-white/5 relative group"
          >
            <button
              type="button"
              onclick={() => removeFaq(i)}
              class="absolute top-2 right-2 text-red-400/50 hover:text-red-400"
              ><Trash2 size={12} /></button
            >
            <input
              type="text"
              bind:value={faq.question}
              placeholder="Câu hỏi"
              class="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-[11px] text-white"
            />
            <textarea
              bind:value={faq.answer}
              placeholder="Câu trả lời"
              rows="2"
              class="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-[11px] text-white/80 resize-none"
            ></textarea>
          </div>
        {/each}
      </div>
    {/if}
  </div>

  <div class="flex flex-col gap-4">
    <div
      class="flex items-center gap-2 text-[9px] font-black text-white/25 tracking-[0.25em]"
    >
      <Shield size={11} class="text-blue-400/60" />
      Hồ sơ pháp lý & Công bố (Regulatory)
    </div>
    <div
      class="grid grid-cols-1 md:grid-cols-2 gap-4 p-5 rounded-3xl bg-white/[0.02] border border-white/5 shadow-inner"
    >
      <div class="flex flex-col gap-1.5">
        <label
          class="text-[9px] font-bold text-white/40 tracking-widest"
          >Số tiếp nhận phiếu công bố</label
        >
        <input
          type="text"
          bind:value={formState.metadata.notification_no}
          placeholder="VD: 259062/24/CBMP-QLD"
          class="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2.5 text-[11px] text-white focus:outline-none focus:border-blue-500/50 transition-colors font-mono"
        />
      </div>
      <div class="flex flex-col gap-1.5">
        <label
          class="text-[9px] font-bold text-white/40 tracking-widest"
          >Ngày cấp</label
        >
        <input
          type="date"
          bind:value={formState.metadata.notification_date}
          class="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2.5 text-[11px] text-white focus:outline-none focus:border-blue-500/50 transition-colors"
        />
      </div>
      <div class="md:col-span-2 flex flex-col gap-1.5">
        <label
          class="text-[9px] font-bold text-white/40 tracking-widest"
          >Cơ quan cấp phép</label
        >
        <input
          type="text"
          bind:value={formState.metadata.authority}
          placeholder="VD: Cục Quản lý Dược - Bộ Y tế"
          class="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2.5 text-[11px] text-white focus:outline-none focus:border-blue-500/50 transition-colors"
        />
      </div>
      <div class="md:col-span-2 flex flex-col gap-1.5">
        <div class="flex items-center justify-between">
          <label
            class="text-[9px] font-bold text-white/40 tracking-widest"
            >Ảnh phiếu công bố
          </label>
          <button
            type="button"
            onclick={scanComplianceImage}
            class="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-400 text-[8px] font-black tracking-tighter hover:bg-blue-500/20 transition-all"
          >
            <RefreshCw size={10} class={isScanning ? "animate-spin" : ""} />
            AI Intel Scan
          </button>
        </div>
        <div class="flex gap-2">
          <input
            type="text"
            bind:value={formState.metadata.notification_doc}
            placeholder="https://storage.smartshop.test/docs/notification-image.jpg"
            class="flex-1 bg-black/40 border border-white/10 rounded-xl px-3 py-2.5 text-[11px] text-white focus:outline-none focus:border-blue-500/50 transition-colors"
          />
          <button
            type="button"
            onclick={() => onOpenVault?.("notification_doc")}
            class="px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-white text-[10px] font-bold hover:bg-white/10 transition-all"
          >
            Chọn Ảnh
          </button>
        </div>

        {#if formState.metadata.notification_doc}
          <div
            class="mt-3 relative group rounded-2xl overflow-hidden border border-white/10 bg-white/[0.02]"
          >
            <img
              src={formState.metadata.notification_doc}
              alt="Phiếu công bố"
              class="w-full h-auto max-h-[300px] object-contain"
            />
            <div
              class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center backdrop-blur-[2px]"
            >
              <button
                type="button"
                onclick={() => (formState.metadata.notification_doc = "")}
                class="px-4 py-2 rounded-full bg-red-500/20 border border-red-500/40 text-red-400 text-[10px] font-black tracking-widest hover:bg-red-500/40 transition-all"
              >
                Gỡ bỏ ảnh
              </button>
            </div>
          </div>
          <p class="text-[8px] text-blue-400/60 mt-1 italic">
            Vui lòng kiểm tra lại ảnh trước khi nhấn AI Intel Scan để có kết quả
            tốt nhất.
          </p>
        {/if}
      </div>
    </div>
  </div>

  <!-- Tóm tắt SGE / Semantic HTML (GEO 2026) -->
  <div class="flex flex-col gap-4">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2 text-[9px] font-black text-white/25 tracking-[0.25em]">
        <Sparkles size={11} class="text-pink-400/60" />
        Tóm tắt Semantic (Google SGE / AI Search)
      </div>
      <button
        type="button"
        onclick={handleAiSuggestSemantic}
        disabled={isSuggestingSemantic}
        class="px-3 py-1.5 rounded-lg bg-pink-500/10 border border-pink-500/30 text-pink-400 text-[9px] font-black tracking-wider flex items-center gap-1.5 disabled:opacity-50"
      >
        {#if isSuggestingSemantic}
          <RefreshCw size={10} class="animate-spin" />
          PHÂN TÍCH...
        {:else}
          XOHI AUTO
        {/if}
      </button>
    </div>
    <div class="p-3 rounded-2xl bg-white/[0.02] border border-white/5">
      <SemanticEditor bind:value={formState.metadata.desc_semantic} />
    </div>
    <p class="text-[8px] text-white/30 italic -mt-2">
      * Cấu trúc danh sách (h2, ul, li) chuẩn Semantic giúp Google SGE dễ dàng trích xuất thông tin sản phẩm làm câu trả lời hàng đầu.
    </p>
  </div>

  <div class="flex flex-col gap-4">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2 text-[9px] font-black text-white/25 tracking-[0.25em]">
        <Beaker size={11} class="text-teal-400/60" />
        Bảng thành phần
      </div>
      <button
        type="button"
        onclick={handleAiSuggestIngredientsGrouped}
        disabled={isSuggestingIngredientsGrouped}
        class="px-3 py-1.5 rounded-lg bg-teal-500/10 border border-teal-500/30 text-teal-400 text-[9px] font-black tracking-wider flex items-center gap-1.5 disabled:opacity-50"
      >
        {#if isSuggestingIngredientsGrouped}
          <RefreshCw size={10} class="animate-spin" />
          PHÂN TÍCH...
        {:else}
          XOHI NHÓM
        {/if}
      </button>
    </div>
    <textarea
      bind:value={formState.metadata.ingredients}
      placeholder="Bảng thành phần đầy đủ..."
      rows="5"
      class="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2.5 text-[11px] text-white/80 resize-none font-mono"
    ></textarea>

    {#if formState.metadata.ingredients_groups && formState.metadata.ingredients_groups.length > 0}
      <div class="flex items-center gap-2 overflow-x-auto py-1 px-0.5 custom-scrollbar min-h-[36px]">
        {#each formState.metadata.ingredients_groups as grp}
          <div class="flex items-center gap-1.5 px-3 py-1 rounded-full bg-teal-500/10 border border-teal-500/20 text-white shrink-0 group relative cursor-pointer hover:bg-teal-500/25 transition-all">
            <span class="text-[9px] font-bold text-teal-300">{grp.group}</span>
            <span class="text-[8px] font-black px-1.5 py-0.5 rounded-full bg-teal-400/20 text-teal-300">{grp.items.length}</span>
            
            <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-max max-w-[280px] p-2.5 rounded-xl bg-[#0d1117] border border-white/10 shadow-2xl opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity duration-200 z-50 text-[9px] text-white/80 leading-relaxed font-sans">
              <div class="font-bold text-teal-300 mb-1 border-b border-white/10 pb-1 flex justify-between gap-4">
                <span>{grp.group}</span>
                <span class="text-white/40">Độ ưu tiên: {grp.priority}</span>
              </div>
              <ul class="list-disc pl-3 flex flex-col gap-0.5 text-white/70">
                {#each grp.items as item}
                  <li>{item}</li>
                {/each}
              </ul>
            </div>
          </div>
        {/each}
      </div>
    {/if}
  </div>

  <!-- Thành phần nổi bật -->
  <div class="flex flex-col gap-4">
    <div class="flex items-center justify-between">
      <div
        class="flex items-center gap-2 text-[9px] font-black text-white/25 tracking-[0.25em]"
      >
        <Star size={11} class="text-amber-400/60" />
        Thành phần nổi bật
      </div>
      <div class="flex items-center gap-2">
        <button
          type="button"
          onclick={handleAiSuggestIngredients}
          disabled={isSuggestingIngredients}
          class="px-3 py-1.5 rounded-lg bg-blue-500/10 border border-blue-500/30 text-blue-400 text-[9px] font-black tracking-wider flex items-center gap-1.5 disabled:opacity-50"
        >
          {#if isSuggestingIngredients}
            <RefreshCw size={10} class="animate-spin" />
            PHÂN TÍCH...
          {:else}
            XOHI AUTO
          {/if}
        </button>
        <button
          type="button"
          onclick={addFeaturedIngredient}
          class="px-3 py-1.5 rounded-lg bg-teal-500/10 border border-teal-500/20 text-teal-400 text-[9px] font-black tracking-wider"
          >Thêm</button
        >
      </div>
    </div>

    {#if formState.metadata.featured_ingredients && formState.metadata.featured_ingredients.length > 0}
      <div class="flex flex-col gap-3">
        {#each formState.metadata.featured_ingredients as item, i}
          <div
            class="flex flex-col gap-2 p-3 rounded-xl bg-white/[0.02] border border-white/5 relative group"
          >
            <button
              type="button"
              onclick={() => removeFeaturedIngredient(i)}
              class="absolute top-2 right-2 text-red-400/50 hover:text-red-400"
              ><Trash2 size={12} /></button
            >
            <div class="grid grid-cols-[56px_1fr] gap-2">
              <div class="relative">
                <input
                  type="text"
                  bind:value={item.icon}
                  onclick={() => (activeIconPicker = i)}
                  readonly
                  class="w-full bg-black/40 border border-white/10 rounded-lg py-2 text-center text-[18px] cursor-pointer hover:bg-white/5 transition-colors"
                />
                {#if activeIconPicker === i}
                  <!-- svelte-ignore a11y_click_events_have_key_events -->
                  <!-- svelte-ignore a11y_no_static_element_interactions -->
                  <div
                    class="fixed inset-0 z-[60]"
                    onclick={() => (activeIconPicker = null)}
                  ></div>
                  <div
                    class="absolute z-[70] top-full left-0 mt-2 p-2 bg-[#1a1a1a] border border-white/10 rounded-xl grid grid-cols-5 gap-1 shadow-2xl min-w-[180px]"
                  >
                    {#each viralIcons as vIcon}
                      <button
                        type="button"
                        onclick={(e) => {
                          e.stopPropagation();
                          item.icon = vIcon.icon;
                          activeIconPicker = null;
                        }}
                        class="w-7 h-7 flex items-center justify-center rounded-lg hover:bg-white/10 transition-colors text-[16px]"
                      >
                        {vIcon.icon}
                      </button>
                    {/each}
                  </div>
                {/if}
              </div>
              <input
                type="text"
                bind:value={item.name}
                placeholder="Tên thành phần"
                class="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-[11px] text-white focus:border-teal-500/50 outline-none"
              />
            </div>
            <textarea
              bind:value={item.benefit}
              placeholder="Lợi ích..."
              rows="2"
              class="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-[11px] text-white/80 resize-none"
            ></textarea>
          </div>
        {/each}
      </div>
    {/if}
  </div>
</div>

<style>
  @reference "tailwindcss";
</style>
