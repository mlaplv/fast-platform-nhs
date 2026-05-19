<script lang="ts">
  import { fade, scale } from "svelte/transition";
  import { tick } from "svelte";
  import FolderTree from "@lucide/svelte/icons/folder-tree";
  import Plus from "@lucide/svelte/icons/plus";
  import Search from "@lucide/svelte/icons/search";
  import Layers from "@lucide/svelte/icons/layers";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import Skull from "@lucide/svelte/icons/skull";
  import CheckSquare from "@lucide/svelte/icons/check-square";
  import Square from "@lucide/svelte/icons/square";
  import Eye from "@lucide/svelte/icons/eye";
  import EyeOff from "@lucide/svelte/icons/eye-off";
  import AlertTriangle from "@lucide/svelte/icons/triangle-alert";
  import ShieldAlert from "@lucide/svelte/icons/shield-alert";
  import { useNanobot } from "$lib/state/nanobot.svelte";
  const nanobot = useNanobot();
  import { apiClient } from "$lib/utils/apiClient";
  import { slugify } from "$lib/utils/format";
  import type { Category, BaseWidgetProps } from "$lib/types";
  import CategoryForm from "./CategoryForm.svelte";
  import CategoryTree from "./CategoryTree.svelte";

  let { data = {} }: BaseWidgetProps = $props();

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

  // ── Confirm Dialog State ──────────────────────────────────────────────────
  type ConfirmMode = "soft" | "hard" | "bulk-soft" | "bulk-hard";
  type ConfirmDialog = {
    open: boolean;
    mode: ConfirmMode;
    ids: string[];
    parentId: string | null;
    categoryName: string;
  };
  let confirmDialog = $state<ConfirmDialog>({
    open: false,
    mode: "soft",
    ids: [],
    parentId: null,
    categoryName: "",
  });
  let isProcessing = $state(false); // Double-call guard

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
  async function openCreate(p: string | null = null) {
    showForm = false;
    await tick();
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
  async function openEdit(cat: Category, p: string | null = null) {
    showForm = false;
    await tick();
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
    const raw: any = cat;
    const meta = raw.metadata || raw.category_metadata;
    formFaqs = meta?.faqs || [];
    
    console.log("[CategoryManagement] Metadata Found:", $state.snapshot(meta));
    console.log("[CategoryManagement] Form FAQs initialized:", $state.snapshot(formFaqs));
    formParentId = p || null; // CNS V2.3: Normalize undefined to null
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

  // ── Helpers: remove IDs khỏi local state ─────────────────────────────────
  /** Elite V2.2: Recursive N-Level tree search - tìm node bất kỳ ở mọi độ sâu */
  function findNodeById(nodes: Category[], id: string): Category | null {
    for (const node of nodes) {
      if (node.id === id) return node;
      if (node.children?.length) {
        const found = findNodeById(node.children, id);
        if (found) return found;
      }
    }
    return null;
  }

  function removeFromTree(ids: string[], parentId: string | null = null) {
    const idSet = new Set(ids);
    if (parentId) {
      // Tìm đệ quy N-Level thay vì chỉ tìm ở root
      const par = findNodeById(categories, parentId);
      if (par) par.children = par.children.filter((c) => !idSet.has(c.id));
      // Force reactivity
      categories = [...categories];
    } else {
      categories = categories.filter((c) => !idSet.has(c.id));
      categories.forEach((c) => {
        if (c.children) c.children = c.children.filter((ch) => !idSet.has(ch.id));
      });
    }
    ids.forEach((id) => selectedIds.delete(id));
    selectedIds = new Set(selectedIds);
  }

  // ── Open confirm dialog ───────────────────────────────────────────────────
  function requestDelete(id: string, parentId: string | null, name: string, mode: "soft" | "hard") {
    confirmDialog = { open: true, mode, ids: [id], parentId, categoryName: name };
  }
  function requestBulkDelete(mode: "bulk-soft" | "bulk-hard") {
    if (selectedIds.size === 0) return;
    confirmDialog = {
      open: true, mode,
      ids: Array.from(selectedIds),
      parentId: null,
      categoryName: `${selectedIds.size} danh mục đã chọn`,
    };
  }
  function closeConfirm() {
    if (!isProcessing) confirmDialog = { ...confirmDialog, open: false };
  }

  // ── Thực thi sau khi xác nhận ─────────────────────────────────────────────
  async function executeConfirmed() {
    if (isProcessing) return;
    isProcessing = true;
    const { mode, ids, parentId } = confirmDialog;
    try {
      if (mode === "soft") {
        await apiClient.delete(`/api/v1/categories/${ids[0]}`);
        removeFromTree(ids, parentId);
        nanobot.showToast("Đã ẩn danh mục (soft delete)", "success");
      } else if (mode === "hard") {
        await apiClient.post("/api/v1/categories/hard-delete", { ids });
        removeFromTree(ids, parentId);
        nanobot.showToast("Đã xóa vĩnh viễn danh mục", "success");
      } else if (mode === "bulk-soft") {
        const res = await apiClient.post<{ count: number; skipped: string[] }>(
          "/api/v1/categories/bulk-delete", { ids }
        );
        removeFromTree(ids);
        if (res.skipped?.length > 0) {
          nanobot.showToast(`Đã ẩn ${res.count} danh mục. Bỏ qua ${res.skipped.length} (có sản phẩm/con)`, "warning");
        } else {
          nanobot.showToast(`Đã ẩn ${res.count} danh mục`, "success");
        }
      } else if (mode === "bulk-hard") {
        const res = await apiClient.post<{ count: number; skipped: string[] }>(
          "/api/v1/categories/bulk-hard-delete", { ids }
        );
        removeFromTree(ids);
        if (res.skipped?.length > 0) {
          nanobot.showToast(`Đã purge ${res.count}. Bỏ qua ${res.skipped.length} (có sản phẩm/con)`, "warning");
        } else {
          nanobot.showToast(`Đã xóa vĩnh viễn ${res.count} danh mục`, "success");
        }
      }
    } catch (e: unknown) {
      const err = e as { detail?: string; message?: string };
      const msg = err?.detail || err?.message || "Thao tác thất bại";
      console.error(`[CategoryManagement] ${mode} failed:`, e);
      // Backend trả BLOCKED → hiển thị lý do rõ ràng
      if (msg.includes("BLOCKED")) {
        nanobot.showToast("❌ Không thể xóa: danh mục có sản phẩm hoặc danh mục con", "error");
      } else {
        nanobot.showToast(msg, "error");
      }
    } finally {
      isProcessing = false;
      confirmDialog = { ...confirmDialog, open: false };
    }
  }

  // ── Quick Toggle Visibility (no confirm needed) ───────────────────────────
  async function quickToggle(id: string, currentMobile: boolean, currentDesktop: boolean) {
    const newActive = !(currentMobile && currentDesktop);
    try {
      await apiClient.post("/api/v1/categories/bulk-status", { ids: [id], active: newActive });
      const updateTree = (list: Category[]) =>
        list.map((c) => {
          if (c.id === id) return { ...c, showOnMobile: newActive, showOnDesktop: newActive };
          if (c.children?.length) c.children = updateTree(c.children);
          return c;
        });
      categories = updateTree(categories);
      nanobot.showToast(newActive ? "Đã bật hiển thị" : "Đã ẩn danh mục", "success");
    } catch (e) {
      console.error("[CategoryManagement] Quick toggle failed:", e);
      nanobot.showToast("Toggle thất bại", "error");
    }
  }

  // bulkDelete → dùng requestBulkDelete("bulk-soft") để qua confirm dialog

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
            class="w-full bg-transparent border-none py-3 pl-8 pr-4 text-[10px] font-mono text-gray-200 placeholder:text-gray-600 focus:outline-none tracking-widest leading-none outline-none"
          />
        </div>
      </div>

      <!-- Actions & Stats -->
      <div class="flex items-center flex-wrap sm:flex-nowrap justify-between lg:justify-end gap-3 w-full lg:w-auto mt-1 lg:mt-0 lg:pr-2">
        <div class="flex items-center gap-2">
          {#if selectedIds.size > 0}
            <div class="flex items-center gap-1.5 pr-2 mr-2 border-r border-white/10">
              <button
                onclick={() => bulkStatusUpdate(true)}
                class="flex items-center gap-2 px-3 py-2 text-[10px] font-mono bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 rounded-xl hover:bg-emerald-500/20 transition-all shadow-[0_0_15px_rgba(16,185,129,0.1)]"
                title="Kích hoạt tất cả"
              ><Eye size={12} /><span class="hidden xl:inline">Active</span></button>
              <button
                onclick={() => bulkStatusUpdate(false)}
                class="flex items-center gap-2 px-3 py-2 text-[10px] font-mono bg-amber-500/10 border border-amber-500/30 text-amber-400 rounded-xl hover:bg-amber-500/20 transition-all shadow-[0_0_15px_rgba(245,158,11,0.1)]"
                title="Vô hiệu hóa tất cả"
              ><EyeOff size={12} /><span class="hidden xl:inline">Deactive</span></button>
            </div>
            <button
              onclick={() => requestBulkDelete("bulk-soft")}
              class="flex items-center gap-1.5 px-3 py-2 text-[10px] font-mono bg-red-500/10 border border-red-500/30 text-red-400 rounded-xl hover:bg-red-500/20 transition-all"
              title="Ẩn hàng loạt (soft delete)"
            ><Trash2 size={13}/><span class="hidden sm:inline">Soft ({selectedIds.size})</span></button>
            <button
              onclick={() => requestBulkDelete("bulk-hard")}
              class="flex items-center gap-1.5 px-3 py-2 text-[10px] font-mono bg-rose-900/30 border border-rose-500/40 text-rose-400 rounded-xl hover:bg-rose-900/50 transition-all shadow-[0_0_15px_rgba(244,63,94,0.15)]"
              title="Xóa vĩnh viễn hàng loạt!"
            ><Skull size={13}/><span class="hidden sm:inline">Purge ({selectedIds.size})</span></button>
          {/if}
          <div
            class="flex sm:hidden items-center gap-2 px-3 py-2 bg-gradient-to-br from-neon-cyan/10 to-transparent border border-neon-cyan/30 rounded-xl text-[10px] font-mono text-neon-cyan tracking-[0.2em] shadow-[0_0_15px_rgba(0,255,255,0.05)]"
          >
            <Layers size={14} class="animate-pulse opacity-70" />
            <span class="font-bold">{categories.length}</span>
          </div>
        </div>

        <div class="flex items-center gap-2 sm:gap-3 ml-auto sm:ml-0">
          <div
            class="hidden sm:flex items-center gap-2 px-4 py-2 bg-gradient-to-br from-neon-cyan/10 to-transparent border border-neon-cyan/30 rounded-xl text-[10px] font-mono text-neon-cyan tracking-[0.2em] shadow-[0_0_15px_rgba(0,255,255,0.05)]"
          >
            <Layers size={14} class="animate-pulse opacity-70" />
            <span class="font-bold">{categories.length}</span> Nodes
          </div>

          <button
            onclick={() => openCreate()}
            class="flex items-center gap-2 px-3 sm:px-4 py-2 sm:py-2 text-[10px] w-full sm:w-auto justify-center font-bold tracking-widest font-mono bg-neon-cyan/10 border border-neon-cyan/30 text-neon-cyan hover:bg-neon-cyan/20 hover:text-white rounded-xl transition-all duration-300"
          >
            <Plus size={14} class="sm:hidden" /><Plus size={12} class="hidden sm:block" /> <span class="hidden sm:inline">Init_Node</span>
          </button>
        </div>
      </div>
    </div>
  </div>

  {#if showForm}
    {#key editingId}
      <CategoryForm
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
      />
    {/key}
  {/if}

  <div class="flex-1 overflow-y-auto custom-scrollbar p-6">
    {#if isLoading}
      <div class="h-full flex items-center justify-center animate-pulse">
        <span
          class="text-[9px] font-mono text-[#00FFFF]/40 tracking-[0.3em]"
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
        onRequestDelete={requestDelete}
        onQuickToggle={quickToggle}
        onReorder={handleReorder}
      />
    {/if}
  </div>
</div>

<!-- ══ CONFIRM DIALOG ══ -->
{#if confirmDialog.open}
  <div
    class="fixed inset-0 z-[9999] flex items-center justify-center p-4"
    role="dialog"
    aria-modal="true"
    transition:fade={{ duration: 150 }}
  >
    <!-- Backdrop -->
    <button
      class="absolute inset-0 bg-black/70 backdrop-blur-sm cursor-default"
      onclick={closeConfirm}
      tabindex="-1"
      aria-label="Đóng"
    ></button>

    <!-- Dialog box -->
    <div
      class="relative z-10 w-full max-w-md bg-[#0d0d0d] border rounded-2xl shadow-2xl overflow-hidden
        {confirmDialog.mode === 'hard' || confirmDialog.mode === 'bulk-hard'
          ? 'border-rose-500/40 shadow-rose-500/10'
          : 'border-red-500/30 shadow-red-500/10'}"
      transition:scale={{ duration: 200, start: 0.95 }}
    >
      <!-- Header -->
      <div
        class="px-6 py-4 border-b flex items-center gap-3
          {confirmDialog.mode === 'hard' || confirmDialog.mode === 'bulk-hard'
            ? 'border-rose-500/20 bg-rose-950/30'
            : 'border-red-500/20 bg-red-950/20'}"
      >
        {#if confirmDialog.mode === 'hard' || confirmDialog.mode === 'bulk-hard'}
          <Skull size={18} class="text-rose-400 shrink-0" />
          <span class="text-[11px] font-mono font-bold text-rose-400 tracking-widest">WARNING: XÓA VĨNH VIỄN</span>
        {:else}
          <AlertTriangle size={18} class="text-red-400 shrink-0" />
          <span class="text-[11px] font-mono font-bold text-red-400 tracking-widest">XÁC NHẬN XÓA</span>
        {/if}
      </div>

      <!-- Body -->
      <div class="px-6 py-5 space-y-4">
        <p class="text-[13px] text-gray-300 leading-relaxed">
          {#if confirmDialog.mode === 'hard' || confirmDialog.mode === 'bulk-hard'}
            <span class="text-rose-400 font-bold">Hành động này không thể hoàn tác!</span> Danh mục sẽ bị xóa khỏi database.
          {:else}
            Danh mục sẽ bị ẩn khỏi giao diện (soft delete, có thể khôi phục).
          {/if}
        </p>
        <div class="bg-white/[0.03] border border-white/10 rounded-xl px-4 py-3 flex items-start gap-3">
          <ShieldAlert size={14} class="text-gray-500 shrink-0 mt-0.5" />
          <span class="text-[11px] font-mono text-gray-400 leading-relaxed">
            <span class="text-white/60">Đối tượng:</span> {confirmDialog.categoryName}
          </span>
        </div>
        {#if confirmDialog.mode === 'hard' || confirmDialog.mode === 'bulk-hard'}
          <div class="bg-rose-950/40 border border-rose-500/20 rounded-xl px-4 py-3">
            <p class="text-[10px] font-mono text-rose-300/80 leading-relaxed">
              ⚠️ Danh mục có sản phẩm hoặc có danh mục con sẽ bị bỏ qua tự động — không thể purge.
            </p>
          </div>
        {:else}
          <div class="bg-amber-950/30 border border-amber-500/20 rounded-xl px-4 py-3">
            <p class="text-[10px] font-mono text-amber-300/80 leading-relaxed">
              ⚠️ Danh mục có sản phẩm hoặc có danh mục con sẽ bị bỏ qua — không thể xóa.
            </p>
          </div>
        {/if}
      </div>

      <!-- Footer -->
      <div class="px-6 py-4 border-t border-white/[0.05] flex items-center justify-end gap-3">
        <button
          onclick={closeConfirm}
          disabled={isProcessing}
          class="px-4 py-2 text-[10px] font-mono text-gray-400 hover:text-white border border-white/10 rounded-xl hover:bg-white/5 transition-all disabled:opacity-50"
        >Hủy bỏ</button>
        <button
          onclick={executeConfirmed}
          disabled={isProcessing}
          class="px-5 py-2 text-[10px] font-mono font-bold rounded-xl transition-all disabled:opacity-50 flex items-center gap-2
            {confirmDialog.mode === 'hard' || confirmDialog.mode === 'bulk-hard'
              ? 'bg-rose-600 hover:bg-rose-500 text-white shadow-[0_0_20px_rgba(244,63,94,0.3)]'
              : 'bg-red-600 hover:bg-red-500 text-white shadow-[0_0_20px_rgba(239,68,68,0.2)]'}"
        >
          {#if isProcessing}
            <div class="w-3 h-3 border border-white/30 border-t-white rounded-full animate-spin"></div>
            XỬ LÝ...
          {:else if confirmDialog.mode === 'hard' || confirmDialog.mode === 'bulk-hard'}
            <Skull size={12} /> PURGE
          {:else}
            <Trash2 size={12} /> XÓA
          {/if}
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  .custom-scrollbar::-webkit-scrollbar {
    width: 4px;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 20px;
  }
</style>
