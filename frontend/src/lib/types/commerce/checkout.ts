import type { GiftInfo } from "$lib/state/commerce/cart.svelte";

export interface CustomItem {
  id: string;
  name: string;
  price: number;
  quantity: number;
  image?: string;
  metadata?: Record<string, unknown>;
}

export interface Voucher {
  id: string;
  title: string;
  desc: string;
  type: 'FIXED' | 'PERCENT' | 'SHIPPING';
  value: number;
  min_spend: number;
  subtitle?: string;
  category: string;
  is_default: boolean;
  priority: number;
}

export interface CheckoutPayload {
  name: string;
  phone: string;
  province: string;
  ward: string;
  street: string;
  shipping_method: 'standard' | 'express';
  note?: string;
  gift_info?: GiftInfo;
  custom_items?: CustomItem[];
}

export interface CheckoutResponse {
  success: boolean;
  ok: boolean;
  id?: string;
  message?: string;
}

export interface CustomerLookupResponse {
  name: string | null;
  province: string | null;
  ward: string | null;
  street: string | null;
  is_recurring: boolean;
  is_trusted_device: boolean;
  name_masked: string | null;
  address_masked: string | null;
}

export interface ProvinceData {
  id: string | number;
  name: string;
  has_express?: boolean;
  express_fee?: number;
  express_supported_wards?: string[];
  wards: string[];
}

export interface CheckoutVariant {
  id: string;
  sku?: string;
  price?: number;
  discountPrice?: number;
  tierIndex?: number[];
}

/** Elite V2.2: Pydantic Validation Error Location Wrapper */
export interface PydanticErrorDetail {
  loc: (string | number)[];
  msg: string;
  type: string;
  ctx?: Record<string, unknown>;
}

export interface PydanticValidationError {
  detail: PydanticErrorDetail[];
}
