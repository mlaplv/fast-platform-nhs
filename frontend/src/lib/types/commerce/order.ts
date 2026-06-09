export type OrderStatus = 'PENDING' | 'PACKED' | 'SHIPPING' | 'DELIVERED' | 'CANCELLED';

export interface OrderItem {
  id: string;              // product_id
  name: string;
  image?: string;          // snapshot image
  image_url?: string;      // legacy image
  quantity?: number;       // legacy qty
  qty?: number;            // backend qty
  unit_price: number;      // unit_price
  total_price: number;     // unit_price * quantity
  variant_id?: string;
  sku?: string;
  variant_name?: string;
  gifts?: {
    name: string;
    qty: number;
    image?: string;
  }[];
}

export interface OrderHistory {
  status: string;
  timestamp: string;
  actor: string;
  note?: string;
}

export interface CustomerInsight {
  ltv: number;
  total_orders: number;
  trust_score: number;
  first_order?: string;
  last_order?: string;
  previous_orders: {
    id: string;
    created_at: string;
    status: string;
    total: number;
    item_count: number;
  }[];
}

export interface GiftInfo {
  sender_name: string;
  sender_phone: string;
  message?: string;
  packaging?: string;
  scheduled_at?: string;
}

export interface CustomRequestItem {
  name: string;
  image_url?: string;
  quantity: number;
  price?: number;
}

export interface OrderMetadata {
  zalo_status?: 'ACTIVE' | 'NOT_FOUND' | 'PENDING';
  gift_info?: GiftInfo;
  custom_requests?: CustomRequestItem[];
  customer_note?: string;
  note?: string;
  shipping_fee?: number;
  voucher_discount?: number;
  combo_discount?: number;
  [key: string]: unknown;
}

export interface Order {
  id: string;
  status: OrderStatus;
  created_at: string;
  total_amount: number;
  total?: number; // Elite V2.2: Alias for total_amount
  items: OrderItem[];
  customer_name: string;
  customer_phone: string;
  customer_address: string;
  
  // Pydantic Aliases (CamelCase Sync)
  customerName?: string;
  customerPhone?: string;
  customerAddress?: string;
  orderMetadata?: OrderMetadata;

  shipping_fee: number;
  payment_method: string;
  note?: string;
  is_trusted_device?: boolean;
  name_masked?: string;
  address_masked?: string;
  order_metadata?: OrderMetadata;

  points_earned?: number;
  points_redeemed?: number;
  point_discount_amount?: number;
}

export interface OrderDetail extends Order {
  history: OrderHistory[];
  insight?: {
    total_orders: number;
  };
  cancellation_reason?: string;
  cancellationReason?: string; // Pydantic Alias
}
