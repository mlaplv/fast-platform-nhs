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
