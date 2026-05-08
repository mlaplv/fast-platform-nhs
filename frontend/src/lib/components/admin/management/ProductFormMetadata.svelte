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
  import type { ProductFormState } from "$lib/types";
  import { useNanobot } from "$lib/state/nanobot.svelte";
  import { apiClient } from "$lib/utils/apiClient";
  import { getIngredientIcon } from "$lib/utils/product";

  const nanobot = useNanobot();

  let { formState = $bindable() } = $props<{
    formState: ProductFormState;
  }>();

  onMount(() => {
    if (!formState.metadata) {
      formState.metadata = { landing_type: 'standard' };
    }
    if (!formState.metadata.landing_type) {
      formState.metadata.landing_type = 'standard';
    }
  });

  /** Viral Intelligence: Auto-suggest icons for ingredients */
  const viralIcons = [
    { icon: '💧', label: 'Cấp ẩm / HA' },
    { icon: '🍋', label: 'Vitamin C / Làm sáng' },
    { icon: '🛡️', label: 'Niacinamide / Bảo vệ' },
    { icon: '🌙', label: 'Retinol / Tái tạo' },
    { icon: '🌿', label: 'Trà xanh / Thảo mộc' },
    { icon: '🧬', label: 'Collagen / Ceramide' },
    { icon: '✨', label: 'Sáng da / Glow' },
    { icon: '☀️', label: 'Chống nắng / SPF' },
    { icon: '🧪', label: 'Acid / AHA / BHA' },
    { icon: '🌱', label: 'Rau má / Cica' },
    { icon: '🍎', label: 'Lựu / Chống oxy hóa' },
    { icon: '🌹', label: 'Hoa hồng / Dịu nhẹ' },
    { icon: '🍯', label: 'Mật ong / Sát khuẩn' },
    { icon: '🫗', label: 'Dầu dưỡng / Olive' },
    { icon: '🌑', label: 'Than hoạt tính / Đất sét' },
    { icon: '🪵', label: 'Cam thảo / Rễ cây' },
    { icon: '🧴', label: 'Lotion / Dưỡng thể' },
    { icon: '🩹', label: 'Phục hồi / Cấp cứu' },
    { icon: '🧼', label: 'Làm sạch / Cleanser' },
    { icon: '💊', label: 'Dược mỹ phẩm / Đặc trị' }
  ];
  let activeIconPicker = $state<number | null>(null);

  $effect(() => {
    if (formState.metadata.featured_ingredients) {
      formState.metadata.featured_ingredients.forEach(item => {
        if (item.name && (!item.icon || item.icon === '🧬')) {
          const smartIcon = getIngredientIcon(item.name);
          if (smartIcon !== '🧬') {
            item.icon = smartIcon;
          }
        }
      });
    }
  });

  const landingTypes = [
    { value: 'standard', label: 'Standard (E-commerce)', desc: 'Giao diện truyền thống' },
    { value: 'stealth', label: 'Stealth Funnel', desc: 'Tối ưu chuyển đổi nhanh (CPA)' },
    { value: 'tiktok', label: 'TikTok Shop Clone', desc: 'Trải nghiệm như TikTok' }
  ];

  // ─── Auto-detect video duration ─────────────────────────────────
  let isDetectingDuration = $state(false);
  let detectError = $state<string | null>(null);

  function isVideoFile(url: string): boolean {
    if (!url) return false;
    const clean = url.split('?')[0].toLowerCase();
    return /\.(mp4|webm|mov|ogg|ogv|avi|mkv)$/.test(clean);
  }

  /** Tạo <video> ẩn, đọ duration từ URL rồi auto-fill video_end_time */
  function detectVideoDuration(url: string): Promise<number | null> {
    return new Promise((resolve) => {
      if (!url || !isVideoFile(url)) { resolve(null); return; }
      const v = document.createElement('video');
      v.preload = 'metadata';
      v.src = url;
      v.onloadedmetadata = () => {
        const dur = isFinite(v.duration) ? Math.round(v.duration * 10) / 10 : null;
        v.src = ''; // giải phóng resource
        resolve(dur);
      };
      v.onerror = () => { v.src = ''; resolve(null); };
      // Timeout 8s đề phòng URL chậm
      setTimeout(() => { v.src = ''; resolve(null); }, 8000);
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
        formState.metadata.video_start_time = formState.metadata.video_start_time ?? 0;
      } else {
        detectError = 'Không đọc được thời lượng';
      }
    } finally {
      isDetectingDuration = false;
    }
  }

  /* 
   * Xóa $effect() ở đây để tránh bị ghi đè video_end_time khi mở load bài từ DB.
   * Chức năng tự động detect giờ sẽ được chuyển sang onchange của ô nhập URL.
   */

  // ─── FAQ Management (GEO 2026) ──────────────────────────────────
  function addFaq() {
    if (!formState.metadata.faqs) formState.metadata.faqs = [];
    formState.metadata.faqs.push({ question: '', answer: '' });
  }

  function removeFaq(index: number) {
    if (!formState.metadata.faqs) return;
    formState.metadata.faqs.splice(index, 1);
  }

  // ─── Featured Ingredients Management ────────────────────────────
  function addFeaturedIngredient() {
    if (!formState.metadata.featured_ingredients) formState.metadata.featured_ingredients = [];
    formState.metadata.featured_ingredients.push({ name: '', benefit: '', icon: '' });
  }

  function removeFeaturedIngredient(index: number) {
    if (!formState.metadata.featured_ingredients) return;
    formState.metadata.featured_ingredients.splice(index, 1);
  }

  let isSuggestingFaqs = $state(false);

  async function handleAiSuggestFaqs() {
    if (!formState.name) {
      nanobot.showToast("Vui lòng nhập tên sản phẩm trước khi gọi XOHI.", "warning");
      return;
    }
    isSuggestingFaqs = true;
    try {
      const res = await apiClient.post<{ data: { question: string, answer: string }[] }>('/api/v1/products/faq-suggest', {
        name: formState.name,
        description: formState.description || ''
      });
      if (res && res.data && Array.isArray(res.data) && res.data.length > 0) {
        if (!formState.metadata.faqs) formState.metadata.faqs = [];
        formState.metadata.faqs.push(...res.data);
        nanobot.showToast("XOHI đã tự động tạo thành công bộ câu hỏi FAQ.", "success");
      } else {
        nanobot.showToast("XOHI không thể tạo thêm câu hỏi. Vui lòng thử lại.", "error");
      }
    } catch (e) {
      console.error('XOHI FAQ Suggestion failed:', e);
      nanobot.showToast("Lỗi kết nối tới hệ thống AI XOHI.", "error");
    } finally {
      isSuggestingFaqs = false;
    }
  }

  function toggleSharePromo() {
    if (!formState.metadata.share_promotion) {
      formState.metadata.share_promotion = {
        enabled: true,
        voucher_id: '',
        voucher_label: 'Giảm 50.000₫',
        voucher_condition: 'Cho đơn từ 0đ',
        cta_text: 'Chia sẻ nhận khuyến mãi',
        share_text: ''
      };
    } else {
      formState.metadata.share_promotion.enabled = !formState.metadata.share_promotion.enabled;
    }
  }
</script>

<div class="flex flex-col gap-6">
  <!-- LANDING TYPE SELECTOR -->
  <div class="flex flex-col gap-3">
    <div class="flex items-center gap-2 text-[9px] font-black text-white/25 uppercase tracking-[0.25em]">
      <Layout size={11} class="text-amber-400/60" />
      Loại hình phễu (Landing Type)
    </div>

    <div class="grid grid-cols-3 gap-2">
      {#each landingTypes as type}
        <button
          type="button"
          onclick={() => formState.metadata.landing_type = type.value as ProductMetadata['landing_type']}
          class="flex flex-col gap-1 p-3 rounded-xl border transition-all text-left {formState.metadata.landing_type === type.value ? 'bg-amber-500/10 border-amber-500/50' : 'bg-white/5 border-white/5 hover:border-white/10'}"
        >
          <span class="text-[10px] font-bold {formState.metadata.landing_type === type.value ? 'text-amber-400' : 'text-white/60'}">{type.label}</span>
          <span class="text-[8px] text-white/30 leading-tight">{type.desc}</span>
        </button>
      {/each}
    </div>
  </div>

  <!-- CONTEXTUAL FIELDS -->
  <div class="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 rounded-2xl bg-white/[0.02] border border-white/5">

    <!-- Scarcity Timer (Stealth/TikTok) -->
    {#if formState.metadata.landing_type !== 'standard'}
      <div class="flex flex-col gap-1.5">
        <label class="text-[9px] font-bold text-white/40 uppercase tracking-wider">Thời gian khan hiếm (Giây)</label>
        <input
          type="number"
          bind:value={formState.metadata.scarcity_seconds}
          placeholder="600"
          class="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-[11px] text-white focus:outline-none focus:border-amber-500/50 transition-colors"
        />
      </div>
    {/if}

    <!-- Video URL – luôn hiển thị, dùng cho cả desktop hero lẫn mobile banner -->
    <div class="flex flex-col gap-1.5 md:col-span-2">
      <label class="text-[9px] font-bold text-white/40 uppercase tracking-wider">Video URL (TikTok/YouTube hoặc đường dẫn nội bộ, ví dụ: /static/video/HN_TikTok.mp4)</label>
      <input
        type="text"
        bind:value={formState.metadata.video_url}
        onchange={() => {
          const url = formState.metadata.video_url;
          if (url && isVideoFile(url)) {
            autoDetectEndTime(url);
          }
        }}
        placeholder="/static/video/HN_TikTok.mp4  hoặc  https://youtu.be/xxxx"
        class="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-[11px] text-white focus:outline-none focus:border-amber-500/50 transition-colors"
      />
      <p class="text-[8px] text-white/25 leading-relaxed">
        Hỗ trợ: đường dẫn nội bộ (.mp4/.webm), YouTube (youtube.com/watch, youtu.be, /shorts/), TikTok (tiktok.com/@.../video/ID)
      </p>
    </div>

    <!-- ⏱ VIDEO PLAYBACK CONTROLS: Start & End time -->
    <div class="md:col-span-2 flex flex-col gap-2 p-3 rounded-xl bg-amber-500/[0.04] border border-amber-500/15">
      <div class="flex items-center justify-between mb-1">
        <div class="flex items-center gap-1.5">
          <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" class="text-amber-400/70"><polygon points="5 3 19 12 5 21 5 3"/></svg>
          <span class="text-[9px] font-black text-amber-400/60 uppercase tracking-[0.25em]">Điều khiển phát video (Trim)</span>
        </div>
        <!-- Trạng thái detect -->
        {#if isDetectingDuration}
          <div class="flex items-center gap-1.5 text-amber-400/60">
            <div class="w-3 h-3 border-2 border-amber-400/40 border-t-amber-400 rounded-full animate-spin"></div>
            <span class="text-[8px] font-mono">Đang phân tích video...</span>
          </div>
        {:else if detectError}
          <span class="text-[8px] text-red-400/70 font-mono">{detectError}</span>
        {:else if formState.metadata.video_end_time}
          <div class="flex items-center gap-1 px-1.5 py-0.5 rounded bg-green-500/10 border border-green-500/20">
            <svg xmlns="http://www.w3.org/2000/svg" width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" class="text-green-400"><polyline points="20 6 9 17 4 12"/></svg>
            <span class="text-[8px] text-green-400 font-mono">Đã detect</span>
          </div>
        {/if}
      </div>
      <div class="grid grid-cols-2 gap-3">
        <div class="flex flex-col gap-1">
          <label class="text-[8px] font-bold text-white/30 uppercase tracking-wider">Bắt đầu từ (giây)</label>
          <div class="relative">
            <input
              type="number"
              min="0"
              step="0.5"
              bind:value={formState.metadata.video_start_time}
              placeholder="0"
              class="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-[11px] text-amber-300 font-mono focus:outline-none focus:border-amber-500/50 transition-colors pr-10"
            />
            <span class="absolute right-2 top-1/2 -translate-y-1/2 text-[9px] text-white/20 font-mono">s</span>
          </div>
          <p class="text-[8px] text-white/20">Bỏ trống = từ đầu</p>
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-[8px] font-bold text-white/30 uppercase tracking-wider">Kết thúc ở (giây)</label>
          <div class="relative flex gap-1">
            <div class="relative flex-1">
              <input
                type="number"
                min="0"
                step="0.5"
                bind:value={formState.metadata.video_end_time}
                placeholder={isDetectingDuration ? 'Đang detect...' : 'Toàn bộ'}
                disabled={isDetectingDuration}
                class="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-[11px] text-amber-300 font-mono focus:outline-none focus:border-amber-500/50 transition-colors pr-10 disabled:opacity-50"
              />
              {#if isDetectingDuration}
                <div class="absolute right-2 top-1/2 -translate-y-1/2 w-3 h-3 border-2 border-amber-400/40 border-t-amber-400 rounded-full animate-spin"></div>
              {:else}
                <span class="absolute right-2 top-1/2 -translate-y-1/2 text-[9px] text-white/20 font-mono">s</span>
              {/if}
            </div>
            <!-- Nút re-detect thủ công -->
            <button
              type="button"
              onclick={() => autoDetectEndTime()}
              disabled={isDetectingDuration || !formState.metadata?.video_url}
              title="Tự động đọc thời lượng video"
              class="px-2 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400/70 hover:bg-amber-500/20 hover:text-amber-300 transition-all disabled:opacity-30 disabled:cursor-not-allowed text-[8px] font-black uppercase tracking-wider whitespace-nowrap shrink-0"
            >
              {isDetectingDuration ? '...' : 'Auto'}
            </button>
          </div>
          <p class="text-[8px] text-white/20">Bỏ trống = phát hết &bull; Tự detect khi nhập URL</p>
        </div>
      </div>
      <!-- Preview range -->
      {#if formState.metadata.video_start_time != null || formState.metadata.video_end_time != null}
        <div class="flex items-center gap-2 mt-1 px-2 py-1 rounded-md bg-black/30 border border-white/5">
          <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" class="text-amber-400/50"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
          <span class="text-[9px] font-mono text-amber-300/70">
            Phát từ <strong>{formState.metadata.video_start_time ?? 0}s</strong>
            {#if formState.metadata.video_end_time}
              → kết thúc lúc <strong>{formState.metadata.video_end_time}s</strong>
              &nbsp;(dài {((formState.metadata.video_end_time ?? 0) - (formState.metadata.video_start_time ?? 0)).toFixed(1)}s)
            {:else}
              → phát hết
            {/if}
          </span>
        </div>
      {/if}
    </div>
  </div>

  <!-- R00 Compliance: UI Labels (Dynamic) -->
  <div class="flex flex-col gap-4">
    <div class="flex items-center gap-2 text-[9px] font-black text-white/25 uppercase tracking-[0.25em]">
      <Zap size={11} class="text-amber-400/60" />
      Cấu hình R00 (UI Strings)
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div class="flex flex-col gap-1.5">
        <label class="text-[9px] font-bold text-white/40 uppercase tracking-wider">Text Loading Sync</label>
        <input
          type="text"
          bind:value={formState.metadata.sync_loading_text}
          placeholder="Đang phân tích dữ liệu AI..."
          class="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-[11px] text-white focus:outline-none focus:border-amber-500/50 transition-colors"
        />
      </div>
      <div class="flex flex-col gap-1.5">
        <label class="text-[9px] font-bold text-white/40 uppercase tracking-wider">Tên Website (SEO)</label>
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
    <div class="flex items-center gap-2 text-[9px] font-black text-white/25 uppercase tracking-[0.25em]">
      <Share2 size={11} class="text-pink-400/60" />
      Lan truyền & Tương tác (Viral 2026)
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 rounded-2xl bg-white/[0.02] border border-white/5">
      <!-- Flash Sale End Time -->
      <div class="flex flex-col gap-1.5">
        <div class="flex items-center justify-between">
          <label class="text-[9px] font-bold text-white/40 uppercase tracking-wider">Thời gian Flash Sale kết thúc</label>
          <label class="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" bind:checked={formState.metadata.is_flash_sale} class="sr-only peer" />
            <div class="w-7 h-4 bg-white/10 rounded-full peer peer-checked:bg-pink-500 transition-all relative after:content-[''] after:absolute after:top-0.5 after:left-0.5 after:bg-white after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:after:translate-x-3"></div>
            <span class="text-[8px] font-black text-white/30 uppercase tracking-widest">Kích hoạt</span>
          </label>
        </div>
        <input
          type="datetime-local"
          bind:value={formState.metadata.flash_sale_end}
          class="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-[11px] text-white focus:outline-none focus:border-pink-500/50 transition-colors"
        />
        <p class="text-[8px] text-white/20 leading-tight">Thiết lập thời điểm kết thúc để hiển thị đồng hồ đếm ngược (Countdown) tạo sự khẩn cấp.</p>
      </div>

      <!-- Initial Likes -->
      <div class="flex flex-col gap-1.5">
        <label class="text-[9px] font-bold text-white/40 uppercase tracking-wider">Lượt thích ban đầu (Social Proof)</label>
        <div class="relative">
          <input
            type="number"
            bind:value={formState.metadata.likes}
            placeholder="0"
            class="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-[11px] text-white focus:outline-none focus:border-pink-500/50 transition-colors pl-9"
          />
          <Heart size={12} class="absolute left-3 top-1/2 -translate-y-1/2 text-pink-500/60" />
        </div>
        <p class="text-[8px] text-white/20 leading-tight">Số lượt tim hiển thị trên thanh ViralBar. Giúp tăng uy tín sản phẩm từ cái nhìn đầu tiên.</p>
      </div>

      <!-- Share Target & Reward -->
      <div class="flex flex-col gap-1.5 md:col-span-2">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div class="flex flex-col gap-1.5">
            <label class="text-[9px] font-bold text-white/40 uppercase tracking-wider">Mục tiêu chia sẻ (Gamification)</label>
            <input
              type="number"
              bind:value={formState.metadata.share_count}
              placeholder="Hiện tại"
              class="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-[11px] text-white focus:outline-none focus:border-pink-500/50 transition-colors"
            />
          </div>
          <div class="flex flex-col gap-1.5">
            <label class="text-[9px] font-bold text-white/40 uppercase tracking-wider">Mốc mục tiêu (Target)</label>
            <input
              type="number"
              bind:value={formState.metadata.share_target}
              placeholder="VD: 1000"
              class="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-[11px] text-white focus:outline-none focus:border-pink-500/50 transition-colors"
            />
          </div>
        </div>
        <div class="flex flex-col gap-1.5 mt-2">
          <label class="text-[9px] font-bold text-white/40 uppercase tracking-wider">Nhãn phần thưởng khi đạt mốc</label>
          <input
            type="text"
            bind:value={formState.metadata.share_reward_label}
            placeholder="VD: Đạt 1k share mở khóa đại tiệc quà tặng!"
            class="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-[11px] text-white focus:outline-none focus:border-pink-500/50 transition-colors"
          />
          <p class="text-[8px] text-white/20 leading-tight italic">Thông điệp này sẽ xuất hiện khi thanh tiến trình (Progress Bar) đạt 100%.</p>
        </div>
      </div>

      <!-- SHARE TO UNLOCK PROMOTION -->
      <div class="md:col-span-2 mt-4 p-4 rounded-xl bg-pink-500/[0.03] border border-pink-500/15">
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-2">
            <Ticket size={14} class="text-pink-400" />
            <span class="text-[10px] font-black text-white/80 uppercase tracking-widest">Chiến dịch Share-to-Unlock</span>
          </div>
          <button
            type="button"
            onclick={toggleSharePromo}
            class="px-3 py-1.5 rounded-lg text-[9px] font-black uppercase tracking-wider transition-all {formState.metadata.share_promotion?.enabled ? 'bg-pink-500/20 text-pink-400 border border-pink-500/30' : 'bg-white/5 text-white/30 border border-white/10'}"
          >
            {formState.metadata.share_promotion?.enabled ? 'Đang bật' : 'Đang tắt'}
          </button>
        </div>

        {#if formState.metadata.share_promotion?.enabled}
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="flex flex-col gap-1.5">
              <label class="text-[9px] font-bold text-white/40 uppercase tracking-wider">ID Voucher trong DB (Liên kết bảo mật)</label>
              <input
                type="text"
                bind:value={formState.metadata.share_promotion.voucher_id}
                placeholder="VD: OSMO50K (phải tồn tại trong hệ thống Voucher)"
                class="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-[11px] text-white focus:outline-none focus:border-pink-500/50 transition-colors font-mono"
              />
              <p class="text-[8px] text-pink-400/60">⚠️ Nhập đúng ID Voucher đã tạo trong mục Khuyến mãi. Hệ thống sẽ đọc từ DB — không expose trong HTML.</p>
            </div>
            <div class="flex flex-col gap-1.5">
              <label class="text-[9px] font-bold text-white/40 uppercase tracking-wider">Tiêu đề Voucher (Label)</label>
              <input
                type="text"
                bind:value={formState.metadata.share_promotion.voucher_label}
                placeholder="VD: Giảm 50.000₫"
                class="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-[11px] text-white focus:outline-none focus:border-pink-500/50 transition-colors"
              />
              <p class="text-[8px] text-white/20 mt-1">VD: GIẢM 50.000₫. Hiển thị trên tem Voucher sau khi mở khóa.</p>
            </div>
            <div class="flex flex-col gap-1.5">
              <label class="text-[9px] font-bold text-white/40 uppercase tracking-wider">Điều kiện (Condition)</label>
              <input
                type="text"
                bind:value={formState.metadata.share_promotion.voucher_condition}
                placeholder="VD: Cho đơn từ 0đ"
                class="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-[11px] text-white focus:outline-none focus:border-pink-500/50 transition-colors"
              />
              <p class="text-[8px] text-white/20 mt-1">Dòng chú thích nhỏ dưới Voucher. VD: Áp dụng cho đơn từ 200k.</p>
            </div>
            <div class="flex flex-col gap-1.5">
              <label class="text-[9px] font-bold text-white/40 uppercase tracking-wider">Lời kêu gọi (CTA Text)</label>
              <input
                type="text"
                bind:value={formState.metadata.share_promotion.cta_text}
                placeholder="Chia sẻ nhận khuyến mãi"
                class="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-[11px] text-white focus:outline-none focus:border-pink-500/50 transition-colors"
              />
              <p class="text-[8px] text-white/20 mt-1">Dòng chữ trên nút bấm chia sẻ. VD: Share để nhận ngay.</p>
            </div>
            <div class="flex flex-col gap-1.5 md:col-span-2">
              <label class="text-[9px] font-bold text-white/40 uppercase tracking-wider">Nội dung mẫu khi chia sẻ (Share Text)</label>
              <textarea
                bind:value={formState.metadata.share_promotion.share_text}
                placeholder="VD: Sản phẩm này tuyệt vời quá, các bạn xem thử nhé!"
                rows="2"
                class="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-[11px] text-white/80 focus:outline-none focus:border-pink-500/50 transition-colors resize-none"
              ></textarea>
              <p class="text-[8px] text-white/20 mt-1">Nội dung sẽ tự động điền vào cửa sổ chia sẻ (Zalo, FB...). Đây là mồi nhử giúp lan truyền tự nhiên.</p>
            </div>
          </div>
        {/if}
      </div>
    </div>
  </div>

  <!-- GEO 2026: Product FAQs (Schema JSON-LD & UI) -->
  <div class="flex flex-col gap-4">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2 text-[9px] font-black text-white/25 uppercase tracking-[0.25em]">
        <HelpCircle size={11} class="text-amber-400/60" />
        Hỏi đáp (FAQ Schema - GEO 2026)
      </div>
      <div class="flex items-center gap-2">
        <button
          type="button"
          onclick={handleAiSuggestFaqs}
          disabled={isSuggestingFaqs}
          class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-500/10 border border-blue-500/30 text-blue-400 hover:bg-blue-600/20 hover:border-blue-500/50 hover:text-blue-300 transition-all text-[9px] font-black uppercase tracking-wider disabled:opacity-50"
        >
          {#if isSuggestingFaqs}
            <RefreshCw size={10} class="animate-spin" />
            ĐANG TẠO...
          {:else}
            <Sparkles size={10} />
            🪄 XOHI AUTO FAQ
          {/if}
        </button>
        <button
          type="button"
          onclick={addFaq}
          class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400 hover:bg-amber-500/20 hover:text-amber-300 transition-all text-[9px] font-black uppercase tracking-wider"
        >
          <Plus size={12} strokeWidth={3} />
          Thêm tay
        </button>
      </div>
    </div>

    {#if formState.metadata.faqs && formState.metadata.faqs.length > 0}
      <div class="flex flex-col gap-3">
        {#each formState.metadata.faqs as faq, i}
          <div class="flex flex-col gap-2 p-3 rounded-xl bg-white/[0.02] border border-white/5 relative group">
            <button
              type="button"
              onclick={() => removeFaq(i)}
              class="absolute top-2 right-2 p-1.5 rounded-lg bg-red-500/10 text-red-400/50 hover:text-red-400 hover:bg-red-500/20 opacity-0 group-hover:opacity-100 transition-all"
              title="Xóa câu hỏi"
            >
              <Trash2 size={12} />
            </button>
            <div class="flex flex-col gap-1.5 pr-8">
              <label class="text-[9px] font-bold text-white/40 uppercase tracking-wider">Câu hỏi {i + 1}</label>
              <input
                type="text"
                bind:value={faq.question}
                placeholder="VD: Sản phẩm có tác dụng phụ không?"
                class="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-[11px] text-white focus:outline-none focus:border-amber-500/50 transition-colors font-medium"
              />
            </div>
            <div class="flex flex-col gap-1.5">
              <label class="text-[9px] font-bold text-white/40 uppercase tracking-wider">Câu trả lời</label>
              <textarea
                bind:value={faq.answer}
                placeholder="VD: Sản phẩm được chiết xuất từ 100% thảo dược thiên nhiên..."
                rows="2"
                class="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-[11px] text-white/80 focus:outline-none focus:border-amber-500/50 transition-colors resize-none leading-relaxed"
              ></textarea>
            </div>
          </div>
        {/each}
      </div>
    {:else}
      <div class="flex items-center justify-center p-6 rounded-2xl border border-dashed border-white/10 bg-white/[0.01]">
        <span class="text-[10px] text-white/20 uppercase font-black tracking-widest text-center">
          Chưa có câu hỏi FAQ.<br/>Thêm FAQ để tăng cường thứ hạng trên AI Search.
        </span>
      </div>
    {/if}
  </div>

  <!-- ─── SECTION: THÀNH PHẦN ──────────────────────────────────────── -->
  <div class="flex flex-col gap-4">
    <div class="flex items-center gap-2 text-[9px] font-black text-white/25 uppercase tracking-[0.25em]">
      <Beaker size={11} class="text-teal-400/60" />
      Thành phần (Ingredients)
    </div>
    <div class="flex flex-col gap-1.5">
      <label class="text-[9px] font-bold text-white/40 uppercase tracking-wider">Bảng thành phần đầy đủ</label>
      <textarea
        bind:value={formState.metadata.ingredients}
        placeholder="VD: Aqua, Niacinamide, Glycerin, Vitamin C (Ascorbic Acid) 10%, Tocopherol (Vitamin E), Allantoin, Panthenol..."
        rows="5"
        class="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2.5 text-[11px] text-white/80 focus:outline-none focus:border-teal-500/50 transition-colors resize-none leading-relaxed font-mono"
      ></textarea>
      <p class="text-[8px] text-white/20 leading-relaxed">
        Nhập đầy đủ INCI list hoặc danh sách thành phần. Dữ liệu này được Helen AI đọc để tư vấn khách hàng.
      </p>
    </div>
  </div>

  <!-- ─── SECTION: THÀNH PHẦN NỔI BẬT ─────────────────────────────── -->
  <div class="flex flex-col gap-4">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2 text-[9px] font-black text-white/25 uppercase tracking-[0.25em]">
        <Star size={11} class="text-amber-400/60" />
        Thành phần nổi bật
      </div>
      <button
        type="button"
        onclick={addFeaturedIngredient}
        class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-teal-500/10 border border-teal-500/20 text-teal-400 hover:bg-teal-500/20 hover:text-teal-300 transition-all text-[9px] font-black uppercase tracking-wider"
      >
        <Plus size={12} strokeWidth={3} />
        Thêm
      </button>
    </div>

    {#if formState.metadata.featured_ingredients && formState.metadata.featured_ingredients.length > 0}
      <div class="flex flex-col gap-3">
        {#each formState.metadata.featured_ingredients as item, i}
          <div class="flex flex-col gap-2 p-3 rounded-xl bg-white/[0.02] border border-white/5 relative group">
            <button
              type="button"
              onclick={() => removeFeaturedIngredient(i)}
              class="absolute top-2 right-2 p-1.5 rounded-lg bg-red-500/10 text-red-400/50 hover:text-red-400 hover:bg-red-500/20 opacity-0 group-hover:opacity-100 transition-all"
              title="Xóa thành phần"
            >
              <Trash2 size={12} />
            </button>

            <div class="grid grid-cols-[56px_1fr] gap-2 pr-8">
              <!-- Icon / Emoji Picker -->
              <div class="flex flex-col gap-1 relative">
                <label class="text-[8px] font-bold text-white/30 uppercase tracking-wider">Icon</label>
                <input
                  type="text"
                  bind:value={item.icon}
                  onclick={() => activeIconPicker = i}
                  placeholder="🧬"
                  maxlength="4"
                  readonly
                  class="w-full bg-black/40 border border-white/10 rounded-lg px-2 py-2 text-[18px] text-center focus:outline-none focus:border-teal-500/50 transition-colors cursor-pointer hover:bg-white/5"
                />
                
                {#if activeIconPicker === i}
                  <!-- svelte-ignore a11y_click_events_have_key_events -->
                  <!-- svelte-ignore a11y_no_static_element_interactions -->
                  <div 
                    class="fixed inset-0 z-[60]" 
                    onclick={(e) => { e.stopPropagation(); activeIconPicker = null; }}
                  ></div>
                  <div class="absolute z-[70] top-full left-0 mt-2 p-2 bg-[#1a1a1a] border border-white/10 rounded-xl grid grid-cols-5 gap-1 shadow-[0_10px_40px_-10px_rgba(0,0,0,0.5)] min-w-[180px]">
                    {#each viralIcons as vIcon}
                      <button
                        type="button"
                        title={vIcon.label}
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
              <!-- Tên thành phần -->
              <div class="flex flex-col gap-1">
                <label class="text-[8px] font-bold text-white/30 uppercase tracking-wider">Tên thành phần {i + 1}</label>
                <input
                  type="text"
                  bind:value={item.name}
                  placeholder="VD: Niacinamide 10%"
                  class="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-[11px] text-white focus:outline-none focus:border-teal-500/50 transition-colors font-semibold"
                />
              </div>
            </div>

            <!-- Lợi ích -->
            <div class="flex flex-col gap-1">
              <label class="text-[8px] font-bold text-white/30 uppercase tracking-wider">Lợi ích / Cơ chế tác động</label>
              <textarea
                bind:value={item.benefit}
                placeholder="VD: Làm mờ thâm nám, đều màu da, ức chế sắc tố melanin hiệu quả lên tới 68%..."
                rows="2"
                class="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-[11px] text-white/80 focus:outline-none focus:border-teal-500/50 transition-colors resize-none leading-relaxed"
              ></textarea>
            </div>
          </div>
        {/each}
      </div>
    {:else}
      <div class="flex items-center justify-center p-6 rounded-2xl border border-dashed border-white/10 bg-white/[0.01]">
        <span class="text-[10px] text-white/20 uppercase font-black tracking-widest text-center">
          Chưa có thành phần nổi bật.<br/>Thêm để highlight trên trang sản phẩm.
        </span>
      </div>
    {/if}
  </div>

</div>

<style>
  @reference "tailwindcss";
</style>
