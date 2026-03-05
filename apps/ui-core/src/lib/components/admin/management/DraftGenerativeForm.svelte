<script lang="ts">
  import { onMount, untrack } from "svelte";
  import { get, set, del } from "idb-keyval";
  import { apiClient } from "$lib/utils/apiClient";
  import AIEditorField from "$lib/components/admin/ui/AIEditorField.svelte";
  import { nanobot } from "$lib/state/nanobot.svelte";

  let { onClose, onSuccess, initialTitle = "", editingId = null } = $props<{ 
    onClose: () => void; 
    onSuccess: () => void;
    initialTitle?: string;
    editingId?: string | null;
  }>();

  const DRAFT_KEY = "news_draft_v2";

  let formData = $state({
    title: initialTitle,
    category: "Tin tức",
    slug: "",
    seo_title: "",
    seo_description: "",
    excerpt: "",
    content: "",
  });

  let isHydrated = $state(false);
  let isSubmitting = $state(false);
  let dbCategories = $state<string[]>(["Tin tức", "Khóa học", "Dịch vụ"]);

  onMount(async () => {
    // 1. Parallel loading: Fetch newest categories & Hydrate local draft
    const fetchCats = async () => {
      try {
        const res = await apiClient.get<any>("/api/v1/categories");
        if (res.data && res.data.length > 0) {
          dbCategories = res.data.map((c: any) => c.name);
        }
      } catch (e) {
        console.error("Categories fetch failed", e);
      }
    };

    const hydrateDraft = async () => {
      if (editingId) {
        // Edit mode: fetch existing from API, ignore IDB draft
        try {
          const res = await apiClient.get<any>(`/api/v1/articles/${editingId}`);
          if (res.data) Object.assign(formData, res.data);
        } catch (e) {
          console.error("Failed to load article for edit", e);
        }
      } else {
        // Create mode: hydrate from local draft
        try {
          const draft = await get(DRAFT_KEY);
          if (draft && typeof draft === "object") {
            Object.assign(formData, draft);
          }
        } catch (e) {
          console.error("IDB Hydration error", e);
        }
      }
    };

    await Promise.allSettled([fetchCats(), hydrateDraft()]);
    
    // Override draft title if XoHi passed a specific new title (mostly for creation)
    if (!editingId && initialTitle && initialTitle !== formData.title) {
        formData.title = initialTitle;
    }

    isHydrated = true;
  });

  $effect(() => {
    if (!isHydrated || editingId) return; // Only auto-save local drafts for new creations
    const snap = $state.snapshot(formData);
    untrack(() => {
      const t = setTimeout(() => set(DRAFT_KEY, snap).catch(console.error), 800);
      return () => clearTimeout(t);
    });
  });

  async function submitDraft() {
    if (!formData.title.trim()) {
      nanobot.showToast("Tiêu đề KHÔNG thể để trống", "error");
      return;
    }
    isSubmitting = true;
    try {
      if (editingId) {
        await apiClient.patch(`/api/v1/articles/${editingId}`, $state.snapshot(formData));
        nanobot.showToast("Cập nhật bài viết thành công", "success");
      } else {
        await apiClient.post("/api/v1/articles", $state.snapshot(formData));
        await del(DRAFT_KEY);
        nanobot.showToast("Trích xuất và đăng bài hoàn tất", "success");
      }
      onSuccess();
    } catch (e: any) {
      nanobot.showToast("Lỗi đăng bài: " + (e.message || "Unknown error"), "error");
    } finally {
      isSubmitting = false;
    }
  }

  function discardDraft() {
    del(DRAFT_KEY).catch(console.error);
    onClose();
  }
</script>

<div class="draft-form-container">
  <div class="header relative">
    <div class="flex flex-col gap-1">
      <h2 class="text-[#00FFFF] font-mono tracking-widest text-lg font-bold uppercase flex items-center gap-2">
        <div class="w-2 h-2 rounded-full bg-[#00FFFF] animate-pulse"></div>
        {editingId ? "CHỈNH SỬA BÀI VIẾT (LIVE)" : "SOẠN BÀI VIẾT (LOCAL DRAFT)"}
      </h2>
      <span class="text-[10px] uppercase font-mono tracking-widest text-gray-500">Mọi thao tác được lưu trữ mã hóa tự động tại máy khách.</span>
    </div>
    <button onclick={onClose} class="text-gray-400 hover:text-white transition-colors text-2xl font-bold p-2 absolute top-0 right-0">&times;</button>
  </div>

  <div class="form-grid">
    <div class="field">
      <label for="title">Tiêu đề *</label>
      <input id="title" type="text" bind:value={formData.title} placeholder="Bắt buộc..." />
    </div>
    <div class="field">
      <label for="category">Chuyên mục *</label>
      <select id="category" bind:value={formData.category}>
        {#each dbCategories as c}
          <option value={c}>{c}</option>
        {/each}
      </select>
    </div>
    <div class="field">
      <label for="slug">SEO Route (Slug)</label>
      <input id="slug" type="text" bind:value={formData.slug} placeholder="Tự tạo tự động nếu để trống" />
    </div>
    <div class="field">
      <label for="seo_title">SEO Meta Title</label>
      <input id="seo_title" type="text" bind:value={formData.seo_title} placeholder="(Tùy chọn)" />
    </div>
    <div class="field span-full">
      <label for="seo_desc">SEO Meta Description</label>
      <textarea id="seo_desc" bind:value={formData.seo_description} rows="2" placeholder="(Tùy chọn)"></textarea>
    </div>
    <div class="field span-full">
      <label for="excerpt">Tóm tắt (Excerpt)</label>
      <textarea id="excerpt" bind:value={formData.excerpt} rows="3" placeholder="Mục giới thiệu ngắn..."></textarea>
    </div>
    <div class="field span-full flex-1 min-h-[300px] flex flex-col">
      <label for="content">Nội dung chi tiết (AI Co-pilot Hỗ trợ)</label>
      <AIEditorField bind:value={formData.content} />
    </div>
  </div>

  <div class="actions">
    <button onclick={discardDraft} class="btn-cancel" disabled={isSubmitting}>HỦY</button>
    <button onclick={submitDraft} class="btn-submit" disabled={isSubmitting}>
      {isSubmitting ? "ĐANG TRIỂN KHAI..." : (editingId ? "CẬP NHẬT" : "ĐĂNG BÀI (SYNC)")}
    </button>
  </div>
</div>

<style>
  .draft-form-container {
    padding: 2rem;
    min-height: 100%;
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
    color: #e2e8f0;
  }
  .header {
    border-bottom: 1px solid rgba(0,255,255,0.1);
    padding-bottom: 1rem;
    margin-bottom: 0.5rem;
  }
  .form-grid {
    display: grid;
    gap: 1.25rem;
    grid-template-columns: 1fr;
    flex-1: 1;
    display: flex;
    flex-direction: column;
  }
  @container (min-width: 500px) {
    .form-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
    }
  }
  .field {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  .field.span-full {
    grid-column: 1 / -1;
  }
  label {
    font-size: 0.75rem;
    font-weight: 600;
    font-family: monospace;
    text-transform: uppercase;
    color: rgba(255, 255, 255, 0.4);
    letter-spacing: 0.05em;
  }
  input, select, textarea {
    background: rgba(0,0,0,0.4);
    border: 1px solid rgba(255,255,255,0.1);
    color: #00FFFF;
    padding: 0.85rem 1rem;
    border-radius: 8px;
    font-size: 0.85rem;
    outline: none;
    transition: all 0.2s;
  }
  input:focus, select:focus, textarea:focus {
    border-color: rgba(0,255,255,0.4);
    background: rgba(0,255,255,0.02);
    box-shadow: 0 0 15px rgba(0,255,255,0.05); /* Glow effect */
  }
  textarea {
    resize: vertical;
    color: white;
  }
  .actions {
    margin-top: 1rem;
    padding-top: 1.5rem;
    display: flex;
    justify-content: flex-end;
    gap: 1rem;
    border-top: 1px solid rgba(255,255,255,0.05);
  }
  .btn-submit {
    background: rgba(0,255,255,0.1);
    color: #00FFFF;
    border: 1px solid rgba(0,255,255,0.3);
    padding: 0.75rem 2.5rem;
    border-radius: 8px;
    font-size: 0.85rem;
    font-family: monospace;
    font-weight: 700;
    letter-spacing: 1px;
    cursor: pointer;
    transition: all 0.2s;
    box-shadow: 0 0 20px rgba(0, 255, 255, 0.1);
  }
  .btn-submit:hover:not(:disabled) {
    background: rgba(0, 255, 255, 0.2);
    box-shadow: 0 0 25px rgba(0, 255, 255, 0.25);
  }
  .btn-cancel {
    background: transparent;
    color: #64748b;
    border: 1px solid rgba(255,255,255,0.1);
    padding: 0.75rem 1.5rem;
    border-radius: 8px;
    font-size: 0.85rem;
    font-family: monospace;
    cursor: pointer;
    transition: all 0.2s;
  }
  .btn-cancel:hover:not(:disabled) {
    color: #ef4444; /* HỦY thì màu đỏ */
    border-color: rgba(239, 68, 68, 0.4);
    background: rgba(239, 68, 68, 0.05);
  }
  button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
</style>
