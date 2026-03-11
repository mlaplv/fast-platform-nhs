<script lang="ts">
  import { onMount } from "svelte";
  import { fade } from "svelte/transition";
  import { apiClient } from "$lib/utils/apiClient";
  import { nanobot } from "$lib/state/nanobot.svelte";
  import { vuiController } from "$lib/vui";
  
  // -- Sub-Components --
  import Header from "./content-factory/Header.svelte";
  import Timeline from "./content-factory/Timeline.svelte";
  import IdeaStep from "./content-factory/IdeaStep.svelte";
  import AssetStep from "./content-factory/AssetStep.svelte";
  import OutlineStep from "./content-factory/OutlineStep.svelte";
  import DraftStep from "./content-factory/DraftStep.svelte";
  import PublishStep from "./content-factory/PublishStep.svelte";
  import ActionButtons from "./content-factory/ActionButtons.svelte";

  let { 
    campaign_id,
    step = $bindable(1),
    status = $bindable("IDLE"),
    progress_msg = $bindable(""),
    title = $bindable(""),
    keywords = $bindable({}),
    assets = $bindable([]),
    outline = $bindable({}),
    draft_content = $bindable(""),
    finalHtml = $bindable(""),
    selectedAvatarUrl = $bindable(null),
  } = $props();

  // -- Local UI Orchestration --
  let viewingStep = $state(step);
  let isEditing = $state(false);
  let isProcessing = $derived(status === "PROCESSING");
  let isLoading = $state(false);
  let isPublishing = $state(false);
  let resultMsg = $state("");
  let customImageUrl = $state("");
  let selectedAssetIndex = $state(0);
  let editedKeywords = $state<any>({});
  let editedDraft = $state("");
  let editorRef = $state<any>(null);

  // -- Sync & Initialization --
  $effect(() => { 
    if (step > viewingStep) viewingStep = step;
  });

  onMount(() => {
    editedKeywords = JSON.parse(JSON.stringify(keywords || {}));
    editedDraft = draft_content || "";
    if (assets?.length > 0 && !selectedAvatarUrl) {
      selectedAvatarUrl = assets[0];
    }
  });

  // -- Event Handlers --
  async function handleApprove() {
    if (isLoading) return;
    isLoading = true;
    try {
      const payload = isEditing ? { edited_data: viewingStep === 1 ? editedKeywords : { content: editedDraft } } : {};
      await apiClient.post(`/api/v1/content/campaigns/${campaign_id}/approve`, payload);
      isEditing = false;
      vuiController.speak(`Duyệt thành công!`);
    } catch (e) {
      console.error("Approve failed:", e);
    } finally {
      isLoading = false;
    }
  }

  async function handleRetry() {
    if (isLoading) return;
    isLoading = true;
    try {
      await apiClient.post(`/api/v1/content/campaigns/${campaign_id}/retry`);
      vuiController.speak(`Đang chạy lại bước này.`);
    } catch (e) {
      console.error("Retry failed:", e);
    } finally {
      isLoading = false;
    }
  }

  async function handleUpdateMetadata() {
    isLoading = true;
    try {
      const payload = viewingStep === 1 ? { keywords: editedKeywords } : { draft_content: editedDraft };
      await apiClient.patch(`/api/v1/content/campaigns/${campaign_id}`, payload);
      keywords = { ...editedKeywords };
      draft_content = editedDraft;
      isEditing = false;
      vuiController.speak("Đã lưu.");
    } catch (e) {
      console.error("Update failed:", e);
    } finally {
      isLoading = false;
    }
  }

  async function handlePublish() {
    if (isPublishing) return;
    isPublishing = true;
    try {
      await apiClient.post(`/api/v1/content/campaigns/${campaign_id}/publish`);
      resultMsg = "Xuất bản thành công!";
      vuiController.speak("Bài viết đã được xuất bản.");
    } catch (e) {
      console.error("Publish failed:", e);
    } finally {
      isPublishing = false;
    }
  }

  async function syncAssetChanges(newIndex?: number) {
    try {
      await apiClient.patch(`/api/v1/content/campaigns/${campaign_id}`, {
        assets_data: assets,
        gold_metadata: { ...keywords, selected_avatar: selectedAvatarUrl, selected_index: newIndex ?? selectedAssetIndex }
      });
    } catch (e) { console.error("Sync failed:", e); }
  }

  function handleImageError(url: string) {
    assets = assets.filter(a => a !== url);
    if (selectedAvatarUrl === url) selectedAvatarUrl = assets[0] || null;
  }

  function deleteAsset(idx: number, e: MouseEvent) {
    e.stopPropagation();
    const removed = assets[idx];
    assets = assets.filter((_, i) => i !== idx);
    if (selectedAvatarUrl === removed) selectedAvatarUrl = assets[0] || null;
    syncAssetChanges();
  }

  function handleMouseMove(e: MouseEvent) {
    const el = e.currentTarget as HTMLElement;
    const rect = el.getBoundingClientRect();
    el.style.setProperty('--mouse-x', `${((e.clientX - rect.left) / rect.width) * 100}%`);
    el.style.setProperty('--mouse-y', `${((e.clientY - rect.top) / rect.height) * 100}%`);
  }

  function handleSelectKeyword(kw: string) {
    keywords.primary_keyword = kw;
    vuiController.speak(`Đã chọn ${kw}.`);
    apiClient.patch(`/api/v1/content/campaigns/${campaign_id}`, { keywords });
  }
</script>

<div 
  class="content-review-card w-full {nanobot.isExpanded ? 'h-full bg-transparent' : 'bg-white/[0.02] border border-white/5 rounded-3xl'} flex flex-col p-8 transition-all duration-700 overflow-hidden shadow-2xl"
  in:fade={{ duration: 600 }}
>
  <Header 
    {viewingStep} {status} {progress_msg} {campaign_id} 
    bind:isEditing toggleExpand={ () => { nanobot.toggleExpand(); } }
    isExpanded={nanobot.isExpanded}
  />

  <Timeline {step} bind:viewingStep bind:isEditing />

  <div class="flex-1 flex gap-6 min-h-0 overflow-hidden relative z-10">
    <div class="flex-1 space-y-5 flex flex-col min-h-0 overflow-hidden">
      {#if viewingStep === 1}
        <IdeaStep 
          bind:isEditing {campaign_id} bind:keywords bind:editedKeywords 
          {handleSelectKeyword} {handleUpdateMetadata} {isLoading} 
        />
      {:else if viewingStep === 2}
        <AssetStep 
          {isProcessing} isExpanded={nanobot.isExpanded} 
          bind:assets bind:customImageUrl bind:selectedAvatarUrl bind:selectedAssetIndex 
          {handleImageError} {syncAssetChanges} {deleteAsset} {handleRetry} {handleMouseMove} 
        />
      {:else if viewingStep === 3}
        <OutlineStep 
          {isEditing} bind:editedDraft bind:draft_content {assets} 
          isExpanded={nanobot.isExpanded} editorAnnotations={[]}
        />
      {:else if viewingStep === 4}
        <DraftStep 
          {campaign_id} {isEditing} bind:editedDraft bind:draft_content 
          {assets} isExpanded={nanobot.isExpanded} bind:editorRef
        />
      {:else if viewingStep === 5}
        <PublishStep 
          {selectedAvatarUrl} bind:viewingStep bind:isEditing bind:keywords 
          {finalHtml} {draft_content} 
        />
      {/if}
    </div>
  </div>

  {#if resultMsg}
    <div class="mt-6 p-4 rounded-2xl bg-blue-500/10 border border-blue-500/20 text-blue-300 text-[13px] font-bold">
      {resultMsg}
    </div>
  {/if}

  <ActionButtons 
    {isLoading} {status} {viewingStep} {step} {isEditing} {isProcessing} {isPublishing}
    {handleRetry} {handleUpdateMetadata} {handlePublish} {handleApprove}
  />
</div>

<style>
  .content-review-card { position: relative; isolation: isolate; }
  :global(.custom-scrollbar::-webkit-scrollbar) { width: 3px; }
  :global(.custom-scrollbar::-webkit-scrollbar-thumb) { background: rgba(59, 130, 246, 0.1); border-radius: 20px; }
  :global(.custom-scrollbar::-webkit-scrollbar-thumb:hover) { background: rgba(59, 130, 246, 0.6); }
  @keyframes shimmer { 0% { transform: translateX(-100%); } 100% { transform: translateX(100%); } }
  :global(.animate-shimmer) { position: relative; overflow: hidden; }
  :global(.animate-shimmer::after) { content: ''; position: absolute; inset: 0; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.08), transparent); animation: shimmer 1.5s infinite linear; }
</style>
