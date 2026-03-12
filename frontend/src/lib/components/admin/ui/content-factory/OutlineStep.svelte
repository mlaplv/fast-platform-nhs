<script lang="ts">
  import RichTextEditor from "../RichTextEditor.svelte";

  let { 
    isEditing, 
    editedDraft = $bindable(""), 
    draft_content = $bindable(""), 
    outline = {},
    assets,
    isExpanded,
    editorAnnotations,
    step = 3
  } = $props();

  // Rule R82.41: Smart Data Mapping — Map structured sections to editor content if draft is empty
  let displayContent = $derived.by(() => {
    // 1. Helper: Convert structured outline (sections) to HTML
    const getStructuredOutline = () => {
      const rawOutline = outline as any;
      if (rawOutline?.html) return rawOutline.html;
      const sections = rawOutline?.sections || rawOutline?.outline?.sections || (Array.isArray(rawOutline) ? rawOutline : []);
      if (sections && sections.length > 0) {
        return sections.map((s: any) => {
           const header = s.heading || s.H2 || s.H3 || s.title || s.Title || "";
           const body = s.content || s.Content || s.body || s.description || "";
           
           const hText = header.replace(/^(H2|H3):/i, "").trim();
           const tag = header.toUpperCase().startsWith("H3") ? "h3" : "h2";
           return `<${tag}>${hText}</${tag}><p>${body}</p>`;
        }).join("\n");
      }
      return "";
    };

    // 2. Logic based on current campaign progress (step prop)
    if (step === 3) {
      // In Step 3, we ALWAYS prioritize the outline.
      if (isEditing) return editedDraft || getStructuredOutline();
      return getStructuredOutline();
    } else {
      // Step 4 or beyond: prioritize draft_content but fallback to outline if empty
      if (isEditing) return editedDraft || draft_content || getStructuredOutline();
      return draft_content || getStructuredOutline();
    }
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
  <div class="flex items-center gap-3">
     <div class="w-8 h-px bg-gradient-to-r from-transparent to-blue-500/50"></div>
     <h5 class="text-[11px] font-black uppercase tracking-[0.2em] text-blue-400">Dàn ý bài viết</h5>
  </div>
  
  <div class="flex-1 rounded-2xl flex flex-col relative group transition-all overflow-hidden {isEditing ? 'border border-white/10 shadow-2xl ring-2 ring-blue-500/30 bg-black/40' : 'bg-transparent'}">
     <RichTextEditor 
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
