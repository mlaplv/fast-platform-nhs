<script lang="ts">
  import { fade } from "svelte/transition";
  import FolderTree from "lucide-svelte/icons/folder-tree";
  import Plus from "lucide-svelte/icons/plus";
  import Search from "lucide-svelte/icons/search";
  import Layers from "lucide-svelte/icons/layers";
  import Trash2 from "lucide-svelte/icons/trash-2";
  import CheckSquare from "lucide-svelte/icons/check-square";
  import Square from "lucide-svelte/icons/square";
  import Eye from "lucide-svelte/icons/eye";
  import EyeOff from "lucide-svelte/icons/eye-off";
  import { useNanobot } from "$lib/state/nanobot.svelte";
  const nanobot = useNanobot();
  import { apiClient } from "$lib/utils/apiClient";
  import { slugify } from "$lib/utils/format";
  import type { Category, BaseWidgetProps } from "$lib/types";
  import CategoryForm from "./CategoryForm.svelte";
  import CategoryTree from "./CategoryTree.svelte";

  let { data = {} } = $props<BaseWidgetProps>();

  let categories = $state<Category[]>([]),
    isLoading = $state(true),
    searchTerm = $state(""),
    showForm = $state(false);
  let editingId = $state<string | null>(null),
    formName = $state(""),
    formSlug = $state(""),
    formDescription = $state(""),
    formSeoTitle = $state(""),
    formSeoDescription = $state(""),
    formImage = $state(""),
    formIcon = $state(""),
    formShowOnMobile = $state(true),
    formShowOnDesktop = $state(true),
    formParentId = $state<string | null>(null),
    formFaqs = $state<{ question: string; answer: string }[]>([]);
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
        const res = await apiClient.get<{ data: Category[]; total: number }>("/api/v1/categories");
        categories = res.data || [];
      } catch (e: unknown) {
        const err = e as Error;
        console.error("[CategoryManagement] Load failed:", err);
        categories = [];
      } finally {
        isLoading = false;
      }
    })();
  });

  // V22: Voice Mutation Injection - Category Management
  $effect(() => {
    const data = nanobot.currentData as Record<string, unknown>;
    const action = nanobot.commandAction;

    if (data?.ui_action === "show_category_management" && data?.intent_type === "MUTATE" && !showForm) {
      editingId = null;
      formName = (data?.name as string) || (data?.title as string) || "";
      formSlug = genSlug(formName);
      formParentId = (data?.parentId as string) || null;
      showForm = true;
      nanobot.clearCurrentData();
      return;
    }

    if (action?.entity === "category") {
      if (action.verb === "create") {
        if (nanobot.consumeCommand("create", "category")) {
          openCreate();
          if (action.args) {
            formName = action.args;
            formSlug = genSlug(action.args);
          }
        }
      } else if (action.verb === "search" && action.args) {
        if (nanobot.consumeCommand("search", "category")) {
          searchTerm = action.args;
        }
      }
    }
  });

  function genSlug(n: string) {
    return slugify(n);
  }
  function openCreate(p: string | null = null) {
    editingId = null;
    formName = "";
    formSlug = "";
    formDescription = "";
    formSeoTitle = "";
    formSeoDescription = "";
    formImage = "";
    formIcon = "";
    formShowOnMobile = true;
    formShowOnDesktop = true;
    formFaqs = [];
    formParentId = p;
    showForm = true;
  }
  function openEdit(cat: Category, p: string | null = null) {
    console.log("[CategoryManagement] Opening Edit. Category Data Snapshot:", $state.snapshot(cat));
    editingId = cat.id;
    formName = cat.name;
    formSlug = cat.slug;
    formDescription = cat.description || "";
    formSeoTitle = cat.seoTitle || "";
    formSeoDescription = cat.seoDescription || "";
    formImage = cat.image || "";
    formIcon = cat.icon || "";
    formShowOnMobile = cat.showOnMobile ?? true;
    formShowOnDesktop = cat.showOnDesktop ?? true;
    
    // Elite V2.2: Dual-Key Metadata Probe (Metadata vs CategoryMetadata)
    // Pydantic có thể serialize vào 'metadata' (key gốc) hoặc 'category_metadata' (alias)
    const raw: any = cat;
    const meta = raw.metadata || raw.category_metadata;
    formFaqs = meta?.faqs || [];
    
    console.log("[CategoryManagement] Metadata Found:", $state.snapshot(meta));
    console.log("[CategoryManagement] Form FAQs initialized:", $state.snapshot(formFaqs));
    formParentId = p;
    showForm = true;
  }
  function toggleSelect(id: string) {
    const n = new Set(selectedIds);
    n.has(id) ? n.delete(id) : n.add(id);
    selectedIds = n;
  }
  function toggleSelectAll() {
    if (allSelected) {
      selectedIds = new Set();
    } else {
      const allIds = new Set<string>();
      const collect = (list: Category[]) => {
        list.forEach(c => {
          allIds.add(c.id);
          if (c.children) collect(c.children);
        });
      };
      collect(categories);
      selectedIds = allIds;
    }
  }
  function toggleExpand(id: string) {
    const n = new Set(expandedIds);
    n.has(id) ? n.delete(id) : n.add(id);
    expandedIds = n;
  }

  async function save() {
    if (!formName.trim()) return;
    const s = formSlug || genSlug(formName);
    const p = {
      name: formName.trim(),
      slug: s,
      parentId: formParentId,
      description: formDescription,
      seoTitle: formSeoTitle,
      seoDescription: formSeoDescription,
      image: formImage,
      icon: formIcon,
      show_on_mobile: formShowOnMobile,
      show_on_desktop: formShowOnDesktop,
      metadata: { faqs: formFaqs }
    };
    try {
      if (editingId) {
        const res = await apiClient.patch<{ data: Category }>(`/api/v1/categories/${editingId}`, p);
        const updated = res.data;
        if (!updated) throw new Error("No data returned from update");

        if (formParentId) {
          const par = categories.find((c) => c.id === formParentId);
          if (par) {
            const i = par.children.findIndex((c) => c.id === editingId);
            if (i >= 0) {
              // Preserve children if backend returned empty list but we have them locally
              const existingChildren = par.children[i].children;
              const existingCount = par.children[i].productCount;
              par.children[i] = { ...updated, children: existingChildren, productCount: existingCount };
            }
          }
        } else {
          const i = categories.findIndex((c) => c.id === editingId);
          if (i >= 0) {
            const existingChildren = categories[i].children;
            const existingCount = categories[i].productCount;
            // Elite V2.2: Deep sync updated data to local store
            // Chú ý: Backend trả về JSON với các key alias (snake_case)
            const up: any = updated;
            categories[i] = { 
              ...categories[i],
              name: up.name ?? categories[i].name,
              slug: up.slug ?? categories[i].slug,
              description: up.description ?? categories[i].description,
              seoTitle: up.seo_title ?? categories[i].seoTitle,
              seoDescription: up.seo_description ?? categories[i].seoDescription,
              image: up.image ?? categories[i].image,
              icon: up.icon ?? categories[i].icon,
              showOnMobile: up.show_on_mobile ?? categories[i].showOnMobile,
              showOnDesktop: up.show_on_desktop ?? categories[i].showOnDesktop,
              category_metadata: up.category_metadata || { faqs: [] },
              children: existingChildren, 
              productCount: existingCount
            };
          }
        }
      } else {
        const res = await apiClient.post<{ data: Category }>("/api/v1/categories", p);
        const created = res.data;
        if (!created) throw new Error("No data returned from creation");

        if (formParentId) {
          const par = categories.find((c) => c.id === formParentId);
          if (par) {
            par.children = [...(par.children || []), created];
            // Auto expand parent to show new node
            const n = new Set(expandedIds);
            n.add(formParentId);
            expandedIds = n;
          }
        } else {
          categories = [...categories, created];
        }
      }
      showForm = false;
      nanobot.showToast(editingId ? "Cập nhật thành công" : "Khởi tạo thành công", "success");
    } catch (e) {
      console.error("[CategoryManagement] Save failed:", e);
      nanobot.showToast("Lưu danh mục thất bại", "error");
    }
  }

  async function del(id: string, p: string | null = null) {
    try {
      await apiClient.delete(`/api/v1/categories/${id}`);
      if (p) {
        const par = categories.find((c) => c.id === p);
        if (par) par.children = par.children.filter((c) => c.id !== id);
      } else {
        categories = categories.filter((c) => c.id !== id);
      }
      selectedIds.delete(id);
      selectedIds = new Set(selectedIds);
      nanobot.showToast("Xóa danh mục thành công", "success");
    } catch (e) {
      console.error("[CategoryManagement] Delete failed:", e);
      nanobot.showToast("Xóa danh mục thất bại", "error");
    }
  }

  async function bulkDelete() {
    if (selectedIds.size === 0) return;
    const ids = Array.from(selectedIds);
    try {
      await apiClient.post("/api/v1/categories/bulk-delete", { ids });
      // Remove from top level and children
      categories = categories.filter((c) => !selectedIds.has(c.id));
      categories.forEach(c => {
        if (c.children) c.children = c.children.filter(ch => !selectedIds.has(ch.id));
      });
      selectedIds = new Set();
      nanobot.showToast(`Đã xóa ${ids.length} danh mục`, "success");
    } catch (e) {
      console.error("[CategoryManagement] Bulk delete failed:", e);
      nanobot.showToast("Xóa hàng loạt thất bại", "error");
    }
  }

  async function bulkStatusUpdate(active: boolean) {
    if (selectedIds.size === 0) return;
    const ids = Array.from(selectedIds);
    try {
      await apiClient.post("/api/v1/categories/bulk-status", { ids, active });
      // R1.5: Zero-hydration local update to avoid full tree re-fetch
      const updateTree = (list: Category[]) => {
        return list.map(c => {
          if (selectedIds.has(c.id)) {
            c = { ...c, showOnMobile: active, showOnDesktop: active };
          }
          if (c.children && c.children.length > 0) {
            c.children = updateTree(c.children);
          }
          return c;
        });
      };
      categories = updateTree(categories);
      nanobot.showToast(`Đã ${active ? 'kích hoạt' : 'vô hiệu hóa'} ${ids.length} danh mục`, "success");
    } catch (e) {
      console.error("[CategoryManagement] Bulk status update failed:", e);
      nanobot.showToast("Cập nhật trạng thái thất bại", "error");
    }
  }

  async function handleReorder(newOrder: Category[]) {
    categories = newOrder;
    try {
      await apiClient.patch("/api/v1/categories/reorder", { ids: newOrder.map(c => c.id) });
      nanobot.showToast("Cập nhật vị trí thành công", "success");
    } catch (e) {
      console.error("[CategoryManagement] Reorder failed:", e);
      nanobot.showToast("Lưu vị trí thất bại", "error");
    }
  }
</script>

<div class="w-full h-full flex flex-col relative bg-[#050505]">
  <div class="flex flex-col gap-6 p-6 border-b border-white/[0.05]">
    {#if showForm}<CategoryForm
        {editingId}
        {formParentId}
        bind:formName
        bind:formSlug
        bind:formDescription
        bind:formSeoTitle
        bind:formSeoDescription
        bind:formImage
        bind:formIcon
        bind:formShowOnMobile
        bind:formShowOnDesktop
        bind:formFaqs
        onSave={save}
        onClose={() => (showForm = false)}
        generateSlug={genSlug}
      />{/if}
    <div
      class="flex flex-col lg:flex-row lg:items-center md:gap-4 gap-3 bg-white/[0.02] border border-white/10 p-3 sm:p-2.5 rounded-2xl"
    >
      <!-- Select All & Search -->
      <div class="flex-1 flex items-center bg-black/50 border border-white/5 rounded-xl pr-4 focus-within:border-neon-cyan/50 focus-within:ring-2 focus-within:ring-neon-cyan/20 transition-all shadow-inner shadow-black/50">
        <button 
          onclick={toggleSelectAll}
          class="flex items-center justify-center pl-2 pr-2 py-3 hover:text-neon-cyan transition-colors group shrink-0"
          title="Select All"
        >
          {#if allSelected}
            <CheckSquare size={16} class="text-neon-cyan" />
          {:else}
            <Square size={16} class="text-gray-500 group-hover:text-gray-300" />
          {/if}
        </button>
        
        <div class="w-px h-5 bg-white/10 mx-2"></div>

        <div class="flex-1 relative group flex items-center">
          <div class="absolute left-1 flex items-center pointer-events-none">
            <Search size={14} class="text-gray-500 group-focus-within:text-neon-cyan group-focus-within:scale-110 transition-all" />
          </div>
          <input
            bind:value={searchTerm}
            type="text"
            placeholder="QUERY_TAXONOMY..."
            class="w-full bg-transparent border-none py-3 pl-8 pr-4 text-[10px] font-mono text-gray-200 placeholder:text-gray-600 focus:outline-none uppercase tracking-widest leading-none outline-none"
          />
        </div>
      </div>

      <!-- Actions & Stats -->
      <div class="flex items-center flex-wrap sm:flex-nowrap justify-between lg:justify-end gap-3 w-full lg:w-auto mt-1 lg:mt-0 lg:pr-2">
        <div class="flex items-center gap-2">
          {#if selectedIds.size > 0}
            <div class="flex items-center gap-2 pr-2 mr-2 border-r border-white/10">
              <button
                onclick={() => bulkStatusUpdate(true)}
                class="flex items-center gap-2 px-3 py-2 text-[10px] font-mono uppercase bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 rounded-xl hover:bg-emerald-500/20 transition-all shadow-[0_0_15px_rgba(16,185,129,0.1)]"
                title="Kích hoạt tất cả"
              >
                <Eye size={12} />
                <span class="hidden xl:inline">Active</span>
              </button>
              <button
                onclick={() => bulkStatusUpdate(false)}
                class="flex items-center gap-2 px-3 py-2 text-[10px] font-mono uppercase bg-amber-500/10 border border-amber-500/30 text-amber-400 rounded-xl hover:bg-amber-500/20 transition-all shadow-[0_0_15px_rgba(245,158,11,0.1)]"
                title="Vô hiệu hóa tất cả"
              >
                <EyeOff size={12} />
                <span class="hidden xl:inline">Deactive</span>
              </button>
            </div>
            <button
              onclick={bulkDelete}
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
        onReorder={handleReorder}
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
