<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import Bot from "@lucide/svelte/icons/bot";
  import Activity from "@lucide/svelte/icons/activity";
  import ShieldAlert from "@lucide/svelte/icons/shield-alert";
  import Coins from "@lucide/svelte/icons/coins";
  import Globe from "@lucide/svelte/icons/globe";
  import RefreshCw from "@lucide/svelte/icons/refresh-cw";
  import TrendingUp from "@lucide/svelte/icons/trending-up";
  import Shield from "@lucide/svelte/icons/shield";
  import Skull from "@lucide/svelte/icons/skull";
  import UserCheck from "@lucide/svelte/icons/user-check";
  import { fade, fly } from "svelte/transition";

  let metrics = $state({
    orders: {} as Record<string, number>,
    errors: {} as Record<string, number>,
    tokens: {} as Record<string, number>,
    total_errors: 0,
    unique_ips: 0,
    blacklisted_ips: [] as Array<{ ip: string; ttl: number }>,
    infraction_ips: [] as Array<{ ip: string; count: number; ttl: number }>,
    is_shutdown: false
  });

  let loading = $state(true);
  let errorMsg = $state("");
  let lastUpdated = $state("");
  let pollInterval: ReturnType<typeof setInterval> | undefined;

  // Manual IP block inputs
  let blockIpInput = $state("");
  let blockDurationInput = $state(86400); // 24 hours in seconds
  let actionLoading = $state(false);

  // Deriving values
  let sandboxOrders = $derived(metrics.orders?.sandbox || 0);
  let realOrders = $derived(metrics.orders?.real || 0);
  let totalOrders = $derived(sandboxOrders + realOrders);
  let totalErrors = $derived(metrics.total_errors || 0);
  
  let conversionRate = $derived(
    totalOrders + totalErrors > 0 
      ? Math.round((realOrders / (totalOrders + totalErrors)) * 100) 
      : 0
  );

  let estimatedRevenue = $derived(realOrders * 450000); // 450.000 VND average order value
  let inputTokens = $derived(metrics.tokens?.input || 0);
  let outputTokens = $derived(metrics.tokens?.output || 0);
  let estimatedCostUSD = $derived(
    ((inputTokens * 0.075) + (outputTokens * 0.30)) / 1000000
  );

  let progressPercentage = $derived(
    Math.min((estimatedCostUSD / 20) * 100, 100)
  );

  let budgetStatus = $derived(
    metrics.is_shutdown 
      ? "SHUTDOWN" 
      : estimatedCostUSD >= 15.0 
        ? "CRITICAL" 
        : estimatedCostUSD >= 5.0 
          ? "WARNING" 
          : "NORMAL"
  );

  async function fetchMetrics() {
    try {
      loading = true;
      const res = await fetch("/api/v1/client/mcp/metrics");
      if (!res.ok) {
        throw new Error(`Failed to fetch metrics: ${res.status}`);
      }
      const data = await res.json();
      if (data.status === "success") {
        metrics = data.metrics;
        errorMsg = "";
      } else {
        errorMsg = data.message || "Unknown error";
      }
    } catch (e: unknown) {
      console.error(e);
      errorMsg = e instanceof Error ? e.message : "Failed to load agent telemetry";
    } finally {
      loading = false;
      lastUpdated = new Date().toLocaleTimeString();
    }
  }

  async function blacklistIP(ipToBlock: string, durationSecs: number) {
    if (!ipToBlock.trim()) return;
    try {
      actionLoading = true;
      const res = await fetch("/api/v1/client/mcp/blacklist", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ ip: ipToBlock.trim(), duration: durationSecs })
      });
      const data = await res.json();
      if (res.ok && data.status === "success") {
        blockIpInput = "";
        await fetchMetrics();
      } else {
        alert(data.message || "Failed to blacklist IP");
      }
    } catch (e) {
      alert("Error: " + e);
    } finally {
      actionLoading = false;
    }
  }

  async function whitelistIP(ipToUnblock: string) {
    if (!confirm(`Bạn có chắc muốn mở chặn cho IP: ${ipToUnblock}?`)) return;
    try {
      actionLoading = true;
      const res = await fetch("/api/v1/client/mcp/whitelist", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ ip: ipToUnblock })
      });
      const data = await res.json();
      if (res.ok && data.status === "success") {
        await fetchMetrics();
      } else {
        alert(data.message || "Failed to whitelist IP");
      }
    } catch (e) {
      alert("Error: " + e);
    } finally {
      actionLoading = false;
    }
  }

  async function reopenGateway() {
    if (!confirm("Bạn có chắc muốn kích hoạt lại cổng A2A và khôi phục bộ đếm ngân sách?")) return;
    try {
      actionLoading = true;
      const res = await fetch("/api/v1/client/mcp/reopen", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        }
      });
      const data = await res.json();
      if (res.ok && data.status === "success") {
        await fetchMetrics();
      } else {
        alert(data.message || "Failed to reopen gateway");
      }
    } catch (e) {
      alert("Error: " + e);
    } finally {
      actionLoading = false;
    }
  }

  onMount(() => {
    fetchMetrics();
    pollInterval = setInterval(fetchMetrics, 10000); // refresh every 10s
  });

  onDestroy(() => {
    if (pollInterval) clearInterval(pollInterval);
  });
</script>

<div 
  class="relative w-full py-6 px-0 transition-all duration-700"
  in:fade={{ duration: 800 }}
>
  <div class="relative z-10 w-full">
    <!-- Header -->
    <div class="flex items-center justify-between mb-8 pb-4 border-b border-white/10">
      <div class="flex items-center gap-4">
        <div class="p-3 bg-white/5 border border-white/10 transition-colors">
          <Bot size={24} class="text-white group-hover:text-amber-400 transition-colors" />
        </div>
        <div>
          <h2 class="text-xl font-bold tracking-tight text-white uppercase">AI Agent Telemetry</h2>
          <p class="text-[10px] font-mono text-gray-500 tracking-[0.2em] uppercase">Agent-to-Agent & Gateway Dashboard</p>
        </div>
      </div>
      
      <div class="flex items-center gap-4">
        <span class="text-[10px] font-mono text-gray-500 uppercase">Updated: {lastUpdated || 'loading...'}</span>
        <button 
          onclick={fetchMetrics} 
          disabled={loading}
          class="p-2.5 bg-white/5 hover:bg-white/10 active:scale-95 disabled:opacity-50 transition-all border border-white/10"
        >
          <RefreshCw size={12} class="text-gray-400 hover:text-white {loading ? 'animate-spin' : ''}" />
        </button>
      </div>
    </div>

    <!-- Main Content -->
    {#if errorMsg}
      <div class="p-4 bg-red-950/20 border border-red-500/20 text-red-400 text-xs font-mono mb-6">
        {errorMsg}
      </div>
    {/if}

    {#if metrics.is_shutdown}
      <div 
        class="p-5 bg-red-950/20 border-l-4 border-red-500 text-red-200 text-xs font-mono mb-8 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4"
        in:fade={{ duration: 300 }}
      >
        <div class="space-y-1">
          <div class="flex items-center gap-2 font-bold text-red-400 uppercase text-sm">
            <ShieldAlert size={16} />
            HỆ THỐNG A2A GATEWAY ĐÃ BỊ KHÓA TỰ ĐỘNG!
          </div>
          <p class="text-[10px] text-gray-400 uppercase leading-relaxed">
            Tổng chi phí LLM Token tiêu thụ đã vượt ngưỡng ngân sách bảo vệ tối đa ($20.00). Cổng A2A đã tạm dừng hoạt động để tránh bị spam phá hoại tài khoản.
          </p>
        </div>
        <button
          type="button"
          disabled={actionLoading}
          onclick={reopenGateway}
          class="shrink-0 py-2.5 px-5 bg-red-500 hover:bg-red-600 disabled:opacity-50 text-white font-bold uppercase tracking-wider text-[10px] border border-red-400 transition-all active:scale-95"
        >
          {actionLoading ? 'Đang kích hoạt...' : 'Kích Hoạt Lại Cổng A2A'}
        </button>
      </div>
    {/if}

    <!-- Bento Grid Layout -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      
      <!-- Card 1: Conversion & Orders (Bento Large) -->
      <div class="lg:col-span-2 bg-[#121212] border-t-2 border-cyan-500/50 p-6 flex flex-col justify-between h-44 hover:bg-[#161616] transition-all">
        <div class="flex justify-between items-start">
          <div class="flex items-center gap-2">
            <Activity size={16} class="text-cyan-400" />
            <span class="text-[10px] font-bold text-gray-400 tracking-wider uppercase">AI Orders Status</span>
          </div>
          <span class="text-[9px] font-mono font-bold text-cyan-400 tracking-wider bg-cyan-500/10 px-2.5 py-0.5">LIVE</span>
        </div>
        <div>
          <div class="text-4xl font-extrabold text-white tracking-tight mb-2">
            {realOrders} <span class="text-sm font-normal text-gray-500">/ {totalOrders} total</span>
          </div>
          <div class="text-[10px] text-gray-400 flex gap-4 font-mono uppercase">
            <span class="text-emerald-400">● {realOrders} Real</span>
            <span class="text-amber-400">○ {sandboxOrders} Sandbox</span>
          </div>
        </div>
      </div>

      <!-- Card 2: Generated Revenue (Bento Large) -->
      <div class="lg:col-span-2 bg-[#121212] border-t-2 border-emerald-500/50 p-6 flex flex-col justify-between h-44 hover:bg-[#161616] transition-all">
        <div class="flex justify-between items-start">
          <div class="flex items-center gap-2">
            <TrendingUp size={16} class="text-emerald-400" />
            <span class="text-[10px] font-bold text-gray-400 tracking-wider uppercase">AI Generated Revenue</span>
          </div>
          <span class="text-[9px] font-mono font-bold text-emerald-400 tracking-wider bg-emerald-500/10 px-2.5 py-0.5">+{conversionRate}% CR</span>
        </div>
        <div>
          <div class="text-4xl font-extrabold text-emerald-400 tracking-tight mb-2">
            {estimatedRevenue.toLocaleString('vi-VN')} <span class="text-sm font-normal text-gray-500 uppercase">VND</span>
          </div>
          <p class="text-[10px] text-gray-400 font-mono uppercase">Avg order value: 450.000đ</p>
        </div>
      </div>

      <!-- Card 3: LLM Cost & Budget Monitoring (Bento Large) -->
      <div class="lg:col-span-2 bg-[#121212] border-t-2 border-purple-500/50 p-6 flex flex-col justify-between h-44 hover:bg-[#161616] transition-all">
        <div class="flex justify-between items-start">
          <div class="flex items-center gap-2">
            <Coins size={16} class="text-purple-400" />
            <span class="text-[10px] font-bold text-gray-400 tracking-wider uppercase">Giám Sát Ngân Sách LLM</span>
          </div>
          <span class="text-[9px] font-mono font-bold tracking-wider px-2.5 py-0.5 uppercase
            {budgetStatus === 'SHUTDOWN' ? 'bg-red-500/15 text-red-400 border border-red-500/20' : 
             budgetStatus === 'CRITICAL' ? 'bg-orange-500/15 text-orange-400 border border-orange-500/20' : 
             budgetStatus === 'WARNING' ? 'bg-amber-500/15 text-amber-400 border border-amber-500/20' : 
             'bg-purple-500/15 text-purple-400 border border-purple-500/10'}"
          >
            {budgetStatus}
          </span>
        </div>
        
        <div class="my-1">
          <div class="flex justify-between items-baseline mb-1">
            <div class="text-3xl font-extrabold text-white tracking-tight">
              ${estimatedCostUSD.toFixed(4)}
              <span class="text-xs font-normal text-gray-500">/ $20.00</span>
            </div>
            <span class="text-xs font-mono text-gray-400">{progressPercentage.toFixed(1)}%</span>
          </div>
          
          <!-- Progress Bar -->
          <div class="w-full h-1.5 bg-white/5 rounded-full overflow-hidden mb-2">
            <div 
              class="h-full rounded-full transition-all duration-500
                {budgetStatus === 'SHUTDOWN' ? 'bg-red-500' : 
                 budgetStatus === 'CRITICAL' ? 'bg-orange-500' : 
                 budgetStatus === 'WARNING' ? 'bg-amber-500' : 
                 'bg-purple-500'}"
              style="width: {progressPercentage}%"
            ></div>
          </div>
        </div>

        <div class="text-[9px] text-gray-500 font-mono flex justify-between uppercase">
          <span>Tokens: {((inputTokens + outputTokens) / 1000).toFixed(1)}k (In: {(inputTokens / 1000).toFixed(1)}k)</span>
          <span class="text-gray-400">Ngưỡng: $5 | $10 | $15 | $20</span>
        </div>
      </div>

      <!-- Card 4: Agent Node Network (Bento Small) -->
      <div class="lg:col-span-2 bg-[#121212] border-t-2 border-amber-500/50 p-6 flex flex-col justify-between h-44 hover:bg-[#161616] transition-all">
        <div class="flex justify-between items-start">
          <div class="flex items-center gap-2">
            <Globe size={16} class="text-amber-400" />
            <span class="text-[10px] font-bold text-gray-400 tracking-wider uppercase">Agent Nodes network</span>
          </div>
          <span class="text-[9px] font-mono font-bold text-amber-400 tracking-wider bg-amber-500/10 px-2.5 py-0.5">ACTIVE</span>
        </div>
        <div>
          <div class="text-4xl font-extrabold text-white tracking-tight mb-2">
            {metrics.unique_ips} <span class="text-sm font-normal text-gray-500 uppercase">nodes</span>
          </div>
          <p class="text-[10px] text-gray-400 font-mono uppercase">Security: API Key Authenticated</p>
        </div>
      </div>

    </div>

    <!-- Error Logs Telemetry -->
    <div class="mt-8 bg-[#121212] border-l-2 border-red-500/50 p-6">
      <div class="flex justify-between items-center mb-6">
        <div class="flex items-center gap-2">
          <ShieldAlert size={16} class="text-red-400" />
          <span class="text-xs font-bold text-gray-300 tracking-wider uppercase">Agent Error Mappings</span>
        </div>
        <span class="text-[10px] font-mono text-red-400 bg-red-950/20 border border-red-500/15 px-3 py-1 uppercase">
          Total Mapped Failures: {totalErrors}
        </span>
      </div>

      {#if Object.keys(metrics.errors || {}).length > 0}
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {#each Object.entries(metrics.errors) as [errCode, count]}
            <div class="bg-black/20 border border-white/5 p-4 flex justify-between items-center">
              <div>
                <div class="text-[9px] font-mono text-gray-500 uppercase">{errCode.replace('_', ' ')}</div>
                <div class="text-xl font-bold text-white tracking-tight mt-1">{count}</div>
              </div>
              <span class="text-[9px] px-2 py-0.5 bg-red-500/10 text-red-400 border border-red-500/10 uppercase font-mono">ERR</span>
            </div>
          {/each}
        </div>
      {:else}
        <p class="text-left text-gray-500 text-xs font-mono uppercase py-4">
          No agent errors logged in the current telemetry window.
        </p>
      {/if}
    </div>

    <!-- Security Shield & Access Control -->
    <div class="mt-8 bg-[#121212] border-l-2 border-amber-500/50 p-6">
      <div class="flex justify-between items-center mb-8 pb-4 border-b border-white/5">
        <div class="flex items-center gap-2">
          <Shield size={16} class="text-amber-500" />
          <span class="text-xs font-bold text-gray-300 tracking-wider uppercase">Security Shield & Access Control</span>
        </div>
        <div class="flex gap-4">
          <span class="text-[10px] font-mono text-amber-500 bg-amber-950/20 border border-amber-500/15 px-3 py-1 uppercase">
            Blacklisted: {metrics.blacklisted_ips?.length || 0}
          </span>
          <span class="text-[10px] font-mono text-red-400 bg-red-950/20 border border-red-500/15 px-3 py-1 uppercase">
            Active Infractions: {metrics.infraction_ips?.length || 0}
          </span>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        <!-- Column 1: Manual Block Form -->
        <div class="bg-transparent lg:border-r border-white/5 pr-0 lg:pr-8 flex flex-col justify-between">
          <div>
            <h3 class="text-xs font-bold text-gray-400 uppercase mb-4 flex items-center gap-2">
              <Skull size={14} class="text-red-400" />
              Chặn Địa Chỉ IP
            </h3>
            <p class="text-[10px] text-gray-500 mb-6 leading-relaxed uppercase font-mono">
              Thủ công chặn một địa chỉ IP truy cập vào hệ thống A2A/MCP Gateway để ngăn chặn tấn công spam hoặc phá hoại.
            </p>
            
            <div class="space-y-4">
              <div>
                <label for="ip-address" class="text-[9px] font-mono text-gray-500 uppercase block mb-1">IP Address</label>
                <input 
                  id="ip-address"
                  type="text" 
                  placeholder="e.g. 192.168.1.100" 
                  bind:value={blockIpInput}
                  disabled={actionLoading}
                  class="w-full bg-transparent border-b border-white/20 px-0 py-2 text-xs font-mono text-white focus:outline-none focus:border-white transition-colors"
                />
              </div>

              <div>
                <label for="block-duration" class="text-[9px] font-mono text-gray-500 uppercase block mb-1">Thời Gian Khóa</label>
                <select 
                  id="block-duration"
                  bind:value={blockDurationInput}
                  disabled={actionLoading}
                  class="w-full bg-transparent border-b border-white/20 px-0 py-2 text-xs text-white focus:outline-none focus:border-white transition-colors"
                >
                  <option value={3600} style="background-color: #121212; color: #ffffff;">1 Giờ</option>
                  <option value={43200} style="background-color: #121212; color: #ffffff;">12 Giờ</option>
                  <option value={86400} style="background-color: #121212; color: #ffffff;">24 Giờ (1 Ngày)</option>
                  <option value={604800} style="background-color: #121212; color: #ffffff;">7 Ngày</option>
                  <option value={2592000} style="background-color: #121212; color: #ffffff;">30 Ngày</option>
                </select>
              </div>
            </div>
          </div>

          <button 
            type="button"
            onclick={() => blacklistIP(blockIpInput, blockDurationInput)}
            disabled={actionLoading || !blockIpInput}
            class="w-full mt-8 bg-red-950/20 hover:bg-red-950/40 active:scale-[0.98] disabled:opacity-30 disabled:pointer-events-none transition-all border border-red-500/20 text-red-400 font-bold text-xs py-2.5 px-0 flex items-center justify-center gap-2 uppercase tracking-wider"
          >
            {actionLoading ? 'Đang xử lý...' : 'Thực Thi Chặn IP'}
          </button>
        </div>

        <!-- Column 2: Active Blacklist -->
        <div class="bg-transparent lg:border-r border-white/5 px-0 lg:px-8">
          <h3 class="text-xs font-bold text-gray-400 uppercase mb-4 flex items-center gap-2">
            <Shield size={14} class="text-amber-400" />
            Danh Sách Bị Chặn ({metrics.blacklisted_ips?.length || 0})
          </h3>
          
          <div class="space-y-3 max-h-[240px] overflow-y-auto custom-scrollbar pr-2">
            {#if metrics.blacklisted_ips && metrics.blacklisted_ips.length > 0}
              {#each metrics.blacklisted_ips as bl}
                <div class="bg-transparent border-b border-white/5 py-3 flex justify-between items-center transition-all hover:border-amber-500/20" in:fly={{ y: 10, duration: 400 }}>
                  <div>
                    <div class="text-xs font-mono font-bold text-white">{bl.ip}</div>
                    <div class="text-[9px] font-mono text-gray-500 uppercase mt-0.5">
                      Hết hạn: {bl.ttl > 0 ? `${Math.ceil(bl.ttl / 3600)}h` : 'Vĩnh viễn'}
                    </div>
                  </div>
                  <button 
                    type="button"
                    onclick={() => whitelistIP(bl.ip)}
                    disabled={actionLoading}
                    class="py-1 px-3 bg-emerald-500/10 hover:bg-emerald-500/20 active:scale-95 transition-all border border-emerald-500/20 text-emerald-400 flex items-center gap-1.5"
                    title="Mở khóa IP"
                  >
                    <UserCheck size={11} />
                    <span class="text-[9px] font-bold uppercase tracking-wider">Mở</span>
                  </button>
                </div>
              {/each}
            {:else}
              <p class="text-left py-10 text-gray-500 text-xs font-mono uppercase italic">
                Chưa có IP nào bị chặn.
              </p>
            {/if}
          </div>
        </div>

        <!-- Column 3: Active Infractions -->
        <div class="bg-transparent pl-0 lg:pl-8">
          <h3 class="text-xs font-bold text-gray-400 uppercase mb-4 flex items-center gap-2">
            <ShieldAlert size={14} class="text-red-400" />
            IP Báo Vi Phạm ({metrics.infraction_ips?.length || 0})
          </h3>
          
          <div class="space-y-3 max-h-[240px] overflow-y-auto custom-scrollbar pr-2">
            {#if metrics.infraction_ips && metrics.infraction_ips.length > 0}
              {#each metrics.infraction_ips as inf}
                <div class="bg-transparent border-b border-white/5 py-3 flex justify-between items-center transition-all hover:border-red-500/20" in:fly={{ y: 10, duration: 400 }}>
                  <div>
                    <div class="text-xs font-mono font-bold text-white">{inf.ip}</div>
                    <div class="text-[9px] font-mono flex items-center gap-1.5 mt-0.5 uppercase">
                      <span class="text-red-400">Vi phạm: {inf.count}/3</span>
                      <span class="text-gray-600">•</span>
                      <span class="text-gray-500">Reset: {inf.ttl}s</span>
                    </div>
                  </div>
                  <button 
                    type="button"
                    onclick={() => blacklistIP(inf.ip, 86400)}
                    disabled={actionLoading}
                    class="py-1 px-3 bg-red-500/10 hover:bg-red-500/20 active:scale-95 transition-all border border-red-500/20 text-red-400 flex items-center gap-1.5"
                    title="Khóa ngay lập tức"
                  >
                    <Skull size={11} />
                    <span class="text-[9px] font-bold uppercase tracking-wider">Khóa</span>
                  </button>
                </div>
              {/each}
            {:else}
              <p class="text-left py-10 text-gray-500 text-xs font-mono uppercase italic">
                Không ghi nhận địa chỉ IP vi phạm.
              </p>
            {/if}
          </div>
        </div>

      </div>
    </div>
  </div>
</div>

<style>
  .custom-scrollbar::-webkit-scrollbar {
    width: 3px;
  }
  .custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.1);
  }
  .custom-scrollbar::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.25);
  }
</style>
