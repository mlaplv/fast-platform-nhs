import { apiClient } from "$lib/utils/apiClient";

export interface KnowledgeItem {
    id: string;
    category: string;
    question: string;
    answer: string;
    is_active: boolean;
    priority: number;
    tags?: string[];
    created_at: string;
}

class SupportKnowledgeState {
    items = $state<KnowledgeItem[]>([]);
    loading = $state(false);
    total = $state(0);
    
    // For editing/creating
    showModal = $state(false);
    editingItem = $state<Partial<KnowledgeItem> | null>(null);
    selectedIds = $state<string[]>([]);
    viewMode = $state<'grid' | 'list'>('grid');
    
    // Type-safe params
    params = $state<{
        category?: string;
        search?: string;
        limit: number;
        offset: number;
    }>({
        limit: 20,
        offset: 0
    });

    // Multi-select state

    // Multi-select state

    fetchItems = async (category?: string, search?: string) => {
        this.loading = true;
        try {
            if (category) this.params.category = category;
            if (search) this.params.search = search;
            
            const res = await apiClient.get<{
                data: KnowledgeItem[];
                total: number;
            }>("/api/v1/admin/support/knowledge", { params: this.params });
            
            if (res) {
                this.items = res.data;
                this.total = res.total;
            }
        } catch (error) {
            console.error("[SupportKB] Fetch error:", error);
        } finally {
            this.loading = false;
        }
    };

    saveItem = async (data: Partial<KnowledgeItem>) => {
        try {
            if (data.id) {
                // Update
                await apiClient.patch(`/api/v1/admin/support/knowledge/${data.id}`, data);
            } else {
                // Create
                await apiClient.post("/api/v1/admin/support/knowledge", data);
            }
            await this.fetchItems();
            this.showModal = false;
            this.editingItem = null;
        } catch (error) {
            console.error("[SupportKB] Save error:", error);
            throw error;
        }
    };

    deleteItem = async (id: string) => {
        if (!confirm("Sếp chắc chắn muốn xóa tri thức này chứ?")) return;
        try {
            await apiClient.delete(`/api/v1/admin/support/knowledge/${id}`);
            await this.fetchItems();
        } catch (error) {
            console.error("[SupportKB] Delete error:", error);
        }
    };

    toggleActive = async (id: string, is_active: boolean) => {
        try {
            await apiClient.patch(`/api/v1/admin/support/knowledge/${id}`, { is_active });
            const item = this.items.find((i: KnowledgeItem) => i.id === id);
            if (item) item.is_active = is_active;
        } catch (error) {
            console.error("[SupportKB] Toggle error:", error);
        }
    };

    bulkDelete = async () => {
        if (this.selectedIds.length === 0) return;
        if (!confirm(`Sếp chắc chắn muốn xóa ${this.selectedIds.length} tri thức đã chọn?`)) return;
        this.loading = true;
        try {
            await apiClient.post("/api/v1/admin/support/knowledge/bulk-delete", { ids: [...this.selectedIds] });
            this.selectedIds = [];
            await this.fetchItems();
        } catch (error) {
            console.error("[SupportKB] Bulk delete error:", error);
        } finally {
            this.loading = false;
        }
    };

    bulkToggleActive = async (is_active: boolean) => {
        if (this.selectedIds.length === 0) return;
        this.loading = true;
        try {
            await apiClient.post("/api/v1/admin/support/knowledge/bulk-toggle", { 
                ids: [...this.selectedIds], 
                is_active 
            });
            this.selectedIds = [];
            await this.fetchItems();
        } catch (error) {
            console.error("[SupportKB] Bulk toggle error:", error);
        } finally {
            this.loading = false;
        }
    };

    toggleSelect = (id: string) => {
        if (this.selectedIds.includes(id)) {
            this.selectedIds = this.selectedIds.filter((i: string) => i !== id);
        } else {
            this.selectedIds = [...this.selectedIds, id];
        }
    };

    toggleSelectAll = () => {
        const itemIds = this.items.map(i => i.id);
        if (itemIds.length === 0) return;
        
        const allSelected = itemIds.every(id => this.selectedIds.includes(id));
        
        if (allSelected) {
            // Deselect only current page items
            this.selectedIds = this.selectedIds.filter(id => !itemIds.includes(id));
        } else {
            // Select all current page items (merge with existing)
            const nextSet = new Set([...this.selectedIds, ...itemIds]);
            this.selectedIds = Array.from(nextSet);
        }
    };

    openEdit = (item: KnowledgeItem | null = null) => {
        this.editingItem = item ? { ...item } : {
            category: "GENERAL",
            question: "",
            answer: "",
            is_active: true,
            priority: 0,
            tags: []
        };
        this.showModal = true;
    };

    reindexBrain = async (nanobot: { 
        showConfirm: (p: { title: string; message: string; confirmLabel: string; cancelLabel: string }) => Promise<boolean>;
        showToast: (m: string, t: 'success' | 'alert' | 'info' | 'error') => void;
    }) => {
        const confirmed = await nanobot.showConfirm({
            title: "NEURAL_REBUILD",
            message: "Sếp muốn Helen 'ôn lại' toàn bộ tri thức hiện có chứ? (Re-indexing sẽ làm mới bộ nhớ Vector)",
            confirmLabel: "XÁC NHẬN",
            cancelLabel: "HỦY"
        });

        if (!confirmed) return;
        
        this.loading = true;
        try {
            await apiClient.post("/api/v1/admin/support/knowledge/reindex");
            nanobot.showToast("Helen đã tái nạp tri thức thành công! ✨", "success");
        } catch (error) {
            console.error("[SupportKB] Reindex error:", error);
            nanobot.showToast("Có lỗi khi Helen tái nạp tri thức. ⚠️", "error");
        } finally {
            this.loading = false;
        }
    };
}

export const supportKbAdmin = new SupportKnowledgeState();
