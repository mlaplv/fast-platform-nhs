<script lang="ts">
  import TiptapEditor from "../tiptap/TiptapEditor.svelte";
  import UltraPremiumLoading from "./UltraPremiumLoading.svelte";
  import { onMount } from "svelte";
  import type { MediaAsset } from "$lib/state/types";
  import { xohiImageStore } from "$lib/state/xohiImage.svelte";
  import { createOutlineController, type RawOutline } from "$lib/state/xohiOutline.svelte";

  interface Props {
    isEditing: boolean;
    editedOutline: string;
    outline: RawOutline;
    assets: (MediaAsset | string)[];
    isExpanded: boolean;
    selectedAvatarUrl: string | null;
    selectedAssetIndex: number;
    editorAnnotations?: unknown[];
    step?: number;
    isProcessing?: boolean;
    campaign_id: string;
  }

  let {
    isEditing,
    editedOutline = $bindable(),
    outline = {} as RawOutline,
    assets = $bindable(),
    isExpanded,
    selectedAvatarUrl = $bindable(),
    selectedAssetIndex = $bindable(),
    editorAnnotations = [],
    step = 3,
    isProcessing = false,
    campaign_id,
  }: Props = $props();

  const ctrl = createOutlineController({
    getOutline: () => outline,
    getEditedOutline: () => editedOutline,
    getAssets: () => assets,
    setEditedOutline: (v) => { editedOutline = v; }
  });

  onMount(() => {
    if (editedOutline === undefined) editedOutline = "";
    if (assets === undefined) assets = [];
    if (selectedAvatarUrl === undefined) selectedAvatarUrl = null;
    if (selectedAssetIndex === undefined) selectedAssetIndex = 0;
  });

  // Ensure editedOutline is initialized when entering edit mode if it was empty
  $effect(() => {
    if (isEditing) ctrl.syncInitialDraft();
  });
</script>

<div class="p-5 md:p-8 flex flex-col flex-1 min-h-0 overflow-hidden">
  <!-- Studio Label -->
  <div class="flex items-center gap-3 shrink-0 mb-4">
    <div class="hidden md:block w-8 h-px bg-gradient-to-r from-transparent to-blue-500/50"></div>
    <h5 class="hidden md:block text-[11px] font-black tracking-[0.2em] text-blue-400/60">
      NEURAL XOHI ·
      <span class="bg-gradient-to-r from-blue-400 via-cyan-300 to-blue-500 bg-clip-text text-transparent drop-shadow-[0_0_8px_rgba(99,179,237,0.6)]">STUDIO</span>
    </h5>
  </div>

  <!-- Editor -->
  <div class="flex flex-col relative flex-1 min-h-0 transition-all duration-500 {isEditing ? 'border border-white/5 shadow-[0_30px_60px_-15px_rgba(0,0,0,0.8)] bg-[#09090b]/40 backdrop-blur-2xl' : 'bg-transparent'}">
     {#if isProcessing}
       <div class="absolute inset-0 z-[var(--z-admin-mobile-backdrop)]">
         <UltraPremiumLoading 
           progress_msg="AI đang thiết kế dàn ý..." 
           viewingStep={3} 
           campaign_id={campaign_id} 
           liveContent={ctrl.displayContent || ""} 
         />
       </div>
     {/if}

     <TiptapEditor
       content={ctrl.displayContent}
       bind:assets={assets}
       bind:selectedAvatarUrl={selectedAvatarUrl}
       bind:selectedAssetIndex={selectedAssetIndex}
       campaignId={campaign_id}
       syncAssetsMode="append"
       onChange={(val) => {
          if (isEditing && val !== editedOutline) {
            editedOutline = val;
          }
       }}
       editable={isEditing}
       placeholder="Đang tạo dàn ý..."
       fullScreen={isExpanded}
       annotations={editorAnnotations}
     />
  </div>
</div>

<style>
  @keyframes shimmer { 0% { opacity: 0.3; } 50% { opacity: 0.7; } 100% { opacity: 0.3; } }
  .animate-pulse { animation: shimmer 2s infinite ease-in-out; }
</style>
