<script lang="ts">
  import RichTextEditor from "../RichTextEditor.svelte";

  let { 
    isEditing, 
    editedDraft = $bindable(""), 
    draft_content = $bindable(""), 
    assets,
    isExpanded,
    editorAnnotations
  } = $props();
</script>

<div class="space-y-4 flex-1 overflow-hidden flex flex-col">
  <div class="flex items-center gap-3">
     <div class="w-8 h-px bg-gradient-to-r from-transparent to-blue-500/50"></div>
     <h5 class="text-[11px] font-black uppercase tracking-[0.2em] text-blue-400">Content Outline</h5>
  </div>
  
  <div class="flex-1 rounded-2xl flex flex-col relative group transition-all overflow-hidden {isEditing ? 'border border-white/10 shadow-2xl ring-2 ring-blue-500/30 bg-black/40' : 'bg-transparent'}">
     <RichTextEditor 
       content={isEditing ? editedDraft : draft_content}
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
