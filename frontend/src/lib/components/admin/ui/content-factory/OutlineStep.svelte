<script lang="ts">
  import TiptapEditor from "../tiptap/TiptapEditor.svelte";
  import type { MediaAsset } from "$lib/state/types";
  import { purifyAIContent } from "$lib/utils/purify";

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
  }

  let {
    isEditing,
    editedOutline = $bindable(),
    outline = {} as RawOutline,
    assets = [] as (MediaAsset | string)[],
    isExpanded,
    editorAnnotations = [],
    step = 3,
    isProcessing = false
  }: Props = $props();
  
  function fixUrl(url: string | null): string {
    if (!url) return "";
    let p = url;
    if (p.startsWith("http")) return p;
    if (p.startsWith("static/")) p = "/" + p;
    if (p.startsWith("uploads/")) p = "/" + p;
    if (!p.startsWith("/")) p = "/uploads/" + p;
    
    if (p.startsWith("/static/uploads/")) p = p.replace("/static/uploads/", "/uploads/");
    return p;
  }

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

    // 3. Rule R82.42: Image Placeholder Replacement — Ported from DraftStep
    if (base && base.includes("[IMAGE_")) {
      const assetList = Array.isArray(assets) ? assets : [];
      assetList.forEach((asset, i) => {
        const url = typeof asset === 'string' ? asset : (asset.file_path || asset.url || '');
        const local = fixUrl(url);
        const placeholder = `[IMAGE_${i + 1}]`;
        // Handle markers inside src first
        const srcPattern = new RegExp(`(src|href)=["']\\s*${placeholder.replace('[', '\\[').replace(']', '\\]')}\\s*["']`, 'g');
        base = base.replace(srcPattern, `$1="${local}"`);

        // Then handle standalone markers (even if wrapped in figure by AI)
        const figurePattern = new RegExp(`(<figure[^>]*>\\s*)?${placeholder.replace('[', '\\[').replace(']', '\\]')}(\\s*<\\/figure>)?`, 'g');
        base = base.replace(figurePattern, `<figure class="content-image"><img src="${local}" alt="content image" loading="lazy" /></figure>`);
      });
      // Cleanup leftover placeholders
      base = base.replace(/\[IMAGE_\d+\]/g, "");
    }

    // 4. Final Purification (Senior Architect V2026)
    return purifyAIContent(base);
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
  <div class="rounded-2xl flex flex-col relative group transition-all {isEditing ? 'border border-white/10 shadow-2xl ring-2 ring-blue-500/30 bg-black/40' : 'bg-transparent'}">
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
