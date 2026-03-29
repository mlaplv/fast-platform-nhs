<script lang="ts">
  import { onMount } from "svelte";
  import Layout from "lucide-svelte/icons/layout";
  import Zap from "lucide-svelte/icons/zap";
  import MessageSquare from "lucide-svelte/icons/message-square";
  import Microscope from "lucide-svelte/icons/microscope";
  import HelpCircle from "lucide-svelte/icons/help-circle";
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
          onclick={() => formMetadata.landing_type = type.value as any}
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

    <!-- Order Bump Price (Always visible) -->
    <div class="flex flex-col gap-1.5">
      <label class="text-[9px] font-bold text-white/40 uppercase tracking-wider">Giá Order Bump (VNĐ)</label>
      <input
        type="number"
        bind:value={formMetadata.order_bump_price}
        placeholder="99000"
        class="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-[11px] text-white focus:outline-none focus:border-amber-500/50 transition-colors"
      />
    </div>

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

    <!-- Video URL (Stealth/TikTok) -->
    {#if formMetadata.landing_type !== 'standard'}
      <div class="flex flex-col gap-1.5 md:col-span-2">
        <label class="text-[9px] font-bold text-white/40 uppercase tracking-wider">Video URL (TikTok/YouTube)</label>
        <input
          type="text"
          bind:value={formMetadata.video_url}
          placeholder="https://..."
          class="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-[11px] text-white focus:outline-none focus:border-amber-500/50 transition-colors"
        />
      </div>
    {/if}
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

  <!-- Advanced Sections (Expandable or Tabs?) -->
  <!-- For now, just render the main headlines to keep it lean as requested -->
  <div class="flex flex-col gap-4 pt-4 border-t border-white/5">
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <!-- Reviews Header -->
      <div class="flex flex-col gap-3 p-4 rounded-2xl bg-white/[0.01] border border-white/5">
        <div class="flex items-center gap-2 text-[8px] font-black text-white/20 uppercase">
          <MessageSquare size={10} /> Đánh giá (Reviews)
        </div>
        <input
          type="text"
          bind:value={formMetadata.reviews_headline}
          placeholder="Khách hàng nói gì về chúng tôi"
          class="w-full bg-transparent border-b border-white/10 py-1 text-[10px] text-white focus:outline-none focus:border-amber-500"
        />
      </div>

      <!-- Science Header -->
      <div class="flex flex-col gap-3 p-4 rounded-2xl bg-white/[0.01] border border-white/5">
        <div class="flex items-center gap-2 text-[8px] font-black text-white/20 uppercase">
          <Microscope size={10} /> Khoa học (Science)
        </div>
        <input
          type="text"
          bind:value={formMetadata.science_headline}
          placeholder="Tại sao nó hiệu quả?"
          class="w-full bg-transparent border-b border-white/10 py-1 text-[10px] text-white focus:outline-none focus:border-amber-500"
        />
      </div>

      <!-- Diagnostics Header -->
      <div class="flex flex-col gap-3 p-4 rounded-2xl bg-white/[0.01] border border-white/5">
        <div class="flex items-center gap-2 text-[8px] font-black text-white/20 uppercase">
          <HelpCircle size={10} /> Chẩn đoán (Diagnostics)
        </div>
        <input
          type="text"
          bind:value={formMetadata.diagnostics_headline}
          placeholder="Lựa chọn dành cho bạn"
          class="w-full bg-transparent border-b border-white/10 py-1 text-[10px] text-white focus:outline-none focus:border-amber-500"
        />
      </div>
    </div>
  </div>
</div>

<style>
  @reference "tailwindcss";
</style>
