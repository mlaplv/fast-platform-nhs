<script lang="ts">
    import Sparkles from "@lucide/svelte/icons/sparkles";
  import MessageSquare from "@lucide/svelte/icons/message-square";
  import FileText from "@lucide/svelte/icons/file-text";
  import Search from "@lucide/svelte/icons/search";
  import ShieldCheck from "@lucide/svelte/icons/shield-check";
  import ShieldAlert from "@lucide/svelte/icons/shield-alert";
  import Globe from "@lucide/svelte/icons/globe";
  import TrendingUp from "@lucide/svelte/icons/trending-up";
  import CalendarIcon from "@lucide/svelte/icons/calendar";
  import ChevronRight from "@lucide/svelte/icons/chevron-right";
  import Zap from "@lucide/svelte/icons/zap";
  import { onMount } from "svelte";
  import ChevronDown from "@lucide/svelte/icons/chevron-down";
  import type { CampaignKeywords } from "$lib/state/types";
  import { createIdeaController } from "$lib/state/xohiIdea.svelte";
  import { useNanobot } from "$lib/state/nanobot.svelte";
  const nanobot = useNanobot();
  import { apiClient } from "$lib/utils/apiClient";
  import NeuralScheduler from "./NeuralScheduler.svelte";

  interface Props {
    isEditing: boolean;
    campaign_id: string;
    keywords: CampaignKeywords;
    editedKeywords: CampaignKeywords;
    creation_config?: Record<string, unknown>;
    editedConfig: Record<string, unknown>;
    handleSelectKeyword: (kw: string) => void;
    handleUpdateMetadata: () => void | Promise<void>;
    handleSyncMetadata?: () => void | Promise<void>;
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
    handleSyncMetadata,
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
    if (!editedConfig) editedConfig = { style: "Viral" };
    if (!editedConfig.style) editedConfig.style = "Viral";

    // CNS V62.2: Restore Scout Report from persisted campaign state
    if (editedKeywords?.scout_report) {
      scoutReport = editedKeywords.scout_report;
      if (editedConfig && !editedConfig.scouting_active) {
        editedConfig.scouting_active = true;
      }
    }

    // CNS V82.2: Elite Restore - Force Autopilot ON if valid schedule exists
    if (!editedConfig.scheduling && editedKeywords?.scheduling) {
      editedConfig.scheduling = editedKeywords.scheduling;
    }
    
    if (editedConfig?.scheduling) {
      interface Scheduling { is_active: boolean; frequency: string; schedule_at: string; }
      const s = editedConfig.scheduling as unknown as Scheduling;
      if (s.frequency && s.schedule_at && !s.is_active) {
        s.is_active = true; // Auto-ON as requested: "auto on khi có lịch"
      }
    }

    // Phase 102.2: Fetch DB Categories for Product Connection
    fetchCategories();
  });

  let dbCategories = $state<{id: string, name: string, depth: int}[]>([]);
  async function fetchCategories() {
    try {
      const res = await apiClient.get('/api/v1/categories?limit=500'); // Higher limit for deep trees
      // CNS V86.5: Recursive Flattening (Phase 102.3 Elite Hierarchy)
      if (res && res.data) {
        const flattened: {id: string, name: string, depth: number}[] = [];
        const process = (cats: {id: string, name: string, children?: any[]}[], depth = 0) => {
          cats.forEach(c => {
            flattened.push({ id: c.id, name: c.name, depth });
            if (c.children && c.children.length > 0) {
              process(c.children, depth + 1);
            }
          });
        };
        process(res.data);
        dbCategories = flattened;
      }
    } catch (e) {
      console.error("[IdeaStep] Failed to fetch/flatten categories", e);
    }
  }

  // CNS V62.2: Scout Intelligence State
  let isScouting = $state(false);
  let scoutReport = $state<ScoutReport | null>(null);

  async function performScout(e?: MouseEvent) {
    if (e) e.stopPropagation();
    
    // CNS V62.4: Atomic Recon Logic - Unified topic selection
    const targetTopic = editedKeywords.primary_keyword || keywords.primary_keyword || editedKeywords.title || keywords.title;

    if (!targetTopic) {
      nanobot.showToast("Dạ Sếp, em cần Từ khóa chính hoặc Tiêu đề để bắt đầu trinh sát ạ!", "warning");
      return;
    }

    // Auto-sync back to edited view for UX consistency
    if (!editedKeywords.primary_keyword) editedKeywords.primary_keyword = targetTopic;

    const startTime = Date.now();
    isScouting = true;
    try {
      // CNS V62.4: Atomic Sync - Backend will persist result to campaign.topic_data["scout_report"]
      const res = await apiClient.post('/api/v1/content/scout', { 
        topic: targetTopic,
        campaign_id: campaign_id 
      });

      if (res.status === 'success') {
        scoutReport = res.data;
        // Sync local state for immediate UI update without F5
        if (editedKeywords) editedKeywords.scout_report = res.data;
        
        // Elite UX: Ensure perception of depth (1.5s neural shimmer)
        const elapsed = Date.now() - startTime;
        if (elapsed < 1500) await new Promise(r => setTimeout(r, 1500 - elapsed));
        
        nanobot.showToast("Báo cáo trinh sát Neural đã được 'Elite' hóa và lưu trữ vĩnh viễn.", "success");
      } else {
        nanobot.showToast("Lỗi trinh sát: " + res.message, "error");
      }
    } catch (e) {
      console.error(e);
      nanobot.showToast("Hệ thống trinh sát gặp sự cố kỹ thuật.", "error");
    } finally {
      isScouting = false;
    }
  }

  // Elite UX: Enforce mandatory writing style default
  $effect(() => {
    if (isEditing && !editedConfig?.style) {
      editedConfig.style = "Viral";
    }
  });

  // CNS V82.8: Elite Context Continuity - Primary Source of Truth: category field
  $effect(() => {
    const cat = editedKeywords?.category;
    if (cat === "Sản phẩm") {
      editedConfig.target_entity = "product";
      editedConfig.style = "Chuyên nghiệp";
    } else if (cat === "Bài viết" || cat === "Chính sách") {
      editedConfig.target_entity = "article";
    }
  });

  // CNS V82.5: Neural Intent Decoding (Prefix-to-Category Snap)
  $effect(() => {
    const title = editedKeywords?.title || "";
    if (title.toLowerCase().startsWith("viết bài:") || title.toLowerCase().startsWith("viết bài ")) {
      editedKeywords.category = "Bài viết";
      // Clean up title for neural processing
      const cleanTitle = title.replace(/^(viết bài:?\s*)/i, "");
      if (cleanTitle && cleanTitle !== title) editedKeywords.title = cleanTitle;
      nanobot.showToast("Dạ Sếp, em đã bẻ lái sang dây chuyền Bài viết ạ!", "info");
    } else if (title.toLowerCase().startsWith("tạo sản phẩm:") || title.toLowerCase().startsWith("tạo sản phẩm ")) {
      editedKeywords.category = "Sản phẩm";
      const cleanTitle = title.replace(/^(tạo sản phẩm:?\s*)/i, "");
      if (cleanTitle && cleanTitle !== title) editedKeywords.title = cleanTitle;
      nanobot.showToast("Dạ Sếp, em đã bẻ lái sang dây chuyền SẢN PHẨM ạ!", "success");
    }
  });

  // CNS V62.3: Restore Scout Report Reactively (if editedKeywords changes externally)
  $effect(() => {
    if (editedKeywords?.scout_report && !scoutReport) {
      scoutReport = editedKeywords.scout_report;
      // CNS V62.5: Force expand if new report arrived and section is hidden
      if (editedConfig && !editedConfig.scouting_active) {
        editedConfig.scouting_active = true;
      }
    }
  });
</script>

{#if isEditing}
  <div class="p-5 md:p-8 space-y-4 flex flex-col">
    <!-- Studio Label -->
    <div class="flex items-center gap-3 shrink-0">
      <div class="hidden md:block w-8 h-px bg-gradient-to-r from-transparent to-blue-500/50"></div>
      <h5 class="hidden md:block text-[11px] font-black uppercase tracking-[0.2em] text-blue-400/60">
        NEURAL XOHI ·
        <span class="bg-gradient-to-r from-blue-400 via-cyan-300 to-blue-500 bg-clip-text text-transparent drop-shadow-[0_0_8px_rgba(99,179,237,0.6)]">STUDIO</span>
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
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
                </button>
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

      <!-- Elite AI-Context Category Selector (No-Manual-Tab Edition) -->
      <div class="p-6 rounded-[2rem] bg-gradient-to-br from-white/[0.03] to-transparent border border-white/10 space-y-4 shadow-2xl relative overflow-hidden">
        <div class="absolute top-0 right-0 w-24 h-24 bg-fuchsia-500/5 blur-[40px] pointer-events-none"></div>
        
        <div class="flex items-center justify-between px-1">
          <label for="elite-category-{campaign_id}" class="text-[11px] font-black uppercase tracking-[0.2em] text-fuchsia-300 flex items-center gap-2">
            {#if editedConfig.target_entity === 'product'}
              <Globe size={14} class="text-amber-400" /> Danh mục sản phẩm
            {:else}
              <Zap size={14} class="text-fuchsia-400" /> Danh mục Bài viết
            {/if}
          </label>
          
          <button 
            type="button"
            onclick={() => editedConfig.target_entity = editedConfig.target_entity === 'product' ? 'article' : 'product'}
            class="text-[8px] font-black px-2 py-0.5 rounded-full bg-white/5 border border-white/10 text-white/40 uppercase tracking-tighter hover:bg-white/10 hover:text-white transition-all"
          >
            Chuyển sang: {editedConfig.target_entity === 'product' ? 'Bài viết' : 'Hàng hóa'}
          </button>
        </div>
        
        <div class="relative group/field z-10">
          <select
            id="elite-category-{campaign_id}"
            class="w-full bg-[#0d0b14] border border-white/10 rounded-2xl px-5 py-4 text-[15px] font-black text-white focus:outline-none focus:border-white/30 transition-all appearance-none cursor-pointer shadow-2xl ring-1 ring-white/5 hover:border-white/20"
            onchange={(e) => {
              const val = e.currentTarget.value;
              const isDb = dbCategories.some(c => c.id === val);
              if (isDb) {
                editedKeywords.category = 'Sản phẩm';
                editedKeywords.category_id = val;
              } else {
                editedKeywords.category = val;
                editedKeywords.category_id = null;
              }
            }}
            value={editedKeywords.category_id || editedKeywords.category}
          >
            <option value="" disabled class="bg-gray-900 text-white/30">-- Vui lòng chọn danh mục phù hợp --</option>
            
            {#if editedConfig.target_entity === 'product'}
              <!-- MODE: HÀNG HÓA - Chỉ hiện danh mục DB (Flat Hierarchy) -->
              {#each dbCategories as cat}
                <option value={cat.id} class="bg-gray-900 text-white py-3">
                  {@html "&nbsp;".repeat(cat.depth * 4)}
                  {cat.depth > 0 ? "└─ " : ""}💎 {cat.name}
                </option>
              {/each}
              {#if dbCategories.length === 0}
                <option disabled class="bg-gray-900 text-red-400 italic">⚠️ Không tìm thấy danh mục DB!</option>
              {/if}
            {:else}
              <!-- MODE: BÀI VIẾT - Chỉ hiện danh mục hệ thống (Enum) -->
              <option value="Bài viết" class="bg-gray-900 text-white py-3">1. Bài viết / Cập nhật mảng</option>
              <option value="Chính sách" class="bg-gray-900 text-white py-3">2. Chính sách / Quy định</option>
            {/if}
          </select>
          <div class="absolute right-5 top-1/2 -translate-y-1/2 pointer-events-none text-white/20 group-hover/field:text-fuchsia-400 transition-colors">
            <ChevronDown size={22} />
          </div>
        </div>

        {#if (editedConfig.target_entity === 'product' && !editedKeywords.category_id) || (!editedConfig.target_entity && !editedKeywords.category)}
           <div class="bg-fuchsia-500/10 p-3 rounded-xl border border-fuchsia-500/20 flex items-center gap-3">
             <ShieldAlert size={16} class="text-fuchsia-400 shrink-0" />
             <p class="text-[11px] text-fuchsia-100 font-bold leading-tight">
               Sếp ơi, hãy chọn một **Danh mục mục tiêu** để bắt đầu nhé!
             </p>
           </div>
        {/if}
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
                {#if editedConfig.target_entity === 'product'}
                  <option value="Chuyên nghiệp" class="bg-gray-900">Mô tả bán hàng (Chuyên nghiệp)</option>
                  <option value="Sáng tạo" class="bg-gray-900">Review trải nghiệm (Sáng tạo)</option>
                  <option value="Viral" class="bg-gray-900">Viral Marketing (Kích cầu)</option>
                  <option value="Hàn lâm" class="bg-gray-900">Thông số kỹ thuật (Chi tiết)</option>
                {:else}
                  <option value="Chuyên nghiệp" class="bg-gray-900">Chuyên nghiệp (Báo chí)</option>
                  <option value="Sáng tạo" class="bg-gray-900">Sáng tạo (Blog/Tâm sự)</option>
                  <option value="Viral" class="bg-gray-900">Phong cách Viral (Tik/X/Threads)</option>
                  <option value="Hàn lâm" class="bg-gray-900">Hàn lâm (Khoa học)</option>
                {/if}
 Sandra: 100% dynamic UX
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
      <div class="pt-8 mt-8 border-t border-white/5 space-y-8">
        
        <!-- Research Intelligence Section (Neural Scout) - NOW PRIMARY -->
        <div class="p-8 rounded-[2.5rem] bg-gradient-to-br from-indigo-500/5 to-transparent border border-indigo-500/10 relative overflow-hidden group/intel">
          <div class="absolute -bottom-20 -right-20 w-64 h-64 bg-indigo-500/10 blur-[80px] rounded-full group-hover/intel:bg-indigo-400/20 transition-all duration-1000"></div>
          
          <div class="flex items-center justify-between relative z-10 mb-8">
            <div class="flex items-center gap-4">
              <div class="w-12 h-12 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center text-indigo-400 shadow-xl shadow-indigo-500/5">
                <Search size={22} strokeWidth={1.5} />
              </div>
              <div>
                <h4 class="text-sm font-black uppercase tracking-[0.2em] text-white">Neural Content Scout</h4>
                <p class="text-[10px] text-indigo-300/40 font-bold uppercase tracking-widest">Trinh sát nội dung & Gợi ý từ đối thủ</p>
              </div>
            </div>

            <button 
              onclick={(e) => { 
                if (!editedConfig.scouting_active) {
                  editedConfig.scouting_active = true;
                  performScout(e);
                } else {
                  editedConfig.scouting_active = false;
                }
              }}
              disabled={isScouting}
              class="px-6 py-2.5 rounded-full text-[10px] font-black uppercase tracking-widest transition-all duration-500 {editedConfig.scouting_active ? 'bg-indigo-500 text-white shadow-xl shadow-indigo-500/20' : 'bg-white/5 text-white/40 border border-white/10 hover:text-white hover:bg-white/10'} {isScouting ? 'animate-pulse cursor-wait' : ''}"
            >
              {#if isScouting}
                Đang trinh sát...
              {:else}
                {editedConfig.scouting_active ? 'Hủy Trinh sát' : 'Kích hoạt Scout Engine'}
              {/if}
            </button>
          </div>

          {#if editedConfig.scouting_active}
            <div class="space-y-8 animate-in fade-in slide-in-from-top-4 duration-1000 relative z-10">
              
              <!-- CNS V62.2: Strategic Intelligence Result (Deep Analysis) -->
              {#if scoutReport?.strategic_analysis}
                <div class="p-8 rounded-[2.5rem] bg-indigo-500/10 border border-indigo-500/20 shadow-2xl relative overflow-hidden group/strat">
                  <div class="absolute top-0 right-0 p-4">
                    <div class="w-8 h-8 rounded-full bg-indigo-500/20 flex items-center justify-center text-indigo-400 animate-pulse">
                      <Zap size={16} />
                    </div>
                  </div>
                  <h5 class="text-[11px] font-black text-indigo-400 uppercase tracking-[0.2em] mb-4 flex items-center gap-2">
                    <ShieldCheck size={14} /> Trình báo Chiến lược AI (Elite Strategy)
                  </h5>
                  <div class="prose prose-invert prose-sm max-w-none text-white/80 leading-relaxed font-medium text-[13px] whitespace-pre-wrap selection:bg-indigo-500/30">
                    {scoutReport.strategic_analysis}
                  </div>
                  
                  {#if scoutReport.ground_truth_summary}
                    <div class="mt-6 pt-6 border-t border-indigo-500/10">
                      <p class="text-[10px] text-indigo-300/40 font-bold uppercase tracking-widest leading-loose">
                        <span class="text-indigo-400">Ground Truth:</span> {scoutReport.ground_truth_summary}
                      </p>
                    </div>
                  {/if}
                </div>
              {:else if isScouting}
                <!-- Shimmer Loading for Strategy -->
                <div class="p-8 rounded-[2.5rem] bg-white/5 border border-white/10 animate-pulse">
                  <div class="h-4 w-48 bg-white/10 rounded-full mb-6"></div>
                  <div class="space-y-3">
                    <div class="h-3 w-full bg-white/5 rounded-full"></div>
                    <div class="h-3 w-5/6 bg-white/5 rounded-full"></div>
                    <div class="h-3 w-4/6 bg-white/5 rounded-full"></div>
                  </div>
                </div>
              {/if}

              <div class="flex flex-col md:flex-row gap-6">
                <!-- Headlines Suggestions -->
                <div class="flex-1 p-6 rounded-3xl bg-black/40 border border-white/5 shadow-inner">
                  <div class="flex items-center justify-between mb-4">
                    <span class="text-[10px] font-black text-white/40 uppercase tracking-widest flex items-center gap-2"><TrendingUp size={12} /> Gợi ý tiêu đề (ADS & TOP 10)</span>
                    <button 
                      onclick={performScout}
                      disabled={isScouting}
                      class="text-[9px] font-black text-indigo-400 hover:underline uppercase tracking-tighter disabled:opacity-50"
                    >
                      {isScouting ? 'Scanning...' : 'Manual Scan'}
                    </button>
                  </div>
                  <div class="space-y-3">
                    {#if scoutReport?.headlines}
                      {#each scoutReport.headlines as suggestion}
                        <button 
                          onclick={() => editedKeywords.title = suggestion.title}
                          class="w-full text-left p-3 rounded-2xl bg-white/[0.03] border border-white/5 hover:bg-indigo-500/10 hover:border-indigo-500/30 transition-all group/h"
                        >
                          <div class="flex items-center justify-between mb-1">
                            <span class="text-[8px] font-black uppercase tracking-tighter {suggestion.type === 'ADS' ? 'text-orange-400' : suggestion.type === 'TOP_10' ? 'text-green-400' : 'text-indigo-400'}">
                              {suggestion.type}
                            </span>
                          </div>
                          <p class="text-[11px] text-white/70 group-hover/h:text-white line-clamp-2">{suggestion.title}</p>
                        </button>
                      {/each}
                    {:else}
                      {#each Array(3) as _}
                        <div class="w-full h-16 rounded-2xl bg-white/5 animate-pulse"></div>
                      {/each}
                    {/if}
                  </div>
                </div>

                <!-- LSI Keywords -->
                <div class="flex-1 p-6 rounded-3xl bg-black/40 border border-white/5 shadow-inner">
                  <div class="flex items-center justify-between mb-4">
                    <span class="text-[10px] font-black text-white/40 uppercase tracking-widest flex items-center gap-2"><Globe size={12} /> Từ khóa Semantic (LSI)</span>
                  </div>
                  <div class="flex flex-wrap gap-2">
                    {#if scoutReport?.semantic_keywords}
                      {#each scoutReport.semantic_keywords as lsi}
                        <button 
                          onclick={() => {
                            if (!(editedKeywords.secondary_keywords || []).includes(lsi)) {
                              editedKeywords.secondary_keywords = [...(editedKeywords.secondary_keywords || []), lsi];
                            }
                          }}
                          class="px-2.5 py-1.5 rounded-lg bg-indigo-400/5 border border-indigo-400/20 text-[10px] text-indigo-400 font-bold hover:bg-indigo-400/20 transition-all uppercase tracking-tighter"
                        >
                          + {lsi}
                        </button>
                      {/each}
                    {:else}
                      {#each Array(8) as _}
                        <div class="w-20 h-6 rounded-lg bg-white/5 animate-pulse"></div>
                      {/each}
                    {/if}
                  </div>
                </div>
              </div>

              <!-- Scout Logs -->
              {#if scoutReport?.logs || isScouting}
                <div class="p-6 rounded-3xl bg-black/60 border border-white/5 font-mono text-[9px] text-white/30 space-y-1 max-h-32 overflow-y-auto">
                  {#each (scoutReport?.logs || ["🕵️ Hệ thống đang khởi động..."]) as log}
                    <div class="flex gap-2">
                      <span class="text-indigo-500/50">›</span>
                      <span>{log}</span>
                    </div>
                  {/each}
                  {#if isScouting}
                    <div class="flex gap-2 animate-pulse">
                      <span class="text-indigo-500/50">›</span>
                      <span>Đang trích xuất dữ liệu thực thể...</span>
                    </div>
                  {/if}
                </div>
              {/if}
            </div>
          {/if}
        </div>

        <!-- Secondary: Post Scheduling -->
         <div class="p-8 rounded-[2.5rem] bg-gradient-to-br from-white/[0.01] to-transparent border border-white/5">
            <NeuralScheduler 
              bind:config={editedConfig} 
              onSync={() => {
                if (handleSyncMetadata) {
                  handleSyncMetadata();
                } else {
                  handleUpdateMetadata();
                }
                // CNS V82.3: Ensure we check the current state after sync trigger
                interface Scheduling { is_active: boolean; frequency: string; schedule_at: string; }
                const sch = editedConfig.scheduling as unknown as Scheduling;
                if (sch?.is_active) {
                  nanobot.showToast(`Autopilot Elite: Đã lên lịch thực thi lúc ${sch.schedule_at} (${sch.frequency})`, "success");
                } else {
                  nanobot.showToast("Autopilot đã chuyển sang chế độ Standby.", "info");
                }
              }} 
            />
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
        NEURAL XOHI ·
        <span class="bg-gradient-to-r from-blue-400 via-cyan-300 to-blue-500 bg-clip-text text-transparent drop-shadow-[0_0_8px_rgba(99,179,237,0.6)]">STUDIO</span>
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
