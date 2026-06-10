<script lang="ts">
  import { fade, fly } from 'svelte/transition';
  import Calendar from "@lucide/svelte/icons/calendar";
  import Clock from "@lucide/svelte/icons/clock";
  import Activity from "@lucide/svelte/icons/activity";
  import ChevronRight from "@lucide/svelte/icons/chevron-right";
  import Target from "@lucide/svelte/icons/target";
  import X from "@lucide/svelte/icons/x";
  import Search from "@lucide/svelte/icons/search";
  import Check from "@lucide/svelte/icons/check";
  import { useNanobot } from "$lib/state/nanobot.svelte";
  const nanobot = useNanobot();
  import { apiClient } from "$lib/utils/apiClient";
  import { portal } from "$lib/core/actions/portal";
  import { Z_INDEX_ADMIN } from "$lib/core/constants/z_index_admin";
  import type { Appointment, Article } from "$lib/types";

  let {
    isOpen = $bindable(),
    appointment = $bindable(),
    onClose,
    onSave
  } = $props<{
    isOpen: boolean;
    appointment: Partial<Appointment>;
    onClose: () => void;
    onSave: () => void;
  }>();

  let isLoading = $state(false);
  let articlesList = $state<Article[]>([]);
  let autopilotAction = $state<'none' | 'publish_article'>('none');
  let selectedArticleId = $state<string>('');
  let isDropdownOpen = $state(false);
  let searchQuery = $state('');

  let selectedArticle = $derived(
    articlesList.find((a) => a.id === selectedArticleId) || 
    (selectedArticleId ? { id: selectedArticleId, title: appointment.metadata_json?.article_title || 'Bài viết đã chọn', category: '' } : null)
  );

  let filteredArticles = $derived(
    articlesList.filter((a) => a.title.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  async function loadArticles() {
    try {
      const res = await apiClient.get("/api/v1/articles/?limit=100&exclude_status=PUBLISHED");
      articlesList = res.data || [];
    } catch (e) {
      console.error("Failed to load articles", e);
    }
  }

  $effect(() => {
    if (isOpen) {
      const metadata = appointment.metadata_json || {};
      autopilotAction = metadata.action === 'publish_article' ? 'publish_article' : 'none';
      selectedArticleId = metadata.article_id || '';
      loadArticles();
    }
  });

  $effect(() => {
    if (autopilotAction === 'publish_article' && appointment.start_time) {
      appointment.end_time = appointment.start_time;
    }
  });

  function prepareMetadata() {
    if (autopilotAction === 'publish_article') {
      const art = articlesList.find(a => a.id === selectedArticleId);
      appointment.metadata_json = {
        action: 'publish_article',
        article_id: selectedArticleId,
        article_title: art ? art.title : (appointment.metadata_json?.article_title || '')
      };
    } else {
      appointment.metadata_json = {};
    }
  }

  async function handleSave() {
    if (!appointment.title || !appointment.start_time || !appointment.end_time) {
      nanobot.showToast("Vui lòng điền đầy đủ thông tin", "warning");
      return;
    }

    if (autopilotAction === 'publish_article' && !selectedArticleId) {
      nanobot.showToast("Vui lòng chọn bài viết cần đăng", "warning");
      return;
    }

    prepareMetadata();

    isLoading = true;
    try {
      const payload = {
        ...appointment,
        metadata_json: appointment.metadata_json || {}
      };

      if (appointment.id) {
        await apiClient.patch(`/api/v1/appointments/${appointment.id}/`, payload);
        nanobot.showToast("Cập nhật lịch hẹn thành công", "success");
      } else {
        await apiClient.post("/api/v1/appointments/", payload);
        nanobot.showToast("Đã lưu lịch hẹn thành công", "success");
      }
      onSave();
      onClose();
    } catch (e) {
      console.error("Failed to save appointment", e);
      nanobot.showToast("Không thể lưu lịch hẹn", "error");
    } finally {
      isLoading = false;
    }
  }

  async function handleDelete() {
    if (!appointment.id) return;
    if (!confirm("Sếp có chắc chắn muốn hủy lịch đăng bài này không?")) return;
    isLoading = true;
    try {
      await apiClient.delete(`/api/v1/appointments/${appointment.id}/`);
      nanobot.showToast("Đã hủy lịch đăng bài thành công", "success");
      onSave();
      onClose();
    } catch (e) {
      console.error("Failed to delete appointment", e);
      nanobot.showToast("Không thể hủy lịch đăng bài", "error");
    } finally {
      isLoading = false;
    }
  }

  const recurringTypes = ['none', 'daily', 'weekly', 'monthly'] as const;
  const operationTypes = ['STRATEGY', 'DEPLOYMENT', 'REVIEW'] as const;
  const stageStatuses = ['UPCOMING', 'ONGOING', 'COMPLETED'] as const;
</script>

{#if isOpen}
  <div use:portal class="relative" style="z-index: {Z_INDEX_ADMIN.MODAL};">
    <!-- Backdrop: Elite Deep Blur -->
    <div
      class="fixed inset-0 bg-black/95 md:bg-black/90 md:backdrop-blur-sm"
      style="z-index: {Z_INDEX_ADMIN.OVERLAY};"
      transition:fade={{ duration: 300 }}
      onclick={onClose}
      aria-label="Close modal"
      role="button"
      tabindex="0"
      onkeydown={(e) => e.key === 'Escape' && onClose()}
    ></div>

    <!-- Drawer Panel: ELITE DESIGN (Right Aligned) -->
    <div
      class="fixed top-0 right-0 h-full w-[500px] max-w-full bg-[#050505] border-l border-white/10 shadow-[-30px_0_50px_rgba(0,0,0,0.8)] flex flex-col overflow-hidden"
      transition:fly={{ x: 500, duration: 300, opacity: 1 }}
      style="z-index: {Z_INDEX_ADMIN.MODAL + 10};"
    >
      <!-- Header Section -->
      <div class="h-16 flex items-center justify-between px-6 border-b border-white/10 relative bg-black/40">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded bg-blue-500/10 border border-blue-500/20 flex items-center justify-center">
            <Activity size={14} class="text-blue-500 animate-pulse" />
          </div>
          <div>
            <h2 class="text-sm font-bold text-white tracking-widest ">
              {appointment.id ? 'Edit Appointment' : 'New Appointment'}
            </h2>
            {#if appointment.id}
              <div class="text-[9px] font-mono text-gray-500 ">SYS_ID: {appointment.id}</div>
            {/if}
          </div>
        </div>
        <button 
          onclick={onClose}
          class="w-8 h-8 flex items-center justify-center text-gray-500 hover:text-white hover:bg-white/10 rounded-lg transition-colors border border-transparent hover:border-white/10"
        >
          <X size={16} />
        </button>

        <!-- Decorative bottom line -->
        <div class="absolute bottom-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-white/10 to-transparent"></div>
      </div>

      <!-- Form Body -->
      <div class="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-8">
        <!-- Title Field -->
        <div class="space-y-3">
          <label class="block text-[8px] font-black text-white/30 tracking-[0.2em] ml-1" for="title">Title</label>
          <input 
            id="title"
            bind:value={appointment.title}
            type="text" 
            placeholder="Elite Strategic Planning..."
            class="w-full bg-white/[0.03] border border-white/5 rounded-2xl px-6 py-5 text-sm font-bold text-white placeholder:text-white/5 focus:outline-none focus:border-blue-500/30 transition-all shadow-inner"
          />
        </div>

        <!-- Date Range Nexus -->
        <div class="grid grid-cols-2 gap-4">
          <div class="space-y-3">
            <label class="block text-[8px] font-black text-white/30 tracking-[0.2em] ml-1" for="start">Start Time</label>
            <div class="relative">
              <input 
                id="start"
                bind:value={appointment.start_time}
                type="datetime-local" 
                class="w-full bg-white/[0.03] border border-white/5 rounded-2xl px-6 py-4 text-[11px] font-bold text-white/80 focus:outline-none focus:border-blue-500/30 transition-all custom-datetime"
              />
              <Calendar size={14} class="absolute right-5 top-1/2 -translate-y-1/2 text-white/10 pointer-events-none" />
            </div>
          </div>
          <div class="space-y-3">
            <label class="block text-[8px] font-black text-white/30 tracking-[0.2em] ml-1" for="end">
              End Time {autopilotAction === 'publish_article' ? '(N/A - Locked)' : ''}
            </label>
            <div class="relative">
              <input 
                id="end"
                bind:value={appointment.end_time}
                type="datetime-local" 
                disabled={autopilotAction === 'publish_article'}
                class="w-full bg-white/[0.03] border border-white/5 rounded-2xl px-6 py-4 text-[11px] font-bold text-white/80 focus:outline-none focus:border-blue-500/30 transition-all custom-datetime disabled:opacity-40 disabled:cursor-not-allowed disabled:border-white/5"
              />
              <Calendar size={14} class="absolute right-5 top-1/2 -translate-y-1/2 text-white/10 pointer-events-none" />
            </div>
          </div>
        </div>

        <!-- Selector Rows -->
        <div class="space-y-8">
          <!-- Recurring Type -->
          <div class="space-y-4">
            <div class="text-[8px] font-black text-white/30 tracking-[0.2em] ml-1">Recurring Type</div>
            <div class="flex flex-wrap gap-2.5">
              {#each recurringTypes as type}
                {@const active = appointment.recurring_type === type}
                <button 
                  onclick={() => appointment.recurring_type = type}
                  class="px-6 py-3 rounded-xl text-[9px] font-black tracking-widest transition-all
                  {active ? 'bg-blue-500 text-white shadow-[0_0_30px_rgba(59,130,246,0.4)] scale-105' : 'bg-white/[0.04] text-white/30 hover:bg-white/[0.08] hover:text-white/60'}"
                >
                  {type}
                </button>
              {/each}
            </div>
          </div>

          <!-- Operation Type -->
          <div class="space-y-4">
            <div class="text-[8px] font-black text-white/30 tracking-[0.2em] ml-1">Operation Type</div>
            <div class="flex flex-wrap gap-2.5">
              {#each operationTypes as type}
                {@const active = appointment.type === type}
                <button 
                  onclick={() => appointment.type = type}
                  class="px-6 py-3 rounded-xl text-[9px] font-black tracking-widest transition-all
                  {active ? 'bg-[#a855f7] text-white shadow-[0_0_30px_rgba(168,85,247,0.4)] scale-105' : 'bg-white/[0.04] text-white/30 hover:bg-white/[0.08] hover:text-white/60'}"
                >
                  {type}
                </button>
              {/each}
            </div>
          </div>

          <!-- Stage Status -->
          <div class="space-y-4">
            <div class="text-[8px] font-black text-white/30 tracking-[0.2em] ml-1">Stage Status</div>
            <div class="flex flex-wrap gap-2.5">
              {#each stageStatuses as status}
                {@const active = appointment.status === status}
                <button 
                  onclick={() => appointment.status = status}
                  class="px-6 py-3 rounded-xl text-[9px] font-black tracking-widest transition-all
                  {active ? 'bg-[#10b981] text-white shadow-[0_0_30px_rgba(16,185,129,0.4)] scale-105' : 'bg-white/[0.04] text-white/30 hover:bg-white/[0.08] hover:text-white/60'}"
                >
                  {status}
                </button>
              {/each}
            </div>
          </div>

          <!-- Autopilot Action -->
          <div class="space-y-4 pt-4 border-t border-white/5">
            <div class="text-[8px] font-black text-white/30 tracking-[0.2em] ml-1">Autopilot Action</div>
            <div class="flex flex-wrap gap-2.5">
              <button 
                onclick={() => autopilotAction = 'none'}
                class="px-6 py-3 rounded-xl text-[9px] font-black tracking-widest transition-all
                {autopilotAction === 'none' ? 'bg-gray-500 text-white shadow-[0_0_30px_rgba(100,116,139,0.4)] scale-105' : 'bg-white/[0.04] text-white/30 hover:bg-white/[0.08] hover:text-white/60'}"
              >
                None
              </button>
              <button 
                onclick={() => autopilotAction = 'publish_article'}
                class="px-6 py-3 rounded-xl text-[9px] font-black tracking-widest transition-all
                {autopilotAction === 'publish_article' ? 'bg-cyan-500 text-white shadow-[0_0_30px_rgba(6,182,212,0.4)] scale-105' : 'bg-white/[0.04] text-white/30 hover:bg-white/[0.08] hover:text-white/60'}"
              >
                Publish Article
              </button>
            </div>
          </div>

          {#if autopilotAction === 'publish_article'}
            <div class="space-y-3 p-4 bg-cyan-500/5 border border-cyan-500/10 rounded-2xl transition-all">
              <label class="block text-[8px] font-black text-cyan-400 tracking-[0.2em] ml-1" for="article-select">Chọn bài viết liên kết</label>
              <div class="relative">
                <!-- Trigger Button -->
                <button
                  id="article-select"
                  type="button"
                  onclick={() => isDropdownOpen = !isDropdownOpen}
                  class="w-full bg-[#09090b] border border-white/5 rounded-xl px-4 py-3.5 text-left text-xs font-bold text-white/90 focus:outline-none focus:border-cyan-500/40 hover:bg-white/[0.02] transition-all flex items-center justify-between"
                >
                  <span class="truncate pr-4">
                    {selectedArticle ? selectedArticle.title : '-- Chọn bài viết --'}
                  </span>
                  <ChevronRight size={14} class="text-white/30 transition-transform duration-200 shrink-0 {isDropdownOpen ? 'rotate-90' : 'rotate-0'}" />
                </button>

                <!-- Dropdown Menu -->
                {#if isDropdownOpen}
                  <!-- Backdrop to close dropdown on click outside -->
                  <div class="fixed inset-0 z-[100]" onclick={() => isDropdownOpen = false}></div>

                  <div 
                    class="absolute left-0 right-0 z-[101] mt-1.5 bg-[#09090b]/95 border border-white/10 rounded-xl shadow-[0_20px_50px_rgba(0,0,0,0.6)] backdrop-blur-md overflow-hidden flex flex-col max-h-64"
                  >
                    <!-- Search Input Box -->
                    <div class="p-2 border-b border-white/5 bg-black/40 flex items-center gap-2">
                      <Search size={12} class="text-white/30 ml-2 shrink-0" />
                      <input
                        type="text"
                        placeholder="Tìm kiếm bài viết..."
                        bind:value={searchQuery}
                        class="w-full bg-transparent border-none text-xs font-bold text-white placeholder:text-white/20 focus:outline-none focus:ring-0 py-1"
                        onclick={(e) => e.stopPropagation()}
                      />
                      {#if searchQuery}
                        <button 
                          type="button" 
                          onclick={(e) => { e.stopPropagation(); searchQuery = ''; }}
                          class="p-1 hover:bg-white/10 rounded-md text-white/30 hover:text-white transition-colors"
                        >
                          <X size={10} />
                        </button>
                      {/if}
                    </div>

                    <!-- Options List -->
                    <div class="overflow-y-auto custom-scrollbar p-1 max-h-48 divide-y divide-white/[0.02]">
                      <!-- Pre-selected fallback option -->
                      {#if selectedArticleId && !articlesList.some(a => a.id === selectedArticleId)}
                        <button
                          type="button"
                          class="w-full text-left px-3 py-2.5 rounded-lg text-xs font-bold transition-all hover:bg-cyan-500/10 text-cyan-400 flex items-center justify-between bg-cyan-500/5 border border-cyan-500/10"
                          onclick={() => {
                            isDropdownOpen = false;
                          }}
                        >
                          <span class="truncate pr-2">{appointment.metadata_json?.article_title || 'Bài viết đã chọn'}</span>
                          <span class="text-[8px] font-black text-cyan-400/70 tracking-widest uppercase shrink-0">Đã chọn</span>
                        </button>
                      {/if}

                      {#if filteredArticles.length === 0}
                        <div class="text-[10px] text-white/30 text-center py-4 font-medium italic">
                          Không tìm thấy bài viết nào
                        </div>
                      {:else}
                        {#each filteredArticles as art}
                          <button
                            type="button"
                            class="w-full text-left px-3 py-2.5 rounded-lg text-xs font-medium transition-all hover:bg-white/[0.04] flex items-center justify-between {selectedArticleId === art.id ? 'bg-cyan-500/10 text-cyan-400 font-bold' : 'text-white/80'}"
                            onclick={() => {
                              selectedArticleId = art.id;
                              isDropdownOpen = false;
                              searchQuery = '';
                            }}
                          >
                            <span class="truncate pr-2">{art.title}</span>
                            {#if selectedArticleId === art.id}
                              <Check size={12} class="text-cyan-400 shrink-0" />
                            {:else if art.category}
                              <span class="text-[8px] font-bold text-white/20 bg-white/5 px-1.5 py-0.5 rounded uppercase tracking-wider shrink-0">{art.category}</span>
                            {/if}
                          </button>
                        {/each}
                      {/if}
                    </div>
                  </div>
                {/if}
              </div>
            </div>
          {/if}
        </div>

        <!-- Submit Nexus -->
        <div class="pt-6 flex gap-3">
          {#if appointment.id}
            <button 
              type="button"
              onclick={handleDelete}
              disabled={isLoading}
              class="flex-1 py-4 rounded-xl border border-red-500/20 hover:border-red-500/40 bg-red-500/5 text-red-500 text-[11px] font-black tracking-[0.2em] hover:scale-[1.02] active:scale-[0.98] transition-all disabled:opacity-50 flex items-center justify-center"
            >
              HỦY LỊCH
            </button>
          {/if}
          <button 
            onclick={handleSave}
            disabled={isLoading}
            class="flex-[2] py-4 rounded-xl bg-gradient-to-r from-blue-600 to-blue-500 text-white text-[11px] font-black tracking-[0.2em] hover:scale-[1.02] active:scale-[0.98] transition-all shadow-[0_10px_30px_-5px_rgba(37,99,235,0.4)] disabled:opacity-50 flex items-center justify-center overflow-hidden relative group"
          >
            <!-- Hover sheen effect -->
            <div class="absolute inset-0 bg-white/20 -translate-x-full group-hover:translate-x-full transition-transform duration-1000"></div>
            
            {#if isLoading}
              <Activity size={16} class="animate-spin mr-3" />
              Processing...
            {:else}
              LƯU THAY ĐỔI
            {/if}
          </button>
        </div>
      </div>
    </div>
  </div>
{/if}

<style>
  .custom-scrollbar::-webkit-scrollbar { width: 4px; }
  .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
  .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.1); border-radius: 4px; }
  .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(0, 255, 255, 0.3); }

  /* Custom styling for datetime-local to match Elite aesthetics */
  .custom-datetime { color-scheme: dark; }
  .custom-datetime::-webkit-calendar-picker-indicator {
    opacity: 0;
    position: absolute;
    right: 0;
    top: 0;
    width: 100%;
    height: 100%;
    cursor: pointer;
  }
</style>
