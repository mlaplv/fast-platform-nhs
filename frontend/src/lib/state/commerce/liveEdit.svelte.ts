import { permissionState } from "../permissions.svelte";
import type { Product, ProductMetadata } from "$lib/types";

class LiveEditStore {
  isEditMode = $state(false);
  isSaving = $state(false);
  originalProduct = $state<Product | null>(null);
  dirtyProduct = $state<Product | null>(null);
  activePath = $state<string | null>(null); // Path of currently focused inline editor
  forceAdmin = $state(false);

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

  // Administrative access detection
  isAdmin = $derived(this.forceAdmin || permissionState.hasRole("SUPER_ADMIN"));

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
      let current: Record<string, any> = this.dirtyProduct as any;

      for (let i = 0; i < keys.length - 1; i++) {
        const key = keys[i];
        const nextKey = keys[i + 1];

        if (current[key] === null || current[key] === undefined || typeof current[key] !== 'object') {
          current[key] = /^\d+$/.test(nextKey) ? [] : {};
        }

        current = current[key];
      }

      current[keys[keys.length - 1]] = value;
      this.dirtyProduct = JSON.parse(JSON.stringify(this.dirtyProduct));
    } catch (error) {
      console.error(`💥 LiveEdit: Failed to update field at ${path}:`, error);
      this.notify(`Lỗi cập nhật dữ liệu: ${(error as any).message}`, "alert");
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
      const token = localStorage.getItem("admin_token") || localStorage.getItem("access_token");
      const p = this.dirtyProduct;
      
      const payload: UpdateProductPayload = {
        name: p.name,
        shortDescription: p.shortDescription,
        metadata: p.metadata,
        price: p.price,
        discountPrice: p.discountPrice,
        status: p.status as any
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
        const err = await response.json();
        this.notify(`Lỗi khi lưu (HTTP ${response.status}): ${err.detail || 'Kiểm tra lỗi'}`, "alert");
      }
    } catch (e: any) {
      this.notify(`Lỗi kết nối máy chủ: ${e.message}`, "alert");
    } finally {
      this.isSaving = false;
    }
  }
}

export const liveEditStore = new LiveEditStore();
