<script lang="ts">
  import { onMount } from "svelte";
  import Layout from "lucide-svelte/icons/layout";
  import Zap from "lucide-svelte/icons/zap";
  import MessageSquare from "lucide-svelte/icons/message-square";
  import Microscope from "lucide-svelte/icons/microscope";
  import HelpCircle from "lucide-svelte/icons/help-circle";
  import Plus from "lucide-svelte/icons/plus";
  import Trash2 from "lucide-svelte/icons/trash-2";
  import Tag from "lucide-svelte/icons/tag";
  import type { ProductMetadata } from "$lib/types";

  let { formMetadata = $bindable() } = $props<{
    formMetadata: ProductMetadata;
  }>();

  onMount(() => {
    if (!formMetadata) formMetadata = { landing_type: 'standard' };
    if (!formMetadata.landing_type) formMetadata.landing_type = 'standard';
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
    const target = url ?? formMetadata?.video_url;
    if (!target || !isVideoFile(target)) return;
    isDetectingDuration = true;
    detectError = null;
    try {
      const dur = await detectVideoDuration(target);
      if (dur !== null) {
        (formMetadata as any).video_end_time = dur;
        (formMetadata as any).video_start_time = (formMetadata as any).video_start_time ?? 0;
      } else {
        detectError = 'Không đọc được thời lượng';
      }
    } finally {
      isDetectingDuration = false;
    }
  }

  /** Khi video_url thay đổi → tự động detect duration */
  $effect(() => {
    const url = formMetadata?.video_url;
    if (url && isVideoFile(url)) {
      // Dùng untrack để khỏi check $derived lặp
      autoDetectEndTime(url);
    }
  });

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
          onclick={() => formMetadata.landing_type = type.value as ProductMetadata['landing_type']}
          class="flex flex-col gap-1 p-3 rounded-xl border transition-all text-left {formMetadata.landing_type === type.value ? 'bg-amber-500/10 border-amber-500/50' : 'bg-white/5 border-white/5 hover:border-white/10'}"
        >
          <span class="text-[10px] font-bold {formMetadata.landing_type === type.value ? 'text-amber-400' : 'text-white/60'}">{type.label}</span>
          <span class="text-[8px] text-white/30 leading-tight">{type.desc}</span>
        </button>
      {/each}
    </div>
  </div>

  <!-- CONTEXTUAL FIELDS -->
  <div class="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 rounded-2xl bg-white/[0.02] border border-white/5">

    <!-- Scarcity Timer (Stealth/TikTok) -->
    {#if formMetadata.landing_type !== 'standard'}
      <div class="flex flex-col gap-1.5">
        <label class="text-[9px] font-bold text-white/40 uppercase tracking-wider">Thời gian khan hiếm (Giây)</label>
        <input
          type="number"
          bind:value={formMetadata.scarcity_seconds}
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
        bind:value={formMetadata.video_url}
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
        {:else if formMetadata.video_end_time}
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
              bind:value={formMetadata.video_start_time}
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
                bind:value={formMetadata.video_end_time}
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
              disabled={isDetectingDuration || !formMetadata?.video_url}
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
      {#if formMetadata.video_start_time != null || formMetadata.video_end_time != null}
        <div class="flex items-center gap-2 mt-1 px-2 py-1 rounded-md bg-black/30 border border-white/5">
          <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" class="text-amber-400/50"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
          <span class="text-[9px] font-mono text-amber-300/70">
            Phát từ <strong>{formMetadata.video_start_time ?? 0}s</strong>
            {#if formMetadata.video_end_time}
              → kết thúc lúc <strong>{formMetadata.video_end_time}s</strong>
              &nbsp;(dài {((formMetadata.video_end_time ?? 0) - (formMetadata.video_start_time ?? 0)).toFixed(1)}s)
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
          bind:value={formMetadata.sync_loading_text}
          placeholder="Đang phân tích dữ liệu AI..."
          class="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-[11px] text-white focus:outline-none focus:border-amber-500/50 transition-colors"
        />
      </div>
      <div class="flex flex-col gap-1.5">
        <label class="text-[9px] font-bold text-white/40 uppercase tracking-wider">Tên Website (SEO)</label>
        <input
          type="text"
          bind:value={formMetadata.seo_site_name}
          placeholder="SmartShop.vn"
          class="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-[11px] text-white focus:outline-none focus:border-amber-500/50 transition-colors"
        />
      </div>
    </div>
  </div>

  <!-- ACTIVE DEALS (PROMOTIONS) -->
  <div class="flex flex-col gap-4 pt-6 border-t border-white/10">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2 text-[9px] font-black text-white/25 uppercase tracking-[0.25em]">
        <Tag size={11} class="text-sky-400/60" />
        Chương trình Khuyến mãi (Combo Deals)
      </div>
      <button 
        type="button"
        onclick={() => {
          if (!formMetadata.active_deals) formMetadata.active_deals = [];
          formMetadata.active_deals.push({ buy_qty: 2, get_qty: 1, fixed_price: 550000, label: 'Mua 2 Tặng 1', scope: 'global' });
        }}
        class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-sky-500/10 border border-sky-500/20 text-[9px] font-bold text-sky-400 hover:bg-sky-500/20 transition-all"
      >
        <Plus size={10} /> Thêm Deal mới
      </button>
    </div>

    <div class="space-y-3">
      {#if formMetadata.active_deals && formMetadata.active_deals.length > 0}
        {#each formMetadata.active_deals as deal, i}
          <div class="p-4 rounded-2xl bg-white/[0.02] border border-white/5 relative group/deal">
            <button 
              type="button"
              onclick={() => formMetadata.active_deals = formMetadata.active_deals.filter((_, idx) => idx !== i)}
              class="absolute top-3 right-3 p-1.5 rounded-md hover:bg-red-500/10 text-white/20 hover:text-red-400 transition-all opacity-0 group-hover/deal:opacity-100"
            >
              <Trash2 size={12} />
            </button>

            <div class="grid grid-cols-2 lg:grid-cols-5 gap-4">
              <div class="flex flex-col gap-1">
                <label class="text-[8px] font-bold text-white/30 uppercase">Số lượng Mua</label>
                <input type="number" bind:value={deal.buy_qty} class="bg-black/40 border border-white/5 rounded-md px-2 py-1.5 text-[10px] text-white" />
              </div>
              <div class="flex flex-col gap-1">
                <label class="text-[8px] font-bold text-white/30 uppercase">Số lượng Tặng</label>
                <input type="number" bind:value={deal.get_qty} class="bg-black/40 border border-white/5 rounded-md px-2 py-1.5 text-[10px] text-white" />
              </div>
              <div class="flex flex-col gap-1">
                <label class="text-[8px] font-bold text-white/30 uppercase">Giá trọn gói (VNĐ)</label>
                <input type="number" bind:value={deal.fixed_price} class="bg-black/40 border border-white/5 rounded-md px-2 py-1.5 text-[10px] text-sky-400 font-bold" />
              </div>
              <div class="flex flex-col gap-1 lg:col-span-1">
                <label class="text-[8px] font-bold text-white/30 uppercase">Phạm vi</label>
                <select bind:value={deal.scope} class="bg-black/40 border border-white/5 rounded-md px-2 py-1.5 text-[10px] text-white outline-none">
                  <option value="global">Toàn bộ (Global)</option>
                  <option value="variant_only">Chỉ biến thể này</option>
                </select>
              </div>
              <div class="flex flex-col gap-1 lg:col-span-1">
                <label class="text-[8px] font-bold text-white/30 uppercase">Nhãn (Label)</label>
                <input type="text" bind:value={deal.label} class="bg-black/40 border border-white/5 rounded-md px-2 py-1.5 text-[10px] text-white" placeholder="Mua 2 Tặng 1..." />
              </div>
            </div>
          </div>
        {/each}
      {:else}
        <div class="py-10 flex flex-col items-center justify-center gap-2 rounded-2xl border border-dashed border-white/10 text-white/20">
          <Tag size={20} class="opacity-50" />
          <span class="text-[9px] font-bold uppercase tracking-widest">Chưa có chương trình khuyến mãi nào</span>
        </div>
      {/if}
    </div>
  </div>
</div>

<style>
  @reference "tailwindcss";
</style>
