import { permissionState, getAuthToken } from "../permissions.svelte";
import type { Product, ProductMetadata } from "$lib/types";

class LiveEditStore {
  isEditMode = $state(false);
  isSaving = $state(false);
  originalProduct = $state<Product | null>(null);
  dirtyProduct = $state<Product | null>(null);
  activePath = $state<string | null>(null); // Path of currently focused inline editor

  // Elite V2.2: Transient HUD State
  notification = $state({
    message: '',
    type: null as 'success' | 'alert' | 'info' | null
  });

  notify(message: string, type: 'success' | 'alert' | 'info' = 'info') {
    this.notification.message = message;
    this.notification.type = type;
    
    // Auto-dismiss after 3s
    setTimeout(() => {
      if (this.notification.message === message) {
        this.notification.message = '';
        this.notification.type = null;
      }
    }, 4000);
  }

  // Elite V2.2 Supreme Security: Administrative access strictly derives from RBAC token
  isAdmin = $derived(permissionState.hasRole("SUPER_ADMIN") || permissionState.hasRole("ADMIN"));

  // Computed helper for components
  get dirtyMetadata() {
    return this.dirtyProduct?.metadata || {};
  }

  init(product: Product) {
    this.originalProduct = JSON.parse(JSON.stringify(product));
    this.dirtyProduct = JSON.parse(JSON.stringify(product));
  }

  toggleEditMode() {
    this.isEditMode = !this.isEditMode;
    if (!this.isEditMode) {
      this.discardChanges();
    }
  }

  updateField(path: string, value: string | number | boolean | object | null) {
    if (!this.dirtyProduct) return;

    try {
      const keys = path.split(".");
      let current = this.dirtyProduct as unknown as Record<string, unknown>;

      for (let i = 0; i < keys.length - 1; i++) {
        const key = keys[i];
        const nextKey = keys[i + 1];

        if (current[key] === null || current[key] === undefined || typeof current[key] !== 'object') {
          current[key] = /^\d+$/.test(nextKey) ? [] : {};
        }

        current = current[key] as Record<string, unknown>;
      }

      current[keys[keys.length - 1]] = value;
      this.dirtyProduct = JSON.parse(JSON.stringify(this.dirtyProduct)) as Product;
    } catch (error) {
      console.error(`💥 LiveEdit: Failed to update field at ${path}:`, error);
      const msg = error instanceof Error ? error.message : String(error);
      this.notify(`Lỗi cập nhật dữ liệu: ${msg}`, "alert");
    }
  }

  discardChanges() {
    this.dirtyProduct = JSON.parse(JSON.stringify(this.originalProduct));
    this.isEditMode = false;
  }

  async save() {
    if (!this.dirtyProduct?.id) return;
    this.isSaving = true;

    try {
      const token = getAuthToken();
      if (!token) {
        this.notify("Không tìm thấy định danh ADMIN. Vui lòng đăng nhập lại.", "alert");
        this.isSaving = false;
        return;
      }
      const p = this.dirtyProduct;
      
      const payload = {
        name: p.name,
        shortDescription: p.shortDescription,
        metadata: p.metadata,
        price: p.price,
        discountPrice: p.discountPrice,
        status: p.status as 'DRAFT' | 'ACTIVE' | 'ARCHIVED'
      };

      const response = await fetch(`/api/v1/products/${p.id}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        this.originalProduct = JSON.parse(JSON.stringify(this.dirtyProduct));
        this.notify("Đã lưu thay đổi thành công!", "success");
        this.isEditMode = false;
        if (typeof window !== "undefined") {
            setTimeout(() => window.location.reload(), 1500);
        }
      } else {
        const err = await response.json().catch(() => ({ detail: "Lỗi phản hồi không xác định" }));
        const reason = err.detail || err.message || "Kiểm tra quyền hạn hoặc đăng nhập lại";
        this.notify(`Lỗi khi lưu (HTTP ${response.status}): ${reason}`, "alert");
        console.error("💥 LiveEdit Save Failure:", { status: response.status, error: err });
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      this.notify(`Lỗi kết nối máy chủ: ${msg}`, "alert");
    } finally {
      this.isSaving = false;
    }
  }

  // Elite V2.2: Global DOM Synchronization!
  // This allows CSS to react to Edit Mode across all components.
  syncToBody = $effect.root(() => {
    $effect(() => {
        if (typeof document !== 'undefined') {
            if (this.isEditMode) {
                document.body.classList.add('live-edit-mode');
            } else {
                document.body.classList.remove('live-edit-mode');
            }
        }
    });
  });
}

export const liveEditStore = new LiveEditStore();
