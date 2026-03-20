<script lang="ts">
  import MissionControlShell from "../admin/ui/MissionControlShell.svelte";
  import AssetStep from "../admin/ui/content-factory/AssetStep.svelte";
  import { Image } from "lucide-svelte";
  import type { MediaAsset } from "$lib/state/types";
  import { Z_INDEX } from "$lib/core/constants/zIndex";

  let {
    isOpen,
    onClose,
    assets = $bindable(),
    reserve_assets = $bindable(),
    selectedAvatarUrl = $bindable(),
    selectedAssetIndex = $bindable()
  }: {
    isOpen: boolean;
    onClose: () => void;
    assets: (MediaAsset | string)[];
    reserve_assets: (MediaAsset | string)[];
    selectedAvatarUrl: string | null;
    selectedAssetIndex: number;
  } = $props();

  // Internal states for AssetStep
  let customImageUrl = $state("");
  let isProcessing = $state(false);

  function handleImageError(url: string) {
    console.error("Image error:", url);
  }

  function syncAssetChanges() {
    // Parent components should bind to the props directly
    console.log("Assets synchronized");
  }

  function deleteAsset(url: string) {
    assets = assets.filter(a => (typeof a === 'string' ? a : a.file_path) !== url);
  }

  function handleRetry() {
    console.log("Retrying asset search...");
  }

  function handleMouseMove(e: MouseEvent) {
    // UI feedback handled internally
  }
</script>

<MissionControlShell
  title="MEDIA INTELLIGENCE"
  protocol="VISUAL_x_SYNC"
  node="ASSET_VAULT_01"
  {isOpen}
  {onClose}
  headerIcon={Image}
  maxWidth="max-w-7xl"
  zIndex="z-[{Z_INDEX.MODAL}]"
>
  <div class="flex flex-col h-full bg-black/20">
    <div class="flex-1 overflow-hidden">
      <AssetStep
        {isProcessing}
        isExpanded={true}
        bind:assets
        bind:reserve_assets
        bind:customImageUrl
        bind:selectedAvatarUrl
        bind:selectedAssetIndex
        {handleImageError}
        {syncAssetChanges}
        {deleteAsset}
        {handleRetry}
        {handleMouseMove}
      />
    </div>

    <!-- HUD Footer -->
    <div class="flex items-center gap-6 text-[9px] font-mono uppercase tracking-widest px-8 py-4 border-t border-white/5 bg-black/40">
      <div class="flex items-center gap-2">
        <div class="w-1.5 h-1.5 rounded-full bg-hacker-green animate-pulse shadow-[0_0_8px_rgba(0,255,0,0.4)]"></div>
        <span class="text-gray-500">AI Optimization Active</span>
      </div>
      <div class="flex items-center gap-2">
        <div class="w-1.5 h-1.5 rounded-full bg-blue-500/40"></div>
        <span class="text-gray-600">Auto-WebP Ready</span>
      </div>
      <div class="flex-1"></div>
      <button 
        onclick={onClose}
        class="px-6 py-2 bg-white/5 hover:bg-white/10 text-white/40 hover:text-white rounded-xl text-[10px] font-black uppercase tracking-widest transition-all border border-white/10"
      >
        DISMISS
      </button>
    </div>
  </div>
</MissionControlShell>
