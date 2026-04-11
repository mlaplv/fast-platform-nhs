import { permissionState } from "../permissions.svelte";
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

  // Administrative access detection
  isAdmin = $derived(permissionState.hasRole("SUPER_ADMIN"));

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

  updateField(path: string, value: any) {
    if (!this.dirtyProduct) return;
    
    const keys = path.split(".");
    let current: any = this.dirtyProduct;
    
    for (let i = 0; i < keys.length - 1; i++) {
        const key = keys[i];
        if (!(key in current)) current[key] = {};
        current = current[key];
    }
    current[keys[keys.length - 1]] = value;
    
    // Elite V2.2: Force reactivity bubble-up for Svelte 5 derived runes
    this.dirtyProduct = JSON.parse(JSON.stringify(this.dirtyProduct));
  }

  discardChanges() {
    this.dirtyProduct = JSON.parse(JSON.stringify(this.originalProduct));
    this.isEditMode = false;
  }

  async save() {
    if (!this.dirtyProduct?.id) {
        console.error("LiveEdit: Missing product ID, cannot save.");
        return;
    }
    this.isSaving = true;
    console.log("🚀 LiveEdit: Initializing save for product:", this.dirtyProduct.id);

    try {
      const token = localStorage.getItem("admin_token") || localStorage.getItem("access_token");
      
      // Elite V2.2: Strict Schema Alignment
      const payload: any = {
        name: this.dirtyProduct.name,
        shortDescription: this.dirtyProduct.shortDescription || (this.dirtyProduct as any).short_description,
        metadata: this.dirtyProduct.metadata,
        price: this.dirtyProduct.price,
        discountPrice: this.dirtyProduct.discountPrice || (this.dirtyProduct as any).discount_price,
        status: this.dirtyProduct.status
      };

      // Clean up undefined fields to avoid strict validation errors
      Object.keys(payload).forEach(key => payload[key] === undefined && delete payload[key]);

      console.log("📦 LiveEdit: Sending payload:", payload);

      const response = await fetch(`/api/v1/products/${this.dirtyProduct.id}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        console.log("✅ LiveEdit: Save successful.");
        this.originalProduct = JSON.parse(JSON.stringify(this.dirtyProduct));
        
        // Elite V2.2: Seamless HUD Feedback
        this.notify("Đã lưu thay đổi thành công!", "success");
        
        this.isEditMode = false;
        if (typeof window !== "undefined") {
            // Delay reload to allow user to see the success toast
            setTimeout(() => window.location.reload(), 1500);
        }
      } else {
        const err = await response.json();
        console.error("❌ LiveEdit: API rejection:", err);
        this.notify(`Lỗi khi lưu (HTTP ${response.status}): ${err.detail || 'Kiểm tra log hệ thống'}`, "alert");
      }
    } catch (e: any) {
      console.error("💥 LiveEdit: Connection error:", e);
      this.notify(`Lỗi kết nối máy chủ: ${e.message}`, "alert");
    } finally {
      this.isSaving = false;
    }
  }
}

export const liveEditStore = new LiveEditStore();
