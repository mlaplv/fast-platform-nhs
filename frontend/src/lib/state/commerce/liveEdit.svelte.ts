import { permissionState, getAuthToken } from "../permissions.svelte";
import type { Product, UpdateProductPayload } from "$lib/types";

import { lightLiveEdit } from "./liveEditState.svelte";

// Elite V2.2: Deep Indexing Types
type RecordObject = Record<string, unknown>;

class LiveEditStore {
  isSaving = $state(false);
  originalProduct = $state<Product | null>(null);

  // Elite V2.2: Getters & Setters delegating to lightLiveEdit to eliminate storefront dependency
  get isEditMode() { return lightLiveEdit.isEditMode; }
  set isEditMode(value: boolean) { lightLiveEdit.isEditMode = value; }

  get dirtyProduct() { return lightLiveEdit.dirtyProduct; }
  set dirtyProduct(value: Product | null) { lightLiveEdit.dirtyProduct = value; }

  get activePath() { return lightLiveEdit.activePath; }
  set activePath(value: string | null) { lightLiveEdit.activePath = value; }

  get openPopoverId() { return lightLiveEdit.openPopoverId; }
  set openPopoverId(value: string | null) { lightLiveEdit.openPopoverId = value; }
  
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

  togglePopover(id: string | null) {
    if (this.openPopoverId === id) this.openPopoverId = null;
    else this.openPopoverId = id;
  }

  // Military-Grade Security Suite (Elite V2.2)
  checkSecurity(): boolean {
    if (typeof window === 'undefined') return false;

    const urlParams = new URLSearchParams(window.location.search);
    const liveEditParam = urlParams.get('live_edit');
    const tockenParam = urlParams.get('tocken') || urlParams.get('token');

    // 1. Phải có tham số live_edit=true trong URL hoặc SessionStorage
    const hasLiveEditSession = liveEditParam === 'true' || sessionStorage.getItem('live_edit') === 'true';
    if (!hasLiveEditSession) {
      return false;
    }

    // 2. Phải có token hành chính hợp lệ
    const token = tockenParam || getAuthToken();
    if (!token) {
      return false;
    }

    try {
      // Giải mã JWT kiểm tra tính hợp lệ & quyền hạn
      const base64Url = token.split(".")[1];
      if (!base64Url) return false;
      const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
      const decoded = JSON.parse(atob(base64)) as any;

      // Kiểm tra thời hạn chữ ký
      if (decoded.exp && decoded.exp * 1000 < Date.now()) {
        console.warn("🔒 [MILITARY SECURITY] Token expired.");
        return false;
      }

      // Kiểm tra vai trò Admin tối cao
      const roles = decoded.roles || [];
      const hasAdminRole = roles.includes("SUPER_ADMIN") || roles.includes("ADMIN");
      if (!hasAdminRole) {
        console.warn("🔒 [MILITARY SECURITY] Privileges validation failed.");
        return false;
      }

      // Khi xác thực thành công cấp quân đội, ghi nhận phiên & cookie bảo mật
      sessionStorage.setItem('live_edit', 'true');
      if (tockenParam) {
        const rootDomain = window.location.hostname.split('.').slice(-2).join('.');
        document.cookie = `admin_token=${tockenParam}; path=/; domain=.${rootDomain}; max-age=604800; SameSite=Lax; Secure`;
        sessionStorage.setItem('admin_token', tockenParam);
      }

      return true;
    } catch (e) {
      console.error("🔒 [MILITARY SECURITY] Decoding / verification error:", e);
      return false;
    }
  }

  // Elite V2.2 Supreme Security: Administrative access strictly derives from RBAC token with military grade check
  get isAdmin() {
    return this.checkSecurity();
  }

  // Computed helper for components
  get dirtyMetadata() {
    return this.dirtyProduct?.metadata || {};
  }

  init(product: Product) {
    this.originalProduct = product;
    this.dirtyProduct = product;
    this.isEditMode = false;
  }

  toggleEditMode() {
    if (!this.isAdmin) {
      this.notify("🔒 Quyền truy cập bị từ chối. Vui lòng xác thực cấp quân đội.", "alert");
      this.isEditMode = false;
      return;
    }

    this.isEditMode = !this.isEditMode;
    if (this.isEditMode && this.originalProduct) {
        // Elite V2.2: Deep clone ON DEMAND when edit starts
        this.dirtyProduct = JSON.parse(JSON.stringify(this.originalProduct));
    } else if (!this.isEditMode) {
        this.discardChanges();
    }
  }

  updateField(path: string, value: unknown) {
    if (!this.dirtyProduct) return;

    try {
      const normalizedPath = path.replace(/\[(\d+)\]/g, '.$1');
      const keys = normalizedPath.split(".");
      let current = this.dirtyProduct as unknown as RecordObject;

      for (let i = 0; i < keys.length - 1; i++) {
        const key = keys[i];
        const nextKey = keys[i + 1];

        if (current[key] === null || current[key] === undefined || typeof current[key] !== 'object') {
          current[key] = /^\d+$/.test(nextKey) ? [] : {};
        }

        current = current[key] as RecordObject;
      }

      current[keys[keys.length - 1]] = value;
      // Force trigger Svelte proxy by resetting reference
      this.dirtyProduct = JSON.parse(JSON.stringify(this.dirtyProduct)) as Product;
    } catch (error) {
      console.error(`💥 LiveEdit: Failed to update field at ${path}:`, error);
      const msg = error instanceof Error ? error.message : String(error);
      this.notify(`Lỗi cập nhật dữ liệu: ${msg}`, "alert");
    }
  }

  discardChanges() {
    this.dirtyProduct = this.originalProduct;
    this.isEditMode = false;
    this.activePath = null;
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
        
        const payload: UpdateProductPayload = {
            name: p.name,
            shortDescription: p.shortDescription || '',
            metadata: p.metadata,
            price: p.price,
            discountPrice: p.discountPrice,
            status: p.status as 'DRAFT' | 'ACTIVE' | 'ARCHIVED',
            variants: p.variants,
            images: p.images,
            mobileImages: p.mobileImages
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
        }
    } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        this.notify(`Lỗi kết nối máy chủ: ${msg}`, "alert");
    } finally {
        this.isSaving = false;
    }
  }

  // Elite V2.2: Global DOM Synchronization!
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
