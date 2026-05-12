<script lang="ts">
  import { fade, fly, draw } from "svelte/transition";
  import { quintOut } from "svelte/easing";
  import BarChart3 from "@lucide/svelte/icons/bar-chart-3";
  import TrendingUp from "@lucide/svelte/icons/trending-up";
  import DollarSign from "@lucide/svelte/icons/dollar-sign";
  import ShoppingCart from "@lucide/svelte/icons/shopping-cart";
  import Calendar from "@lucide/svelte/icons/calendar";

  let { data } = $props();

  // State
  let activeTab = $state("Ngày");
  const tabs = ["Ngày", "Tháng", "Quý", "Năm"];

  // Data mapping
  let seriesMap: Record<string, any> = $derived({
    Ngày: data?.series_data?.daily,
    Tháng: data?.series_data?.monthly,
    Quý: data?.series_data?.quarterly,
    Năm: data?.series_data?.yearly,
  });

  // Data processing
  let series = $derived(
    seriesMap[activeTab] || { labels: [], revenue: [], orders: [] },
  );
  let labels = $derived(series.labels || []);
  let revenueData = $derived(series.revenue || []);
  let orderData = $derived(series.orders || []);

  // Summary values
  let totalRevenue = $derived(revenueData.reduce((a: number, b: number) => a + b, 0));
  let totalOrders = $derived(orderData.reduce((a: number, b: number) => a + b, 0));
  let avgRevenue = $derived(totalRevenue / (labels.length || 1));

  // Header value: Synchronize with AI's spoken response (injected_count or revenue)
  // Fallback to totalRevenue if data.revenue is missing
  let displayRevenue = $derived(
    data?.injected_count !== undefined ? data.injected_count :
    data?.revenue !== undefined ? data.revenue : totalRevenue,
  );

  // Synchronize with AI's timeframe (V60.1)
  $effect(() => {
    if (data?.raw_timeframe === "this_month") activeTab = "Tháng";
    if (data?.raw_timeframe === "today") activeTab = "Ngày";
    if (data?.raw_timeframe === "this_year") activeTab = "Năm";
  });

  // Dynamic Growth Calculation (V59.3)
  let growth = $derived.by(() => {
    if (revenueData.length < 2) return 0;
    const current = revenueData[revenueData.length - 1];
    const previous = revenueData[revenueData.length - 2] || 1;
    return ((current - previous) / previous) * 100;
  });

  // Chart dimensions (Responsive)
  const width = 800;
  const height = 300;
  const padding = 40;

  // Scales
  let maxRevenue = $derived(Math.max(...revenueData, 1000000) * 1.2);
  let maxOrders = $derived(Math.max(...orderData, 5) * 1.2);

  function getX(index: number) {
    return padding + (index * (width - 2 * padding)) / (labels.length - 1 || 1);
  }

  function getYRevenue(value: number) {
    return height - padding - (value * (height - 2 * padding)) / maxRevenue;
  }

  function getYOrders(value: number) {
    return height - padding - (value * (height - 2 * padding)) / maxOrders;
  }

  // Formatting
  const formatCurrency = (val: number) => {
    if (val >= 1000000) return (val / 1000000).toFixed(1) + "M";
    if (val >= 1000) return (val / 1000).toFixed(0) + "K";
    return val.toString();
  };

  // Header labels
  const tabLabelMap: Record<string, string> = {
    Ngày: "30 ngày gần nhất",
    Tháng: "12 tháng qua",
    Quý: "8 quý gần nhất",
    Năm: "5 năm qua",
  };

  // Header value: Synchronize with AI's spoken response context
  let reportedTotal = $derived(data?.revenue);
  let periodLabel = $derived(data?.period_label || "Báo cáo");
</script>

<div
  class="w-full h-full flex flex-col p-4 sm:p-6 pb-40 font-sans select-none overflow-y-auto"
>
  <!-- Header Section -->
  <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-6 mb-8 shrink-0">
    <div class="flex flex-col gap-1">
      <div class="flex items-center gap-3 mb-1">
        <h2
          class="text-[10px] uppercase tracking-[0.2em] text-emerald-500 font-bold flex items-center gap-2"
        >
          <BarChart3 size={12} />
          Biểu đồ diễn biến
        </h2>
        {#if reportedTotal !== undefined}
          <div
            class="px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-[9px] font-mono text-emerald-400 uppercase tracking-widest animate-pulse truncate max-w-[180px]"
          >
            {periodLabel}: {reportedTotal.toLocaleString("vi-VN")}đ
          </div>
        {/if}
      </div>

      <div class="flex flex-col">
        <div class="flex items-baseline gap-2">
          <span class="text-3xl sm:text-4xl font-black text-white tracking-tighter">
            {displayRevenue.toLocaleString("vi-VN")}
          </span>
          <span class="text-lg text-emerald-500 font-bold">đ</span>
        </div>
        <span
          class="text-[10px] text-zinc-500 font-medium uppercase tracking-widest"
        >
          {data?.revenue !== undefined || data?.injected_count !== undefined 
            ? (data?.period_label || "Doanh thu theo báo cáo")
            : `Tổng doanh thu ${tabLabelMap[activeTab]}`}
        </span>
      </div>
    </div>

    <!-- Timeframe Tabs -->
    <div
      class="flex bg-white/5 p-1 rounded-xl border border-white/10 backdrop-blur-md overflow-x-auto scrollbar-none snap-x"
    >
      {#each tabs as tab}
        <button
          class="flex-1 sm:flex-none px-4 sm:px-5 py-1.5 text-[10px] sm:text-xs font-bold rounded-lg transition-all duration-300 snap-start {activeTab ===
          tab
            ? 'bg-emerald-500 text-black shadow-[0_0_15px_rgba(16,185,129,0.4)]'
            : 'text-zinc-400 hover:text-white'}"
          onclick={() => (activeTab = tab)}
        >
          {tab}
        </button>
      {/each}
    </div>
  </div>

  <!-- Chart Area -->
  <div
    class="w-full aspect-video sm:aspect-[8/3] relative bg-white/[0.02] rounded-3xl border border-white/5 p-4 sm:p-6 overflow-hidden group shrink-0 flex items-center justify-center shadow-inner"
  >
    {#if labels.length > 0}
      <!-- Grid Lines -->
      <svg viewBox="0 0 {width} {height}" class="w-full h-full">
        {#each [0, 0.25, 0.5, 0.75, 1] as tick}
          <line
            x1={padding}
            x2={width - padding}
            y1={getYRevenue(maxRevenue * tick)}
            y2={getYRevenue(maxRevenue * tick)}
            stroke="white"
            stroke-opacity="0.05"
            stroke-dasharray="4"
          />
        {/each}

        <!-- Revenue Bars -->
        {#each revenueData as val, i}
          {@const x = getX(i)}
          {@const y = getYRevenue(val)}
          {@const barWidth =
            ((width - 2 * padding) / (labels.length || 1)) * 0.6}
          <rect
            x={x - barWidth / 2}
            {y}
            width={barWidth}
            height={height - padding - y}
            rx="4"
            fill="url(#barGradient)"
            class="transition-all duration-500 hover:brightness-125 cursor-pointer"
          >
            <title>{labels[i]}: {val.toLocaleString()}đ</title>
          </rect>
        {/each}

        <!-- Order Line -->
        {#if orderData.length > 1}
          {@const d = orderData
            .map(
              (val: number, i: number) =>
                `${i === 0 ? "M" : "L"} ${getX(i)} ${getYOrders(val)}`,
            )
            .join(" ")}
          <path
            {d}
            fill="none"
            stroke="#818cf8"
            stroke-width="3"
            stroke-linecap="round"
            stroke-linejoin="round"
            class="drop-shadow-[0_0_8px_rgba(129,140,248,0.5)]"
            in:draw={{ duration: 1500, easing: quintOut }}
          />
          {#each orderData as val, i}
            <circle
              cx={getX(i)}
              cy={getYOrders(val)}
              r="4"
              fill="#818cf8"
              class="stroke-white/20 stroke-[3px]"
            />
          {/each}
        {/if}

        <!-- X-Axis Labels -->
        {#each labels as label, i}
          {#if labels.length < 15 || i % Math.ceil(labels.length / 8) === 0}
            <text
              x={getX(i)}
              y={height - 10}
              text-anchor="middle"
              class="text-[10px] fill-zinc-500 font-medium"
            >
              {label}
            </text>
          {/if}
        {/each}

        <!-- Gradients -->
        <defs>
          <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#10b981" />
            <stop offset="100%" stop-color="#064e3b" stop-opacity="0.2" />
          </linearGradient>
        </defs>
      </svg>
    {:else}
      <!-- Empty State -->
      <div class="flex flex-col items-center gap-3 opacity-40" in:fade>
        <div class="p-4 rounded-full bg-white/5 border border-white/10">
          <Calendar size={32} class="text-zinc-500" />
        </div>
        <p class="text-xs font-mono uppercase tracking-[0.2em] text-zinc-400">
          Không có dữ liệu cho {activeTab}
        </p>
      </div>
    {/if}
  </div>

  <!-- Legend & Stats Section -->
  <div class="grid grid-cols-1 xs:grid-cols-2 md:grid-cols-3 gap-4 sm:gap-6 mt-8">
    <div
      class="flex items-center gap-4 bg-white/5 p-4 rounded-2xl border border-white/5 hover:bg-white/[0.08] transition-colors"
    >
      <div class="p-3 rounded-xl bg-emerald-500/10 text-emerald-500 shadow-[inset_0_0_10px_rgba(16,185,129,0.1)]">
        <DollarSign size={20} />
      </div>
      <div class="flex flex-col">
        <span
          class="text-[10px] uppercase tracking-widest text-zinc-500 font-bold"
          >TB Doanh thu</span
        >
        <span class="text-lg sm:text-xl font-bold text-white"
          >{formatCurrency(avgRevenue)}</span
        >
      </div>
    </div>

    <div
      class="flex items-center gap-4 bg-white/5 p-4 rounded-2xl border border-white/5 hover:bg-white/[0.08] transition-colors"
    >
      <div class="p-3 rounded-xl bg-indigo-500/10 text-indigo-400 shadow-[inset_0_0_10px_rgba(129,140,248,0.1)]">
        <ShoppingCart size={20} />
      </div>
      <div class="flex flex-col">
        <span
          class="text-[10px] uppercase tracking-widest text-zinc-500 font-bold"
          >Số đơn hàng</span
        >
        <span class="text-lg sm:text-xl font-bold text-white">{totalOrders}</span>
      </div>
    </div>

    <div
      class="flex items-center gap-4 bg-white/5 p-4 rounded-2xl border {growth >=
      0
        ? 'border-emerald-500/20 shadow-[0_0_20px_rgba(16,185,129,0.05)]'
        : 'border-red-500/20 shadow-[0_0_20px_rgba(239,68,68,0.05)]'} hover:brightness-110 transition-all xs:col-span-2 md:col-span-1"
    >
      <div
        class="p-3 rounded-xl {growth >= 0
          ? 'bg-emerald-500'
          : 'bg-red-500'} text-black shadow-lg"
      >
        <TrendingUp size={20} class={growth >= 0 ? "" : "rotate-180"} />
      </div>
      <div class="flex flex-col">
        <span
          class="text-[10px] uppercase tracking-widest {growth >= 0
            ? 'text-emerald-500/80'
            : 'text-red-500/80'} font-extrabold">Tăng trưởng</span
        >
        <span class="text-lg sm:text-xl font-black text-white"
          >{growth >= 0 ? "+" : ""}{growth.toFixed(1)}%</span
        >
      </div>
    </div>
  </div>
</div>

<style>
  .font-sans {
    font-family: "Be Vietnam Pro", "Be Vietnam Pro", sans-serif;
  }
  .scrollbar-none::-webkit-scrollbar {
    display: none;
  }
  .scrollbar-none {
    -ms-overflow-style: none;
    scrollbar-width: none;
  }
</style>
