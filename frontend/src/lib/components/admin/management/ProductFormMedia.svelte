<script lang="ts">
  import ImagePlus from "lucide-svelte/icons/image-plus";
  import Trash2 from "lucide-svelte/icons/trash-2";
  import AlertTriangle from "lucide-svelte/icons/triangle-alert";
  import { resolveMediaUrl } from "$lib/state/utils";
  import ImagePreviewModal from "../ui/ImagePreviewModal.svelte";

  let {
    formImages = $bindable(),
    formMobileImages = $bindable(),
    onOpenVault
  } = $props<{
    formImages: string[];
    formMobileImages: string[];
    onOpenVault: (isMobile: boolean, index?: number | null) => void;
  }>();

  let previewUrl = $state<string | null>(null);
  let brokenImages = $state<Set<string>>(new Set());

  function handleImageError(imgSrc: string) {
    brokenImages = new Set([...brokenImages, imgSrc]);
  }

  function removeImage(index: number, isMobile = false) {
    if (isMobile) {
      formMobileImages = formMobileImages.filter((_, i) => i !== index);
    } else {
      formImages = formImages.filter((_, i) => i !== index);
    }
  }

  // Clear broken state when images change (e.g. replaced)
  $effect(() => {
    formImages;
    formMobileImages;
    brokenImages = new Set();
  });

  function setAsPrimary(index: number, isMobile = false) {
    if (index === 0) return;
    if (isMobile) {
      const img = formMobileImages[index];
      formMobileImages.splice(index, 1);
      formMobileImages = [img, ...formMobileImages];
    } else {
      const img = formImages[index];
      formImages.splice(index, 1);
      formImages = [img, ...formImages];
    }
  }

  let draggedIndex = $state<number | null>(null);
  let dragSourceIsMobile = $state(false);
  let dropTargetIndex = $state<number | null>(null);

  function handleDragStart(e: DragEvent, index: number, isMobile: boolean) {
    const arr = isMobile ? formMobileImages : formImages;
    if (!arr[index]) return;
    draggedIndex = index;
    dragSourceIsMobile = isMobile;
    if (e.dataTransfer) {
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/plain', index.toString());
    }
  }

  function handleDragOver(e: DragEvent, index: number, targetIsMobile: boolean) {
    e.preventDefault();
    if (draggedIndex === null || dragSourceIsMobile !== targetIsMobile || draggedIndex === index) return;
    dropTargetIndex = index;
  }

  function handleDragLeave() {
    dropTargetIndex = null;
  }

  function handleDrop(e: DragEvent, index: number, targetIsMobile: boolean) {
    e.preventDefault();
    if (draggedIndex === null || dragSourceIsMobile !== targetIsMobile || draggedIndex === index) {
      draggedIndex = null;
      dropTargetIndex = null;
      return;
    }
    
    if (targetIsMobile) {
      const newImages = [...formMobileImages];
      const [movedImage] = newImages.splice(draggedIndex, 1);
      newImages.splice(index, 0, movedImage);
      formMobileImages = newImages;
    } else {
      const newImages = [...formImages];
      const [movedImage] = newImages.splice(draggedIndex, 1);
      newImages.splice(index, 0, movedImage);
      formImages = newImages;
    }

    draggedIndex = null;
    dropTargetIndex = null;
  }

  function handleDragEnd() {
    draggedIndex = null;
    dropTargetIndex = null;
  }
</script>

<div class="max-h-[600px] overflow-y-auto scrollbar-mission pr-1 -mr-1 flex flex-col gap-8">
  
  <ImagePreviewModal imageUrl={previewUrl} onClose={() => previewUrl = null} />

  <!-- DESKTOP IMAGES SECTION -->
  <div class="flex flex-col gap-3">
    <div class="flex items-center justify-between">
      <span class="text-[8px] font-black uppercase tracking-widest text-white/40">Ảnh Desktop (4:5 / 1:1)</span>
      <span class="text-[8px] font-bold text-amber-500/50">{formImages.length} items</span>
    </div>
    <div class="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-2 2xl:grid-cols-3 gap-3">
      {#each formImages.filter(img => img && (img.includes('/') || img.startsWith('blob:'))) as img, i}
        {@const resolved = resolveMediaUrl(img)}
        {@const isBroken = brokenImages.has(resolved)}
        <div
          class="aspect-square rounded-xl bg-white/5 border relative group overflow-hidden shadow-inner flex shrink-0 cursor-pointer active:cursor-grabbing transition-all duration-300
            {draggedIndex === i && !dragSourceIsMobile ? 'opacity-40 scale-95 border-amber-500/50' : 'opacity-100 scale-100'}
            {isBroken ? 'border-red-500/30 bg-red-500/5' : ''}
            {dropTargetIndex === i && !dragSourceIsMobile ? (draggedIndex !== null && draggedIndex < i ? 'border-r-4 border-r-amber-500 border-white/10' : 'border-l-4 border-l-amber-500 border-white/10') : !isBroken ? 'border-white/10' : ''}"
          draggable="true"
          ondragstart={(e) => handleDragStart(e, i, false)}
          ondragover={(e) => handleDragOver(e, i, false)}
          ondragleave={handleDragLeave}
          ondrop={(e) => handleDrop(e, i, false)}
          ondragend={handleDragEnd}
        >
          {#if isBroken}
            <div class="absolute inset-0 flex flex-col items-center justify-center gap-3">
              <AlertTriangle size={24} class="text-red-400/60" />
              <span class="text-[8px] font-black uppercase tracking-widest text-red-400/60">Ảnh bị lỗi</span>
              <div class="flex gap-2">
                <button onclick={() => onOpenVault(false, i)} class="p-2 bg-white/20 text-white rounded-full hover:bg-white/40 transition-all shadow-lg border border-white/30" title="Thay thế ảnh"><ImagePlus size={14} /></button>
                {#if i !== 0}
                  <button onclick={() => setAsPrimary(i, false)} class="px-2 py-1 bg-amber-500/90 text-black text-[9px] font-black uppercase tracking-wider rounded border border-amber-400/50 hover:bg-amber-400 transition-colors shadow-lg">Đại diện</button>
                {/if}
                <button onclick={() => removeImage(i, false)} class="p-2 bg-red-500/20 text-red-500 rounded-full hover:bg-red-500 hover:text-white transition-all shadow-lg border border-red-500/30"><Trash2 size={14} /></button>
              </div>
            </div>
          {:else}
            <img src={resolved} alt="Product Desktop" class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110 pointer-events-auto" onclick={(e) => { e.preventDefault(); e.stopPropagation(); previewUrl = resolved; }} onerror={() => handleImageError(resolved)} />
            <div class="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 flex flex-col items-center justify-center gap-2 transition-opacity pointer-events-none">
              <div class="pointer-events-auto flex gap-2">
                <button onclick={() => onOpenVault(false, i)} class="p-2 bg-white/20 text-white rounded-full hover:bg-white/40 transition-all shadow-lg border border-white/30" title="Thay thế ảnh"><ImagePlus size={14} /></button>
                {#if i !== 0}
                  <button onclick={() => setAsPrimary(i, false)} class="px-2 py-1 bg-amber-500/90 text-black text-[9px] font-black uppercase tracking-wider rounded border border-amber-400/50 hover:bg-amber-400 transition-colors shadow-lg">Đại diện</button>
                {/if}
                <button onclick={() => removeImage(i, false)} class="p-2 bg-red-500/20 text-red-500 rounded-full hover:bg-red-500 hover:text-white transition-all shadow-lg border border-red-500/30"><Trash2 size={14} /></button>
              </div>
            </div>
          {/if}
          {#if i === 0}
            <div class="absolute top-1 left-1 px-1.5 py-0.5 bg-amber-500 text-black rounded text-[7px] font-black uppercase tracking-wider shadow-lg">Ảnh Đại Diện</div>
          {/if}
        </div>
      {/each}

      <button onclick={() => onOpenVault(false)} class="aspect-square rounded-xl border-2 border-dashed border-white/10 bg-white/[0.01] hover:bg-amber-500/[0.03] hover:border-amber-500/40 flex flex-col items-center justify-center gap-2 group transition-all shrink-0">
        <div class="w-8 h-8 rounded-full bg-amber-500/10 flex items-center justify-center text-amber-400/50 group-hover:text-amber-400 transition-colors"><ImagePlus size={16} /></div>
        <div class="text-[8px] font-black uppercase tracking-widest text-white/30 group-hover:text-amber-400 text-center">Desktop<br>Media</div>
      </button>
    </div>
  </div>

  <!-- MOBILE IMAGES SECTION (9:16) -->
  <div class="flex flex-col gap-3">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2">
        <span class="text-[8px] font-black uppercase tracking-widest text-cyan-400">Ảnh Mobile (9:16)</span>
        <div class="px-1.5 py-0.5 rounded bg-cyan-400/10 text-cyan-400 text-[6px] font-black uppercase">Elite Hero v2.2</div>
      </div>
      <span class="text-[8px] font-bold text-cyan-500/50">{formMobileImages.length} items</span>
    </div>
    <div class="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-2 2xl:grid-cols-3 gap-3">
      {#each formMobileImages.filter(img => img && (img.includes('/') || img.startsWith('blob:'))) as img, i}
        {@const resolved = resolveMediaUrl(img)}
        {@const isBroken = brokenImages.has(resolved)}
        <div 
          class="aspect-[9/16] rounded-xl bg-white/5 border relative group overflow-hidden shadow-inner flex shrink-0 cursor-grab active:cursor-grabbing transition-all duration-300
            {draggedIndex === i && dragSourceIsMobile ? 'opacity-40 scale-95 border-cyan-500/50' : 'opacity-100 scale-100'}
            {isBroken ? 'border-red-500/30 bg-red-500/5' : ''}
            {dropTargetIndex === i && dragSourceIsMobile ? (draggedIndex !== null && draggedIndex < i ? 'border-r-4 border-r-cyan-500 border-white/10' : 'border-l-4 border-l-cyan-500 border-white/10') : !isBroken ? 'border-white/10' : ''}"
          draggable="true"
          ondragstart={(e) => handleDragStart(e, i, true)}
          ondragover={(e) => handleDragOver(e, i, true)}
          ondragleave={handleDragLeave}
          ondrop={(e) => handleDrop(e, i, true)}
          ondragend={handleDragEnd}
        >
          {#if isBroken}
            <!-- Broken Mobile Image State -->
            <div class="absolute inset-0 flex flex-col items-center justify-center gap-3">
              <AlertTriangle size={24} class="text-red-400/60" />
              <span class="text-[8px] font-black uppercase tracking-widest text-red-400/60">Ảnh bị lỗi</span>
              <div class="flex gap-2">
                <button onclick={() => onOpenVault(true, i)} class="p-2 bg-white/20 text-white rounded-full hover:bg-white/40 transition-all shadow-lg border border-white/30" title="Thay thế ảnh"><ImagePlus size={14} /></button>
                <button onclick={() => removeImage(i, true)} class="p-2 bg-red-500/20 text-red-500 rounded-full hover:bg-red-500 hover:text-white transition-all shadow-lg border border-red-500/30"><Trash2 size={14} /></button>
              </div>
            </div>
          {:else}
            <img src={resolved} alt="Product Mobile" class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110 pointer-events-auto" onclick={() => previewUrl = resolved} onerror={() => handleImageError(resolved)} />
            <div class="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 flex flex-col items-center justify-center gap-2 transition-opacity pointer-events-none">
              <div class="pointer-events-auto flex gap-2">
                <button onclick={() => onOpenVault(true, i)} class="p-2 bg-white/20 text-white rounded-full hover:bg-white/40 transition-all shadow-lg border border-white/30" title="Thay thế ảnh"><ImagePlus size={14} /></button>
                <button onclick={() => removeImage(i, true)} class="p-2 bg-red-500/20 text-red-500 rounded-full hover:bg-red-500 hover:text-white transition-all shadow-lg border border-red-500/30 pointer-events-auto"><Trash2 size={14} /></button>
              </div>
            </div>
          {/if}
        </div>
      {/each}

      <button onclick={() => onOpenVault(true)} class="aspect-[9/16] rounded-xl border-2 border-dashed border-white/10 bg-white/[0.01] hover:bg-cyan-500/[0.03] hover:border-cyan-500/40 flex flex-col items-center justify-center gap-2 group transition-all shrink-0">
        <div class="w-8 h-8 rounded-full bg-cyan-500/10 flex items-center justify-center text-cyan-400/50 group-hover:text-cyan-400 transition-colors"><ImagePlus size={16} /></div>
        <div class="text-[8px] font-black uppercase tracking-widest text-white/30 group-hover:text-cyan-400 text-center">Mobile<br>Media</div>
      </button>
    </div>
  </div>

</div>
