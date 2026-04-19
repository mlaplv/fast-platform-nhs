export type OrderStatus = 'PENDING' | 'PACKED' | 'SHIPPING' | 'DELIVERED' | 'CANCELLED';

export interface OrderItem {
  id: string;              // product_id
  name: string;
  image_url?: string;
  quantity: number;        // qty
  unit_price: number;      // unit_price
  total_price: number;     // unit_price * quantity
  variant_id?: string;
  sku?: string;
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

export interface Order {
  id: string;
  status: OrderStatus;
  created_at: string;
  total_amount: number;
  items: OrderItem[];
  customer_name: string;
  customer_phone: string;
  customer_address: string;
  shipping_fee: number;
  payment_method: string;
  note?: string;
  is_trusted_device?: boolean;
  name_masked?: string;
  address_masked?: string;
  order_metadata?: {
    zalo_status?: 'ACTIVE' | 'NOT_FOUND' | 'PENDING';
    gift_info?: GiftInfo;
    custom_requests?: CustomRequestItem[];
    customer_note?: string;
    note?: string;
    [key: string]: unknown;
  };
}

export interface OrderDetail extends Order {
  history: OrderHistory[];
  insight?: {
    total_orders: number;
  };
  cancellation_reason?: string;
}
