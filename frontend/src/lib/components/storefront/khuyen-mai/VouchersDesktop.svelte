<script lang="ts">
  import { fade, fly } from "svelte/transition";
  import { onMount } from "svelte";
  import type { Voucher, Product } from "$lib/types";
  import { formatCurrency } from "$lib/utils/format";
  import ProductCard from "$lib/components/storefront/home/ProductCard.svelte";
  import Ticket from "@lucide/svelte/icons/ticket";
  import Tag from "@lucide/svelte/icons/tag";
  import Truck from "@lucide/svelte/icons/truck";

  let { vouchers = [], products = [] }: { vouchers: Voucher[]; products: Product[] } = $props();

  // Desktop states
  let activeTab = $state<"ALL" | "DISCOUNT" | "SHIPPING">("ALL");
  const tabs = [
    { id: "ALL" as const, label: "Tất cả", icon: Ticket },
    { id: "DISCOUNT" as const, label: "Giảm giá", icon: Tag },
    { id: "SHIPPING" as const, label: "Miễn ship", icon: Truck },
  ];

  const filtered = $derived(
    activeTab === "ALL"
      ? vouchers
      : vouchers.filter((v) => v.category === activeTab)
  );

  // Pagination states
  let currentPage = $state(1);
  const itemsPerPage = 6;

  $effect(() => {
    // Reset page to 1 when changing active tab
    activeTab;
    currentPage = 1;
  });

  const paginatedFiltered = $derived(
    filtered.slice(
      (currentPage - 1) * itemsPerPage,
      currentPage * itemsPerPage
    )
  );

  const totalPages = $derived(Math.ceil(filtered.length / itemsPerPage));

  // Live countdown timer state (FOMO urgency)
  let timeLeft = $state({ hours: 0, minutes: 0, seconds: 0 });
  function updateCountdown() {
    const now = new Date();
    const endOfDay = new Date();
    endOfDay.setHours(23, 59, 59, 999);
    const diff = endOfDay.getTime() - now.getTime();

    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((diff % (1000 * 60)) / 1000);

    timeLeft = { hours, minutes, seconds };
  }

  onMount(() => {
    updateCountdown();
    const timer = setInterval(updateCountdown, 1000);

    return () => {
      clearInterval(timer);
    };
  });

  let copiedId = $state<string | null>(null);
  let activeConditionVoucherId = $state<string | null>(null);

  async function copyCode(id: string) {
    try {
      await navigator.clipboard.writeText(id);
      copiedId = id;
      setTimeout(() => {
        copiedId = null;
      }, 2000);
    } catch {
      // Fallback
    }
  }

  function usedPercent(v: Voucher): number {
    if (!v.usage_limit || v.usage_limit <= 0) return 0;
    return Math.min(100, Math.round((v.used_count / v.usage_limit) * 100));
  }

  function isExhausted(v: Voucher): boolean {
    return !!(v.usage_limit && v.used_count >= v.usage_limit);
  }

  function quantityLeft(v: Voucher): number | null {
    if (!v.usage_limit) return null;
    return Math.max(0, v.usage_limit - v.used_count);
  }

  function formatShort(val: number): string {
    if (!val) return "0đ";
    if (val >= 1000000) {
      return `${val / 1000000}Mđ`;
    }
    if (val >= 1000) {
      return `${val / 1000}kđ`;
    }
    return `${val}đ`;
  }
</script>

<div class="voucher-page" in:fade={{ duration: 250 }}>
  <!-- ===== HERO BADGE/TITLE SYSTEM (SHOPEE STYLE RIBBON) ===== -->
  <div class="ribbon-title-container">
    <img
      src="/uploads/img/vn-voucher.webp"
      alt="Ưu Đãi Ngập Tràn"
      class="ribbon-title-img"
    />
    <p class="ribbon-subtitle">
      Số lượng có hạn, dành cho những bạn nhanh nhất.
    </p>
  </div>



  <!-- ===== TABS ===== -->
  <div class="tab-bar">
    {#each tabs as tab}
      {@const Icon = tab.icon}
      <button
        id="voucher-tab-{tab.id.toLowerCase()}"
        class="tab-btn {activeTab === tab.id ? 'tab-active' : ''}"
        onclick={() => {
          activeTab = tab.id;
        }}
      >
        <span class="tab-icon">
          <Icon size={16} />
        </span>
        {tab.label}
      </button>
    {/each}
  </div>

  <!-- ===== VOUCHER GRID ===== -->
  <div class="voucher-grid">
    {#if filtered.length === 0}
      <div class="empty-state">
        <div class="empty-icon">🎟️</div>
        <p class="empty-title">Chưa có ưu đãi nào</p>
        <p class="empty-sub">Hãy quay lại sau khi hệ thống tung deal mới!</p>
      </div>
    {:else}
      {#each paginatedFiltered as v, i (v.id)}
        {@const pct = usedPercent(v)}
        <div
          class="voucher-card {isExhausted(v) ? 'card-exhausted' : ''}"
          in:fly={{ y: 20, duration: 300, delay: i * 40 }}
        >
          <!-- LEFT STUB -->
          <div
            class="card-stub {v.category === 'SHIPPING'
              ? 'stub-ship'
              : 'stub-discount'}"
          >
            <svg
              class="stub-svg"
              viewBox="0 0 100 100"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <!-- Speed lines -->
              <line
                x1="15"
                y1="38"
                x2="35"
                y2="38"
                stroke="white"
                stroke-width="6"
                stroke-linecap="round"
              />
              <line
                x1="10"
                y1="50"
                x2="35"
                y2="50"
                stroke="white"
                stroke-width="6"
                stroke-linecap="round"
              />
              <line
                x1="15"
                y1="62"
                x2="35"
                y2="62"
                stroke="white"
                stroke-width="6"
                stroke-linecap="round"
              />
              <!-- Shopping bag outline -->
              <rect
                x="42"
                y="35"
                width="40"
                height="40"
                rx="8"
                stroke="white"
                stroke-width="6"
              />
              <path
                d="M52 35C52 26 58 20 62 20C66 20 72 26 72 35"
                stroke="white"
                stroke-width="6"
                stroke-linecap="round"
              />
              <!-- O letter inside bag -->
              <circle cx="62" cy="55" r="7" stroke="white" stroke-width="4" fill="none" />
            </svg>
            <div class="stub-label">OSMO</div>
          </div>

          <!-- RIGHT CONTENT -->
          <div class="card-body">
            {#if pct > 70}
              <span class="hot-pill">x10</span>
            {/if}

            <div class="card-title-row">
              <span class="card-title">
                {#if v.type === "PERCENT"}
                  Giảm {v.value}%
                {:else}
                  Giảm {formatShort(v.value)}
                {/if}
              </span>
            </div>

            <!-- Red bordered Exclusive tag badge -->
            <div class="exclusive-tag-row">
              <span class="exclusive-badge"
                >Độc quyền - {v.id.substring(0, 8)}...</span
              >
            </div>

            <!-- Shortened conditions -->
            <p class="card-detail">
              {#if v.type === "PERCENT" && v.max_discount}
                Giảm tối đa {formatShort(v.max_discount)}
              {:else}
                Giảm tối đa {formatShort(v.value)}
              {/if}
              Đơn Tối Thiểu {formatShort(v.min_spend)}
            </p>

            <!-- Usage text -->
            <p class="usage-status-text">Đã dùng {pct}%</p>

            <!-- Action row -->
            <div class="card-action-row">
              {#if isExhausted(v)}
                <button class="btn-exhausted" disabled>Hết lượt sử dụng</button>
              {:else}
                <button
                  id="copy-voucher-{v.id}"
                  class="btn-save {copiedId === v.id ? 'btn-copied' : ''}"
                  onclick={() => copyCode(v.id)}
                >
                  {copiedId === v.id ? "Đã lưu ✓" : "Lưu"}
                </button>
              {/if}
              <button
                type="button"
                class="terms-link-btn"
                onclick={() =>
                  (activeConditionVoucherId =
                    activeConditionVoucherId === v.id ? null : v.id)}
              >
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="3"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  style="width: 10px; height: 10px;"
                >
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
                Thỏa điều kiện
              </button>
            </div>
          </div>

          <!-- Slide down / Absolute condition overlay with voucher code details -->
          {#if activeConditionVoucherId === v.id}
            <div class="condition-overlay" transition:fade={{ duration: 150 }}>
              <div class="condition-box">
                <div class="condition-header">
                  <p class="condition-title">Chi Tiết Điều Kiện</p>
                  <button
                    type="button"
                    class="btn-close-x"
                    onclick={() => (activeConditionVoucherId = null)}>×</button
                  >
                </div>

                <div class="code-stamp-container">
                  <span class="code-stamp-label">MÃ GIẢM GIÁ</span>
                  <div class="code-stamp-box">
                    <span class="code-stamp-text">{v.id}</span>
                    <button
                      class="btn-stamp-copy"
                      onclick={() => copyCode(v.id)}
                    >
                      {copiedId === v.id ? "Đã chép ✓" : "Sao chép"}
                    </button>
                  </div>
                </div>

                <div class="condition-content-scroll">
                  <ul class="condition-list">
                    <li>
                      Áp dụng cho đơn hàng tối thiểu <strong>{formatCurrency(v.min_spend)}</strong>.
                    </li>
                    {#if v.type === "PERCENT" && v.max_discount}
                      <li>
                        Giảm tối đa lên đến <strong>{formatCurrency(v.max_discount)}</strong>.
                      </li>
                    {/if}
                    <li>Mỗi khách hàng sử dụng tối đa 1 lần.</li>
                    {#if quantityLeft(v) !== null}
                      <li>
                        Còn lại <strong>{quantityLeft(v)}</strong> lượt sử dụng.
                      </li>
                    {/if}
                    <li>
                      Hạn sử dụng: Vui lòng sử dụng sớm trước khi hết lượt.
                    </li>
                  </ul>
                </div>

                <button
                  class="btn-close-condition"
                  onclick={() => (activeConditionVoucherId = null)}
                  >Đồng ý</button
                >
              </div>
            </div>
          {/if}
        </div>
      {/each}
    {/if}
  </div>

  <!-- ===== PAGINATION CONTROLS ===== -->
  {#if totalPages > 1}
    <div class="pagination-wrap">
      <button
        type="button"
        class="pagination-btn arrow-btn"
        disabled={currentPage === 1}
        onclick={() => {
          currentPage = Math.max(1, currentPage - 1);
          window.scrollTo({ top: 0, behavior: "smooth" });
        }}
      >
        ‹ Trước
      </button>

      <div class="page-numbers">
        {#each Array.from({ length: totalPages }, (_, idx) => idx + 1) as page}
          <button
            type="button"
            class="pagination-btn num-btn {currentPage === page
              ? 'num-active'
              : ''}"
            onclick={() => {
              currentPage = page;
              window.scrollTo({ top: 0, behavior: "smooth" });
            }}
          >
            {page}
          </button>
        {/each}
      </div>

      <button
        type="button"
        class="pagination-btn arrow-btn"
        disabled={currentPage === totalPages}
        onclick={() => {
          currentPage = Math.min(totalPages, currentPage + 1);
          window.scrollTo({ top: 0, behavior: "smooth" });
        }}
      >
        Sau ›
      </button>
    </div>
  {/if}

  <!-- ===== APPLICABLE PRODUCTS SECTION ===== -->
  {#if products.length > 0}
    <div class="applicable-products-wrap">
      <div class="applicable-products-header">
        <h2 class="applicable-products-title">🛍️ Gợi Ý Sản Phẩm Áp Dụng Mã</h2>
        <p class="applicable-products-sub">
          Khám phá ngay bộ sưu tập mỹ phẩm chuẩn Nhật và tận hưởng trọn vẹn
          những đặc quyền ưu đãi dành riêng cho bạn!
        </p>
      </div>

      <div class="applicable-products-grid">
        {#each products.slice(0, 10) as product, i (product.id)}
          <ProductCard {product} index={i} />
        {/each}
      </div>
    </div>
  {/if}
</div>

<style>
  /* ─── PAGE ─────────────────────────────────────── */
  .voucher-page {
    min-height: 100vh;
    background: #f5f5f5;
    padding-bottom: 60px;
  }

  /* ─── RIBBON HEADER ─────────────────────────────── */
  .ribbon-title-container {
    background: transparent;
    padding: 16px 0 8px 0;
    max-width: 1200px;
    margin: 0 auto;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
  }
  .ribbon-title-img {
    max-width: 450px;
    width: 100%;
    height: auto;
    display: block;
    margin: 0 0 12px;
    filter: none;
    border: none;
    outline: none;
    box-shadow: none;
    background: transparent;
    mix-blend-mode: multiply;
  }
  .ribbon-subtitle {
    font-size: 14px;
    color: #777777;
    margin: 0;
    font-weight: 500;
    text-align: left;
  }

  /* ─── TABS ─────────────────────────────────────── */
  .tab-bar {
    display: flex;
    gap: 8px;
    padding: 16px 16px 0;
    max-width: 1200px;
    margin: 0 auto;
  }
  .tab-btn {
    display: flex;
    align-items: center;
    gap: 6px;
    background: #fff;
    border: 1px solid #e0e0e0;
    padding: 8px 18px;
    border-radius: 8px;
    font-size: 13px;
    color: #555;
    font-weight: 750;
    cursor: pointer;
    transition: all 0.2s ease;
  }
  .tab-btn:hover {
    border-color: #ee4d2d;
    color: #ee4d2d;
  }
  .tab-active {
    background: #ee4d2d;
    border-color: #ee4d2d;
    color: #fff;
    box-shadow: 0 4px 14px rgba(238, 77, 45, 0.3);
  }
  .tab-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }

  /* ─── GRID ──────────────────────────────────────── */
  .voucher-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    padding: 20px 16px;
    max-width: 1200px;
    margin: 0 auto;
  }
  @media (max-width: 1024px) {
    .voucher-grid {
      grid-template-columns: repeat(2, 1fr);
    }
  }
  .voucher-card {
    display: flex;
    background: #fff;
    border-radius: 14px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
    overflow: hidden;
    border: 1px solid #f0f0f0;
    transition:
      box-shadow 0.2s ease,
      transform 0.2s ease;
    position: relative;
  }
  .voucher-card:hover {
    box-shadow: 0 8px 24px rgba(0,0,0,0.08);
    transform: translateY(-2px);
  }
  .card-exhausted {
    opacity: 0.65;
  }

  /* ─── CARD PARTS ────────────────────────────────── */
  .card-stub {
    width: 80px;
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 12px 6px;
  }
  .stub-discount {
    background: #ee4d2d;
  }
  .stub-ship {
    background: #ee4d2d;
  }

  .card-stub::after {
    content: "";
    position: absolute;
    right: -5px;
    top: 0;
    bottom: 0;
    width: 10px;
    background-image: radial-gradient(
      circle at right center,
      transparent 4px,
      #ee4d2d 5px
    );
    background-size: 10px 12px;
    background-repeat: repeat-y;
    z-index: 2;
  }
  .stub-svg {
    width: 44px;
    height: 44px;
    filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.12));
  }
  .stub-label {
    font-size: 10px;
    font-weight: 900;
    color: rgba(255, 255, 255, 0.95);
    letter-spacing: 1.5px;
    margin-top: 4px;
  }

  .card-body {
    flex: 1;
    padding: 16px 16px 14px 20px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    position: relative;
  }

  /* ─── CARD CONTENT ──────────────────────────────── */
  .hot-pill {
    position: absolute;
    top: 8px;
    right: 8px;
    background: #ee4d2d;
    color: #fff;
    font-size: 9px;
    font-weight: 900;
    padding: 2px 6px;
    border-radius: 4px;
    letter-spacing: 0.5px;
  }
  .card-title-row {
    margin-bottom: 2px;
  }
  .card-title {
    font-size: 18px;
    font-weight: 900;
    color: #111;
  }
  .exclusive-tag-row {
    margin-bottom: 6px;
  }
  .exclusive-badge {
    display: inline-block;
    font-size: 10px;
    font-weight: 700;
    color: #ee4d2d;
    border: 1.2px solid #ee4d2d;
    border-radius: 4px;
    padding: 2px 6px;
    background: rgba(238, 77, 45, 0.03);
  }
  .card-detail {
    font-size: 11px;
    color: #666;
    margin: 0 0 10px 0;
    line-height: 1.4;
  }

  /* ─── PROGRESS BAR ──────────────────────────────── */
  .usage-status-text {
    font-size: 10px;
    color: #999;
    font-weight: 700;
    margin: 0 0 6px 0;
  }

  /* ─── BUTTONS ───────────────────────────────────── */
  .card-action-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
    margin-top: auto;
  }
  .btn-save {
    background: #ee4d2d;
    color: #fff;
    border: none;
    border-radius: 6px;
    padding: 6px 16px;
    font-size: 12px;
    font-weight: 850;
    cursor: pointer;
    transition: all 0.2s ease;
  }
  .btn-save:hover {
    background: #d63a1e;
  }
  .btn-copied {
    background: #2e7d32 !important;
  }
  .btn-exhausted {
    background: #cccccc;
    color: #555555;
    border: none;
    border-radius: 6px;
    padding: 6px 16px;
    font-size: 12px;
    font-weight: 850;
    cursor: not-allowed;
  }

  .terms-link-btn {
    font-size: 11px;
    color: #2e7d32;
    font-weight: 850;
    background: rgba(46, 125, 50, 0.06);
    border: 1px solid rgba(46, 125, 50, 0.2);
    border-radius: 20px;
    cursor: pointer;
    transition: all 0.2s ease;
    padding: 3px 10px;
    display: inline-flex;
    align-items: center;
    gap: 4px;
  }
  .terms-link-btn:hover {
    background: rgba(46, 125, 50, 0.12);
    border-color: rgba(46, 125, 50, 0.4);
    transform: scale(1.03);
  }

  /* ─── CONDITION OVERLAY ─────────────────────────── */
  .condition-overlay {
    position: absolute;
    inset: 0;
    background: rgba(255, 255, 255, 0.98);
    z-index: 10;
    padding: 14px 16px;
    display: flex;
    animation: fadeIn 0.15s ease-out;
  }
  .condition-box {
    width: 100%;
    display: flex;
    flex-direction: column;
  }
  .condition-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1.5px solid #eee;
    padding-bottom: 6px;
    margin-bottom: 10px;
  }
  .condition-title {
    font-size: 13px;
    font-weight: 900;
    color: #222;
    margin: 0;
  }
  .btn-close-x {
    background: none;
    border: none;
    font-size: 20px;
    color: #aaa;
    cursor: pointer;
    line-height: 1;
    padding: 0 4px;
  }
  .btn-close-x:hover {
    color: #ee4d2d;
  }

  /* Premium Coupon Code Stamp */
  .code-stamp-container {
    margin-bottom: 10px;
    background: #fafafa;
    border: 1px dashed #ddd;
    border-radius: 6px;
    padding: 6px 10px;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  .code-stamp-label {
    font-size: 9px;
    font-weight: 900;
    color: #999;
    letter-spacing: 0.5px;
  }
  .code-stamp-box {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .code-stamp-text {
    font-size: 15px;
    font-weight: 900;
    color: #ee4d2d;
    font-family: "Courier New", Courier, monospace;
    letter-spacing: 0.5px;
  }
  .btn-stamp-copy {
    background: #ee4d2d;
    color: #fff;
    border: none;
    border-radius: 6px;
    padding: 3px 10px;
    font-size: 10px;
    font-weight: 900;
    cursor: pointer;
    transition: background 0.2s;
  }
  .btn-stamp-copy:hover {
    background: #d63a1e;
  }

  .condition-content-scroll {
    flex: 1;
    overflow-y: auto;
    margin-bottom: 10px;
    padding-right: 4px;
  }
  .condition-content-scroll::-webkit-scrollbar {
    width: 4px;
  }
  .condition-content-scroll::-webkit-scrollbar-thumb {
    background: #ddd;
    border-radius: 2px;
  }
  .condition-list {
    margin: 0;
    padding: 0 0 0 16px;
    font-size: 11px;
    color: #555;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .condition-list li {
    line-height: 1.4;
  }
  .btn-close-condition {
    background: #222;
    color: #fff;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 12px;
    font-weight: 900;
    cursor: pointer;
    transition: background 0.2s;
    text-align: center;
    width: 100%;
  }
  .btn-close-condition:hover {
    background: #333;
  }

  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: scale(0.98);
    }
    to {
      opacity: 1;
      transform: scale(1);
    }
  }

  /* ─── SUGGESTIONS SECTION ─────────────────────────── */
  .applicable-products-wrap {
    max-width: 1200px;
    margin: 40px auto 0;
    padding: 0 16px;
  }
  .applicable-products-header {
    margin-bottom: 20px;
    border-bottom: 2px solid #ee4d2d;
    padding-bottom: 8px;
  }
  .applicable-products-title {
    font-size: 18px;
    font-weight: 900;
    color: #111;
    margin: 0 0 4px;
  }
  .applicable-products-sub {
    font-size: 13px;
    color: #666;
    margin: 0;
  }
  .applicable-products-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 12px;
  }
  @media (max-width: 1024px) {
    .applicable-products-grid {
      grid-template-columns: repeat(4, 1fr);
    }
  }
  @media (max-width: 768px) {
    .applicable-products-grid {
      grid-template-columns: repeat(3, 1fr);
    }
  }
  @media (max-width: 480px) {
    .applicable-products-grid {
      grid-template-columns: repeat(2, 1fr);
      gap: 8px;
    }
  }

  /* ─── RESPONSIVE ────────────────────────────────── */
  @media (max-width: 480px) {
    .voucher-grid {
      grid-template-columns: 1fr;
      padding: 16px 12px;
    }
    .tab-bar {
      flex-wrap: wrap;
    }
    .card-stub {
      width: 70px;
      min-width: 70px;
    }
  }
</style>
