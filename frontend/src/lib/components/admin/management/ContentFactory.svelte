<script lang="ts">
  import { onMount } from "svelte";
  import { nanobot } from "$lib/state/nanobot.svelte";
  import { apiClient } from "$lib/utils/apiClient";
  import { fade } from "svelte/transition";
  import Megaphone from "lucide-svelte/icons/megaphone";
  import CheckCircle from "lucide-svelte/icons/check-circle";
  import CampaignFilters from "./CampaignFilters.svelte";
  import CampaignListItem from "./CampaignListItem.svelte";
  import BulkActionBar from "./BulkActionBar.svelte";
  import type { CampaignData } from "$lib/state/types";

  let allCampaigns: CampaignData[] = $state([]);
  let isLoading = $state(true);
  let deletingId = $state<string | null>(null);

  // Pagination Matrix (Phase 5)
  let offset = $state(0);
  let limit = 20;
  let totalCount = $state(0);
  let hasMore = $state(false);
  let isLoadingMore = $state(false);

  // States for Filtering
  let searchInput = $state("");
  let activeStatus = $state("all");
  let activeCategory = $state("all");
  let activeStep = $state<number | "all">("all");

  // Selection Matrix (Phase 5)
  let selectedIds = $state(new Set<string>());

  function toggleSelection(id: string) {
    if (selectedIds.has(id)) {
      selectedIds.delete(id);
    } else {
      selectedIds.add(id);
    }
    selectedIds = new Set(selectedIds); // Trigger reactivity
  }

  function selectAll() {
    const visible = filteredCampaigns();
    if (selectedIds.size === visible.length && visible.length > 0) {
      selectedIds = new Set();
    } else {
      selectedIds = new Set(visible.map(c => c.id));
    }
  }

  // Derived filtered list
  let filteredCampaigns = $derived(() => {
    return allCampaigns.filter(c => {
      const matchStatus = activeStatus === "all" || c.status === activeStatus;
      const matchCategory = activeCategory === "all" || c.category === activeCategory;
      const matchStep = activeStep === "all" || c.current_step === activeStep;
      const matchSearch = !searchInput || 
        (c.topic_data?.title?.toLowerCase() || "").includes(searchInput.toLowerCase()) ||
        (c.source_input?.toLowerCase() || "").includes(searchInput.toLowerCase()) ||
        c.id.includes(searchInput);
      return matchStatus && matchCategory && matchStep && matchSearch;
    });
  });

  onMount(async () => {
    await loadCampaigns();
  });

  async function loadCampaigns(isAppend = false) {
    if (isAppend) {
      isLoadingMore = true;
    } else {
      isLoading = true;
      offset = 0;
    }

    try {
      const raw = await apiClient.get<{
        items: CampaignData[];
        total: number;
        has_more: boolean;
        limit: number;
        offset: number;
      }>(`/api/v1/content/campaigns?limit=${limit}&offset=${offset}`);
      const data = raw?.items || [];
      
      if (isAppend) {
        allCampaigns = [...allCampaigns, ...data];
      } else {
        allCampaigns = data;
      }

      totalCount = raw?.total || allCampaigns.length;
      hasMore = raw?.has_more || false;
      
      if (hasMore) {
        offset += limit;
      }
    } catch (e) {
      console.error("[ContentFactory] Failed to load campaigns:", e);
      if (!isAppend) allCampaigns = [];
    } finally {
      isLoading = false;
      isLoadingMore = false;
    }
  }

  async function deleteCampaign(id: string) {
    if (deletingId) return; // Prevent concurrent single deletes during bulk or same
    const confirmed = await nanobot.showConfirm({
      title: "PURGE_ENACTMENT",
      message: "Are you sure you want to permanently delete this campaign node and its historical traces?",
      confirmLabel: "EXECUTE",
      cancelLabel: "ABORT"
    });

    if (!confirmed) return;

    deletingId = id;
    try {
      const res = await apiClient.delete<{ status: string; message?: string }>(`/api/v1/content/campaigns/${id}`);
      
      if (res?.status === "error") {
        nanobot.showToast(`Lỗi: ${res.message || "Không thể thực hiện"}`, "error");
        return;
      }

      allCampaigns = allCampaigns.filter(c => c.id !== id);
      
      // Trigger Log Re-sync (Phase 4): Robust re-sync that doesn't block UI
      try {
        const sessionId = "account"; // standard session for global factory logs
        if (nanobot.chat) {
          await nanobot.chat.hydrateHistory(sessionId, undefined, undefined, true);
        }
      } catch (e) {
        console.warn("[ContentFactory] Refresh failed, but deletion OK:", e);
      }
      
      nanobot.showToast(res?.message || "Đã tiêu hủy chiến dịch và toàn bộ logs liên quan.", "success");
    } catch (err: unknown) {
      const e = err as Error;
      console.error("[ContentFactory] Delete crash:", e);
      nanobot.showToast(e?.message || "Thao tác thất bại (Lỗi hệ thống)", "error");
    } finally {
      deletingId = null;
    }
  }

  // Bulk Command Interface (Phase 5)
  async function handleBulkDelete() {
    const ids = Array.from(selectedIds);
    if (ids.length === 0) return;

    const confirmed = await nanobot.showConfirm({
      title: "PROTOCOL_MASS_PURGE",
      message: `You are about to permanently erase ${ids.length} campaign nodes. This action is irreversible. Proceed?`,
      confirmLabel: "EXECUTE_BATCH",
      cancelLabel: "ABORT"
    });

    if (!confirmed) return;

    isLoading = true;
    let successCount = 0;
    try {
      for (const id of ids) {
        // Visual feedback per item if possible
        try {
          const res = await apiClient.delete<{ status: string; message?: string }>(`/api/v1/content/campaigns/${id}`);
          if (res.status !== "error") successCount++;
        } catch (e) {
          console.error(`[Bulk] Failed to delete ${id}:`, e);
        }
      }

      nanobot.showToast(`Batch operation complete: ${successCount}/${ids.length} entities purged.`, "success");
      selectedIds = new Set();
      await loadCampaigns(false); // Reset list
      
      // Global re-sync
      if (nanobot.chat) {
        await nanobot.chat.hydrateHistory("account", undefined, undefined, true);
      }
    } finally {
      isLoading = false;
    }
  }

  async function handleBulkArchive() {
    const ids = Array.from(selectedIds);
    if (ids.length === 0) return;

    nanobot.showToast(`Archiving ${ids.length} entities... (Stub)`, "info");
    selectedIds = new Set();
  }

  function resumeCampaign(campaign: CampaignData) {
    nanobot.closeUniversalModal();
    nanobot.resumeCampaign(campaign as unknown as Record<string, unknown>);
  }

  async function handleCreateCampaign() {
    const topic = await nanobot.showConfirm({
      title: "PROTOCOL_INITIALIZE",
      message: "Please enter the topic or core intent for this new campaign node.",
      confirmLabel: "EXECUTE_INIT",
      cancelLabel: "ABORT",
      isPrompt: true,
      promptPlaceholder: "e.g. 'Viết bài về iPhone 17 Pro Max'..."
    });

    if (topic && topic.trim()) {
      nanobot.processCommand(topic, "text");
      nanobot.closeUniversalModal();
    }
  }

  function handleSearchInput(e: Event) {
    // Standard pattern works with binding
  }

  // V22: Voice Mutation Injection - Content Factory Navigation
  $effect(() => {
    const action = nanobot.commandAction;
    if (action?.entity === "campaign") {
      if (action.verb === "search" && action.args) {
        if (nanobot.consumeCommand("search", "campaign")) {
          searchInput = action.args;
        }
      } else if (action.verb === "create") {
        if (nanobot.consumeCommand("create", "campaign")) {
          handleCreateCampaign();
        }
      }
    }
  });
</script>

<div class="w-full h-full flex flex-col bg-[#050505] overflow-hidden" in:fade={{ duration: 300 }}>
  <!-- Filters Nexus -->
  <CampaignFilters 
    bind:searchInput 
    bind:activeStatus 
    bind:activeCategory
    bind:activeStep
    {isLoading}
    totalItems={totalCount}
    onRefresh={() => loadCampaigns(false)}
    onSearchInput={handleSearchInput}
    onCreateNew={handleCreateCampaign}
  />

  <!-- Main Scroll View -->
  <div class="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-4">
    {#if isLoading && allCampaigns.length === 0}
      <div class="h-full flex flex-col items-center justify-center gap-4">
          <div class="w-12 h-12 border-2 border-neon-cyan/10 border-t-neon-cyan rounded-full animate-spin"></div>
          <span class="text-[10px] font-mono text-neon-cyan/50 uppercase tracking-[0.4em]">SYNCHRONIZING_ARCHIVES...</span>
      </div>
    {:else if filteredCampaigns().length === 0}
      <div class="h-full flex flex-col items-center justify-center gap-6 opacity-40">
        <div class="w-20 h-20 rounded-full border border-white/5 bg-white/[0.02] flex items-center justify-center">
           <Megaphone size={32} class="text-gray-600" />
        </div>
        <div class="text-center">
           <p class="text-[11px] font-mono uppercase tracking-[0.3em] text-white/60 mb-2">ZERO_MATCH_FOUND</p>
           <p class="text-[10px] font-mono text-gray-700 italic">No campaign entities found matching current filter profile.</p>
        </div>
        <button 
           onclick={() => { searchInput = ""; activeStatus = "all"; activeCategory = "all"; }}
           class="px-4 py-2 border border-white/10 rounded-lg text-[9px] font-mono font-bold uppercase tracking-widest hover:border-white/20 hover:text-white transition-all"
        >
           Reset Filters
        </button>
      </div>
    {:else}
      <!-- List Header / Select All Control -->
      <div class="max-w-6xl mx-auto mb-2 px-5 flex items-center justify-between">
         <div class="flex items-center gap-3">
            <button 
              onclick={selectAll}
              class="flex items-center gap-2 group/all"
            >
               <div class="w-5 h-5 rounded-md border-2 transition-all flex items-center justify-center
                 {selectedIds.size === filteredCampaigns().length && filteredCampaigns().length > 0 ? 'bg-neon-cyan border-neon-cyan' : 'border-white/10 bg-white/[0.02] group-hover/all:border-white/20'}">
                  {#if selectedIds.size === filteredCampaigns().length && filteredCampaigns().length > 0}
                    <CheckCircle size={14} class="text-black" strokeWidth={3} />
                  {:else if selectedIds.size > 0}
                    <div class="w-2 h-0.5 bg-neon-cyan rounded-full"></div>
                  {/if}
               </div>
               <span class="text-[10px] font-mono font-bold text-gray-500 uppercase tracking-widest group-hover/all:text-gray-300 transition-colors">Select_All_Visible</span>
            </button>
         </div>
      </div>

      <div class="grid grid-cols-1 gap-4 max-w-6xl mx-auto">
        {#each filteredCampaigns() as campaign, i (campaign.id)}
          <CampaignListItem 
             {campaign} 
             onAction={resumeCampaign} 
             onDelete={deleteCampaign}
             isDeleting={deletingId === campaign.id}
             isSelected={selectedIds.has(campaign.id)}
             onToggleSelection={toggleSelection}
          />
        {/each}
      </div>

      {#if hasMore}
        <div class="max-w-6xl mx-auto py-8 flex justify-center">
          <button
            onclick={() => loadCampaigns(true)}
            disabled={isLoadingMore}
            class="group relative px-8 py-3 bg-white/[0.02] hover:bg-neon-cyan/10 border border-white/10 hover:border-neon-cyan/30 rounded-xl transition-all active:scale-95 disabled:opacity-50 disabled:pointer-events-none"
          >
             {#if isLoadingMore}
               <div class="flex items-center gap-3">
                  <div class="w-4 h-4 border-2 border-neon-cyan/20 border-t-neon-cyan rounded-full animate-spin"></div>
                  <span class="text-[10px] font-mono text-neon-cyan uppercase tracking-[0.2em]">FETCHING_RESOURCES...</span>
               </div>
             {:else}
               <div class="flex flex-col items-center">
                  <span class="text-[10px] font-mono font-black text-gray-400 group-hover:text-neon-cyan uppercase tracking-[0.3em] transition-colors">LOAD_MORE_RESOURCES</span>
                  <div class="w-full h-[1px] bg-white/5 mt-1 relative overflow-hidden">
                     <div class="absolute inset-0 bg-neon-cyan/50 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000"></div>
                  </div>
               </div>
             {/if}
          </button>
        </div>
      {/if}
    {/if}
  </div>

  <!-- Optional Stats Footer (Premium Feel) -->
  <div class="h-10 shrink-0 border-t border-white/5 bg-black/40 backdrop-blur-md px-6 flex items-center justify-between">
     <div class="flex items-center gap-4">
        <div class="flex items-center gap-1.5">
           <div class="w-1.5 h-1.5 rounded-full bg-green-500/60 shadow-[0_0_8px_rgba(34,197,94,0.4)]"></div>
           <span class="text-[9px] font-mono text-gray-500 uppercase tracking-tighter">Nexus_Stable</span>
        </div>
        <div class="w-[1px] h-3 bg-white/5"></div>
        <span class="text-[9px] font-mono text-gray-600 uppercase tracking-tighter">Admin_Active: {nanobot.userEmail || "SYSTEM"}</span>
     </div>
     <div class="flex items-center gap-4">
        <span class="text-[9px] font-mono text-gray-600">V69.1_TRINITY</span>
     </div>
  </div>

  <BulkActionBar 
    selectedCount={selectedIds.size} 
    onClear={() => selectedIds = new Set()} 
    onDeleteBulk={handleBulkDelete}
    onArchiveBulk={handleBulkArchive}
  />
</div>

<style>
  .custom-scrollbar::-webkit-scrollbar {
    width: 3px;
    height: 3px;
  }
  .custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 4px;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb:hover {
    background: rgba(0, 255, 255, 0.2);
  }
</style>
