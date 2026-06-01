import { formatCurrency } from '$lib/utils/format';

export interface VoucherUI {
  id: string;
  label: string;
  sub: string;
  type: 'ship' | 'discount';
  value: number;
}

/**
 * Standardize string for comparison, removing accents and transforming to uppercase
 */
export function cleanString(s: string): string {
  return (s || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toUpperCase();
}

/**
 * Check if a voucher is a viral voucher
 */
export function isViralVoucher(
  v: { id: string; label?: string; title?: string; is_viral?: boolean },
  sharePromoVoucherId?: string | null
): boolean {
  return !!v.is_viral || (!!sharePromoVoucherId && v.id === sharePromoVoucherId);
}

// --- HIGH PERFORMANCE INDEXING & MEMOIZATION ENGINES ---
// 1. Memoization Cache for processProductVouchers
interface CacheEntry {
  result: VoucherUI[];
  timestamp: number;
}
const processCache = new Map<string, CacheEntry>();

// 2. Global Voucher O(1) Lookup Index Maps
let lastGlobalVouchersLength = -1;
const globalVoucherIndexMap = new Map<string, any>();
const globalVouchersForAll = new Array<any>();
const globalVouchersByProductMap = new Map<string, any[]>();

/**
 * Re-index global vouchers for O(1) lookups whenever length or reference changes
 */
function rebuildVoucherIndexes(globalVouchers: any[] = []): void {
  const currentLen = globalVouchers?.length ?? 0;
  if (currentLen === lastGlobalVouchersLength && globalVoucherIndexMap.size > 0) {
    return; // Already indexed
  }

  globalVoucherIndexMap.clear();
  globalVouchersForAll.length = 0;
  globalVouchersByProductMap.clear();

  for (const v of globalVouchers || []) {
    if (!v || !v.id) continue;
    globalVoucherIndexMap.set(v.id, v);

    const applicableIds = v.metadata_json?.applicable_product_ids || [];
    if (Array.isArray(applicableIds) && applicableIds.length > 0) {
      for (const pId of applicableIds) {
        if (!globalVouchersByProductMap.has(pId)) {
          globalVouchersByProductMap.set(pId, []);
        }
        globalVouchersByProductMap.get(pId)!.push(v);
      }
    } else {
      globalVouchersForAll.push(v);
    }
  }
  lastGlobalVouchersLength = currentLen;
}

/**
 * Calculate the absolute discount value of a voucher for a given product price (O(1) Complexity)
 */
export function getVoucherDisplayValue(
  v: { id: string; value?: number; type?: string; sub?: string; subtitle?: string; label?: string; title?: string },
  productPrice: number,
  globalVouchers: any[] = []
): number {
  let rawVal = typeof v.value === 'number' ? v.value : 0;
  const subText = cleanString(v.sub || v.subtitle || '').toLowerCase();
  const labelText = cleanString(v.label || v.title || '').toLowerCase();

  if (rawVal === 0) {
    rebuildVoucherIndexes(globalVouchers);
    const found = globalVoucherIndexMap.get(v.id);
    if (found) {
      rawVal = found.value || 0;
      if (found.type === 'PERCENT') {
        return (productPrice * rawVal) / 100;
      }
    }
  }

  if (subText.includes('%') || labelText.includes('%')) {
    const parsedPercent = parseInt((v.sub || v.subtitle || v.label || v.title || '').replace(/[^0-9]/g, ''), 10);
    if (!isNaN(parsedPercent)) {
      return (productPrice * parsedPercent) / 100;
    }
  }

  if (rawVal > 0) {
    const typeLower = String(v.type).toLowerCase();
    const isPercent = 
      rawVal <= 100 && 
      (typeLower === 'percent' || 
       String(v.id).toLowerCase().includes('pct') || 
       subText.includes('%'));
       
    if (isPercent) {
      return (productPrice * rawVal) / 100;
    }
    return rawVal;
  }

  const parsed = parseInt(subText.replace(/[^0-9]/g, ''), 10);
  return isNaN(parsed) ? 0 : parsed;
}

interface ProcessParams {
  product: any;
  globalVouchers: any[];
  isViralUnlocked: boolean;
  unlockedVoucherInfo: { code: string; label?: string } | null;
  productPrice: number;
}

/**
 * Unifies voucher loading, processing, normalization, and sorting for all storefront product detail views
 * Uses High-Performance Memoization Caching and O(1) Indexing Engine.
 */
export function processProductVouchers({
  product,
  globalVouchers,
  isViralUnlocked,
  unlockedVoucherInfo,
  productPrice
}: ProcessParams): VoucherUI[] {
  if (!product) return [];

  // --- 1. MEMOIZATION CACHE HIT TEST ---
  const globalLen = globalVouchers?.length ?? 0;
  const cacheKey = `${product.id}_${isViralUnlocked ? '1' : '0'}_${productPrice}_${unlockedVoucherInfo?.code || ''}_${globalLen}`;
  const cached = processCache.get(cacheKey);
  const now = Date.now();
  if (cached && (now - cached.timestamp < 3000)) {
    return cached.result; // Cache Hit: Instant 0ms response!
  }

  const metadata = product.product_metadata || product.metadata || {};
  const sharePromoVoucherId = metadata.share_promotion?.voucher_id || null;

  let rawList: any[] = [];

  // --- 2. LOAD VOUCHERS VIA INDEXING ENGINE ---
  if (Array.isArray(metadata.vouchers) && metadata.vouchers.length > 0) {
    rawList = metadata.vouchers.map((v: any) => ({
      id: v.id,
      label: v.label || v.title || v.id,
      sub: v.sub || v.subtitle || (v.type === 'SHIPPING' ? 'Miễn phí vận chuyển' : v.type === 'PERCENT' ? `Giảm ${v.value}%` : `Giảm ${formatCurrency(v.value)}`),
      type: (v.type === 'SHIPPING' || String(v.type).toLowerCase() === 'ship') ? 'ship' : 'discount',
      value: v.value || 0
    }));
  } else {
    rebuildVoucherIndexes(globalVouchers);
    
    // O(1) Product Vouchers retrieval instead of O(N) filter
    const productSpecific = globalVouchersByProductMap.get(product.id) || [];
    const combined = [...globalVouchersForAll, ...productSpecific];

    rawList = combined.map((v: any) => ({
      id: v.id,
      label: v.title || v.id,
      sub: v.subtitle || (v.type === 'SHIPPING' ? 'Miễn phí vận chuyển' : v.type === 'PERCENT' ? `Giảm ${v.value}%` : `Giảm ${formatCurrency(v.value)}`),
      type: v.type === 'SHIPPING' ? 'ship' : 'discount',
      value: v.value || 0
    }));
  }

  // --- 3. FILTER LOCKED VIRAL VOUCHERS ---
  let processed = rawList.filter(v => {
    return !isViralVoucher(v, sharePromoVoucherId) || isViralUnlocked;
  });

  // --- 4. INJECT UNLOCKED VIRAL VOUCHER ---
  if (unlockedVoucherInfo) {
    processed = processed.filter(
      v => !isViralVoucher(v, sharePromoVoucherId) && v.id !== unlockedVoucherInfo.code
    );
    processed.unshift({
      id: unlockedVoucherInfo.code,
      label: unlockedVoucherInfo.label || 'Voucher lan tỏa',
      sub: 'Đã mở khóa từ chiến dịch',
      type: 'discount',
      value: 79000
    });
  }

  // --- 5. SORT DESCENDING BY CALCULATED VALUE ---
  const sorted = [...processed].sort((a, b) => {
    const valA = getVoucherDisplayValue(a, productPrice, globalVouchers);
    const valB = getVoucherDisplayValue(b, productPrice, globalVouchers);
    return valB - valA;
  });

  // --- 6. CATEGORIZE & PRIORITIZE VIRAL VOUCHERS ---
  const viralVouchers = sorted.filter(v => isViralVoucher(v, sharePromoVoucherId));
  const regularDiscount = sorted.filter(v => !isViralVoucher(v, sharePromoVoucherId) && v.type === 'discount');
  const regularShipping = sorted.filter(v => !isViralVoucher(v, sharePromoVoucherId) && v.type === 'ship');

  const finalResult = [...viralVouchers, ...regularDiscount, ...regularShipping] as VoucherUI[];

  // --- 7. POPULATE MEMOIZATION CACHE ---
  processCache.set(cacheKey, {
    result: finalResult,
    timestamp: now
  });

  return finalResult;
}
