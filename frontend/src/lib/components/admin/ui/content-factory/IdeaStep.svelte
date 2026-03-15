<script lang="ts">
  import {
    Sparkles,
    MessageSquare,
    FileText
  } from "lucide-svelte";
  import { vuiController } from "$lib/vui";

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
  } = $props();
</script>

{#if isEditing}
  <div class="space-y-4">
    <div class="group/input">
      <label for="title-{campaign_id}" class="text-[10px] text-white/40 uppercase font-bold mb-1.5 ml-1 block">Tiêu đề bài viết</label>
      <div class="relative">
        <MessageSquare size={14} class="absolute left-3 top-1/2 -translate-y-1/2 text-white/20" />
        <input
          id="title-{campaign_id}"
          bind:value={editedKeywords.title}
          class="w-full bg-black/20 border border-white/10 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500/50 transition-all"
        />
      </div>
    </div>
    <div class="group/input">
      <label for="primary-{campaign_id}" class="text-[10px] text-white/40 uppercase font-bold mb-1.5 ml-1 block">Từ khóa chính</label>
      <div class="relative">
        <Sparkles size={14} class="absolute left-3 top-1/2 -translate-y-1/2 text-white/20" />
        <input
          id="primary-{campaign_id}"
          bind:value={editedKeywords.primary_keyword}
          class="w-full bg-black/20 border border-white/10 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500/50 transition-all"
        />
      </div>
    </div>
    <div class="group/input">
      <label class="text-[10px] text-white/40 uppercase font-bold mb-1.5 ml-1 block">Từ khóa phụ</label>
      <div class="flex flex-wrap gap-2 p-3 bg-black/20 border border-white/10 rounded-xl min-h-[44px]">
        {#each (editedKeywords?.secondary_keywords || []) as kw, kwIdx}
          <span class="flex items-center gap-1 px-2 py-1 rounded-full bg-white/10 border border-white/10 text-xs text-white/70">
            {kw}
            <button
              type="button"
              onclick={() => {
                const arr = [...(editedKeywords.secondary_keywords || [])];
                const removed = arr.splice(kwIdx, 1);
                editedKeywords.secondary_keywords = arr;
                vuiController.speak(`Đã xóa từ khóa ${removed}.`);
              }}
              class="ml-1 text-white/30 hover:text-red-400 transition-colors"
            >&times;</button>
          </span>
        {/each}
        <input
          placeholder="Thêm từ khóa + Enter"
          class="flex-1 min-w-[120px] bg-transparent text-xs text-white/60 placeholder-white/20 outline-none"
          onkeydown={(e) => {
            if ((e.key === 'Enter' || e.key === ',') && e.currentTarget.value.trim()) {
              e.preventDefault();
              const val = e.currentTarget.value.trim();
              const arr = [...(editedKeywords.secondary_keywords || []), val];
              editedKeywords.secondary_keywords = arr;
              vuiController.speak(`Đã thêm từ khóa ${val}.`);
              e.currentTarget.value = '';
            }
          }}
        />
      </div>
    </div>
    
    <div class="group/input">
      <label for="desc-{campaign_id}" class="text-[10px] text-white/40 uppercase font-bold mb-1.5 ml-1 block">Meta Description (SEO)</label>
      <div class="relative">
        <FileText size={14} class="absolute left-3 top-3 text-white/20" />
        <textarea
          id="desc-{campaign_id}"
          bind:value={editedKeywords.description}
          rows="3"
          class="w-full bg-black/20 border border-white/10 rounded-xl pl-10 pr-4 py-2 text-sm text-white focus:outline-none focus:border-blue-500/50 transition-all resize-none"
          placeholder="Nhập mô tả chuẩn SEO..."
        ></textarea>
      </div>
    </div>

    <div class="group/input">
      <label for="category-{campaign_id}" class="text-[10px] text-white/40 uppercase font-bold mb-1.5 ml-1 block">Danh mục (Category)</label>
      <div class="relative">
        <FileText size={14} class="absolute left-3 top-1/2 -translate-y-1/2 text-white/20" />
        <select
          id="category-{campaign_id}"
          bind:value={editedKeywords.category}
          class="w-full bg-black/20 border border-white/10 rounded-xl pl-10 pr-10 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500/50 transition-all appearance-none cursor-pointer"
        >
          <option value="Tin tức" class="bg-gray-900 text-white">Tin tức</option>
          <option value="Chính sách" class="bg-gray-900 text-white">Chính sách</option>
        </select>
        <div class="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-white/40">
          <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>
        </div>
      </div>
    </div>

    <!-- Phase 35: Creative Brief Configuration -->
    <div class="pt-4 mt-4 border-t border-white/5 space-y-4">
      <div class="hidden md:flex items-center gap-2 mb-2">
        <Sparkles size={12} class="text-blue-400" />
        <span class="text-[10px] font-black uppercase tracking-[0.2em] text-white/40">Cấu hình luồng sáng tạo</span>
      </div>

      <div class="grid grid-cols-2 gap-4">
        <div class="group/input">
          <label class="text-[10px] text-white/40 uppercase font-bold mb-1.5 ml-1 block">Phong cách (Style)</label>
          <select 
            bind:value={editedConfig.style}
            class="w-full bg-black/10 border border-white/5 rounded-xl px-4 py-2 text-xs text-white outline-none focus:border-blue-500/50 transition-all"
          >
            <option value="Chuyên nghiệp" class="bg-gray-900">Chuyên nghiệp</option>
            <option value="Sáng tạo" class="bg-gray-900">Sáng tạo</option>
            <option value="Viral" class="bg-gray-900">Viral</option>
            <option value="Hàn lâm" class="bg-gray-900">Hàn lâm</option>
          </select>
        </div>

        <div class="group/input">
          <label class="text-[10px] text-white/40 uppercase font-bold mb-1.5 ml-1 block">Hình ảnh (Tối đa)</label>
          <select 
            bind:value={editedConfig.max_assets}
            class="w-full bg-black/10 border border-white/5 rounded-xl px-4 py-2 text-xs text-white outline-none focus:border-blue-500/50 transition-all appearance-none cursor-pointer"
          >
            <option value={1} class="bg-gray-900">1 ảnh</option>
            <option value={2} class="bg-gray-900">2 ảnh</option>
            <option value={3} class="bg-gray-900">3 ảnh</option>
            <option value={5} class="bg-gray-900">5 ảnh (Khuyên dùng)</option>
            <option value={8} class="bg-gray-900">8 ảnh</option>
            <option value={10} class="bg-gray-900">10 ảnh (Max)</option>
          </select>
        </div>

        <div class="group/input">
          <label class="text-[10px] text-white/40 uppercase font-bold mb-1.5 ml-1 block">Độ dài (Số từ)</label>
          <select 
            bind:value={editedConfig.word_count}
            class="w-full bg-black/10 border border-white/5 rounded-xl px-4 py-2 text-xs text-white outline-none focus:border-blue-500/50 transition-all appearance-none cursor-pointer"
          >
            <option value={300} class="bg-gray-900">300 - 500 từ (Tin nhanh)</option>
            <option value={500} class="bg-gray-900">500 - 800 từ (Blog chuẩn)</option>
            <option value={800} class="bg-gray-900">800 - 1200 từ (Chuyên sâu)</option>
            <option value={1500} class="bg-gray-900">1500 - 2000+ từ (Pillar Page)</option>
          </select>
        </div>

        <div class="group/input">
          <label class="text-[10px] text-white/40 uppercase font-bold mb-1.5 ml-1 block">Mật độ đoạn (H2/H3)</label>
          <select 
            bind:value={editedConfig.max_sections}
            class="w-full bg-black/10 border border-white/5 rounded-xl px-4 py-2 text-xs text-white outline-none focus:border-blue-500/50 transition-all appearance-none cursor-pointer"
          >
            <option value={3} class="bg-gray-900">2 - 3 đoạn</option>
            <option value={5} class="bg-gray-900">3 - 5 đoạn (Dễ đọc)</option>
            <option value={8} class="bg-gray-900">5 - 8 đoạn</option>
            <option value={12} class="bg-gray-900">8 - 12+ đoạn (Chi tiết)</option>
          </select>
        </div>
      </div>
    </div>
  </div>
{:else}
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
{/if}
