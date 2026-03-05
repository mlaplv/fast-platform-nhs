<script lang="ts">
  import { slide } from "svelte/transition";
  import X from "lucide-svelte/icons/x";

  let {
    editingId,
    formParentId,
    formName = $bindable(),
    formSlug = $bindable(),
    onSave,
    onClose,
    generateSlug,
  } = $props<{
    editingId: string | null;
    formParentId: string | null;
    formName: string;
    formSlug: string;
    onSave: () => void;
    onClose: () => void;
    generateSlug: (name: string) => string;
  }>();
</script>

<div
  class="bg-[#050505]/95 md:bg-black/60 md:backdrop-blur-md border border-[#00FFFF]/20 rounded-2xl p-5 flex flex-col gap-4 shadow-[0_8px_30px_rgba(0,0,0,0.5)] my-2 relative overflow-hidden"
  transition:slide={{ duration: 300, axis: "y" }}
>
  <div
    class="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-[#00FFFF]/50 to-transparent opacity-50"
  ></div>
  <div
    class="text-[11px] font-bold text-[#00FFFF] uppercase tracking-widest flex items-center gap-2"
  >
    {editingId ? "✏️ Modify Taxonomy Node" : "➕ Initialize Taxonomy Node"}
    {#if formParentId}
      <span
        class="text-gray-500 font-mono text-[9px] px-2 py-0.5 rounded bg-white/5 border border-white/10"
        >// Sub-category link active</span
      >
    {/if}
  </div>
  <div class="flex items-center gap-3">
    <div
      class="flex-1 relative group bg-black/50 border border-white/5 hover:border-white/10 focus-within:border-[#00FFFF]/40 rounded-xl transition-colors shadow-inner"
    >
      <input
        bind:value={formName}
        oninput={() => {
          if (!editingId) formSlug = generateSlug(formName);
        }}
        placeholder="Enter taxonomy name..."
        class="w-full bg-transparent py-2.5 px-4 text-sm text-gray-100 placeholder:text-gray-600 focus:outline-none focus:ring-1 focus:ring-[#00FFFF]/20 rounded-xl transition-shadow"
      />
    </div>
    <div
      class="w-48 relative group bg-black/50 border border-white/5 hover:border-white/10 focus-within:border-[#00FFFF]/40 rounded-xl transition-colors shadow-inner"
    >
      <span
        class="absolute left-3 top-1/2 -translate-y-1/2 text-[9px] text-gray-500 font-mono"
        >ID:</span
      >
      <input
        bind:value={formSlug}
        placeholder="slug-id..."
        class="w-full bg-transparent py-2.5 pl-8 pr-4 text-[11px] text-gray-300 placeholder:text-gray-600 focus:outline-none focus:ring-1 focus:ring-[#00FFFF]/20 rounded-xl font-mono transition-shadow"
      />
    </div>
    <button
      onclick={onSave}
      class="px-5 py-2.5 bg-gradient-to-r from-[#00FFFF]/20 to-[#00FFFF]/5 border border-[#00FFFF]/40 rounded-xl text-[11px] font-bold font-mono text-[#00FFFF] hover:text-white hover:shadow-[0_0_15px_rgba(0,255,255,0.2)] hover:scale-[1.02] transition-all duration-300 uppercase tracking-widest whitespace-nowrap"
    >
      {editingId ? "Execute_Update" : "Commit_Node"}
    </button>
    <button
      onclick={onClose}
      class="p-2.5 text-gray-500 hover:text-red-400 bg-white/5 hover:bg-red-500/10 border border-transparent hover:border-red-500/20 rounded-xl transition-all"
      title="Cancel"
    >
      <X size={16} />
    </button>
  </div>
</div>
