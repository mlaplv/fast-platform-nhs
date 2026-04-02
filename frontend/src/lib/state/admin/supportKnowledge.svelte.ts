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

    // Multi-select state
    selectedIds = $state<string[]>([]);

    async fetchItems(category?: string, search?: string) {
        this.loading = true;
        try {
            const params: any = {};
            if (category) params.category = category;
            if (search) params.search = search;
            
            const res = await apiClient.get<any>("/api/v1/admin/support/knowledge", { params });
            if (res && res.data) {
                this.items = res.data;
                this.total = res.total;
            }
        } catch (error) {
            console.error("[SupportKB] Fetch error:", error);
        } finally {
            this.loading = false;
        }
    }

    async saveItem(data: Partial<KnowledgeItem>) {
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
    }

    async deleteItem(id: string) {
        if (!confirm("Sếp chắc chắn muốn xóa tri thức này chứ?")) return;
        try {
            await apiClient.delete(`/api/v1/admin/support/knowledge/${id}`);
            await this.fetchItems();
        } catch (error) {
            console.error("[SupportKB] Delete error:", error);
        }
    }

    async toggleActive(id: string, is_active: boolean) {
        try {
            await apiClient.patch(`/api/v1/admin/support/knowledge/${id}`, { is_active });
            const item = this.items.find(i => i.id === id);
            if (item) item.is_active = is_active;
        } catch (error) {
            console.error("[SupportKB] Toggle error:", error);
        }
    }

    async bulkDelete() {
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
    }

    async bulkToggleActive(is_active: boolean) {
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
    }

    toggleSelect(id: string) {
        if (this.selectedIds.includes(id)) {
            this.selectedIds = this.selectedIds.filter(i => i !== id);
        } else {
            this.selectedIds = [...this.selectedIds, id];
        }
    }

    toggleSelectAll() {
        if (this.selectedIds.length === this.items.length) {
            this.selectedIds = [];
        } else {
            this.selectedIds = this.items.map(i => i.id);
        }
    }

    openEdit(item: KnowledgeItem | null = null) {
        this.editingItem = item ? { ...item } : {
            category: "GENERAL",
            question: "",
            answer: "",
            is_active: true,
            priority: 0,
            tags: []
        };
        this.showModal = true;
    }
}

export const supportKbAdmin = new SupportKnowledgeState();
