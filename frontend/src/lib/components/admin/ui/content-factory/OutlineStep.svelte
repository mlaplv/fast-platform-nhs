<script lang="ts">
  import TiptapEditor from "../tiptap/TiptapEditor.svelte";
  import type { MediaAsset } from "$lib/state/types";

  interface OutlineSection {
    heading?: string;
    H2?: string;
    H3?: string;
    title?: string;
    Title?: string;
    content?: string;
    Content?: string;
    body?: string;
    description?: string;
  }

  interface RawOutline {
    html?: string;
    sections?: OutlineSection[];
    outline?: {
      sections?: OutlineSection[];
    };
  }

  let {
    isEditing,
    editedDraft = $bindable(),
    draft_content = $bindable(),
    outline = {} as RawOutline,
    assets = [] as (MediaAsset | string)[],
    isExpanded,
    editorAnnotations,
    step = 3
  } = $props();

  // Rule R82.41: Smart Data Mapping — Map structured sections to editor content if draft is empty
  let displayContent = $derived.by(() => {
    // 1. Helper: Convert structured outline (sections) to HTML
    const getStructuredOutline = () => {
      const rawOutline = outline as RawOutline;
      if (rawOutline?.html) return rawOutline.html;

      const sections = rawOutline?.sections || rawOutline?.outline?.sections || (Array.isArray(rawOutline) ? rawOutline as unknown as OutlineSection[] : []);

      if (sections && sections.length > 0) {
        return sections.map((s: OutlineSection) => {
           const header = s.heading || s.H2 || s.H3 || s.title || s.Title || "";
           const body = s.content || s.Content || s.body || s.description || "";

           const hText = header.replace(/^(H2|H3):/i, "").trim();
           const tag = header.toUpperCase().startsWith("H3") ? "h3" : "h2";
           return `<${tag}>${hText}</${tag}><p>${body}</p>`;
        }).join("\n");
      }
      return "";
    };

    // 2. Step 3 logic: ALWAYS prioritize the outline.
    let base = (isEditing ? editedDraft : "") || getStructuredOutline();

    // 3. Rule R82.42: Image Placeholder Replacement — Ported from DraftStep
    if (base && base.includes("[IMAGE_")) {
      const assetList = Array.isArray(assets) ? assets : [];
      assetList.forEach((asset, i) => {
        const url = typeof asset === 'string' ? asset : asset.url;
        const placeholder = `[IMAGE_${i + 1}]`;
        // Handle markers inside src first
        const srcPattern = new RegExp(`(src|href)=["']\\s*${placeholder.replace('[', '\\[').replace(']', '\\]')}\\s*["']`, 'g');
        base = base.replace(srcPattern, `$1="${url}"`);

        // Then handle standalone markers (even if wrapped in figure by AI)
        const figurePattern = new RegExp(`(<figure[^>]*>\\s*)?${placeholder.replace('[', '\\[').replace(']', '\\]')}(\\s*<\\/figure>)?`, 'g');
        base = base.replace(figurePattern, `<figure class="content-image"><img src="${url}" alt="content image" loading="lazy" /></figure>`);
      });
      // Cleanup leftover placeholders
      base = base.replace(/\[IMAGE_\d+\]/g, "");
    }

    return base || "";
  });

  // Ensure editedDraft is initialized when entering edit mode if it was empty
  $effect(() => {
    if (isEditing && !editedDraft) {
      const fallback = displayContent;
      if (fallback) editedDraft = fallback;
    }
  });
</script>

<div class="space-y-4 flex-1 overflow-hidden flex flex-col">
  <div class="flex-1 rounded-2xl flex flex-col relative group transition-all overflow-hidden {isEditing ? 'border border-white/10 shadow-2xl ring-2 ring-blue-500/30 bg-black/40' : 'bg-transparent'}">
     <TiptapEditor 
       content={displayContent}
       assets={assets}
       onChange={(val) => {
          if (isEditing) editedDraft = val;
          else draft_content = val;
       }}
       editable={isEditing}
       placeholder="Đang tạo dàn ý..."
       fullScreen={isExpanded}
       annotations={editorAnnotations}
     />
  </div>
</div>
