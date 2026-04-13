/**
 * Mutation Executor — maps (target, verb) → API call.
 * Called AFTER user confirms the smart form.
 */
import { apiClient, ApiError } from "$lib/utils/apiClient";
import type { User, Product, Category, Article, Order } from "$lib/types";

export interface MutationResult {
  success: boolean;
  message: string;
  data?: unknown;
}

const VI_TARGET: Record<string, string> = {
  user: "nhân viên",
  product: "sản phẩm",
  category: "danh mục",
  news: "bài viết",
  order: "đơn hàng",
};

const VI_VERB: Record<string, string> = {
  create: "tạo",
  edit: "cập nhật",
  delete: "xóa",
  update_status: "cập nhật trạng thái",
};

export async function executeMutation(
  target: string,
  verb: string,
  formData: Record<string, string>,
  entityId?: string,
): Promise<MutationResult> {
  const label = VI_TARGET[target] || target;
  const verbLabel = VI_VERB[verb] || verb;

  try {
    let res: unknown;

    if (verb === "create") {
      res = await createEntity(target, formData);
    } else if (verb === "delete" && entityId) {
      res = await deleteEntity(target, entityId);
    } else if (verb === "edit" && entityId) {
      res = await editEntity(target, entityId, formData);
    } else if (verb === "update_status" && entityId) {
      res = await updateStatus(target, entityId, formData);
    } else {
      return {
        success: false,
        message: `Chưa hỗ trợ thao tác "${verbLabel}" cho ${label}.`,
      };
    }

    const name = formData.name || formData.title || "";
    const successMsg = name
      ? `Đã ${verbLabel} ${label} "${name}" thành công.`
      : `Đã ${verbLabel} ${label} thành công.`;

    return { success: true, message: successMsg, data: res };
  } catch (e: unknown) {
    const errMsg = e instanceof ApiError ? e.message : (e as Error)?.message || "Lỗi không xác định.";
    return {
      success: false,
      message: `Không thể ${verbLabel} ${label}: ${errMsg}`,
    };
  }
}

// ── CREATE ──

async function createEntity(
  target: string,
  data: Record<string, string>,
): Promise<User | Product | Category | Article | { status: string }> {
  switch (target) {
    case "user": {
      // Register new user via auth endpoint
      const payload: Record<string, unknown> = {
        name: data.name,
        email: data.email,
        password: data.password,
      };
      const res = await apiClient.post<User>("/api/v1/auth/register", payload);
      // After creation, assign role if not default
      if (data.role && data.role !== "staff" && res?.id) {
        await apiClient
          .patch<{ status: string }>(`/api/v1/users/${res.id}/roles`, {
            roles: [data.role],
          })
          .catch(() => {
            /* Role assignment is best-effort */
          });
      }
      return res;
    }
    case "product":
      return apiClient.post<Product>("/api/v1/products", {
        name: data.name,
        price: Number(data.price) || 0,
        stock: Number(data.stock) || 0,
        status: data.status || "DRAFT",
        description: data.description || "",
        type: "RETAIL",
      });
    case "category":
      return apiClient.post<Category>("/api/v1/categories", {
        name: data.name,
      });
    case "news":
      return apiClient.post<Article>("/api/v1/articles", {
        title: data.title,
        category: data.category || "Bài viết",
        excerpt: data.excerpt || "",
        content: data.content || "",
        slug: data.slug || undefined,
        seo_title: data.seo_title || undefined,
        seo_description: data.seo_description || undefined,
        status: "DRAFT",
      });
    default:
      throw new Error(`Unsupported create target: ${target}`);
  }
}

// ── DELETE ──

async function deleteEntity(target: string, entityId: string): Promise<{ status: string }> {
  const endpoint = `/api/v1/${target === "news" ? "articles" : target + "s"}/${entityId}`;
  return apiClient.delete<{ status: string }>(endpoint);
}

// ── EDIT ──

async function editEntity(
  target: string,
  entityId: string,
  data: Record<string, string>,
): Promise<User | Product | Category | Article | Order> {
  const endpoint = `/api/v1/${target === "news" ? "articles" : target + "s"}/${entityId}`;
  return apiClient.patch<User | Product | Category | Article | Order>(endpoint, data);
}

// ── UPDATE STATUS ──

async function updateStatus(
  target: string,
  entityId: string,
  data: Record<string, string>,
): Promise<{ status: string }> {
  if (target === "order") {
    return apiClient.patch<{ status: string }>(`/api/v1/orders/${entityId}/status`, {
      status: data.status,
    });
  }
  throw new Error(`Unsupported update_status target: ${target}`);
}
