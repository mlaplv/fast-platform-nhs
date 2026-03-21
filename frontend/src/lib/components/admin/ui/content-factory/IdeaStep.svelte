<script lang="ts">
  import {
    Sparkles,
    MessageSquare,
    FileText
  } from "lucide-svelte";
  import { onMount } from "svelte";
  import type { CampaignKeywords } from "$lib/state/types";
  import { createIdeaController } from "$lib/state/xohiIdea.svelte";

  interface Props {
    isEditing: boolean;
    campaign_id: string;
    keywords: CampaignKeywords;
    editedKeywords: CampaignKeywords;
    creation_config?: Record<string, unknown>;
    editedConfig: Record<string, unknown>;
    handleSelectKeyword: (kw: string) => void;
    handleUpdateMetadata: () => void | Promise<void>;
    isLoading: boolean;
  }

  let {
    isEditing = $bindable(),
    campaign_id,
    keywords = $bindable(),
    editedKeywords = $bindable(),
    creation_config = {},
    editedConfig = $bindable(),
    handleSelectKeyword,
    handleUpdateMetadata,
    isLoading
  }: Props = $props();

  const ctrl = createIdeaController({
    getKeywords: () => keywords,
    setKeywords: (v) => { keywords = v; },
    getEditedKeywords: () => editedKeywords,
    setEditedKeywords: (v) => { editedKeywords = v; },
    getEditedConfig: () => editedConfig,
    setEditedConfig: (v) => { editedConfig = v; },
    onSelectKeyword: handleSelectKeyword
  });

  onMount(() => {
    if (isEditing === undefined) isEditing = false;
    if (keywords === undefined) keywords = {} as CampaignKeywords;
    if (editedKeywords === undefined) editedKeywords = {} as CampaignKeywords;
    if (editedConfig === undefined) editedConfig = {};
  });
</script>

{#if isEditing}
  <div class="p-5 md:p-8 space-y-4 flex flex-col">
    <!-- Studio Label -->
    <div class="flex items-center gap-3 shrink-0">
      <div class="hidden md:block w-8 h-px bg-gradient-to-r from-transparent to-blue-500/50"></div>
      <h5 class="hidden md:block text-[11px] font-black uppercase tracking-[0.2em] text-blue-400/60">
        XOHI ·
        <span class="bg-gradient-to-r from-blue-400 via-cyan-300 to-blue-500 bg-clip-text text-transparent drop-shadow-[0_0_8px_rgba(99,179,237,0.6)]">NEURAL STUDIO</span>
      </h5>
    </div>
    <div class="space-y-4">
      <div class="group/input">
        <label for="title-{campaign_id}" class="text-[10px] text-blue-300 uppercase font-black tracking-widest mb-1.5 ml-1 block">Tiêu đề (Headline) 🚀</label>
        <div class="relative group/field">
          <div class="absolute inset-0 bg-blue-500/10 rounded-xl blur-md opacity-0 group-focus-within/field:opacity-100 transition-opacity"></div>
          <MessageSquare size={14} class="absolute left-3 top-1/2 -translate-y-1/2 text-blue-400/50 group-focus-within/field:text-blue-400 transition-colors" />
          <input
            id="title-{campaign_id}"
            bind:value={editedKeywords.title}
            class="w-full relative bg-[#0c0a0f]/80 backdrop-blur-xl border border-white/5 rounded-xl pl-10 pr-4 py-3 text-[13px] font-bold tracking-tight text-white placeholder-white/20 focus:outline-none focus:border-blue-500/50 focus:bg-white/[0.03] transition-all shadow-[inset_0_1px_rgba(255,255,255,0.05)]"
            placeholder="Nhập tiêu đề viral..."
          />
        </div>
      </div>

      <!-- Keyword Group: Primary & Secondary in one distinct card -->
      <div class="p-4 rounded-2xl bg-gradient-to-br from-white/[0.03] to-transparent border border-white/5 relative overflow-hidden space-y-4 shadow-[inset_0_1px_rgba(255,255,255,0.05)]">
        <div class="absolute top-0 right-0 w-32 h-32 bg-cyan-500/10 blur-[50px] pointer-events-none"></div>
        
        <div class="group/field relative z-10">
          <label for="primary-{campaign_id}" class="text-[10px] text-cyan-300 uppercase font-black tracking-widest mb-1.5 ml-1 flex items-center gap-1.5">
            <Sparkles size={12} class="animate-pulse" /> Từ khóa chính (Focus Keyword)
          </label>
          <div class="relative">
            <input
              id="primary-{campaign_id}"
              bind:value={editedKeywords.primary_keyword}
              class="w-full bg-[#0c0a0f]/80 backdrop-blur-xl border border-white/5 rounded-xl px-4 py-3 text-[13px] font-bold tracking-tight text-cyan-50 focus:outline-none focus:border-cyan-500/50 focus:bg-cyan-500/5 transition-all shadow-[inset_0_1px_rgba(255,255,255,0.05)]"
              placeholder="Ví dụ: cách làm giàu..."
            />
          </div>
        </div>
        <div class="group/field relative z-10">
          <label for="secondary-{campaign_id}" class="text-[10px] text-white/40 uppercase font-bold mb-1.5 ml-1 block">Từ khóa phụ (LSI / Semantic)</label>
          <div class="flex flex-wrap gap-2 p-3 bg-black/40 border border-white/5 rounded-xl min-h-[50px] shadow-[inset_0_2px_10px_rgba(0,0,0,0.5)]">
            {#each (editedKeywords?.secondary_keywords || []) as kw, kwIdx}
              <span class="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/5 border border-white/10 text-[11px] font-medium text-white/80 hover:bg-white/10 hover:border-white/20 transition-all">
                {kw}
                <button
                  type="button"
                  onclick={() => ctrl.removeSecondaryKeyword(kwIdx)}
                  class="ml-1 text-white/30 hover:text-red-400 transition-colors"
                ><svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg></button>
              </span>
            {/each}
            <input
              id="secondary-{campaign_id}"
              placeholder="Gõ từ khóa & Enter..."
              class="flex-1 min-w-[140px] bg-transparent text-[11px] font-medium text-white/80 placeholder-white/20 outline-none pl-2"
              onkeydown={ctrl.handleSecondaryKeydown}
            />
        </div>
      </div>
      
      </div>

      <div class="group/field">
        <label for="desc-{campaign_id}" class="text-[10px] text-green-300/80 uppercase font-black tracking-widest mb-1.5 ml-1 flex items-center gap-1">
          <FileText size={12} /> Meta Description (SEO)
        </label>
        <div class="relative">
          <textarea
            id="desc-{campaign_id}"
            bind:value={editedKeywords.description}
            rows="3"
            class="w-full bg-[#0c0a0f]/80 backdrop-blur-xl border border-white/5 rounded-xl p-4 text-[12px] leading-snug text-white focus:outline-none focus:border-green-500/30 focus:bg-green-500/5 transition-all resize-none shadow-[inset_0_1px_rgba(255,255,255,0.05)]"
            placeholder="Tóm tắt nội dung hấp dẫn để tăng CTR..."
          ></textarea>
        </div>
      </div>

      <div class="group/field">
        <label for="category-{campaign_id}" class="text-[10px] text-fuchsia-300/80 uppercase font-black tracking-widest mb-1.5 ml-1 block">Danh mục (Category/Phễu)</label>
        <div class="relative">
          <select
            id="category-{campaign_id}"
            bind:value={editedKeywords.category}
            class="w-full bg-[#0c0a0f]/80 backdrop-blur-xl border border-white/5 rounded-xl px-4 py-3 text-[12px] font-bold text-white focus:outline-none focus:border-fuchsia-500/50 focus:bg-fuchsia-500/5 transition-all appearance-none cursor-pointer shadow-[inset_0_1px_rgba(255,255,255,0.05)]"
          >
            <option value="Tin tức" class="bg-gray-900 text-white font-medium">1. Tin tức / Cập nhật mảng</option>
            <option value="Chính sách" class="bg-gray-900 text-white font-medium">2. Chính sách / Quy định</option>
            <option value="Kiến thức" class="bg-gray-900 text-white font-medium">3. Kiến thức chuyên sâu (Pillar)</option>
            <option value="Viral" class="bg-gray-900 text-white font-medium">4. Giải trí / Viral Content</option>
          </select>
          <div class="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-white/40">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>
          </div>
        </div>
      </div>

      <!-- Phase 35: Creative Brief Configuration (Viral Style) -->
      <div class="pt-6 mt-6 border-t border-white/5 space-y-4">
        <div class="hidden md:flex items-center gap-2 mb-4">
          <div class="w-6 h-6 rounded-full bg-blue-500/20 flex items-center justify-center border border-blue-500/30">
            <Sparkles size={12} class="text-blue-400" />
          </div>
          <span class="text-[11px] font-black uppercase tracking-[0.2em] text-white/80 bg-gradient-to-r from-blue-300 to-cyan-300 bg-clip-text text-transparent">Cấu hình luồng AI Creative</span>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div class="group/field">
            <label for="style-{campaign_id}" class="text-[9px] text-white/40 uppercase font-black tracking-widest mb-1.5 ml-1 block">Phong cách (Voice)</label>
            <div class="relative">
              <select 
                id="style-{campaign_id}"
                bind:value={editedConfig.style}
                class="w-full bg-[#0c0a0f]/80 backdrop-blur-xl border border-white/5 rounded-xl px-4 py-2.5 text-[11px] font-bold text-white outline-none focus:border-blue-500/50 transition-all appearance-none shadow-[inset_0_1px_rgba(255,255,255,0.05)]"
              >
                <option value="Chuyên nghiệp" class="bg-gray-900">Chuyên nghiệp (Báo chí)</option>
                <option value="Sáng tạo" class="bg-gray-900">Sáng tạo (Blog/Tâm sự)</option>
                <option value="Viral" class="bg-gray-900">Phong cách Viral (Tik/X/Threads)</option>
                <option value="Hàn lâm" class="bg-gray-900">Hàn lâm (Khoa học)</option>
              </select>
              <div class="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-white/30"><svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg></div>
            </div>
          </div>

          <div class="group/field">
            <label for="assets-{campaign_id}" class="text-[9px] text-white/40 uppercase font-black tracking-widest mb-1.5 ml-1 block">Hình ảnh (Max)</label>
            <div class="relative">
              <select 
                id="assets-{campaign_id}"
                bind:value={editedConfig.max_assets}
                class="w-full bg-[#0c0a0f]/80 backdrop-blur-xl border border-white/5 rounded-xl px-4 py-2.5 text-[11px] font-bold text-white outline-none focus:border-blue-500/50 transition-all appearance-none cursor-pointer shadow-[inset_0_1px_rgba(255,255,255,0.05)]"
              >
                <option value={1} class="bg-gray-900">1 ảnh (Thumbnail)</option>
                <option value={3} class="bg-gray-900">3 ảnh (Vừa)</option>
                <option value={5} class="bg-gray-900">5 ảnh (Standard)</option>
                <option value={10} class="bg-gray-900">10 ảnh (Max Limit)</option>
              </select>
              <div class="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-white/30"><svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg></div>
            </div>
          </div>

          <div class="group/field">
            <label for="words-{campaign_id}" class="text-[9px] text-white/40 uppercase font-black tracking-widest mb-1.5 ml-1 block">Độ dài chữ</label>
            <div class="relative">
              <select 
                id="words-{campaign_id}"
                bind:value={editedConfig.word_count}
                class="w-full bg-[#0c0a0f]/80 backdrop-blur-xl border border-white/5 rounded-xl px-4 py-2.5 text-[11px] font-bold text-white outline-none focus:border-blue-500/50 transition-all appearance-none cursor-pointer shadow-[inset_0_1px_rgba(255,255,255,0.05)]"
              >
                <option value={300} class="bg-gray-900">300 (Tin nhanh)</option>
                <option value={500} class="bg-gray-900">500 (Phổ thông)</option>
                <option value={800} class="bg-gray-900">800 (Bài sâu)</option>
                <option value={1500} class="bg-gray-900">1500+ (Pillar)</option>
              </select>
              <div class="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-white/30"><svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg></div>
            </div>
          </div>

          <div class="group/field">
            <label for="sections-{campaign_id}" class="text-[9px] text-white/40 uppercase font-black tracking-widest mb-1.5 ml-1 block">Mật độ thẻ (H2/H3)</label>
            <div class="relative">
              <select 
                id="sections-{campaign_id}"
                bind:value={editedConfig.max_sections}
                class="w-full bg-[#0c0a0f]/80 backdrop-blur-xl border border-white/5 rounded-xl px-4 py-2.5 text-[11px] font-bold text-white outline-none focus:border-blue-500/50 transition-all appearance-none cursor-pointer shadow-[inset_0_1px_rgba(255,255,255,0.05)]"
              >
                <option value={3} class="bg-gray-900">2 - 3 Thẻ H2</option>
                <option value={5} class="bg-gray-900">3 - 5 Thẻ H2</option>
                <option value={8} class="bg-gray-900">5 - 8 Thẻ H2</option>
                <option value={12} class="bg-gray-900">8 - 12 Thẻ H2 (Lớn)</option>
              </select>
              <div class="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-white/30"><svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
{:else}
  <div class="p-5 md:p-8 space-y-4 flex flex-col">
    <!-- Studio Label -->
    <div class="flex items-center gap-3 shrink-0">
      <div class="hidden md:block w-8 h-px bg-gradient-to-r from-transparent to-blue-500/50"></div>
      <h5 class="hidden md:block text-[11px] font-black uppercase tracking-[0.2em] text-blue-400/60">
        XOHI ·
        <span class="bg-gradient-to-r from-blue-400 via-cyan-300 to-blue-500 bg-clip-text text-transparent drop-shadow-[0_0_8px_rgba(99,179,237,0.6)]">NEURAL STUDIO</span>
      </h5>
    </div>
    <div class="space-y-2">
      <h4 class="text-lg font-bold text-white leading-snug tracking-tight">
        {keywords.title || 'Đang phân tích tiêu đề...'}
      </h4>
      <p class="text-[11px] text-white/40 font-medium uppercase tracking-wider">Style: 
        <span class="text-white/70 italic">{keywords.persona || 'Chuyên gia phân tích'}</span>
        <span class="mx-2 opacity-30">|</span> Category:
        <span class="text-white/70 italic">{keywords.category || 'Uncategorized'}</span>
      </p>
    </div>
    <div class="flex flex-wrap gap-2">
      {#if keywords.primary_keyword}
        <button 
          class="px-3 py-1 rounded-full bg-blue-500/20 text-blue-300 text-[11px] font-bold border border-blue-500/30 hover:bg-blue-500/30 transition-all shadow-lg shadow-blue-500/5 cursor-default"
          title="Từ khóa chính hiện tại"
        >
          {keywords.primary_keyword}
        </button>
      {:else}
        <span class="px-3 py-1 rounded-full bg-white/5 text-white/20 text-[11px] font-medium border border-white/5 animate-pulse">
          Đang chờ từ khóa...
        </span>
      {/if}
      
      {#each (keywords?.secondary_keywords || []) as kw}
        <button 
          onclick={() => handleSelectKeyword(kw)}
          class="px-3 py-1 rounded-full bg-white/5 text-white/40 text-[11px] font-medium border border-white/5 hover:border-blue-500/30 hover:text-blue-400/80 transition-all active:scale-95"
          title="Click để chọn làm Từ khóa chính"
        >
          {kw}
        </button>
      {/each}
    </div>

    {#if keywords.description}
      <div class="p-3 rounded-xl bg-white/[0.03] border border-white/5 relative group/desc">
        <div class="flex items-center gap-2 mb-1 text-white/30 group-hover/desc:text-blue-400 transition-colors">
          <FileText size={10} />
          <span class="text-[9px] font-black uppercase tracking-widest">SEO Meta Description</span>
        </div>
        <p class="text-[11px] text-white/60 leading-relaxed italic line-clamp-2">
          "{keywords.description}"
        </p>
      </div>
    {/if}
  </div>
{/if}
