<script lang="ts">
  import TiptapEditor from "../tiptap/TiptapEditor.svelte";
  import type { MediaAsset } from "$lib/state/types";
  import { purifyAIContent } from "$lib/utils/purify";
  import { resolveMediaUrl, processContentImages } from "$lib/state/utils";

  interface OutlineSection {
    heading?: string;
    H2?: string;
    H3?: string;
    title?: string;
    Title?: string;
    content?: string;
    Content?: string;
    body?: string;
    text?: string;
    description?: string;
  }

  type RawOutline = {
    html?: string;
    sections?: OutlineSection[];
    outline?: {
      sections?: OutlineSection[];
    };
    outline_data?: {
      sections?: OutlineSection[];
    };
  } | OutlineSection[] | string;

  interface Props {
    isEditing: boolean;
    editedOutline: string;
    outline: RawOutline;
    assets: (MediaAsset | string)[];
    isExpanded: boolean;
    editorAnnotations?: unknown[];
    step?: number;
    isProcessing?: boolean;
    campaign_id: string;
  }

  let {
    isEditing,
    editedOutline = $bindable(),
    outline = {} as RawOutline,
    assets = [] as (MediaAsset | string)[],
    isExpanded,
    editorAnnotations = [],
    step = 3,
    isProcessing = false,
    campaign_id,
  }: Props = $props();

  // Rule R82.41: Smart Data Mapping — Map structured sections to editor content if draft is empty
  let displayContent = $derived.by(() => {
    // 1. Helper: Convert structured outline (sections) to HTML
    const getStructuredOutline = (): string => {
      if (typeof outline === 'string') return outline;
      
      // Robust type guarding for the union
      const isPlainObject = (val: unknown): val is Record<string, unknown> => 
        typeof val === 'object' && val !== null && !Array.isArray(val);

      if (isPlainObject(outline) && 'html' in outline && typeof outline.html === 'string') {
        return outline.html;
      }

      const sections: OutlineSection[] = 
        isPlainObject(outline)
          ? ((outline.sections as OutlineSection[]) || 
             (outline.outline as any)?.sections || // fallback for nested
             (outline.outline_data as any)?.sections || [])
          : (Array.isArray(outline) ? outline : []);

      if (sections.length > 0) {
        return sections.map((s) => {
           const header = s.heading || s.H2 || s.H3 || s.title || s.Title || "";
           const body = s.content || s.Content || s.body || s.description || s.text || "";

           const hText = header.replace(/^(H2|H3):/i, "").trim();
           const tag = header.toUpperCase().startsWith("H3") ? "h3" : "h2";
           return `<${tag}>${hText}</${tag}><p>${body}</p>`;
        }).join("\n");
      }
      return "";
    };

    // 2. Step 3 logic: ALWAYS prioritize the outline.
    let base = (isEditing ? editedOutline : "") || getStructuredOutline();

    // 3. Rule R82.42: Image Placeholder Replacement (Elite V2.2 Unified)
    const currentAssets = xohiImageStore.assets.length > 0 ? xohiImageStore.assets : assets;
    return processContentImages(base, currentAssets);
  });

  // Ensure editedOutline is initialized when entering edit mode if it was empty
  $effect(() => {
    if (isEditing && !editedOutline) {
      const fallback = displayContent;
      if (fallback) editedOutline = fallback;
    }
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
     {#if isProcessing && !displayContent}
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
       content={displayContent}
       assets={assets}
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
