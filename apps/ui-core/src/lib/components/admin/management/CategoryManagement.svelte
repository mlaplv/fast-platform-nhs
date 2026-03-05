<script lang="ts">
  import { fade } from "svelte/transition";
  import FolderTree from "lucide-svelte/icons/folder-tree";
  import Plus from "lucide-svelte/icons/plus";
  import Search from "lucide-svelte/icons/search";
  import Layers from "lucide-svelte/icons/layers";
  import Trash2 from "lucide-svelte/icons/trash-2";
  import CheckSquare from "lucide-svelte/icons/check-square";
  import Square from "lucide-svelte/icons/square";
  import { nanobot } from "$lib/state/nanobot.svelte";
  import { apiClient } from "$lib/utils/apiClient";
  import CategoryForm from "./CategoryForm.svelte";
  import CategoryTree from "./CategoryTree.svelte";

  interface Category {
    id: string;
    name: string;
    slug: string;
    productCount: number;
    children: Category[];
  }

  let categories = $state<Category[]>([]),
    isLoading = $state(true),
    searchTerm = $state(""),
    showForm = $state(false);
  let editingId = $state<string | null>(null),
    formName = $state(""),
    formSlug = $state(""),
    formParentId = $state<string | null>(null);
  let selectedIds = $state<Set<string>>(new Set()),
    expandedIds = $state<Set<string>>(new Set());

  let filteredCategories = $derived.by(() => {
    if (!searchTerm) return categories;
    const t = searchTerm.toLowerCase();
    return categories.filter(
      (c) =>
        c.name?.toLowerCase().includes(t) ||
        c.slug?.toLowerCase().includes(t) ||
        c.children?.some((ch) => ch.name?.toLowerCase().includes(t)),
    );
  });

  let allSelected = $derived(
    categories.length > 0 && selectedIds.size === categories.length,
  );

  $effect(() => {
    (async () => {
      try {
        categories = await apiClient.get<Category[]>("/api/v1/categories");
      } catch {
        categories = [];
      } finally {
        isLoading = false;
      }
    })();
  });

  // V22: Voice Mutation Injection - Category Management
  $effect(() => {
    const data = nanobot.currentData;
    const action = nanobot.commandAction;

    if (data?.ui_action === "show_category_management" && data?.intent_type === "MUTATE" && !showForm) {
      editingId = null;
      formName = data.name || data.title || "";
      formSlug = genSlug(formName);
      formParentId = data.parentId || null;
      showForm = true;
      nanobot.clearCurrentData();
      return;
    }

    if (action?.entity === "category") {
      if (action.verb === "create") {
        openCreate();
        if (action.args) {
          formName = action.args;
          formSlug = genSlug(action.args);
        }
      } else if (action.verb === "search" && action.args) searchTerm = action.args;
      nanobot.clearCommandAction();
    }
  });

  function genSlug(n: string) {
    return n
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/đ/g, "d")
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/(^-|-$)/g, "");
  }
  function openCreate(p: string | null = null) {
    editingId = null;
    formName = "";
    formSlug = "";
    formParentId = p;
    showForm = true;
  }
  function openEdit(cat: Category, p: string | null = null) {
    editingId = cat.id;
    formName = cat.name;
    formSlug = cat.slug;
    formParentId = p;
    showForm = true;
  }
  function toggleSelect(id: string) {
    const n = new Set(selectedIds);
    n.has(id) ? n.delete(id) : n.add(id);
    selectedIds = n;
  }
  function toggleExpand(id: string) {
    const n = new Set(expandedIds);
    n.has(id) ? n.delete(id) : n.add(id);
    expandedIds = n;
  }

  async function save() {
    if (!formName.trim()) return;
    const s = formSlug || genSlug(formName);
    const p = { name: formName.trim(), slug: s, parentId: formParentId };
    try {
      if (editingId) {
        await apiClient.patch(`/api/v1/categories/${editingId}`, p);
        if (formParentId) {
          const par = categories.find((c) => c.id === formParentId);
          if (par) {
            const i = par.children.findIndex((c) => c.id === editingId);
            if (i >= 0) {
              par.children[i].name = formName.trim();
              par.children[i].slug = s;
            }
          }
        } else {
          const i = categories.findIndex((c) => c.id === editingId);
          if (i >= 0) {
            categories[i].name = formName.trim();
            categories[i].slug = s;
          }
        }
      } else {
        const res = await apiClient.post<Category>("/api/v1/categories", p);
        if (formParentId) {
          const par = categories.find((c) => c.id === formParentId);
          if (par) par.children = [...par.children, res];
        } else categories = [...categories, res];
      }
      showForm = false;
    } catch {
      console.error("Save Category Failed");
    }
  }

  async function del(id: string, p: string | null = null) {
    try {
      await apiClient.delete(`/api/v1/categories/${id}`);
    } catch {}
    if (p) {
      const par = categories.find((c) => c.id === p);
      if (par) par.children = par.children.filter((c) => c.id !== id);
    } else categories = categories.filter((c) => c.id !== id);
    selectedIds.delete(id);
    selectedIds = new Set(selectedIds);
  }
</script>

<div class="w-full h-full flex flex-col relative bg-[#050505]">
  <div class="flex flex-col gap-6 p-6 border-b border-white/[0.05]">
    {#if showForm}<CategoryForm
        {editingId}
        {formParentId}
        bind:formName
        bind:formSlug
        onSave={save}
        onClose={() => (showForm = false)}
        generateSlug={genSlug}
      />{/if}
    <div
      class="flex flex-col lg:flex-row lg:items-center md:gap-4 gap-3 bg-white/[0.02] border border-white/10 p-3 sm:p-2.5 rounded-2xl"
    >
      <!-- Search Input -->
      <div class="flex-1 relative group w-full lg:min-w-[250px]">
        <div class="absolute inset-y-0 left-4 flex items-center pointer-events-none">
          <Search size={16} class="text-gray-500 group-focus-within:text-neon-cyan group-focus-within:scale-110 transition-all" />
        </div>
        <input
          bind:value={searchTerm}
          type="text"
          placeholder="QUERY_TAXONOMY..."
          class="w-full bg-black/50 border border-white/5 rounded-xl py-3 pl-12 pr-4 text-[11px] font-mono text-gray-200 placeholder:text-gray-600 focus:outline-none focus:border-neon-cyan/50 focus:ring-2 focus:ring-neon-cyan/20 transition-all uppercase tracking-widest shadow-inner shadow-black/50"
        />
      </div>

      <!-- Actions & Stats -->
      <div class="flex items-center flex-wrap sm:flex-nowrap justify-between lg:justify-end gap-3 w-full lg:w-auto mt-1 lg:mt-0 lg:pr-2">
        <div class="flex items-center gap-2">
          {#if selectedIds.size > 0}
            <button
              onclick={() => {
                apiClient.post("/api/v1/categories/bulk-delete", {
                  ids: Array.from(selectedIds),
                });
                categories = categories.filter((c) => !selectedIds.has(c.id));
                selectedIds = new Set();
              }}
              class="flex items-center gap-2 px-3 py-2 text-[10px] font-mono uppercase bg-red-500/10 border border-red-500/30 text-red-400 rounded-xl hover:bg-red-500/20 transition-all shadow-[0_0_15px_rgba(239,68,68,0.1)]"
              ><Trash2 size={12} class="hidden sm:block"/><Trash2 size={14} class="sm:hidden"/><span class="hidden sm:inline">Purge ({selectedIds.size})</span><span class="sm:hidden">({selectedIds.size})</span></button
            >
          {/if}
          <div
            class="flex sm:hidden items-center gap-2 px-3 py-2 bg-gradient-to-br from-neon-cyan/10 to-transparent border border-neon-cyan/30 rounded-xl text-[10px] font-mono text-neon-cyan uppercase tracking-[0.2em] shadow-[0_0_15px_rgba(0,255,255,0.05)]"
          >
            <Layers size={14} class="animate-pulse opacity-70" />
            <span class="font-bold">{categories.length}</span>
          </div>
        </div>

        <div class="flex items-center gap-2 sm:gap-3 ml-auto sm:ml-0">
          <div
            class="hidden sm:flex items-center gap-2 px-4 py-2 bg-gradient-to-br from-neon-cyan/10 to-transparent border border-neon-cyan/30 rounded-xl text-[10px] font-mono text-neon-cyan uppercase tracking-[0.2em] shadow-[0_0_15px_rgba(0,255,255,0.05)]"
          >
            <Layers size={14} class="animate-pulse opacity-70" />
            <span class="font-bold">{categories.length}</span> Nodes
          </div>

          <button
            onclick={() => openCreate()}
            class="flex items-center gap-2 px-3 sm:px-4 py-2 sm:py-2 text-[10px] w-full sm:w-auto justify-center font-bold tracking-widest font-mono uppercase bg-neon-cyan/10 border border-neon-cyan/30 text-neon-cyan hover:bg-neon-cyan/20 hover:text-white rounded-xl transition-all duration-300"
          >
            <Plus size={14} class="sm:hidden" /><Plus size={12} class="hidden sm:block" /> <span class="hidden sm:inline">Init_Node</span>
          </button>
        </div>
      </div>
    </div>
  </div>

  <div class="flex-1 overflow-y-auto custom-scrollbar p-6">
    {#if isLoading}
      <div class="h-full flex items-center justify-center animate-pulse">
        <span
          class="text-[9px] font-mono text-[#00FFFF]/40 uppercase tracking-[0.3em]"
          >Mapping Taxonomy...</span
        >
      </div>
    {:else}
      <CategoryTree
        categories={filteredCategories}
        {selectedIds}
        {expandedIds}
        onToggleSelect={toggleSelect}
        onToggleExpand={toggleExpand}
        onAddSub={openCreate}
        onEdit={openEdit}
        onDelete={del}
      />
    {/if}
  </div>
</div>

<style>
  .custom-scrollbar::-webkit-scrollbar {
    width: 4px;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 20px;
  }
</style>
