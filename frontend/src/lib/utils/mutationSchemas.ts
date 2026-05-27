/**
 * Mutation Field Schemas — defines required fields per (target, verb).
 * AI pre-fills what it extracts; user completes the rest in the form.
 */
import type { FormField } from "$lib/state/types";
import type { Category } from "$lib/types";
import { apiClient } from "$lib/utils/apiClient";

export type MutationVerb = "create" | "edit" | "delete" | "update_status";
export type MutationTarget =
  | "user"
  | "product"
  | "category"
  | "article"
  | "order";

export interface MutationSchema {
  title: string;
  message: string;
  confirmLabel: string;
  fields: FormField[];
}

// ── SCHEMAS ──────────────────────────────────────────────

const USER_CREATE: MutationSchema = {
  title: "TẠO NHÂN VIÊN MỚI",
  message: "Điền thông tin nhân viên mới:",
  confirmLabel: "TẠO NHÂN VIÊN",
  fields: [
    {
      key: "name",
      label: "Họ và tên",
      type: "text",
      required: true,
      placeholder: "Nguyễn Văn A",
    },
    {
      key: "email",
      label: "Email",
      type: "email",
      required: true,
      placeholder: "nhanvien@company.com",
    },
    {
      key: "password",
      label: "Mật khẩu",
      type: "password",
      required: true,
      placeholder: "Tối thiểu 6 ký tự",
    },
    {
      key: "role",
      label: "Vai trò",
      type: "select",
      required: true,
      defaultValue: "staff",
      options: [
        { value: "staff", label: "Nhân viên" },
        { value: "admin", label: "Quản trị viên" },
      ],
    },
  ],
};

const PRODUCT_CREATE: MutationSchema = {
  title: "TẠO SẢN PHẨM MỚI",
  message: "Điền thông tin sản phẩm:",
  confirmLabel: "TẠO SẢN PHẨM",
  fields: [
    {
      key: "name",
      label: "Tên sản phẩm",
      type: "text",
      required: true,
      placeholder: "Tên sản phẩm",
    },
    {
      key: "price",
      label: "Giá (VND)",
      type: "number",
      required: true,
      placeholder: "0",
    },
    {
      key: "stock",
      label: "Tồn kho",
      type: "number",
      required: false,
      placeholder: "0",
      defaultValue: "0",
    },
    {
      key: "status",
      label: "Trạng thái",
      type: "select",
      required: true,
      defaultValue: "DRAFT",
      options: [
        { value: "DRAFT", label: "Nháp" },
        { value: "ACTIVE", label: "Đang bán" },
        { value: "INACTIVE", label: "Ngừng bán" },
      ],
    },
    {
      key: "description",
      label: "Mô tả",
      type: "textarea",
      required: false,
      placeholder: "Mô tả sản phẩm (tùy chọn)",
    },
  ],
};

const CATEGORY_CREATE: MutationSchema = {
  title: "TẠO DANH MỤC MỚI",
  message: "Điền tên danh mục:",
  confirmLabel: "TẠO DANH MỤC",
  fields: [
    {
      key: "name",
      label: "Tên danh mục",
      type: "text",
      required: true,
      placeholder: "Tên danh mục",
    },
  ],
};

const ARTICLE_CREATE: MutationSchema = {
  title: "TẠO BÀI VIẾT MỚI",
  message: "Điền thông tin bài viết:",
  confirmLabel: "TẠO BÀI VIẾT",
  fields: [
    {
      key: "title",
      label: "Tiêu đề",
      type: "text",
      required: true,
      placeholder: "Tiêu đề bài viết",
    },
    {
      key: "category",
      label: "Chuyên mục",
      type: "select",
      required: true,
      defaultValue: "",
      options: [], // Will be populated dynamically
    },
    {
      key: "excerpt",
      label: "Tóm tắt",
      type: "textarea",
      required: false,
      placeholder: "Mô tả ngắn (tùy chọn)",
    },
    {
      key: "content",
      label: "Nội dung bài viết",
      type: "textarea",
      required: false,
      placeholder: "Nội dung đầy đủ",
    },
    {
      key: "slug",
      label: "Đường dẫn SEO (Slug)",
      type: "text",
      required: false,
      placeholder: "Để trống sẽ tự động tạo từ tiêu đề",
    },
    {
      key: "seo_title",
      label: "SEO Title",
      type: "text",
      required: false,
      placeholder: "Tiêu đề chuẩn SEO",
    },
    {
      key: "seo_description",
      label: "SEO Description",
      type: "textarea",
      required: false,
      placeholder: "Tóm tắt chuẩn SEO cho Meta Description",
    },
  ],
};

const ORDER_UPDATE_STATUS: MutationSchema = {
  title: "CẬP NHẬT TRẠNG THÁI ĐƠN HÀNG",
  message: "Chọn trạng thái mới:",
  confirmLabel: "CẬP NHẬT",
  fields: [
    {
      key: "status",
      label: "Trạng thái",
      type: "select",
      required: true,
      options: [
        { value: "pending", label: "Tiếp nhận đơn hàng" },
        { value: "packed", label: "Đã đóng gói bảo mật" },
        { value: "shipping", label: "Đang vận chuyển" },
        { value: "delivered", label: "Giao thành công" },
        { value: "cancelled", label: "Đã hủy" },
      ],
    },
  ],
};

// ── DELETE — confirm only, no form fields ──

function deleteSchema(target: string): MutationSchema {
  const VI_TARGET: Record<string, string> = {
    user: "nhân viên",
    product: "sản phẩm",
    category: "danh mục",
    news: "bài viết",
    order: "đơn hàng",
  };
  const label = VI_TARGET[target] || target;
  return {
    title: `XÓA ${label.toUpperCase()}`,
    message: `Xác nhận xóa ${label} này? Hành động không thể hoàn tác.`,
    confirmLabel: "XÓA",
    fields: [],
  };
}

// ── REGISTRY ──

const SCHEMA_MAP: Record<string, Record<string, MutationSchema>> = {
  user: { create: USER_CREATE },
  product: { create: PRODUCT_CREATE },
  category: { create: CATEGORY_CREATE },
  news: { create: ARTICLE_CREATE },
  order: { update_status: ORDER_UPDATE_STATUS },
};

/**
 * Get the form schema for a mutation.
 * Returns schema with fields pre-filled from AI-extracted entities.
 */
export async function getMutationSchema(
  target: string,
  verb: string,
  entities: Record<string, string> = {},
): Promise<MutationSchema | null> {
  if (verb === "delete") {
    return deleteSchema(target);
  }

  const targetSchemas = SCHEMA_MAP[target];
  if (!targetSchemas) return null;

  const schema = { ...targetSchemas[verb] }; // shallow copy
  if (!schema) return null;

  // Dynamically load categories for news article
  if (target === "news" && schema.fields) {
    try {
      const categoryData = await apiClient.get<Category[]>("/api/v1/categories") || [];
      const opts = categoryData.map((c: Category) => ({
        value: c.name,
        label: c.name,
      }));

      schema.fields = schema.fields.map((f) => {
        if (f.key === "category") {
          return {
            ...f,
            options: opts,
            defaultValue: opts.length > 0 ? opts[0].value : "",
          };
        }
        return f;
      });
    } catch (e) {
      console.error("Failed to fetch dynamically categories", e);
    }
  }

  // Pre-fill fields from AI-extracted entities
  const filledFields = schema.fields.map((f) => ({
    ...f,
    defaultValue: entities[f.key] || f.defaultValue || "",
  }));

  return { ...schema, fields: filledFields };
}
