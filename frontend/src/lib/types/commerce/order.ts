export type OrderStatus = 'PENDING' | 'PACKED' | 'SHIPPING' | 'DELIVERED' | 'CANCELLED';

export interface OrderItem {
  id: string;
  name: string;
  image?: string;
  image_url?: string;
  quantity: number;
  qty?: number;
  price: number;
  unit_price?: number;
  total_price?: number;
  totalPrice?: number;
  variant?: string;
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
  image?: string;
  image_url?: string;
  qty?: number;
  quantity?: number;
}

export interface Order {
  id: string;
  status: OrderStatus;
  created_at: string;
  createdAt?: string;
  total_amount: number;
  total?: number;
  items: OrderItem[];
  customer_name: string;
  customerName?: string;
  customer_phone: string;
  customerPhone?: string;
  customer_address: string;
  customerAddress?: string;
  name_masked?: string;
  address_masked?: string;
  shipping_fee: number;
  payment_method: string;
  note?: string;
  itemCount?: number;
  is_trusted_device?: boolean;
  order_metadata?: {
    zalo_status?: 'ACTIVE' | 'NOT_FOUND' | 'PENDING';
    gift_info?: GiftInfo;
    custom_requests?: CustomRequestItem[];
    customer_note?: string;
    note?: string;
    [key: string]: unknown;
  };
  orderMetadata?: {
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
  insight?: CustomerInsight;
  cancellationReason?: string;
}
