<script lang="ts">
  import TiptapEditor from "../tiptap/TiptapEditor.svelte";
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
    assets = $bindable([] as (MediaAsset | string)[]),
    isExpanded,
    selectedAvatarUrl = $bindable(null as string | null),
    selectedAssetIndex = $bindable(0),
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
  });

  // Ensure editedOutline is initialized when entering edit mode if it was empty
  $effect(() => {
    if (isEditing) ctrl.syncInitialDraft();
  });
</script>

<div class="p-5 md:p-8 space-y-4 flex flex-col">
  <!-- Studio Label -->
  <div class="flex items-center gap-3 shrink-0">
    <div class="hidden md:block w-8 h-px bg-gradient-to-r from-transparent to-blue-500/50"></div>
    <h5 class="hidden md:block text-[11px] font-black uppercase tracking-[0.2em] text-blue-400/60">
      XOHI ·
      <span class="bg-gradient-to-r from-blue-400 via-cyan-300 to-blue-500 bg-clip-text text-transparent drop-shadow-[0_0_8px_rgba(99,179,237,0.6)]">NEURAL STUDIO</span>
    </h5>
  </div>

  <!-- Editor -->
  <div class="flex flex-col relative transition-all duration-500 {isEditing ? 'border border-white/5 shadow-[0_30px_60px_-15px_rgba(0,0,0,0.8)] bg-[#09090b]/40 backdrop-blur-2xl' : 'bg-transparent'}">
     {#if isProcessing && !ctrl.displayContent}
       <div class="absolute inset-0 z-20 flex flex-col items-center justify-center bg-slate-950/60 backdrop-blur-md animate-in fade-in duration-700">
         <div class="relative">
           <!-- Spinning Ring -->
           <div class="w-20 h-20 rounded-full border-t-2 border-r-2 border-blue-500/40 animate-spin"></div>
           <!-- Inner Glow -->
           <div class="absolute inset-0 m-auto w-12 h-12 bg-blue-500/10 rounded-full blur-xl animate-pulse"></div>
         </div>
         <div class="mt-8 flex flex-col items-center gap-2">
           <span class="text-[10px] font-black uppercase tracking-[0.3em] text-blue-400/80 animate-pulse">AI đang thiết kế dàn ý</span>
           <div class="flex gap-1">
              <div class="w-1 h-1 rounded-full bg-blue-500/40 animate-bounce" style="animation-delay: 0s"></div>
              <div class="w-1 h-1 rounded-full bg-blue-500/40 animate-bounce" style="animation-delay: 0.1s"></div>
              <div class="w-1 h-1 rounded-full bg-blue-500/40 animate-bounce" style="animation-delay: 0.2s"></div>
           </div>
         </div>
       </div>
     {/if}

     <TiptapEditor
       content={ctrl.displayContent}
       bind:assets={assets}
       bind:selectedAvatarUrl={selectedAvatarUrl}
       bind:selectedAssetIndex={selectedAssetIndex}
       campaignId={campaign_id}
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
